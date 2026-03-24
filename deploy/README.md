# 部署方案

当前实际跑通的部署拓扑是：

- `volcano`：前端静态资源 + Nginx 反向代理
- `laptop`：主后端 `main:app` + 内容分析 worker `worker_main:app`

## 整体链路

1. 浏览器访问 `volcano`
2. 前端页面由 `volcano` 上的 Nginx 直接提供
3. 前端请求 `/api/*` 时，Nginx 反代到 `laptop:8000`
4. `laptop` 主后端处理传播力分析、评论分析等请求
5. 真实内容分析任务再由主后端转发给同机的 `laptop:8001`

## 前置条件

两台机器都需要：

- 项目代码
- Tailscale 互通

`laptop` 额外需要：

- `uv`
- `ffmpeg`
- `yt-dlp`
- NVIDIA 驱动

## 1. 同步代码

如果不能在服务器直接 `git clone`，推荐从本地用 `rsync` 同步：

```bash
rsync -avz --progress \
  --exclude '.git' \
  --exclude 'frontend/node_modules' \
  --exclude 'frontend/dist' \
  --exclude 'backend/.venv' \
  --exclude 'backend/__pycache__' \
  /path/to/fastapi-video-analyses/ \
  volcano:~/fastapi-video-analyses/
```

```bash
rsync -avz --progress \
  --exclude '.git' \
  --exclude 'frontend/node_modules' \
  --exclude 'frontend/dist' \
  --exclude 'backend/.venv' \
  --exclude 'backend/__pycache__' \
  /path/to/fastapi-video-analyses/ \
  laptop:~/fastapi-video-analyses/
```

## 2. 在 laptop 上部署主后端

安装依赖：

```bash
cd ~/fastapi-video-analyses/backend
uv sync
```

创建 `deploy/laptop/main-backend.env`：

```env
CONTENT_ANALYSIS_WORKER_URL=http://127.0.0.1:8001
CONTENT_ANALYSIS_WORKER_TOKEN=replace_with_the_same_token_as_worker
```

安装并启动服务：

```bash
mkdir -p ~/.config/systemd/user
cp ~/fastapi-video-analyses/deploy/laptop/bilibili-main-backend.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now bilibili-main-backend.service
```

建议打开 linger：

```bash
sudo loginctl enable-linger mari
```

## 3. 在 laptop 上部署内容分析 worker

复制环境变量模板：

```bash
cp ~/fastapi-video-analyses/deploy/laptop/worker.env.example ~/fastapi-video-analyses/deploy/laptop/worker.env
```

推荐配置如下：

```env
MOONSHOT_API_KEY=
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=kimi-k2-0711-preview
TRANSCRIBE_BACKEND=faster_whisper
WHISPER_BIN=
YT_DLP_BIN=/your/yt-dlp/path
WHISPER_MODEL=base
WHISPER_LANGUAGE=zh
FASTER_WHISPER_DEVICE=cuda
FASTER_WHISPER_COMPUTE_TYPE=float16
FASTER_WHISPER_MODEL_PATH=
FASTER_WHISPER_DOWNLOAD_ROOT=/home/mari/fastapi-video-analyses/backend/content_analysis/artifacts/faster_whisper_models
FASTER_WHISPER_LOCAL_FILES_ONLY=false
HF_ENDPOINT=https://hf-mirror.com
CONTENT_ANALYSIS_WORKER_TOKEN=replace_with_the_same_token_as_main_backend
LD_LIBRARY_PATH=/home/mari/fastapi-video-analyses/backend/.venv/lib/python3.12/site-packages/nvidia/cublas/lib:/home/mari/fastapi-video-analyses/backend/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib
```

GPU 版 `faster-whisper` 还需要额外安装 CUDA 运行库：

```bash
cd ~/fastapi-video-analyses/backend
uv pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*
```

安装并启动 worker：

```bash
mkdir -p ~/.config/systemd/user
cp ~/fastapi-video-analyses/deploy/laptop/bilibili-content-worker.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now bilibili-content-worker.service
```

如果只是临时前台启动，也可以直接用：

```bash
cd ~/fastapi-video-analyses
chmod +x deploy/laptop/start-worker.sh
./deploy/laptop/start-worker.sh
```

## 4. 在 volcano 上部署前端和反向代理

构建前端：

```bash
cd ~/fastapi-video-analyses/frontend
npm install
npm run build
```

把 `deploy/volcano/nginx.volcano.conf` 放到 Nginx 站点配置目录，并确认 `/api/` 反代地址指向 `laptop:8000`：

```nginx
location /api/ {
    proxy_pass http://100.74.44.119:8000/api/;
}
```

重载 Nginx：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 5. 验证

在 `laptop` 上验证：

```bash
systemctl --user status bilibili-main-backend.service
systemctl --user status bilibili-content-worker.service
curl http://127.0.0.1:8000/api/health
curl -H "X-Worker-Token: your_token" http://127.0.0.1:8001/worker/health
```

在 `volcano` 上验证：

```bash
curl http://127.0.0.1/api/health
```

公网验证：

```bash
curl http://your-server-ip/api/health
```

## 6. 运行时注意事项

- `faster-whisper` 首次运行会下载模型，建议设置 `HF_ENDPOINT=https://hf-mirror.com`
- 如果模型已下载到本地，可以设置 `FASTER_WHISPER_MODEL_PATH`，并将 `FASTER_WHISPER_LOCAL_FILES_ONLY=true`
- GPU 路径除了驱动，还必须把 `nvidia-cublas-cu12` 和 `nvidia-cudnn-cu12` 的库目录加入 `LD_LIBRARY_PATH`
- 某些噪声较大的视频在 `vad_filter=True` 时会被过滤空，当前代码已经自动回退到 `vad_filter=False`
