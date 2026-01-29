"""
Pydantic 数据模式定义
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 账号相关 ====================

class AccountBase(BaseModel):
    """账号基础模式"""
    platform: str = Field(..., description="平台类型: douyin, weixin, xiaohongshu")
    nickname: Optional[str] = Field(None, description="昵称")


class AccountCreate(AccountBase):
    """创建账号"""
    pass


class AccountUpdate(BaseModel):
    """更新账号"""
    nickname: Optional[str] = None
    status: Optional[str] = None


class AccountResponse(AccountBase):
    """账号响应"""
    id: int
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 内容相关 ====================

class ContentBase(BaseModel):
    """内容基础模式"""
    title: str = Field(..., min_length=1, max_length=500, description="标题")
    description: Optional[str] = Field(None, description="文案描述")
    tags: Optional[List[str]] = Field(None, description="话题标签")


class ContentCreate(ContentBase):
    """创建内容"""
    video_path: Optional[str] = None
    cover_path: Optional[str] = None


class ContentUpdate(BaseModel):
    """更新内容"""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    video_path: Optional[str] = None
    cover_path: Optional[str] = None


class ContentResponse(ContentBase):
    """内容响应"""
    id: int
    video_path: Optional[str] = None
    cover_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 发布任务相关 ====================

class PublishTaskBase(BaseModel):
    """发布任务基础模式"""
    content_id: int
    account_id: int


class PublishTaskCreate(PublishTaskBase):
    """创建发布任务"""
    scheduled_at: Optional[datetime] = None


class BatchPublishCreate(BaseModel):
    """批量发布创建"""
    content_ids: List[int] = Field(..., description="内容ID列表")
    account_ids: List[int] = Field(..., description="账号ID列表")
    scheduled_at: Optional[datetime] = None


class PublishTaskResponse(PublishTaskBase):
    """发布任务响应"""
    id: int
    status: str
    error_message: Optional[str] = None
    published_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    content: Optional[ContentResponse] = None
    account: Optional[AccountResponse] = None

    class Config:
        from_attributes = True


# ==================== 批量操作相关 ====================

class BatchContentCreate(BaseModel):
    """批量创建内容"""
    items: List[ContentCreate] = Field(..., description="内容列表")


class BatchUpdateTitle(BaseModel):
    """批量更新标题"""
    content_ids: List[int] = Field(..., description="内容ID列表")
    title_template: str = Field(..., description="标题模板，支持 {index} 占位符")


class BatchUpdateTags(BaseModel):
    """批量更新话题标签"""
    content_ids: List[int] = Field(..., description="内容ID列表")
    tags: List[str] = Field(..., description="话题标签列表")


class BatchUpdateDescription(BaseModel):
    """批量更新文案"""
    content_ids: List[int] = Field(..., description="内容ID列表")
    description: str = Field(..., description="文案内容")


# ==================== 二维码登录相关 ====================

class QRCodeResponse(BaseModel):
    """二维码响应"""
    qrcode_url: str = Field(..., description="二维码图片URL (base64)")
    session_id: str = Field(..., description="会话ID")
    platform: str = Field(..., description="平台类型")


class QRCodeStatusResponse(BaseModel):
    """二维码状态响应"""
    status: str = Field(..., description="状态: waiting, scanned, confirmed, expired")
    account_id: Optional[int] = Field(None, description="登录成功后的账号ID")
    message: Optional[str] = None


# ==================== 日志相关 ====================

class LogResponse(BaseModel):
    """日志响应"""
    id: int
    level: str
    module: Optional[str] = None
    message: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LogQuery(BaseModel):
    """日志查询"""
    level: Optional[str] = None
    module: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    """消息响应"""
    message: str
    success: bool = True


class PaginatedResponse(BaseModel):
    """分页响应"""
    total: int
    items: List
    page: int
    page_size: int
