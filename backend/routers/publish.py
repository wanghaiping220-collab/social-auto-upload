"""
发布管理路由
"""
import json
import asyncio
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Account, Content, PublishTask, PublishStatus, AccountStatus
from backend.schemas import (
    PublishTaskCreate, PublishTaskResponse, BatchPublishCreate, MessageResponse
)
from backend.services.douyin import douyin_service
from backend.services.weixin import weixin_service
from backend.services.xiaohongshu import xiaohongshu_service
from backend.utils.logger import get_logger, log_publish

logger = get_logger("publish")

router = APIRouter(prefix="/publish", tags=["发布管理"])

# 平台服务映射
PLATFORM_SERVICES = {
    "douyin": douyin_service,
    "weixin": weixin_service,
    "xiaohongshu": xiaohongshu_service
}


@router.get("/tasks", response_model=List[PublishTaskResponse])
async def get_publish_tasks(
    status: str = None,
    account_id: int = None,
    content_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取发布任务列表"""
    query = db.query(PublishTask)

    if status:
        query = query.filter(PublishTask.status == status)

    if account_id:
        query = query.filter(PublishTask.account_id == account_id)

    if content_id:
        query = query.filter(PublishTask.content_id == content_id)

    tasks = query.order_by(PublishTask.created_at.desc()).offset(skip).limit(limit).all()

    return tasks


@router.get("/tasks/{task_id}", response_model=PublishTaskResponse)
async def get_publish_task(task_id: int, db: Session = Depends(get_db)):
    """获取单个发布任务详情"""
    task = db.query(PublishTask).filter(PublishTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.post("/tasks", response_model=PublishTaskResponse)
async def create_publish_task(
    data: PublishTaskCreate,
    db: Session = Depends(get_db)
):
    """创建单个发布任务"""
    # 验证内容和账号存在
    content = db.query(Content).filter(Content.id == data.content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    account = db.query(Account).filter(Account.id == data.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    task = PublishTask(
        content_id=data.content_id,
        account_id=data.account_id,
        status=PublishStatus.PENDING.value,
        scheduled_at=data.scheduled_at
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.post("/batch", response_model=MessageResponse)
async def create_batch_publish_tasks(
    data: BatchPublishCreate,
    db: Session = Depends(get_db)
):
    """批量创建发布任务"""
    created_count = 0

    for content_id in data.content_ids:
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            continue

        for account_id in data.account_ids:
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                continue

            # 检查是否已存在相同的待发布任务
            existing = db.query(PublishTask).filter(
                PublishTask.content_id == content_id,
                PublishTask.account_id == account_id,
                PublishTask.status.in_([PublishStatus.PENDING.value, PublishStatus.UPLOADING.value])
            ).first()

            if existing:
                continue

            task = PublishTask(
                content_id=content_id,
                account_id=account_id,
                status=PublishStatus.PENDING.value,
                scheduled_at=data.scheduled_at
            )
            db.add(task)
            created_count += 1

    db.commit()

    return MessageResponse(
        message=f"成功创建 {created_count} 个发布任务",
        success=True
    )


async def execute_publish_task(task_id: int, db: Session):
    """执行单个发布任务"""
    task = db.query(PublishTask).filter(PublishTask.id == task_id).first()
    if not task:
        return

    account = db.query(Account).filter(Account.id == task.account_id).first()
    content = db.query(Content).filter(Content.id == task.content_id).first()

    if not account or not content:
        task.status = PublishStatus.FAILED.value
        task.error_message = "账号或内容不存在"
        db.commit()
        return

    if account.status != AccountStatus.ACTIVE.value:
        task.status = PublishStatus.FAILED.value
        task.error_message = "账号未登录或已过期"
        db.commit()
        return

    if not account.cookies:
        task.status = PublishStatus.FAILED.value
        task.error_message = "账号登录信息无效"
        db.commit()
        return

    # 更新状态为上传中
    task.status = PublishStatus.UPLOADING.value
    db.commit()

    try:
        service = PLATFORM_SERVICES.get(account.platform)
        if not service:
            raise Exception(f"不支持的平台: {account.platform}")

        # 解析标签
        tags = json.loads(content.tags) if content.tags else []

        # 执行发布
        success, message, video_url = await service.publish_content(
            account_id=account.id,
            cookies=account.cookies,
            video_path=content.video_path,
            title=content.title,
            description=content.description or "",
            tags=tags,
            cover_path=content.cover_path,
            content_id=content.id
        )

        if success:
            task.status = PublishStatus.PUBLISHED.value
            task.published_url = video_url
            task.published_at = datetime.utcnow()
        else:
            task.status = PublishStatus.FAILED.value
            task.error_message = message

    except Exception as e:
        task.status = PublishStatus.FAILED.value
        task.error_message = str(e)
        logger.error(f"发布任务执行失败: {e}")

    task.updated_at = datetime.utcnow()
    db.commit()


@router.post("/execute/{task_id}", response_model=MessageResponse)
async def execute_single_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """执行单个发布任务"""
    task = db.query(PublishTask).filter(PublishTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status not in [PublishStatus.PENDING.value, PublishStatus.FAILED.value]:
        raise HTTPException(status_code=400, detail="任务状态不允许执行")

    # 在后台执行
    background_tasks.add_task(execute_publish_task, task_id, db)

    return MessageResponse(message="任务已开始执行", success=True)


@router.post("/execute-all", response_model=MessageResponse)
async def execute_all_pending_tasks(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """执行所有待发布任务（一键发布）"""
    pending_tasks = db.query(PublishTask).filter(
        PublishTask.status == PublishStatus.PENDING.value
    ).all()

    if not pending_tasks:
        return MessageResponse(message="没有待发布的任务", success=True)

    # 按账号分组，避免同一账号并发操作
    tasks_by_account = {}
    for task in pending_tasks:
        if task.account_id not in tasks_by_account:
            tasks_by_account[task.account_id] = []
        tasks_by_account[task.account_id].append(task.id)

    async def execute_account_tasks(account_id: int, task_ids: List[int]):
        """顺序执行同一账号的任务"""
        for task_id in task_ids:
            await execute_publish_task(task_id, db)
            await asyncio.sleep(5)  # 任务间隔5秒

    # 为每个账号创建后台任务
    for account_id, task_ids in tasks_by_account.items():
        background_tasks.add_task(execute_account_tasks, account_id, task_ids)

    return MessageResponse(
        message=f"已开始执行 {len(pending_tasks)} 个发布任务",
        success=True
    )


@router.post("/retry/{task_id}", response_model=MessageResponse)
async def retry_failed_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """重试失败的任务"""
    task = db.query(PublishTask).filter(PublishTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != PublishStatus.FAILED.value:
        raise HTTPException(status_code=400, detail="只能重试失败的任务")

    # 重置状态
    task.status = PublishStatus.PENDING.value
    task.error_message = None
    db.commit()

    # 在后台执行
    background_tasks.add_task(execute_publish_task, task_id, db)

    return MessageResponse(message="任务已重新加入队列", success=True)


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
async def delete_publish_task(task_id: int, db: Session = Depends(get_db)):
    """删除发布任务"""
    task = db.query(PublishTask).filter(PublishTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.delete(task)
    db.commit()

    return MessageResponse(message="任务已删除", success=True)


@router.get("/stats")
async def get_publish_stats(db: Session = Depends(get_db)):
    """获取发布统计"""
    total = db.query(PublishTask).count()
    pending = db.query(PublishTask).filter(PublishTask.status == PublishStatus.PENDING.value).count()
    uploading = db.query(PublishTask).filter(PublishTask.status == PublishStatus.UPLOADING.value).count()
    published = db.query(PublishTask).filter(PublishTask.status == PublishStatus.PUBLISHED.value).count()
    failed = db.query(PublishTask).filter(PublishTask.status == PublishStatus.FAILED.value).count()

    return {
        "total": total,
        "pending": pending,
        "uploading": uploading,
        "published": published,
        "failed": failed
    }
