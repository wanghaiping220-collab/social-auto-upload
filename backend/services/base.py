"""
平台服务基类
"""
import os
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from playwright.async_api import Page, BrowserContext

from backend.utils.logger import get_logger, log_publish, log_account
from backend.utils.browser import browser_manager, QRCodeLoginSession


class BasePlatformService(ABC):
    """平台服务基类"""

    # 平台名称
    PLATFORM_NAME: str = "base"
    # 登录页面URL
    LOGIN_URL: str = ""
    # 创作者中心URL
    CREATOR_URL: str = ""
    # 发布页面URL
    PUBLISH_URL: str = ""

    def __init__(self):
        self.logger = get_logger(self.PLATFORM_NAME)
        self.browser_manager = browser_manager

    async def create_login_session(self, session_id: str) -> QRCodeLoginSession:
        """
        创建登录会话

        Args:
            session_id: 会话ID

        Returns:
            QRCodeLoginSession
        """
        session = QRCodeLoginSession(
            session_id=session_id,
            platform=self.PLATFORM_NAME,
            browser_manager=self.browser_manager
        )

        await session.start(
            qrcode_url=self.LOGIN_URL,
            check_callback=self.check_login_status
        )

        return session

    @abstractmethod
    async def check_login_status(self, page: Page) -> Dict[str, Any]:
        """
        检查登录状态

        Args:
            page: 浏览器页面

        Returns:
            {"status": "waiting|scanned|confirmed|expired", "user_info": {...}}
        """
        pass

    @abstractmethod
    async def get_user_info(self, page: Page) -> Dict[str, Any]:
        """
        获取用户信息

        Args:
            page: 浏览器页面

        Returns:
            {"username": str, "nickname": str, "avatar_url": str}
        """
        pass

    @abstractmethod
    async def upload_video(
        self,
        page: Page,
        video_path: str,
        title: str,
        description: str = "",
        tags: list = None,
        cover_path: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        上传视频

        Args:
            page: 浏览器页面
            video_path: 视频文件路径
            title: 标题
            description: 文案描述
            tags: 话题标签列表
            cover_path: 封面图片路径

        Returns:
            (success: bool, message: str, video_url: Optional[str])
        """
        pass

    async def publish_content(
        self,
        account_id: int,
        cookies: str,
        video_path: str,
        title: str,
        description: str = "",
        tags: list = None,
        cover_path: str = None,
        content_id: int = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        发布内容

        Args:
            account_id: 账号ID
            cookies: Cookies JSON字符串
            video_path: 视频文件路径
            title: 标题
            description: 文案描述
            tags: 话题标签
            cover_path: 封面图片路径
            content_id: 内容ID

        Returns:
            (success: bool, message: str, video_url: Optional[str])
        """
        context = None
        page = None

        try:
            # 获取浏览器上下文
            context = await self.browser_manager.get_context(
                str(account_id),
                self.PLATFORM_NAME
            )

            # 加载cookies
            await self.browser_manager.load_cookies(context, cookies)

            # 打开发布页面
            page = await context.new_page()
            await page.goto(self.PUBLISH_URL, wait_until="networkidle")

            # 等待页面加载
            await asyncio.sleep(2)

            # 检查登录状态
            login_check = await self.check_login_status(page)
            if login_check["status"] != "confirmed":
                log_publish(
                    self.PLATFORM_NAME,
                    account_id,
                    content_id or 0,
                    "failed",
                    error="账号登录已过期"
                )
                return False, "账号登录已过期，请重新登录", None

            # 上传视频
            success, message, video_url = await self.upload_video(
                page=page,
                video_path=video_path,
                title=title,
                description=description,
                tags=tags or [],
                cover_path=cover_path
            )

            if success:
                log_publish(
                    self.PLATFORM_NAME,
                    account_id,
                    content_id or 0,
                    "published",
                    url=video_url
                )
            else:
                log_publish(
                    self.PLATFORM_NAME,
                    account_id,
                    content_id or 0,
                    "failed",
                    error=message
                )

            return success, message, video_url

        except Exception as e:
            error_msg = f"发布失败: {str(e)}"
            self.logger.error(error_msg)
            log_publish(
                self.PLATFORM_NAME,
                account_id,
                content_id or 0,
                "failed",
                error=error_msg
            )
            return False, error_msg, None

        finally:
            if page:
                await page.close()

    async def check_account_status(self, cookies: str) -> Tuple[bool, str]:
        """
        检查账号状态

        Args:
            cookies: Cookies JSON字符串

        Returns:
            (is_valid: bool, message: str)
        """
        context = None
        page = None

        try:
            context = await self.browser_manager.get_context(
                "check_status",
                self.PLATFORM_NAME
            )

            await self.browser_manager.load_cookies(context, cookies)

            page = await context.new_page()
            await page.goto(self.CREATOR_URL, wait_until="networkidle")

            await asyncio.sleep(2)

            result = await self.check_login_status(page)

            if result["status"] == "confirmed":
                return True, "账号状态正常"
            else:
                return False, "账号登录已过期"

        except Exception as e:
            return False, f"检查失败: {str(e)}"

        finally:
            if page:
                await page.close()
            await self.browser_manager.close_context("check_status", self.PLATFORM_NAME)
