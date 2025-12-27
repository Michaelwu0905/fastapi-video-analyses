# B站视频分析系统

一个前后端分离的B站视频分析项目，输入B站视频链接即可获取视频的详细信息。

## 技术栈

- **后端**: FastAPI + Python 3.11
- **前端**: Vue 3 + Vite
- **部署**: Docker + Nginx
- **HTTP客户端**: httpx (后端) / axios (前端)

## 功能特点

- 支持标准B站视频链接和短链接 (b23.tv)
- 获取视频标题、简介、时长等基本信息
- 显示UP主名称和发布时间
- 展示视频数据统计（播放量、弹幕、点赞、投币、收藏、分享）
- 简约界面设计，响应式布局

## 快速开始

### 方式一：Docker 部署（推荐）

确保已安装 Docker 和 Docker Compose，然后在项目根目录执行：

```bash
# 构建并启动容器
docker-compose up --build

# 后台运行
docker-compose up -d --build

# 停止服务
docker-compose down
```

启动后访问 http://localhost 即可使用系统。

### 方式二：本地开发

#### 1. 启动后端服务

```bash
# 进入项目根目录，激活虚拟环境
.\venv\Scripts\activate

# 启动FastAPI服务器
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

后端服务将在 http://127.0.0.1:8000 运行

#### 2. 启动前端服务

```bash
# 新开一个终端，进入前端目录
cd frontend

# 安装依赖（首次运行需要）
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:3000 运行

## API 接口

### POST /api/analyze

分析B站视频，获取详细信息

**请求体:**
```json
{
  "url": "https://www.bilibili.com/video/BVxxxxx"
}
```

**响应:**
```json
{
  "status": "success",
  "bvid": "BV1GJ411x7h7",
  "title": "视频标题",
  "author": "UP主名称",
  "desc": "视频简介",
  "view": 1234567,
  "view_formatted": "123.5万",
  "danmaku": 12345,
  "like": 54321,
  "coin": 11111,
  "favorite": 22222,
  "share": 3333,
  "duration": 360,
  "duration_formatted": "06:00",
  "pubdate": "2024-01-01 12:00:00",
  "msg": "成功访问B站视频"
}
```

### GET /api/health

健康检查接口

## 项目结构

```
fastapi-video-analyses/
├── backend/
│   ├── main.py              # FastAPI 后端主程序
│   ├── Dockerfile           # 后端容器配置
│   └── requirements.txt     # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── App.vue          # Vue 主组件
│   │   ├── main.js          # Vue 入口文件
│   │   └── style.css        # 全局样式
│   ├── index.html           # HTML 入口
│   ├── package.json         # 前端依赖配置
│   ├── vite.config.js       # Vite 配置
│   ├── Dockerfile           # 前端容器配置
│   └── nginx.conf           # Nginx 代理配置
├── docker-compose.yml       # 容器编排配置
├── venv/                    # Python 虚拟环境
└── README.md
```

## 注意事项

1. Docker 部署时前端通过 Nginx 代理访问后端，无需额外配置跨域
2. 本地开发时需分别启动前后端服务
3. B站API可能有访问频率限制，请勿过于频繁请求
