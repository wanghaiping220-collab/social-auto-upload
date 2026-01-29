"""
日志管理路由
"""
import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import SystemLog
from backend.schemas import LogResponse, LogQuery
from backend.utils.logger import LOG_DIR

router = APIRouter(prefix="/logs", tags=["日志管理"])


@router.get("", response_model=List[LogResponse])
async def get_logs(
    level: Optional[str] = Query(None, description="日志级别 (DEBUG, INFO, WARNING, ERROR)"),
    module: Optional[str] = Query(None, description="模块名"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取系统日志"""
    query = db.query(SystemLog)

    if level:
        query = query.filter(SystemLog.level == level.upper())

    if module:
        query = query.filter(SystemLog.module.contains(module))

    if start_time:
        query = query.filter(SystemLog.created_at >= start_time)

    if end_time:
        query = query.filter(SystemLog.created_at <= end_time)

    logs = query.order_by(desc(SystemLog.created_at)).offset(offset).limit(limit).all()

    return logs


@router.get("/recent")
async def get_recent_logs(
    minutes: int = Query(30, ge=1, le=1440, description="最近多少分钟"),
    level: Optional[str] = Query(None, description="日志级别"),
    db: Session = Depends(get_db)
):
    """获取最近的日志"""
    start_time = datetime.utcnow() - timedelta(minutes=minutes)

    query = db.query(SystemLog).filter(SystemLog.created_at >= start_time)

    if level:
        query = query.filter(SystemLog.level == level.upper())

    logs = query.order_by(desc(SystemLog.created_at)).limit(500).all()

    return [
        {
            "id": log.id,
            "level": log.level,
            "module": log.module,
            "message": log.message,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]


@router.get("/files")
async def get_log_files():
    """获取日志文件列表"""
    if not os.path.exists(LOG_DIR):
        return {"files": []}

    files = []
    for filename in os.listdir(LOG_DIR):
        filepath = os.path.join(LOG_DIR, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            files.append({
                "name": filename,
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    files.sort(key=lambda x: x["modified_at"], reverse=True)

    return {"files": files}


@router.get("/files/{filename}")
async def download_log_file(filename: str):
    """下载日志文件"""
    filepath = os.path.join(LOG_DIR, filename)

    if not os.path.exists(filepath):
        return {"error": "文件不存在"}

    # 安全检查：确保文件在LOG_DIR内
    if not os.path.abspath(filepath).startswith(os.path.abspath(LOG_DIR)):
        return {"error": "无效的文件路径"}

    return FileResponse(
        filepath,
        media_type="text/plain",
        filename=filename
    )


@router.get("/stats")
async def get_log_stats(
    hours: int = Query(24, ge=1, le=168, description="统计最近多少小时"),
    db: Session = Depends(get_db)
):
    """获取日志统计"""
    start_time = datetime.utcnow() - timedelta(hours=hours)

    # 按级别统计
    from sqlalchemy import func

    level_stats = db.query(
        SystemLog.level,
        func.count(SystemLog.id).label("count")
    ).filter(
        SystemLog.created_at >= start_time
    ).group_by(SystemLog.level).all()

    # 按模块统计
    module_stats = db.query(
        SystemLog.module,
        func.count(SystemLog.id).label("count")
    ).filter(
        SystemLog.created_at >= start_time
    ).group_by(SystemLog.module).order_by(
        desc(func.count(SystemLog.id))
    ).limit(10).all()

    return {
        "time_range": {
            "start": start_time.isoformat(),
            "end": datetime.utcnow().isoformat(),
            "hours": hours
        },
        "by_level": {stat.level: stat.count for stat in level_stats},
        "by_module": {stat.module or "unknown": stat.count for stat in module_stats}
    }


@router.delete("/clear")
async def clear_old_logs(
    days: int = Query(30, ge=1, le=365, description="清理多少天前的日志"),
    db: Session = Depends(get_db)
):
    """清理旧日志"""
    cutoff = datetime.utcnow() - timedelta(days=days)

    deleted = db.query(SystemLog).filter(SystemLog.created_at < cutoff).delete()
    db.commit()

    return {
        "message": f"已清理 {deleted} 条日志",
        "cutoff_date": cutoff.isoformat()
    }
