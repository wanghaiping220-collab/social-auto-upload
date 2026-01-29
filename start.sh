#!/bin/bash

# 社交媒体批量分发系统启动脚本

echo "======================================"
echo "  社交媒体批量分发系统"
echo "======================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未安装 Python3"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 未安装 Node.js"
    exit 1
fi

# 创建数据目录
mkdir -p data/videos logs

# 安装 Python 依赖
echo ""
echo ">>> 安装 Python 依赖..."
pip install -r requirements.txt -q

# 安装 Playwright 浏览器
echo ""
echo ">>> 安装 Playwright 浏览器..."
playwright install chromium

# 安装前端依赖
echo ""
echo ">>> 安装前端依赖..."
cd frontend
npm install --silent
cd ..

# 启动后端服务
echo ""
echo ">>> 启动后端服务 (端口 8000)..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端服务
echo ""
echo ">>> 启动前端服务 (端口 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "======================================"
echo "  启动完成!"
echo ""
echo "  前端地址: http://localhost:3000"
echo "  后端API: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止服务"
echo "======================================"

# 等待进程
wait $BACKEND_PID $FRONTEND_PID
