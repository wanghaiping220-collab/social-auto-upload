"""
浏览器自动化工具模块
使用 Playwright 实现浏览器控制
"""
import os
import asyncio
import base64
from typing import Optional, Dict, Any, Callable
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from backend.utils.logger import get_logger

logger = get_logger("browser")

# 浏览器用户数据目录
USER_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "browser_data")
os.makedirs(USER_DATA_DIR, exist_ok=True)


class BrowserManager:
    """浏览器管理器"""

    _instance = None
    _playwright = None
    _browser: Optional[Browser] = None
    _contexts: Dict[str, BrowserContext] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self):
        """初始化浏览器"""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            logger.info("Playwright 已初始化")

        if self._browser is None:
            self._browser = await self._playwright.chromium.launch(
                headless=False,  # 非无头模式，方便用户扫码
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
            logger.info("Chromium 浏览器已启动")

    async def get_context(self, context_id: str, platform: str) -> BrowserContext:
        """
        获取或创建浏览器上下文

        Args:
            context_id: 上下文ID (通常用账号ID)
            platform: 平台名称

        Returns:
            BrowserContext
        """
        await self.initialize()

        key = f"{platform}_{context_id}"

        if key not in self._contexts:
            # 创建独立的上下文，支持持久化cookies
            context_dir = os.path.join(USER_DATA_DIR, key)
            os.makedirs(context_dir, exist_ok=True)

            context = await self._browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )

            # 注入反检测脚本
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // 修改 plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // 修改 languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh']
                });
            """)

            self._contexts[key] = context
            logger.info(f"创建浏览器上下文: {key}")

        return self._contexts[key]

    async def close_context(self, context_id: str, platform: str):
        """关闭浏览器上下文"""
        key = f"{platform}_{context_id}"
        if key in self._contexts:
            await self._contexts[key].close()
            del self._contexts[key]
            logger.info(f"关闭浏览器上下文: {key}")

    async def save_cookies(self, context: BrowserContext) -> str:
        """保存cookies为JSON字符串"""
        import json
        cookies = await context.cookies()
        return json.dumps(cookies, ensure_ascii=False)

    async def load_cookies(self, context: BrowserContext, cookies_json: str):
        """从JSON字符串加载cookies"""
        import json
        cookies = json.loads(cookies_json)
        await context.add_cookies(cookies)

    async def screenshot_to_base64(self, page: Page) -> str:
        """截图并转为base64"""
        screenshot = await page.screenshot()
        return base64.b64encode(screenshot).decode("utf-8")

    async def close(self):
        """关闭所有资源"""
        for key, context in list(self._contexts.items()):
            await context.close()
            logger.info(f"关闭上下文: {key}")

        self._contexts.clear()

        if self._browser:
            await self._browser.close()
            self._browser = None
            logger.info("浏览器已关闭")

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            logger.info("Playwright 已停止")


class QRCodeLoginSession:
    """二维码登录会话"""

    def __init__(
        self,
        session_id: str,
        platform: str,
        browser_manager: BrowserManager
    ):
        self.session_id = session_id
        self.platform = platform
        self.browser_manager = browser_manager
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.status = "initializing"  # initializing, waiting, scanned, confirmed, expired, error
        self.qrcode_base64: Optional[str] = None
        self.cookies: Optional[str] = None
        self.user_info: Dict[str, Any] = {}
        self._check_task: Optional[asyncio.Task] = None

    async def start(self, qrcode_url: str, check_callback: Callable):
        """
        启动登录会话

        Args:
            qrcode_url: 登录页面URL
            check_callback: 状态检查回调函数
        """
        try:
            self.context = await self.browser_manager.get_context(
                self.session_id,
                self.platform
            )
            self.page = await self.context.new_page()

            await self.page.goto(qrcode_url, wait_until="networkidle")

            # 等待二维码出现
            await asyncio.sleep(2)

            # 截取二维码区域
            self.qrcode_base64 = await self.browser_manager.screenshot_to_base64(self.page)
            self.status = "waiting"

            logger.info(f"二维码登录会话已启动: {self.session_id}")

            # 启动状态检查任务
            self._check_task = asyncio.create_task(
                self._check_login_status(check_callback)
            )

        except Exception as e:
            self.status = "error"
            logger.error(f"启动登录会话失败: {e}")
            raise

    async def _check_login_status(self, check_callback: Callable):
        """检查登录状态"""
        max_wait = 120  # 最长等待2分钟
        waited = 0

        while waited < max_wait and self.status in ["waiting", "scanned"]:
            try:
                result = await check_callback(self.page)

                if result["status"] == "scanned" and self.status == "waiting":
                    self.status = "scanned"
                    logger.info(f"二维码已被扫描: {self.session_id}")

                elif result["status"] == "confirmed":
                    self.status = "confirmed"
                    self.cookies = await self.browser_manager.save_cookies(self.context)
                    self.user_info = result.get("user_info", {})
                    logger.info(f"登录成功: {self.session_id}")
                    return

                elif result["status"] == "expired":
                    self.status = "expired"
                    logger.warning(f"二维码已过期: {self.session_id}")
                    return

            except Exception as e:
                logger.error(f"检查登录状态异常: {e}")

            await asyncio.sleep(2)
            waited += 2

        if self.status not in ["confirmed", "expired"]:
            self.status = "expired"
            logger.warning(f"登录超时: {self.session_id}")

    async def close(self):
        """关闭会话"""
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass

        if self.page:
            await self.page.close()

        await self.browser_manager.close_context(self.session_id, self.platform)

        logger.info(f"登录会话已关闭: {self.session_id}")


# 全局浏览器管理器实例
browser_manager = BrowserManager()


# 导出
__all__ = [
    "browser_manager",
    "BrowserManager",
    "QRCodeLoginSession"
]
