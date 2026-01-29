"""
数据库模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from backend.database import Base


class PlatformType(str, enum.Enum):
    """平台类型"""
    DOUYIN = "douyin"           # 抖音
    WEIXIN_VIDEO = "weixin"     # 视频号
    XIAOHONGSHU = "xiaohongshu" # 小红书


class AccountStatus(str, enum.Enum):
    """账号状态"""
    ACTIVE = "active"           # 活跃
    INACTIVE = "inactive"       # 未登录
    EXPIRED = "expired"         # 登录过期
    BANNED = "banned"           # 被封禁


class PublishStatus(str, enum.Enum):
    """发布状态"""
    PENDING = "pending"         # 待发布
    UPLOADING = "uploading"     # 上传中
    PUBLISHED = "published"     # 已发布
    FAILED = "failed"           # 发布失败
    SCHEDULED = "scheduled"     # 定时发布


class Account(Base):
    """账号模型"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)  # 平台类型
    username = Column(String(255), nullable=True)  # 用户名
    nickname = Column(String(255), nullable=True)  # 昵称
    avatar_url = Column(Text, nullable=True)       # 头像URL
    cookies = Column(Text, nullable=True)          # 登录cookies (JSON格式)
    status = Column(String(50), default=AccountStatus.INACTIVE.value)  # 账号状态
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)  # 最后登录时间

    # 关联关系
    publish_tasks = relationship("PublishTask", back_populates="account")

    def __repr__(self):
        return f"<Account(id={self.id}, platform={self.platform}, nickname={self.nickname})>"


class Content(Base):
    """内容模型"""
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)    # 标题
    description = Column(Text, nullable=True)       # 文案描述
    tags = Column(Text, nullable=True)              # 话题标签 (JSON数组)
    video_path = Column(Text, nullable=True)        # 视频文件路径
    cover_path = Column(Text, nullable=True)        # 封面图片路径
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    publish_tasks = relationship("PublishTask", back_populates="content")

    def __repr__(self):
        return f"<Content(id={self.id}, title={self.title})>"


class PublishTask(Base):
    """发布任务模型"""
    __tablename__ = "publish_tasks"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    status = Column(String(50), default=PublishStatus.PENDING.value)  # 发布状态
    error_message = Column(Text, nullable=True)     # 错误信息
    published_url = Column(Text, nullable=True)     # 发布后的链接
    scheduled_at = Column(DateTime, nullable=True)  # 定时发布时间
    published_at = Column(DateTime, nullable=True)  # 实际发布时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    content = relationship("Content", back_populates="publish_tasks")
    account = relationship("Account", back_populates="publish_tasks")

    def __repr__(self):
        return f"<PublishTask(id={self.id}, status={self.status})>"


class SystemLog(Base):
    """系统日志模型"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)      # 日志级别
    module = Column(String(100), nullable=True)     # 模块名
    message = Column(Text, nullable=False)          # 日志消息
    details = Column(Text, nullable=True)           # 详细信息 (JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.level})>"
