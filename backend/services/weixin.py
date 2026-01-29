"""
微信视频号平台服务
"""
import asyncio
from typing import Dict, Any, Tuple, Optional
from playwright.async_api import Page

from backend.services.base import BasePlatformService
from backend.utils.logger import get_logger

logger = get_logger("weixin")


class WeixinVideoService(BasePlatformService):
    """微信视频号平台服务"""

    PLATFORM_NAME = "weixin"
    LOGIN_URL = "https://channels.weixin.qq.com/login"
    CREATOR_URL = "https://channels.weixin.qq.com/platform"
    PUBLISH_URL = "https://channels.weixin.qq.com/platform/post/create"

    async def check_login_status(self, page: Page) -> Dict[str, Any]:
        """检查视频号登录状态"""
        try:
            current_url = page.url

            # 检查是否在登录页面
            if "login" in current_url.lower():
                # 检查是否有扫码成功的提示
                scanned_element = await page.query_selector(
                    ".login__type__container__scan-suc, .scan-success"
                )
                if scanned_element:
                    return {"status": "scanned"}

                # 检查二维码是否过期
                expired_element = await page.query_selector(
                    ".login__type__container__ing__refresh, .qrcode-expired"
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
        """获取视频号用户信息"""
        try:
            await asyncio.sleep(2)

            # 获取头像
            avatar_element = await page.query_selector(
                ".finder-nickname-img, .header-avatar img, .avatar img"
            )
            avatar_url = ""
            if avatar_element:
                avatar_url = await avatar_element.get_attribute("src") or ""

            # 获取昵称
            nickname_element = await page.query_selector(
                ".finder-nickname, .header-nickname, .nickname"
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
        """上传视频到视频号"""
        try:
            logger.info(f"开始上传视频到视频号: {video_path}")

            # 等待上传区域出现
            upload_area = await page.wait_for_selector(
                ".post-uploader, input[type='file']",
                timeout=15000
            )

            # 找到文件输入框
            file_input = await page.query_selector("input[type='file'][accept*='video']")
            if not file_input:
                file_input = await page.query_selector("input[type='file']")

            if file_input:
                await file_input.set_input_files(video_path)
                logger.info("视频文件已选择，等待上传...")

            # 等待上传完成
            await page.wait_for_selector(
                ".uploader-progress-success, .upload-success, [class*='upload-done']",
                timeout=300000
            )
            logger.info("视频上传完成")

            await asyncio.sleep(3)

            # 填写描述（视频号把标题和描述合并）
            content = title
            if description:
                content = f"{title}\n\n{description}"

            desc_input = await page.query_selector(
                ".weui-desktop-form-common__textarea, textarea[placeholder*='描述'], .post-desc textarea"
            )
            if desc_input:
                await desc_input.fill("")
                await desc_input.fill(content[:1000])  # 视频号限制1000字
                logger.info("已填写描述")

            # 添加话题标签
            if tags:
                tag_content = " ".join([f"#{tag}" for tag in tags[:10]])
                current_content = await desc_input.input_value() if desc_input else ""
                if desc_input:
                    await desc_input.fill(f"{current_content}\n{tag_content}")
                logger.info(f"已添加话题标签")

            # 上传封面
            if cover_path:
                cover_btn = await page.query_selector(
                    ".cover-uploader input[type='file'], .change-cover input"
                )
                if cover_btn:
                    await cover_btn.set_input_files(cover_path)
                    await asyncio.sleep(2)
                    logger.info("已上传封面")

            # 点击发布按钮
            await asyncio.sleep(2)
            publish_btn = await page.query_selector(
                ".weui-desktop-btn_primary, button:has-text('发表'), .post-btn"
            )
            if publish_btn:
                await publish_btn.click()
                logger.info("已点击发布按钮")

            # 等待发布完成
            await asyncio.sleep(5)

            # 检查是否发布成功
            success_element = await page.query_selector(
                ".publish-success, .weui-desktop-dialog__title:has-text('成功')"
            )

            if success_element or "platform" in page.url:
                logger.info("视频发布成功")
                return True, "发布成功", None
            else:
                error_element = await page.query_selector(
                    ".weui-desktop-dialog__title, .error-msg"
                )
                if error_element:
                    error_text = await error_element.inner_text()
                    if "失败" in error_text or "错误" in error_text:
                        return False, f"发布失败: {error_text}", None

                return True, "发布请求已提交", None

        except Exception as e:
            error_msg = f"上传视频失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None


# 单例
weixin_service = WeixinVideoService()
