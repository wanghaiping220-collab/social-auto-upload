"""
账号管理路由
"""
import uuid
import json
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Account, AccountStatus
from backend.schemas import (
    AccountCreate, AccountUpdate, AccountResponse,
    QRCodeResponse, QRCodeStatusResponse, MessageResponse
)
from backend.services.douyin import douyin_service
from backend.services.weixin import weixin_service
from backend.services.xiaohongshu import xiaohongshu_service
from backend.utils.logger import get_logger, log_account
from backend.utils.browser import QRCodeLoginSession

logger = get_logger("accounts")

router = APIRouter(prefix="/accounts", tags=["账号管理"])

# 存储登录会话
login_sessions: Dict[str, QRCodeLoginSession] = {}

# 平台服务映射
PLATFORM_SERVICES = {
    "douyin": douyin_service,
    "weixin": weixin_service,
    "xiaohongshu": xiaohongshu_service
}


@router.get("", response_model=list[AccountResponse])
async def get_accounts(
    platform: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """获取账号列表"""
    query = db.query(Account)

    if platform:
        query = query.filter(Account.platform == platform)

    if status:
        query = query.filter(Account.status == status)

    accounts = query.order_by(Account.created_at.desc()).all()
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """获取单个账号详情"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account


@router.post("/qrcode", response_model=QRCodeResponse)
async def generate_qrcode(
    platform: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    生成登录二维码

    Args:
        platform: 平台类型 (douyin, weixin, xiaohongshu)
    """
    if platform not in PLATFORM_SERVICES:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    session_id = str(uuid.uuid4())

    try:
        service = PLATFORM_SERVICES[platform]
        session = await service.create_login_session(session_id)

        login_sessions[session_id] = session

        log_account("generate_qrcode", platform, status="success")

        return QRCodeResponse(
            qrcode_url=f"data:image/png;base64,{session.qrcode_base64}",
            session_id=session_id,
            platform=platform
        )

    except Exception as e:
        log_account("generate_qrcode", platform, status="failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"生成二维码失败: {str(e)}")


@router.get("/qrcode/{session_id}/status", response_model=QRCodeStatusResponse)
async def check_qrcode_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """检查二维码扫描状态"""
    if session_id not in login_sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    session = login_sessions[session_id]

    # 如果登录成功，创建账号记录
    if session.status == "confirmed" and session.cookies:
        # 检查是否已存在相同的账号
        existing = db.query(Account).filter(
            Account.platform == session.platform,
            Account.nickname == session.user_info.get("nickname", "")
        ).first()

        if existing:
            # 更新现有账号
            existing.cookies = session.cookies
            existing.status = AccountStatus.ACTIVE.value
            existing.last_login_at = datetime.utcnow()
            existing.avatar_url = session.user_info.get("avatar_url", existing.avatar_url)
            db.commit()
            account_id = existing.id
        else:
            # 创建新账号
            account = Account(
                platform=session.platform,
                nickname=session.user_info.get("nickname", f"用户_{session_id[:8]}"),
                username=session.user_info.get("username", ""),
                avatar_url=session.user_info.get("avatar_url", ""),
                cookies=session.cookies,
                status=AccountStatus.ACTIVE.value,
                last_login_at=datetime.utcnow()
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            account_id = account.id

        # 清理会话
        await session.close()
        del login_sessions[session_id]

        log_account("login", session.platform, account_id=account_id, status="success")

        return QRCodeStatusResponse(
            status="confirmed",
            account_id=account_id,
            message="登录成功"
        )

    return QRCodeStatusResponse(
        status=session.status,
        account_id=None,
        message={
            "waiting": "等待扫码",
            "scanned": "已扫码，请在手机上确认",
            "expired": "二维码已过期，请刷新",
            "error": "登录出错"
        }.get(session.status, "")
    )


@router.post("/qrcode/{session_id}/refresh", response_model=QRCodeResponse)
async def refresh_qrcode(
    session_id: str,
    db: Session = Depends(get_db)
):
    """刷新二维码"""
    if session_id not in login_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    old_session = login_sessions[session_id]
    platform = old_session.platform

    # 关闭旧会话
    await old_session.close()
    del login_sessions[session_id]

    # 创建新会话
    new_session_id = str(uuid.uuid4())

    try:
        service = PLATFORM_SERVICES[platform]
        session = await service.create_login_session(new_session_id)

        login_sessions[new_session_id] = session

        return QRCodeResponse(
            qrcode_url=f"data:image/png;base64,{session.qrcode_base64}",
            session_id=new_session_id,
            platform=platform
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新二维码失败: {str(e)}")


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    data: AccountUpdate,
    db: Session = Depends(get_db)
):
    """更新账号信息"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if data.nickname is not None:
        account.nickname = data.nickname

    if data.status is not None:
        account.status = data.status

    account.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(account)

    log_account("update", account.platform, account_id=account_id, status="success")

    return account


@router.delete("/{account_id}", response_model=MessageResponse)
async def delete_account(account_id: int, db: Session = Depends(get_db)):
    """删除账号"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    platform = account.platform
    db.delete(account)
    db.commit()

    log_account("delete", platform, account_id=account_id, status="success")

    return MessageResponse(message="账号已删除", success=True)


@router.post("/{account_id}/check", response_model=MessageResponse)
async def check_account_status(account_id: int, db: Session = Depends(get_db)):
    """检查账号登录状态"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.cookies:
        account.status = AccountStatus.INACTIVE.value
        db.commit()
        return MessageResponse(message="账号未登录", success=False)

    service = PLATFORM_SERVICES.get(account.platform)
    if not service:
        return MessageResponse(message="不支持的平台", success=False)

    is_valid, message = await service.check_account_status(account.cookies)

    if is_valid:
        account.status = AccountStatus.ACTIVE.value
    else:
        account.status = AccountStatus.EXPIRED.value

    db.commit()

    return MessageResponse(message=message, success=is_valid)
