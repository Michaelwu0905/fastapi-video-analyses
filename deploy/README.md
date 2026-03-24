# 部署方案

当前部署分支采用以下拓扑：

- `volcano`：前端 + 主后端
- `laptop`：内容分析 worker

## volcano

1. 将项目代码拉到服务器
2. 复制 `deploy/volcano/backend.env.example` 为 `deploy/volcano/backend.env`
3. 将 `CONTENT_ANALYSIS_WORKER_URL` 改成 `laptop` 可访问地址
4. 将 `CONTENT_ANALYSIS_WORKER_TOKEN` 设置为随机长字符串
5. 执行：

```bash
cd deploy/volcano
docker compose up -d --build
```

## laptop

1. 安装 `uv`、`yt-dlp`、`whisper`、`ffmpeg`
2. 将项目代码拉到笔记本
3. 复制 `deploy/laptop/worker.env.example` 为 `deploy/laptop/worker.env`
4. 保证 `CONTENT_ANALYSIS_WORKER_TOKEN` 与 `volcano` 配置一致
5. 如果 `whisper` 或 `yt-dlp` 不是通过 `PATH` 可直接访问，可在 `worker.env` 中设置：

```env
WHISPER_BIN=/your/whisper/path
YT_DLP_BIN=/your/yt-dlp/path
```

5. 启动：

```bash
cd /path/to/fastapi-video-analyses
chmod +x deploy/laptop/start-worker.sh
./deploy/laptop/start-worker.sh
```

如需开机自启，可参考 `deploy/laptop/bilibili-content-worker.service`。
