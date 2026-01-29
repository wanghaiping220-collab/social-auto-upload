# Social Media Batch Uploader

社交媒体多账号批量分发上传系统 - 本地部署版

## 功能特性

- **账号管理**: 通过扫描二维码新增账号、支持账号删除和修改
- **多平台支持**: 抖音、视频号、小红书
- **批量上传**: 支持批量自定义标题、话题、文案
- **一键发布**: 一键批量发布到多个平台
- **友好界面**: 现代化的前端交互界面
- **稳定日志**: 完善的后台日志系统

## 技术栈

### 后端
- Python 3.9+
- FastAPI (高性能Web框架)
- SQLite (本地数据库)
- Playwright (浏览器自动化)
- Loguru (日志管理)

### 前端
- React 18
- Ant Design 5 (企业级UI组件库)
- Vite (构建工具)

## 快速开始

### 1. 安装依赖

```bash
# 安装后端依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium

# 安装前端依赖
cd frontend
npm install
```

### 2. 启动服务

```bash
# 启动后端服务 (端口 8000)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端开发服务 (新终端, 端口 3000)
cd frontend
npm run dev
```

### 3. 访问应用

打开浏览器访问: http://localhost:3000

## 项目结构

```
social-auto-upload/
├── backend/                 # 后端服务
│   ├── main.py             # FastAPI 应用入口
│   ├── database.py         # 数据库配置
│   ├── models.py           # 数据模型
│   ├── schemas.py          # Pydantic 模式
│   ├── routers/            # API 路由
│   │   ├── accounts.py     # 账号管理 API
│   │   ├── upload.py       # 上传管理 API
│   │   └── publish.py      # 发布管理 API
│   ├── services/           # 业务服务
│   │   ├── douyin.py       # 抖音服务
│   │   ├── weixin.py       # 视频号服务
│   │   └── xiaohongshu.py  # 小红书服务
│   └── utils/              # 工具函数
│       ├── logger.py       # 日志配置
│       └── browser.py      # 浏览器工具
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── pages/          # 页面
│   │   ├── services/       # API 服务
│   │   └── App.tsx         # 应用入口
│   └── package.json
├── data/                   # 数据目录
│   ├── videos/             # 视频文件
│   └── database.db         # SQLite 数据库
├── logs/                   # 日志目录
├── requirements.txt        # Python 依赖
└── README.md
```

## 使用说明

### 添加账号

1. 进入"账号管理"页面
2. 点击"添加账号"按钮
3. 选择平台（抖音/视频号/小红书）
4. 使用手机APP扫描显示的二维码
5. 扫码成功后账号自动添加

### 批量上传

1. 进入"内容管理"页面
2. 点击"上传视频"批量选择视频文件
3. 为每个视频设置标题、话题、文案
4. 可使用"批量设置"快速配置

### 一键发布

1. 选择要发布的内容
2. 选择目标账号和平台
3. 点击"一键发布"
4. 在日志面板查看发布进度

## 注意事项

- 请确保网络稳定
- 首次使用需要登录各平台账号
- 建议定期检查账号登录状态
- 发布频率不宜过高，避免被平台限制

## License

MIT License
