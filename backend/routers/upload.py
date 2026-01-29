"""
内容上传管理路由
"""
import os
import json
import uuid
import shutil
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Content
from backend.schemas import (
    ContentCreate, ContentUpdate, ContentResponse,
    BatchContentCreate, BatchUpdateTitle, BatchUpdateTags,
    BatchUpdateDescription, MessageResponse
)
from backend.utils.logger import get_logger, log_operation

logger = get_logger("upload")

router = APIRouter(prefix="/contents", tags=["内容管理"])

# 视频存储目录
VIDEO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "videos")
os.makedirs(VIDEO_DIR, exist_ok=True)


@router.get("", response_model=List[ContentResponse])
async def get_contents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取内容列表"""
    contents = db.query(Content).order_by(Content.created_at.desc()).offset(skip).limit(limit).all()

    # 解析tags字段
    result = []
    for content in contents:
        content_dict = {
            "id": content.id,
            "title": content.title,
            "description": content.description,
            "tags": json.loads(content.tags) if content.tags else [],
            "video_path": content.video_path,
            "cover_path": content.cover_path,
            "created_at": content.created_at,
            "updated_at": content.updated_at
        }
        result.append(content_dict)

    return result


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: int, db: Session = Depends(get_db)):
    """获取单个内容详情"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    return {
        "id": content.id,
        "title": content.title,
        "description": content.description,
        "tags": json.loads(content.tags) if content.tags else [],
        "video_path": content.video_path,
        "cover_path": content.cover_path,
        "created_at": content.created_at,
        "updated_at": content.updated_at
    }


@router.post("/upload")
async def upload_videos(
    files: List[UploadFile] = File(...),
    titles: str = Form(None),  # JSON数组字符串
    descriptions: str = Form(None),  # JSON数组字符串
    tags: str = Form(None),  # JSON数组字符串 (每个元素也是数组)
    db: Session = Depends(get_db)
):
    """
    批量上传视频文件

    Args:
        files: 视频文件列表
        titles: 标题列表 (JSON数组)
        descriptions: 描述列表 (JSON数组)
        tags: 标签列表 (JSON二维数组)
    """
    try:
        # 解析参数
        title_list = json.loads(titles) if titles else []
        desc_list = json.loads(descriptions) if descriptions else []
        tag_list = json.loads(tags) if tags else []

        created_contents = []

        for i, file in enumerate(files):
            # 生成唯一文件名
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(VIDEO_DIR, unique_filename)

            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # 获取对应的标题、描述、标签
            title = title_list[i] if i < len(title_list) else os.path.splitext(file.filename)[0]
            description = desc_list[i] if i < len(desc_list) else ""
            content_tags = tag_list[i] if i < len(tag_list) else []

            # 创建内容记录
            content = Content(
                title=title,
                description=description,
                tags=json.dumps(content_tags, ensure_ascii=False),
                video_path=file_path
            )
            db.add(content)
            db.commit()
            db.refresh(content)

            created_contents.append({
                "id": content.id,
                "title": content.title,
                "video_path": content.video_path
            })

            logger.info(f"上传视频成功: {file.filename} -> {content.id}")

        log_operation("upload_videos", "upload", status="success",
                     details={"count": len(created_contents)})

        return {
            "success": True,
            "message": f"成功上传 {len(created_contents)} 个视频",
            "contents": created_contents
        }

    except Exception as e:
        log_operation("upload_videos", "upload", status="failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("", response_model=ContentResponse)
async def create_content(data: ContentCreate, db: Session = Depends(get_db)):
    """创建内容记录（不上传文件）"""
    content = Content(
        title=data.title,
        description=data.description,
        tags=json.dumps(data.tags or [], ensure_ascii=False),
        video_path=data.video_path,
        cover_path=data.cover_path
    )
    db.add(content)
    db.commit()
    db.refresh(content)

    return {
        "id": content.id,
        "title": content.title,
        "description": content.description,
        "tags": data.tags or [],
        "video_path": content.video_path,
        "cover_path": content.cover_path,
        "created_at": content.created_at,
        "updated_at": content.updated_at
    }


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    data: ContentUpdate,
    db: Session = Depends(get_db)
):
    """更新内容"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    if data.title is not None:
        content.title = data.title

    if data.description is not None:
        content.description = data.description

    if data.tags is not None:
        content.tags = json.dumps(data.tags, ensure_ascii=False)

    if data.video_path is not None:
        content.video_path = data.video_path

    if data.cover_path is not None:
        content.cover_path = data.cover_path

    content.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(content)

    return {
        "id": content.id,
        "title": content.title,
        "description": content.description,
        "tags": json.loads(content.tags) if content.tags else [],
        "video_path": content.video_path,
        "cover_path": content.cover_path,
        "created_at": content.created_at,
        "updated_at": content.updated_at
    }


@router.delete("/{content_id}", response_model=MessageResponse)
async def delete_content(content_id: int, db: Session = Depends(get_db)):
    """删除内容"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    # 删除视频文件
    if content.video_path and os.path.exists(content.video_path):
        os.remove(content.video_path)

    # 删除封面文件
    if content.cover_path and os.path.exists(content.cover_path):
        os.remove(content.cover_path)

    db.delete(content)
    db.commit()

    return MessageResponse(message="内容已删除", success=True)


