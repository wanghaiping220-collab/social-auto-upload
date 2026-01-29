"""
小红书平台服务
"""
import asyncio
from typing import Dict, Any, Tuple, Optional
from playwright.async_api import Page

from backend.services.base import BasePlatformService
from backend.utils.logger import get_logger

logger = get_logger("xiaohongshu")


class XiaohongshuService(BasePlatformService):
    """小红书平台服务"""

    PLATFORM_NAME = "xiaohongshu"
    LOGIN_URL = "https://creator.xiaohongshu.com/login"
    CREATOR_URL = "https://creator.xiaohongshu.com/creator/home"
    PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"

    async def check_login_status(self, page: Page) -> Dict[str, Any]:
        """检查小红书登录状态"""
        try:
            current_url = page.url

            # 检查是否在登录页面
            if "login" in current_url.lower():
                # 检查是否有扫码成功的提示
                scanned_element = await page.query_selector(
                    ".scan-success, .qrcode-scanned"
                )
                if scanned_element:
                    return {"status": "scanned"}

                # 检查二维码是否过期
                expired_element = await page.query_selector(
                    ".qrcode-expired, .refresh-qrcode"
                )
                if expired_element:
                    expired_visible = await expired_element.is_visible()
                    if expired_visible:
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
        """获取小红书用户信息"""
        try:
            await asyncio.sleep(2)

            # 获取头像
            avatar_element = await page.query_selector(
                ".user-avatar img, .creator-avatar img, .avatar img"
            )
            avatar_url = ""
            if avatar_element:
                avatar_url = await avatar_element.get_attribute("src") or ""

            # 获取昵称
            nickname_element = await page.query_selector(
                ".user-name, .creator-name, .nickname"
            )
            nickname = ""
            if nickname_element:
                nickname = await nickname_element.inner_text()

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
        """上传视频到小红书"""
        try:
            logger.info(f"开始上传视频到小红书: {video_path}")

            # 点击发布视频选项（如果需要）
            video_tab = await page.query_selector(
                ".publish-tab-video, [data-type='video'], button:has-text('视频')"
            )
            if video_tab:
                await video_tab.click()
                await asyncio.sleep(1)

            # 找到文件输入框
            file_input = await page.wait_for_selector(
                "input[type='file'][accept*='video'], input[type='file']",
                timeout=15000
            )

            if file_input:
                await file_input.set_input_files(video_path)
                logger.info("视频文件已选择，等待上传...")

            # 等待上传完成
            await page.wait_for_selector(
                ".upload-success, .progress-complete, [class*='upload-done']",
                timeout=300000
            )
            logger.info("视频上传完成")

            await asyncio.sleep(3)

            # 填写标题
            title_input = await page.query_selector(
                "input[placeholder*='标题'], .title-input input, #title"
            )
            if title_input:
                await title_input.fill("")
                await title_input.fill(title[:20])  # 小红书标题限制20字
                logger.info(f"已填写标题: {title[:20]}")

            # 填写描述
            desc_input = await page.query_selector(
                "textarea[placeholder*='描述'], .desc-input textarea, #desc"
            )
            if desc_input:
                full_desc = description or ""
                if tags:
                    tag_str = " ".join([f"#{tag}" for tag in tags[:10]])
                    full_desc = f"{full_desc}\n\n{tag_str}" if full_desc else tag_str

                await desc_input.fill("")
                await desc_input.fill(full_desc[:1000])
                logger.info("已填写描述和话题")

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
                "button:has-text('发布'), .publish-btn, .submit-btn"
            )
            if publish_btn:
                await publish_btn.click()
                logger.info("已点击发布按钮")

            # 等待发布完成
            await asyncio.sleep(5)

            # 检查是否发布成功
            success_element = await page.query_selector(
                ".publish-success, .success-tip, [class*='success']"
            )

            if success_element or "home" in page.url or "creator" in page.url:
                logger.info("视频发布成功")
                return True, "发布成功", None
            else:
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
xiaohongshu_service = XiaohongshuService()
