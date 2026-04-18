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
- 基于 AHP 层次分析法计算综合传播力评价结果
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
TRANSCRIBE_BACKEND=auto
WHISPER_BIN=/your/whisper/path
YT_DLP_BIN=/your/yt-dlp/path
WHISPER_MODEL=base
WHISPER_LANGUAGE=zh
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16
FASTER_WHISPER_MODEL_PATH=
FASTER_WHISPER_DOWNLOAD_ROOT=
FASTER_WHISPER_LOCAL_FILES_ONLY=false
HF_ENDPOINT=https://hf-mirror.com
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

## 当前线上部署拓扑

当前跑通并正在使用的拓扑是：

- `volcano`：只负责前端静态资源和 Nginx 反向代理
- `laptop`：负责主后端 `main:app` 和内容分析 worker `worker_main:app`

请求链路如下：

1. 用户访问 `volcano` 上的前端页面
2. 前端请求 `volcano` 的 `/api/*`
3. `volcano` 上的 Nginx 将 `/api/*` 反代到 `laptop:8000`
4. `laptop` 主后端处理传播力分析、评论分析等轻量接口
5. 主后端将真实内容分析任务转发到同机的 `laptop:8001`
6. worker 负责 `yt-dlp` 下载、`faster-whisper` 转写和 LangChain 内容分析

这样做的原因是：

- `volcano` 的 `4核4G` 更适合做公网入口和静态页面服务
- `laptop` 有 `i7-12700H + RTX 3060`，更适合承担真实视频转写和内容分析
- 主站公网入口稳定，重任务又不会压垮公网服务器

部署相关文件位于：

- `deploy/volcano/nginx.volcano.conf`
- `deploy/laptop/main-backend.env.example`
- `deploy/laptop/worker.env.example`
- `deploy/laptop/bilibili-main-backend.service`
- `deploy/laptop/bilibili-content-worker.service`
- `deploy/laptop/start-main-backend.sh`
- `deploy/laptop/start-worker.sh`
- `deploy/README.md`

## 当前部署流程

下面是当前项目的推荐部署顺序。

### 1. 准备两台机器

- `volcano` 和 `laptop` 都安装并登录 Tailscale，确保互相可达
- 在 `volcano` 上确认可以访问 `laptop:8000`
- 在 `laptop` 上安装：
  - `uv`
  - `ffmpeg`
  - `yt-dlp`
  - NVIDIA 驱动

### 2. 同步代码

如果服务器无法直接 `git clone`，可以从本地使用 `rsync` 同步代码到两台机器：

```bash
rsync -avz --progress \
  --exclude '.git' \
  --exclude 'frontend/node_modules' \
  --exclude 'frontend/dist' \
  --exclude 'backend/.venv' \
  --exclude 'backend/__pycache__' \
  /Users/yourname/path/to/fastapi-video-analyses/ \
  volcano:~/fastapi-video-analyses/
```

```bash
rsync -avz --progress \
  --exclude '.git' \
  --exclude 'frontend/node_modules' \
  --exclude 'frontend/dist' \
  --exclude 'backend/.venv' \
  --exclude 'backend/__pycache__' \
  /Users/yourname/path/to/fastapi-video-analyses/ \
  laptop:~/fastapi-video-analyses/
```

### 3. 在 laptop 上部署主后端

```bash
cd ~/fastapi-video-analyses/backend
uv sync
```

创建 `deploy/laptop/main-backend.env`：

```env
CONTENT_ANALYSIS_WORKER_URL=http://127.0.0.1:8001
CONTENT_ANALYSIS_WORKER_TOKEN=与你的 worker 保持一致
```

安装 user service：

```bash
mkdir -p ~/.config/systemd/user
cp ~/fastapi-video-analyses/deploy/laptop/bilibili-main-backend.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now bilibili-main-backend.service
```

建议再开启 linger，保证重启后 user service 也会自动恢复：

```bash
sudo loginctl enable-linger mari
```

### 4. 在 laptop 上部署内容分析 worker

创建 `deploy/laptop/worker.env`，至少配置这些项：

```env
MOONSHOT_API_KEY=your_key
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=kimi-k2-0711-preview
TRANSCRIBE_BACKEND=faster_whisper
YT_DLP_BIN=/your/yt-dlp/path
WHISPER_MODEL=base
WHISPER_LANGUAGE=zh
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16
FASTER_WHISPER_DOWNLOAD_ROOT=/home/mari/fastapi-video-analyses/backend/content_analysis/artifacts/faster_whisper_models
FASTER_WHISPER_LOCAL_FILES_ONLY=false
HF_ENDPOINT=https://hf-mirror.com
CONTENT_ANALYSIS_WORKER_TOKEN=与你的主后端保持一致
LD_LIBRARY_PATH=/home/mari/fastapi-video-analyses/backend/.venv/lib/python3.12/site-packages/nvidia/cublas/lib:/home/mari/fastapi-video-analyses/backend/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib
```

首次为 GPU 版 `faster-whisper` 准备 CUDA 运行库：

```bash
cd ~/fastapi-video-analyses/backend
uv pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*
```

安装 worker service：

```bash
mkdir -p ~/.config/systemd/user
cp ~/fastapi-video-analyses/deploy/laptop/bilibili-content-worker.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now bilibili-content-worker.service
```

### 5. 在 volcano 上部署前端和 Nginx

构建前端：

```bash
cd ~/fastapi-video-analyses/frontend
npm install
npm run build
```

将 `deploy/volcano/nginx.volcano.conf` 放到 Nginx 站点配置中，并把 `/api/` 反代地址改成你的 `laptop` Tailscale 地址，例如：

```nginx
location /api/ {
    proxy_pass http://100.x.y.z:8000/api/;
}
```

然后重载 Nginx：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 6. 验证

在 `laptop` 上：

```bash
systemctl --user status bilibili-main-backend.service
systemctl --user status bilibili-content-worker.service
curl http://127.0.0.1:8000/api/health
curl -H "X-Worker-Token: your_token" http://127.0.0.1:8001/worker/health
```

在 `volcano` 上：

```bash
curl http://127.0.0.1/api/health
```

公网验证：

```bash
curl http://your-server-ip/api/health
```

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
5. `TRANSCRIBE_BACKEND` 支持 `auto`、`faster_whisper`、`whisper_cli` 三种模式。
6. `faster-whisper` 首次下载模型时建议配置 `HF_ENDPOINT=https://hf-mirror.com`，避免直接访问 Hugging Face 官方源失败。
7. GPU 版 `faster-whisper` 除了 NVIDIA 驱动外，还需要 `nvidia-cublas-cu12` 和 `nvidia-cudnn-cu12` 等运行库，并通过 `LD_LIBRARY_PATH` 暴露给 worker 进程。
8. 对于部分低质量或背景音较强的视频，`vad_filter=True` 可能会把整段音频过滤空；当前代码已在 VAD 产出空文本时自动回退到 `vad_filter=False`。
9. 样例索引模式适合本地快速验证，真实模式更适合实际视频分析。
