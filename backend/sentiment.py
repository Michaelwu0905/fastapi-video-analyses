"""
情感分析模块：使用 DistilBERT 多语言模型对中文评论进行三分类。
模型：lxyuan/distilbert-base-multilingual-cased-sentiments-student
分类：positive（正面）/ neutral（中性）/ negative（负面）

采用单例模式，避免重复加载模型。
首次使用时自动从 Hugging Face 下载模型（约 250MB），之后从本地缓存读取。
"""

import asyncio
from functools import lru_cache

# 懒加载：仅在首次调用时才导入 transformers，避免启动变慢
_pipeline = None


def _get_pipeline():
    """单例模式加载模型，自动选择 GPU/CPU。"""
    global _pipeline
    if _pipeline is None:
        from transformers import pipeline
        import torch

        device = 0 if torch.cuda.is_available() else -1
        device_name = "GPU" if device == 0 else "CPU"
        print(f"[情感分析] 正在加载 DistilBERT 模型（使用 {device_name}）...")

        _pipeline = pipeline(
            "sentiment-analysis",
            model="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
            device=device,
            truncation=True,
            max_length=512,
        )
        print("[情感分析] 模型加载完成。")
    return _pipeline


# 标签映射：将模型输出统一为中文兼容的英文标签
_LABEL_MAP = {
    "positive": "positive",
    "neutral": "neutral",
    "negative": "negative",
}

# 置信度阈值：低于此值归为 neutral（避免强行二分）
_CONFIDENCE_THRESHOLD = 0.70


def analyze_batch(texts: list[str]) -> list[str]:
    """
    批量推理，返回与输入等长的标签列表。
    标签值为 'positive' / 'neutral' / 'negative'。

    Args:
        texts: 评论文本列表

    Returns:
        对应的情感标签列表
    """
    if not texts:
        return []

    pipe = _get_pipeline()

    # batch_size=32 在 CPU 上是合理大小，GPU 可适当增大
    results = pipe(texts, batch_size=32)

    labels = []
    for result in results:
        raw_label = result["label"].lower()
        score = result["score"]

        # 置信度不足时归为中性
        if score < _CONFIDENCE_THRESHOLD:
            label = "neutral"
        else:
            label = _LABEL_MAP.get(raw_label, "neutral")

        labels.append(label)

    return labels


async def analyze_batch_async(texts: list[str]) -> list[str]:
    """
    异步版批量推理：在线程池中运行，避免阻塞事件循环。
    FastAPI 后台任务应调用此函数。
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, analyze_batch, texts)
