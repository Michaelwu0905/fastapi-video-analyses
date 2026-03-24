# B站视频传播力与内容分析系统

一个前后端分离的 B 站视频分析项目，输入 B 站视频链接后可以同时查看：

- 视频基础信息与传播力指标
- 评论抓取与情感分析结果
- 视频内容摘要、标签与关键片段
- 对任意视频的真实下载、转写与内容分析任务状态

## 技术栈

- 后端：FastAPI + Python 3.11
- 前端：Vue 3 + Vite
- 内容分析：LangChain + Moonshot 兼容接口 + Whisper
- 部署：Docker + Nginx
- HTTP 客户端：httpx / axios

## 当前功能

- 支持标准 B 站视频链接和 `b23.tv` 短链接
- 获取视频标题、简介、时长、发布时间、UP 主等基础信息
- 展示播放、弹幕、点赞、投币、收藏、分享等统计指标
- 计算传播力综合得分与粘性度
- 爬取评论并进行情感分析
- 展示视频内容摘要、标签和关键片段
- 优先使用后端内置样例索引做内容分析
- 样例索引未命中时，自动切换到真实视频下载与 Whisper 转写链路
- 前端展示真实内容分析任务的排队、执行、成功和失败状态
- 支持将真实内容分析任务转发到独立 worker 节点执行

## 快速开始

### 方式一：Docker 部署

确保已安装 Docker 和 Docker Compose，然后在项目根目录执行：

```bash
docker-compose up --build
```

后台运行：

```bash
docker-compose up -d --build
```

停止服务：

```bash
docker-compose down
```

启动后访问 `http://localhost`。

### 方式二：本地开发

#### 1. 启动后端

```bash
cd backend
uv sync
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

后端运行在 `http://127.0.0.1:8000`。

如果你要启用真实视频内容分析，建议额外准备：

- `yt-dlp`
- `whisper`
- `ffmpeg`

并在 `backend/.env` 中配置：

```env
MOONSHOT_API_KEY=your_moonshot_api_key
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=kimi-k2-0711-preview
WHISPER_MODEL=base
WHISPER_LANGUAGE=zh
```

可直接参考 `backend/.env.example`。

#### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 `http://localhost:3000`。

## 主要接口

### `POST /api/analyze`

分析 B 站视频基础信息和传播力指标。

### `POST /api/fetch-comments`

抓取评论并启动后台情感分析任务。

### `GET /api/comments/{bvid}`

获取已保存评论。

### `GET /api/sentiment-status/{bvid}`

查询评论情感分析进度。

### `GET /api/sentiment/{bvid}`

获取情感统计结果与评论列表。

### `POST /api/content-analysis`

优先使用后端内置样例索引进行内容分析，返回摘要、标签和关键片段。

### `POST /api/content-analysis/start-real`

为任意真实 B 站视频启动下载、转写和内容分析任务。

### `GET /api/content-analysis/status/{bvid}`

查询真实内容分析任务状态。

### `GET /api/content-analysis/result/{bvid}`

获取真实内容分析结果。

### `GET /api/health`

健康检查。

## 推荐生产部署

当前更推荐的生产拓扑是：

- `volcano`：部署前端和主后端
- `laptop`：部署内容分析 worker

这样可以把 `yt-dlp + whisper + LangChain` 的重任务从 `4核4G` 的公网服务器上挪开，避免真实转写拖慢主站响应。

部署相关文件位于：

- `deploy/volcano/docker-compose.yml`
- `deploy/volcano/backend.env.example`
- `deploy/laptop/worker.env.example`
- `deploy/laptop/start-worker.sh`
- `deploy/laptop/bilibili-content-worker.service`
- `deploy/README.md`

## 项目结构

```text
fastapi-video-analyses/
├── backend/
│   ├── main.py                      # FastAPI 主程序
│   ├── worker_main.py               # 内容分析 worker 入口
│   ├── database.py                  # 评论与情感分析数据存取
│   ├── sentiment.py                 # 评论情感分析逻辑
│   ├── content_analysis/            # 视频内容分析模块
│   │   ├── pipeline.py              # 内容分析主流程
│   │   ├── service.py               # 内容分析任务共享逻辑
│   │   ├── loaders.py               # 样例源与真实视频源解析
│   │   ├── transcribe.py            # 下载与 Whisper 转写
│   │   ├── llm.py                   # LLM 摘要、问答、标签提取
│   │   ├── config.py                # 内容分析配置与路径
│   │   ├── sample_data/             # 内置样例索引与转写文本
│   │   └── artifacts/               # 下载缓存与转写缓存
│   ├── .env.example                 # 内容分析环境变量示例
│   ├── pyproject.toml               # 后端依赖定义
│   ├── uv.lock                      # 后端锁文件
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/
│   │   └── composables/
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── deploy/
│   ├── volcano/                     # volcano 服务器部署文件
│   └── laptop/                      # laptop worker 启动文件
└── README.md
```

## 说明

1. 当前真实内容分析任务状态保存在内存中，后端重启后不会保留。
2. `backend/content_analysis/artifacts/` 用于缓存下载音频和转写文本。
3. 当设置了 `CONTENT_ANALYSIS_WORKER_URL` 后，主后端会把真实内容分析请求转发到独立 worker。
4. `CONTENT_ANALYSIS_WORKER_TOKEN` 用于主后端和 worker 之间的简单鉴权，两个节点必须保持一致。
5. 样例索引模式适合本地快速验证，真实模式更适合实际视频分析。
