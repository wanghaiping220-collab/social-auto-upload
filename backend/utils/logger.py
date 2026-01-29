"""
日志配置模块
使用 loguru 提供强大的日志功能
"""
import os
import sys
import json
from datetime import datetime
from loguru import logger
from typing import Optional

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 移除默认处理器
logger.remove()

# 控制台输出格式
console_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# 文件输出格式
file_format = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level: <8} | "
    "{name}:{function}:{line} | "
    "{message}"
)

# 添加控制台处理器
logger.add(
    sys.stderr,
    format=console_format,
    level="INFO",
    colorize=True
)

# 添加文件处理器 - 常规日志
logger.add(
    os.path.join(LOG_DIR, "app_{time:YYYY-MM-DD}.log"),
    format=file_format,
    level="DEBUG",
    rotation="00:00",  # 每天轮转
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩旧日志
    encoding="utf-8"
)

# 添加文件处理器 - 错误日志
logger.add(
    os.path.join(LOG_DIR, "error_{time:YYYY-MM-DD}.log"),
    format=file_format,
    level="ERROR",
    rotation="00:00",
    retention="90 days",
    compression="zip",
    encoding="utf-8"
)


class DatabaseLogHandler:
    """数据库日志处理器"""

    def __init__(self):
        self._db = None

    def set_db(self, db_session):
        """设置数据库会话"""
        self._db = db_session

    def write(self, message):
        """写入日志到数据库"""
        if self._db is None:
            return

        try:
            from backend.models import SystemLog
            record = message.record
            log_entry = SystemLog(
                level=record["level"].name,
                module=record["name"],
                message=record["message"],
                details=json.dumps({
                    "function": record["function"],
                    "line": record["line"],
                    "file": record["file"].name if record["file"] else None,
                    "extra": dict(record["extra"])
                }, ensure_ascii=False)
            )
            self._db.add(log_entry)
            self._db.commit()
        except Exception as e:
            # 避免日志处理器异常导致程序崩溃
            pass


# 全局数据库日志处理器实例
db_log_handler = DatabaseLogHandler()


def get_logger(name: str = "app"):
    """获取命名的日志器"""
    return logger.bind(name=name)


def log_operation(
    operation: str,
    module: str,
    status: str = "success",
    details: Optional[dict] = None,
    error: Optional[str] = None
):
    """
    记录操作日志

    Args:
        operation: 操作名称
        module: 模块名
        status: 状态 (success/failed/warning)
        details: 详细信息
        error: 错误信息
    """
    log = get_logger(module)

    message = f"[{operation}] status={status}"

    if details:
        message += f" details={json.dumps(details, ensure_ascii=False)}"

    if error:
        message += f" error={error}"

    if status == "success":
        log.info(message)
    elif status == "warning":
        log.warning(message)
    else:
        log.error(message)


def log_publish(
    platform: str,
    account_id: int,
    content_id: int,
    status: str,
    error: Optional[str] = None,
    url: Optional[str] = None
):
    """
    记录发布日志

    Args:
        platform: 平台名称
        account_id: 账号ID
        content_id: 内容ID
        status: 发布状态
        error: 错误信息
        url: 发布后的URL
    """
    log = get_logger("publish")

    details = {
        "platform": platform,
        "account_id": account_id,
        "content_id": content_id,
        "status": status
    }

    if url:
        details["url"] = url

    message = f"[发布] platform={platform} account={account_id} content={content_id} status={status}"

    if error:
        message += f" error={error}"
        log.error(message)
    elif status == "published":
        message += f" url={url}"
        log.success(message)
    else:
        log.info(message)


def log_account(
    operation: str,
    platform: str,
    account_id: Optional[int] = None,
    status: str = "success",
    error: Optional[str] = None
):
    """
    记录账号操作日志

    Args:
        operation: 操作类型 (login/logout/create/delete/update)
        platform: 平台名称
        account_id: 账号ID
        status: 状态
        error: 错误信息
    """
    log = get_logger("account")

    message = f"[账号{operation}] platform={platform}"

    if account_id:
        message += f" account_id={account_id}"

    message += f" status={status}"

    if error:
        message += f" error={error}"
        log.error(message)
    else:
        log.info(message)


# 导出
__all__ = [
    "logger",
    "get_logger",
    "log_operation",
    "log_publish",
    "log_account",
    "db_log_handler",
    "LOG_DIR"
]