@router.post("/batch/delete", response_model=MessageResponse)
async def batch_delete_contents(
    content_ids: List[int],
    db: Session = Depends(get_db)
):
    """批量删除内容"""
    deleted_count = 0

    for content_id in content_ids:
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            if content.video_path and os.path.exists(content.video_path):
                os.remove(content.video_path)
            if content.cover_path and os.path.exists(content.cover_path):
                os.remove(content.cover_path)
            db.delete(content)
            deleted_count += 1

    db.commit()

    log_operation("batch_delete", "upload", status="success",
                 details={"count": deleted_count})

    return MessageResponse(
        message=f"成功删除 {deleted_count} 个内容",
        success=True
    )


@router.post("/batch/update-title", response_model=MessageResponse)
async def batch_update_title(data: BatchUpdateTitle, db: Session = Depends(get_db)):
    """批量更新标题"""
    updated_count = 0

    for i, content_id in enumerate(data.content_ids):
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            # 支持模板，{index}会被替换为序号
            title = data.title_template.replace("{index}", str(i + 1))
            content.title = title
            content.updated_at = datetime.utcnow()
            updated_count += 1

    db.commit()

    log_operation("batch_update_title", "upload", status="success",
                 details={"count": updated_count})

    return MessageResponse(
        message=f"成功更新 {updated_count} 个内容的标题",
        success=True
    )


@router.post("/batch/update-tags", response_model=MessageResponse)
async def batch_update_tags(data: BatchUpdateTags, db: Session = Depends(get_db)):
    """批量更新话题标签"""
    updated_count = 0

    for content_id in data.content_ids:
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            content.tags = json.dumps(data.tags, ensure_ascii=False)
            content.updated_at = datetime.utcnow()
            updated_count += 1

    db.commit()

    log_operation("batch_update_tags", "upload", status="success",
                 details={"count": updated_count, "tags": data.tags})

    return MessageResponse(
        message=f"成功更新 {updated_count} 个内容的话题标签",
        success=True
    )


@router.post("/batch/update-description", response_model=MessageResponse)
async def batch_update_description(
    data: BatchUpdateDescription,
    db: Session = Depends(get_db)
):
    """批量更新文案"""
    updated_count = 0

    for content_id in data.content_ids:
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            content.description = data.description
            content.updated_at = datetime.utcnow()
            updated_count += 1

    db.commit()

    log_operation("batch_update_description", "upload", status="success",
                 details={"count": updated_count})

    return MessageResponse(
        message=f"成功更新 {updated_count} 个内容的文案",
        success=True
    )
