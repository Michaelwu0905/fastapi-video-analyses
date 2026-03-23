# langchain-bilibili

一个基于 `LangChain` 的 B 站视频内容识别项目，使用 `uv` 管理依赖，支持：

- 本地转写文本分析
- B 站 `BV` 号或视频链接输入
- Moonshot Kimi 摘要与问答
- 本地回退模式
- `yt-dlp + whisper` 的真实下载与转写流程

当前项目重点是先把“视频来源 -> 转写文本 -> 摘要/标签/问答”这条链路跑通，并保留继续扩展 OCR、抽帧和向量检索的空间。

## 功能概览

- 支持三种输入方式：本地文本文件、B 站 `BV` 号、B 站 URL
- 将转写内容切分为 `LangChain Document`
- 生成视频摘要
- 提取标签和关键高亮片段
- 基于相关片段进行问答
- 配置 Kimi 后使用大模型输出
- 未配置 Kimi 时自动回退到本地规则模式
- 可选启用真实 B 站下载与本地 Whisper 转写

## 环境要求

- Python `3.9` 到 `<3.14`
- `uv`
- 可选：
  `yt-dlp`
  `whisper`
  `ffmpeg`

如果你要跑真实 B 站下载与转写，建议先确保以下命令可用：

```bash
yt-dlp --version
whisper --help
ffmpeg -version
```

## 安装

```bash
uv sync
```

复制配置文件：

```bash
cp .env.example .env
```

`.env` 示例：

```env
MOONSHOT_API_KEY=your_moonshot_api_key
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=kimi-k2-0711-preview
WHISPER_MODEL=base
WHISPER_LANGUAGE=zh
```

配置说明：

- `MOONSHOT_API_KEY`：Kimi API Key
- `MOONSHOT_BASE_URL`：Moonshot OpenAI 兼容接口地址
- `MOONSHOT_MODEL`：Kimi 模型名
- `WHISPER_MODEL`：本地 Whisper 模型，默认 `base`
- `WHISPER_LANGUAGE`：转写语言，默认 `zh`

## 运行方式

默认示例：

```bash
uv run langchain-bilibili
```

分析本地转写文本：

```bash
uv run langchain-bilibili --input ./your_transcript.txt
```

按 `BV` 号运行：

```bash
uv run langchain-bilibili --bv BV1demo4117Kx
```

按 B 站 URL 运行：

```bash
uv run langchain-bilibili --url "https://www.bilibili.com/video/BV1demo4117Kx"
```

带问题运行：

```bash
uv run langchain-bilibili --question "视频里有没有提到向量检索？"
```

输出 JSON：

```bash
uv run langchain-bilibili --question "视频里有哪些功能？" --json
```

禁用 Kimi，强制使用本地回退模式：

```bash
uv run langchain-bilibili --disable-llm
```

## 真实 B 站处理

如果你希望对真实 B 站视频执行下载和转写，可以启用：

```bash
uv run langchain-bilibili --real-bilibili --url "https://www.bilibili.com/video/BVxxxxxxxxxx"
```

说明：

- 默认 `--bv` 和 `--url` 会优先走本地示例索引，便于离线开发
- 加上 `--real-bilibili` 后，程序会尝试调用 `yt-dlp` 下载音频，再调用 `whisper` 生成转写
- 下载的音频与生成的转写会缓存到 `artifacts/`
- 同一个视频如果已经缓存过，会优先复用缓存结果

首次运行真实转写时，Whisper 可能需要下载模型文件。当前默认模型是 `base`，比 `medium` 或 `large` 更适合先验证链路。

## 输入文本格式

本地文本可以直接使用普通转写内容：

```text
大家好，这里是第一段。
这里是第二段。
```

也兼容带时间戳的格式：

```text
[00:00] 大家好，这里是第一段。
[00:08] 这里是第二段。
```

当前版本不会展示时间线信息，而是直接展示视频内容本身。

## 输出内容

程序当前会输出以下几类结果：

- 视频来源信息
- 摘要
- 标签
- 关键内容片段
- 问答结果
- 结构化 JSON 输出

是否使用了 Kimi，会在结果里显示 `summary_mode`、`tags_mode`、`answer_mode`。

## 项目结构

```text
sample_data/sample_video.txt         示例转写文本
sample_data/bilibili_videos.json     本地 B 站示例索引
artifacts/downloads/                 下载音频缓存
artifacts/transcripts/               转写文本缓存
src/langchain_bilibili/config.py     配置加载
src/langchain_bilibili/loaders.py    视频来源解析
src/langchain_bilibili/llm.py        Kimi 调用封装
src/langchain_bilibili/pipeline.py   主流程与 CLI
src/langchain_bilibili/tools.py      外部工具检查
src/langchain_bilibili/transcribe.py 下载与转写执行层
```

## 当前限制

- 默认的 `BV` / URL 分析模式仍以本地示例索引为主，真实抓取需要显式加 `--real-bilibili`
- 真实下载与转写依赖本机外部工具
- 向量库检索、OCR、抽帧、多模态分析还没有接入
- Kimi 在线调用依赖可用的 API Key 和网络环境

## 下一步方向

- 接入真实 B 站元数据抓取
- 增加转写结果持久化与索引管理
- 引入向量库做更稳定的片段检索
- 接入 OCR 和视频抽帧
- 丰富标签分类与结构化输出
