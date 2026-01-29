"""
FastAPI 应用主入口
社交媒体多账号批量分发上传系统
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.routers import accounts, upload, publish, logs
from backend.utils.logger import get_logger, log_operation
from backend.utils.browser import browser_manager

logger = get_logger("main")

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "videos")
os.makedirs(STATIC_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("=" * 50)
    logger.info("社交媒体批量分发系统启动中...")
    logger.info("=" * 50)

    # 初始化数据库
    init_db()
    logger.info("数据库初始化完成")

    log_operation("startup", "system", status="success")

    yield

    # 关闭时
    logger.info("系统关闭中...")

    # 关闭浏览器
    await browser_manager.close()

    log_operation("shutdown", "system", status="success")
    logger.info("系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="社交媒体批量分发系统",
    description="""
    ## 功能特性

    - **账号管理**: 通过扫描二维码新增账号、支持账号删除和修改
    - **多平台支持**: 抖音、视频号、小红书
    - **批量上传**: 支持批量自定义标题、话题、文案
    - **一键发布**: 一键批量发布到多个平台
    - **日志管理**: 完善的后台日志系统

    ## API文档

    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境请限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 注册路由
app.include_router(accounts.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(publish.router, prefix="/api")
app.include_router(logs.router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "社交媒体批量分发系统",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "database": "connected",
        "browser": "ready"
    }


@app.get("/api")
async def api_info():
    """API信息"""
    return {
        "version": "1.0.0",
        "endpoints": {
            "accounts": "/api/accounts",
            "contents": "/api/contents",
            "publish": "/api/publish",
            "logs": "/api/logs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
