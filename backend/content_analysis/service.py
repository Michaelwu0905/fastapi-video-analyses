from __future__ import annotations

import asyncio
from typing import Any

from .pipeline import run_demo


def build_content_analysis_payload(result: dict) -> dict:
    """提取前端展示所需的内容分析字段，避免返回过大的中间结果。"""
    source = result.get("source", {}) or {}
    return {
        "summary": result.get("summary", ""),
        "summary_mode": result.get("summary_mode", "fallback"),
        "tags": result.get("tags", []),
        "tags_mode": result.get("tags_mode", "fallback"),
        "highlights": result.get("highlights", [])[:3],
        "source": {
            "type": source.get("type", ""),
            "title": source.get("title", ""),
            "identifier": source.get("identifier", ""),
            "uploader": source.get("uploader", ""),
            "description": source.get("description", ""),
            "url": source.get("url", ""),
        },
    }


def get_content_analysis_task(tasks: dict[str, dict[str, Any]], bvid: str) -> dict[str, Any]:
    return tasks.setdefault(
        bvid,
        {
            "status": "idle",
            "message": "尚未开始内容分析",
            "content_analysis": None,
            "error": None,
        },
    )


async def run_real_content_analysis_task(tasks: dict[str, dict[str, Any]], bvid: str, url: str):
    task = get_content_analysis_task(tasks, bvid)
    task.update(
        {
            "status": "running",
            "message": "正在下载音频并转写视频内容，这一步可能需要数分钟",
            "error": None,
        }
    )

    try:
        result = await asyncio.to_thread(
            run_demo,
            url=url,
            use_llm=True,
            use_real_bilibili=True,
        )
        task.update(
            {
                "status": "success",
                "message": "视频内容分析完成",
                "content_analysis": build_content_analysis_payload(result),
                "error": None,
            }
        )
    except ImportError as exc:
        task.update(
            {
                "status": "error",
                "message": "内容分析依赖未安装",
                "error": str(exc),
            }
        )
    except Exception as exc:
        task.update(
            {
                "status": "error",
                "message": "真实视频内容分析失败",
                "error": str(exc),
            }
        )
