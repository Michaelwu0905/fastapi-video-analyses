from __future__ import annotations

import asyncio
import os
import re
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from content_analysis.service import get_content_analysis_task, run_real_content_analysis_task


app = FastAPI(title="B站视频内容分析 Worker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VideoRequest(BaseModel):
    url: str


CONTENT_ANALYSIS_TASKS: dict[str, dict[str, Any]] = {}


def extract_bvid(url: str) -> str | None:
    patterns = [
        r"BV[a-zA-Z0-9]+",
        r"bilibili\.com/video/(BV[a-zA-Z0-9]+)",
        r"b23\.tv/([a-zA-Z0-9]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            bvid = match.group(0) if "BV" in match.group(0) else match.group(1)
            if bvid.startswith("BV"):
                return bvid
            return bvid

    return None


def verify_worker_token(x_worker_token: str | None) -> None:
    expected = os.getenv("CONTENT_ANALYSIS_WORKER_TOKEN", "").strip()
    if expected and x_worker_token != expected:
        raise HTTPException(status_code=401, detail="worker token 校验失败")


@app.post("/worker/content-analysis/start-real")
async def start_real_video_content_analysis(
    request: VideoRequest,
    x_worker_token: str | None = Header(default=None),
):
    verify_worker_token(x_worker_token)

    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="视频链接不能为空")

    bvid = extract_bvid(url)
    if not bvid:
        raise HTTPException(status_code=400, detail="无法从链接中提取BV号，请检查链接格式")

    task = get_content_analysis_task(CONTENT_ANALYSIS_TASKS, bvid)
    if task["status"] in {"queued", "running"}:
        return {
            "status": "accepted",
            "bvid": bvid,
            "task_status": task["status"],
            "message": task["message"],
        }

    if task["status"] == "success" and task["content_analysis"]:
        return {
            "status": "success",
            "bvid": bvid,
            "task_status": "success",
            "message": task["message"],
            "content_analysis": task["content_analysis"],
        }

    task.update(
        {
            "status": "queued",
            "message": "已创建真实视频内容分析任务，正在排队执行",
            "content_analysis": None,
            "error": None,
        }
    )
    asyncio.create_task(run_real_content_analysis_task(CONTENT_ANALYSIS_TASKS, bvid, url))
    return {
        "status": "accepted",
        "bvid": bvid,
        "task_status": "queued",
        "message": task["message"],
    }


@app.get("/worker/content-analysis/status/{bvid}")
async def get_video_content_analysis_status(
    bvid: str,
    x_worker_token: str | None = Header(default=None),
):
    verify_worker_token(x_worker_token)

    task = CONTENT_ANALYSIS_TASKS.get(bvid)
    if task is None:
        raise HTTPException(status_code=404, detail="未找到该视频的内容分析任务")

    return {
        "status": "success",
        "bvid": bvid,
        "task_status": task["status"],
        "message": task["message"],
        "finished": task["status"] in {"success", "error"},
        "error": task["error"],
    }


@app.get("/worker/content-analysis/result/{bvid}")
async def get_video_content_analysis_result(
    bvid: str,
    x_worker_token: str | None = Header(default=None),
):
    verify_worker_token(x_worker_token)

    task = CONTENT_ANALYSIS_TASKS.get(bvid)
    if task is None:
        raise HTTPException(status_code=404, detail="未找到该视频的内容分析任务")

    if task["status"] == "success" and task["content_analysis"]:
        return {
            "status": "success",
            "bvid": bvid,
            "content_analysis": task["content_analysis"],
        }

    if task["status"] == "error":
        raise HTTPException(status_code=500, detail=task["error"] or "内容分析失败")

    raise HTTPException(status_code=409, detail="内容分析尚未完成")


@app.get("/worker/health")
async def health_check(x_worker_token: str | None = Header(default=None)):
    verify_worker_token(x_worker_token)
    return {"status": "ok", "message": "内容分析 worker 运行正常"}
