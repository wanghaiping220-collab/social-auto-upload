"""
抖音平台服务
"""
import asyncio
from typing import Dict, Any, Tuple, Optional
from playwright.async_api import Page

from backend.services.base import BasePlatformService
from backend.utils.logger import get_logger

logger = get_logger("douyin")


class DouyinService(BasePlatformService):
    """抖音平台服务"""

    PLATFORM_NAME = "douyin"
    LOGIN_URL = "https://creator.douyin.com/"
    CREATOR_URL = "https://creator.douyin.com/creator-micro/home"
    PUBLISH_URL = "https://creator.douyin.com/creator-micro/content/upload"

    async def check_login_status(self, page: Page) -> Dict[str, Any]:
        """检查抖音登录状态"""
        try:
            current_url = page.url

            # 检查是否在登录页面
            if "login" in current_url.lower() or "passport" in current_url.lower():
                # 检查是否有扫码成功的提示
                scanned_element = await page.query_selector(".qrcode-scaned, .scan-success")
                if scanned_element:
                    return {"status": "scanned"}

                # 检查二维码是否过期
                expired_element = await page.query_selector(".qrcode-expired, .refresh-btn")
                if expired_element:
                    return {"status": "expired"}

                return {"status": "waiting"}

            # 已登录，获取用户信息
            user_info = await self.get_user_info(page)
            return {
                "status": "confirmed",
                "user_info": user_info
            }

        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return {"status": "waiting"}

    async def get_user_info(self, page: Page) -> Dict[str, Any]:
        """获取抖音用户信息"""
        try:
            # 等待用户信息加载
            await page.wait_for_selector(".creator-avatar, .user-avatar", timeout=10000)

            # 获取头像
            avatar_element = await page.query_selector(".creator-avatar img, .user-avatar img")
            avatar_url = await avatar_element.get_attribute("src") if avatar_element else ""

            # 获取昵称
            nickname_element = await page.query_selector(".creator-name, .user-name")
            nickname = await nickname_element.inner_text() if nickname_element else ""

            return {
                "username": "",
                "nickname": nickname.strip(),
                "avatar_url": avatar_url
            }

        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return {"username": "", "nickname": "", "avatar_url": ""}

    async def upload_video(
        self,
        page: Page,
        video_path: str,
        title: str,
        description: str = "",
        tags: list = None,
        cover_path: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """上传视频到抖音"""
        try:
            logger.info(f"开始上传视频到抖音: {video_path}")

            # 等待上传按钮出现
            upload_button = await page.wait_for_selector(
                "input[type='file'], .upload-btn input",
                timeout=15000
            )

            # 上传视频文件
            await upload_button.set_input_files(video_path)
            logger.info("视频文件已选择，等待上传...")

            # 等待上传完成
            await page.wait_for_selector(
                ".upload-success, .progress-success, [class*='success']",
                timeout=300000  # 5分钟超时
            )
            logger.info("视频上传完成")

            # 等待页面跳转到编辑页面
            await asyncio.sleep(3)

            # 填写标题
            title_input = await page.query_selector(
                "input[placeholder*='标题'], textarea[placeholder*='标题'], .title-input input"
            )
            if title_input:
                await title_input.fill("")
                await title_input.fill(title[:80])  # 抖音标题限制80字
                logger.info(f"已填写标题: {title[:80]}")

            # 填写描述/文案
            if description:
                desc_input = await page.query_selector(
                    "textarea[placeholder*='描述'], textarea[placeholder*='文案'], .desc-input textarea"
                )
                if desc_input:
                    await desc_input.fill("")
                    await desc_input.fill(description[:500])
                    logger.info("已填写描述")

            # 添加话题标签
            if tags:
                for tag in tags[:5]:  # 最多5个标签
                    tag_input = await page.query_selector(
                        "input[placeholder*='话题'], .topic-input input"
                    )
                    if tag_input:
                        await tag_input.fill(f"#{tag}")
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(0.5)
                logger.info(f"已添加话题标签: {tags[:5]}")

            # 上传封面
            if cover_path:
                cover_btn = await page.query_selector(
                    ".cover-upload input[type='file'], .change-cover input"
                )
                if cover_btn:
                    await cover_btn.set_input_files(cover_path)
                    await asyncio.sleep(2)
                    logger.info("已上传封面")

            # 点击发布按钮
            await asyncio.sleep(2)
            publish_btn = await page.query_selector(
                "button:has-text('发布'), .publish-btn, [class*='publish']"
            )
            if publish_btn:
                await publish_btn.click()
                logger.info("已点击发布按钮")

            # 等待发布完成
            await asyncio.sleep(5)

            # 检查是否发布成功
            success_element = await page.query_selector(
                ".publish-success, [class*='success'], .toast-success"
            )

            if success_element:
                logger.info("视频发布成功")
                return True, "发布成功", None
            else:
                # 检查错误信息
                error_element = await page.query_selector(".error-msg, .toast-error")
                if error_element:
                    error_text = await error_element.inner_text()
                    return False, f"发布失败: {error_text}", None

                return True, "发布请求已提交", None

        except Exception as e:
            error_msg = f"上传视频失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None


# 单例
douyin_service = DouyinService()
