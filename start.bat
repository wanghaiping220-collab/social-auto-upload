@echo off
chcp 65001 >nul
title 社交媒体批量分发系统

echo ======================================
echo   社交媒体批量分发系统
echo ======================================

REM 创建数据目录
if not exist "data\videos" mkdir data\videos
if not exist "logs" mkdir logs

REM 安装 Python 依赖
echo.
echo ^>^>^> 安装 Python 依赖...
pip install -r requirements.txt -q

REM 安装 Playwright 浏览器
echo.
echo ^>^>^> 安装 Playwright 浏览器...
playwright install chromium

REM 安装前端依赖
echo.
echo ^>^>^> 安装前端依赖...
cd frontend
call npm install --silent
cd ..

REM 启动后端服务
echo.
echo ^>^>^> 启动后端服务 (端口 8000)...
start "Backend" cmd /c "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端服务
echo.
echo ^>^>^> 启动前端服务 (端口 3000)...
cd frontend
start "Frontend" cmd /c "npm run dev"
cd ..

echo.
echo ======================================
echo   启动完成!
echo.
echo   前端地址: http://localhost:3000
echo   后端API: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo.
echo   关闭此窗口可停止服务
echo ======================================

pause
