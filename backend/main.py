from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Any
from pathlib import Path
import httpx
import re
import datetime
import asyncio
import os

from database import (
    init_db, save_comments, get_comments, get_comment_count,
    get_pending_comments, update_sentiments, get_sentiment_stats,
    save_analysis_history, update_analysis_history_summary, get_recent_analysis_history,
)
from sentiment import analyze_batch_async
from content_analysis.pipeline import run_demo
from content_analysis.service import (
    build_content_analysis_payload,
    get_content_analysis_task,
    run_real_content_analysis_task,
)


async def run_sentiment_analysis(bvid: str):
    """后台情感分析任务：对指定视频的所有待分析评论批量推理并写回数据库"""
    try:
        pending = await get_pending_comments(bvid)
        if not pending:
            print(f"[情感分析] {bvid} 无待分析评论，跳过。")
            return

        print(f"[情感分析] 开始分析 {bvid}，共 {len(pending)} 条评论...")
        texts = [item["content"] for item in pending]
        ids   = [item["id"]      for item in pending]

        labels = await analyze_batch_async(texts)

        results = [{"id": id_, "sentiment": label} for id_, label in zip(ids, labels)]
        await update_sentiments(results)
        print(f"[情感分析] {bvid} 分析完成，共写入 {len(results)} 条标签。")
    except Exception as e:
        print(f"[情感分析] {bvid} 分析失败：{e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    print("数据库初始化完成")
    yield
    # 关闭时的清理工作（如需要）


app = FastAPI(title="B站视频分析系统", lifespan=lifespan)

# 配置CORS，允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class VideoRequest(BaseModel):
    url: str

class CommentRequest(BaseModel):
    bvid: str
    aid: int  # 需要aid来调用评论API


CONTENT_ANALYSIS_TASKS: dict[str, dict[str, Any]] = {}
CONTENT_ANALYSIS_WORKER_URL = os.getenv("CONTENT_ANALYSIS_WORKER_URL", "").strip().rstrip("/")
CONTENT_ANALYSIS_WORKER_TOKEN = os.getenv("CONTENT_ANALYSIS_WORKER_TOKEN", "").strip()
FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


# 通用请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com"
}

COGNITIVE_FEEDBACK_KEYWORDS = [
    "学到了", "涨知识", "长知识", "看懂了", "懂了", "原来如此",
    "原来是", "受教了", "科普", "明白了", "了解了",
]

QUESTION_COMMENT_KEYWORDS = [
    "为什么", "怎么", "如何", "是不是", "真的吗",
    "能不能", "有没有", "为啥", "啥意思", "求解释",
]


def extract_bvid(url: str) -> str:
    """从B站URL中提取BV号"""
    patterns = [
        r'BV[a-zA-Z0-9]+',
        r'bilibili\.com/video/(BV[a-zA-Z0-9]+)',
        r'b23\.tv/([a-zA-Z0-9]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            bvid = match.group(0) if 'BV' in match.group(0) else match.group(1)
            if bvid.startswith('BV'):
                return bvid
            return bvid
    
    return None


def format_duration(seconds: int) -> str:
    """将秒数格式化为 mm:ss 或 hh:mm:ss"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_number(num: int) -> str:
    """格式化数字，大于1万显示为 x.x万"""
    if num >= 10000:
        return f"{num/10000:.1f}万"
    return str(num)


def safe_div(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    lowered = text.strip().lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def build_knowledge_effect_stats(comments: list[dict], sentiment_stats: dict) -> dict:
    total = len(comments)
    if total == 0:
        return {
            "cognitive_feedback_count": 0,
            "cognitive_feedback_ratio": 0,
            "cognitive_feedback_ratio_percent": "0.00%",
            "question_comment_count": 0,
            "question_comment_ratio": 0,
            "question_comment_ratio_percent": "0.00%",
            "sentiment_polarization": 0,
            "sentiment_polarization_percent": "0.00%",
            "controversy_score": 0,
            "controversy_score_percent": "0.00%",
        }

    cognitive_feedback_count = sum(
        1 for comment in comments
        if contains_any_keyword(comment.get("content", ""), COGNITIVE_FEEDBACK_KEYWORDS)
    )
    question_comment_count = sum(
        1 for comment in comments
        if "？" in comment.get("content", "")
        or "?" in comment.get("content", "")
        or contains_any_keyword(comment.get("content", ""), QUESTION_COMMENT_KEYWORDS)
    )

    cognitive_feedback_ratio = safe_div(cognitive_feedback_count, total)
    question_comment_ratio = safe_div(question_comment_count, total)
    sentiment_polarization = safe_div(
        sentiment_stats.get("positive", 0) + sentiment_stats.get("negative", 0),
        total,
    )
    controversy_score = safe_div(
        min(sentiment_stats.get("positive", 0), sentiment_stats.get("negative", 0)) * 2,
        total,
    )

    return {
        "cognitive_feedback_count": cognitive_feedback_count,
        "cognitive_feedback_ratio": round(cognitive_feedback_ratio, 6),
        "cognitive_feedback_ratio_percent": format_percent(cognitive_feedback_ratio),
        "question_comment_count": question_comment_count,
        "question_comment_ratio": round(question_comment_ratio, 6),
        "question_comment_ratio_percent": format_percent(question_comment_ratio),
        "sentiment_polarization": round(sentiment_polarization, 6),
        "sentiment_polarization_percent": format_percent(sentiment_polarization),
        "controversy_score": round(controversy_score, 6),
        "controversy_score_percent": format_percent(controversy_score),
    }


def worker_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    if CONTENT_ANALYSIS_WORKER_TOKEN:
        headers["X-Worker-Token"] = CONTENT_ANALYSIS_WORKER_TOKEN
    return headers


async def call_content_analysis_worker(method: str, path: str, json_body: dict | None = None) -> dict:
    if not CONTENT_ANALYSIS_WORKER_URL:
        raise HTTPException(status_code=503, detail="内容分析 worker 未配置")

    url = f"{CONTENT_ANALYSIS_WORKER_URL}{path}"
    timeout = httpx.Timeout(10.0, read=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.request(
                method,
                url,
                json=json_body,
                headers=worker_headers(),
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"连接内容分析 worker 失败：{str(exc)}")

    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text or "worker 返回了无效响应"}

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=payload.get("detail", "worker 请求失败"))

    return payload


@app.post("/api/content-analysis")
async def analyze_video_content(request: VideoRequest):
    """分析视频内容，当前阶段优先走本地转写索引与规则回退。"""
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="视频链接不能为空")

    try:
        result = await asyncio.to_thread(
            run_demo,
            url=url,
            use_llm=False,
            use_real_bilibili=False,
        )
        bvid = extract_bvid(url)
        if bvid:
            await update_analysis_history_summary(
                bvid,
                result.get("summary", ""),
            )
        return {
            "status": "success",
            "content_analysis": build_content_analysis_payload(result),
        }
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="当前内容分析仅支持后端内置示例索引中的 BV 号，尚未命中真实转写链路",
        )
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=f"内容分析依赖未安装：{str(exc)}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"内容分析参数错误：{str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"内容分析失败：{str(exc)}")


@app.post("/api/content-analysis/start-real")
async def start_real_video_content_analysis(request: VideoRequest):
    """对任意 B 站视频启动真实下载、转写和内容分析任务。"""
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="视频链接不能为空")

    bvid = extract_bvid(url)
    if not bvid:
        raise HTTPException(status_code=400, detail="无法从链接中提取BV号，请检查链接格式")

    if CONTENT_ANALYSIS_WORKER_URL:
        payload = await call_content_analysis_worker(
            "POST",
            "/worker/content-analysis/start-real",
            {"url": url},
        )
        if payload.get("task_status") == "success" and payload.get("content_analysis"):
            await update_analysis_history_summary(
                bvid,
                payload["content_analysis"].get("summary", ""),
            )
        return payload

    task = get_content_analysis_task(CONTENT_ANALYSIS_TASKS, bvid)
    if task["status"] in {"queued", "running"}:
        return {
            "status": "accepted",
            "bvid": bvid,
            "task_status": task["status"],
            "message": task["message"],
        }

    if task["status"] == "success" and task["content_analysis"]:
        await update_analysis_history_summary(
            bvid,
            task["content_analysis"].get("summary", ""),
        )
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


@app.get("/api/content-analysis/status/{bvid}")
async def get_video_content_analysis_status(bvid: str):
    """查询真实视频内容分析任务状态。"""
    if CONTENT_ANALYSIS_WORKER_URL:
        return await call_content_analysis_worker(
            "GET",
            f"/worker/content-analysis/status/{bvid}",
        )

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


@app.get("/api/content-analysis/result/{bvid}")
async def get_video_content_analysis_result(bvid: str):
    """获取真实视频内容分析结果。"""
    if CONTENT_ANALYSIS_WORKER_URL:
        payload = await call_content_analysis_worker(
            "GET",
            f"/worker/content-analysis/result/{bvid}",
        )
        await update_analysis_history_summary(
            bvid,
            payload["content_analysis"].get("summary", ""),
        )
        return payload

    task = CONTENT_ANALYSIS_TASKS.get(bvid)
    if task is None:
        raise HTTPException(status_code=404, detail="未找到该视频的内容分析任务")

    if task["status"] == "success" and task["content_analysis"]:
        await update_analysis_history_summary(
            bvid,
            task["content_analysis"].get("summary", ""),
        )
        return {
            "status": "success",
            "bvid": bvid,
            "content_analysis": task["content_analysis"],
        }

    if task["status"] == "error":
        raise HTTPException(status_code=500, detail=task["error"] or "内容分析失败")

    raise HTTPException(status_code=409, detail="内容分析尚未完成")


@app.post("/api/analyze")
async def analyze_video(request: VideoRequest):
    """分析B站视频，获取详细信息"""
    url = request.url.strip()
    print(f"收到请求，正在分析：{url}")
    
    async with httpx.AsyncClient() as client:
        try:
            # 处理短链接
            if 'b23.tv' in url:
                resp = await client.get(url, headers=HEADERS, follow_redirects=True)
                url = str(resp.url)
                print(f"短链接重定向到：{url}")
            
            # 提取BV号
            bvid = extract_bvid(url)
            if not bvid:
                raise HTTPException(status_code=400, detail="无法从链接中提取BV号，请检查链接格式")
            
            print(f"提取到BV号：{bvid}")
            
            # 调用B站官方API获取视频信息
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            response = await client.get(api_url, headers=HEADERS)
            data = response.json()
            
            if data.get("code") != 0:
                error_msg = data.get("message", "未知错误")
                raise HTTPException(status_code=400, detail=f"B站API返回错误：{error_msg}")
            
            video_data = data.get("data", {})
            stat = video_data.get("stat", {})
            owner = video_data.get("owner", {})
            
            pubdate_timestamp = video_data.get("pubdate", 0)
            pubdate = datetime.datetime.fromtimestamp(pubdate_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            age_days = max(1, (datetime.datetime.now() - datetime.datetime.fromtimestamp(pubdate_timestamp)).days + 1)
            
            # 查询已爬取的评论数量
            saved_count = await get_comment_count(bvid)
            
            # 提取统计数据用于计算传播力指标
            view = stat.get("view", 0)
            danmaku = stat.get("danmaku", 0)
            coin = stat.get("coin", 0)
            favorite = stat.get("favorite", 0)
            like = stat.get("like", 0)
            share = stat.get("share", 0)
            reply = stat.get("reply", 0)
            
            # 计算综合得分
            composite_score = (0.728 * view + 0.154 * danmaku + 0.327 * coin 
                             + 0.242 * favorite - 0.192 * like - 0.157 * share)
            
            # 计算粘性度 (避免除零)
            stickiness = (coin + favorite + share) / view if view > 0 else 0
            daily_views = view / age_days
            like_rate = safe_div(like, view)
            coin_rate = safe_div(coin, view)
            favorite_rate = safe_div(favorite, view)
            share_rate = safe_div(share, view)
            reply_rate = safe_div(reply, view)
            composite_interaction_rate = safe_div(reply + danmaku, view)
            recognition_rate = safe_div(coin + favorite + share, view)
            danmaku_density = safe_div(danmaku, max(video_data.get("duration", 0) / 60, 1))
            
            result = {
                "status": "success",
                "bvid": bvid,
                "url": url,
                "aid": video_data.get("aid", 0),  # 返回aid用于评论爬取
                "title": video_data.get("title", "未知标题"),
                "author": owner.get("name", "未知UP主"),
                "author_face": owner.get("face", ""),
                "cover": video_data.get("pic", ""),
                "desc": video_data.get("desc", "暂无简介"),
                "view": view,
                "view_formatted": format_number(view),
                "danmaku": danmaku,
                "danmaku_formatted": format_number(danmaku),
                "like": like,
                "like_formatted": format_number(like),
                "coin": coin,
                "coin_formatted": format_number(coin),
                "favorite": favorite,
                "favorite_formatted": format_number(favorite),
                "share": share,
                "share_formatted": format_number(share),
                "reply": reply,
                "reply_formatted": format_number(reply),
                "duration": video_data.get("duration", 0),
                "duration_formatted": format_duration(video_data.get("duration", 0)),
                "pubdate": pubdate,
                "age_days": age_days,
                "saved_comments_count": saved_count,  # 已保存的评论数
                # 传播力指标
                "composite_score": round(composite_score, 2),
                "composite_score_formatted": format_number(round(composite_score, 2)),
                "stickiness": round(stickiness, 4),
                "stickiness_percent": f"{stickiness * 100:.2f}%",
                "daily_views": round(daily_views, 2),
                "daily_views_formatted": format_number(round(daily_views)),
                "like_rate": round(like_rate, 6),
                "like_rate_percent": format_percent(like_rate),
                "coin_rate": round(coin_rate, 6),
                "coin_rate_percent": format_percent(coin_rate),
                "favorite_rate": round(favorite_rate, 6),
                "favorite_rate_percent": format_percent(favorite_rate),
                "share_rate": round(share_rate, 6),
                "share_rate_percent": format_percent(share_rate),
                "reply_rate": round(reply_rate, 6),
                "reply_rate_percent": format_percent(reply_rate),
                "composite_interaction_rate": round(composite_interaction_rate, 6),
                "composite_interaction_rate_percent": format_percent(composite_interaction_rate),
                "recognition_rate": round(recognition_rate, 6),
                "recognition_rate_percent": format_percent(recognition_rate),
                "danmaku_density": round(danmaku_density, 2),
                "danmaku_density_formatted": f"{danmaku_density:.2f}条/分钟",
                "msg": "成功访问B站视频"
            }
            await save_analysis_history(result)
            return result
            
        except httpx.RequestError as exc:
            raise HTTPException(status_code=400, detail=f"网络请求错误：{str(exc)}")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(exc)}")


@app.post("/api/fetch-comments")
async def fetch_comments(request: CommentRequest):
    """爬取B站视频评论并保存到数据库"""
    bvid = request.bvid
    aid = request.aid
    
    print(f"开始爬取评论：bvid={bvid}, aid={aid}")
    
    all_comments = []
    seen_rpids = set()  # 用于爬虫层去重，避免分页重叠导致重复
    page = 1
    max_pages = 10  # 最多爬取10页，避免请求过多
    
    async with httpx.AsyncClient() as client:
        try:
            while page <= max_pages:
                # B站评论API
                api_url = f"https://api.bilibili.com/x/v2/reply/main?type=1&oid={aid}&mode=3&ps=20&pn={page}"
                response = await client.get(api_url, headers=HEADERS)
                data = response.json()
                
                if data.get("code") != 0:
                    break
                
                replies = data.get("data", {}).get("replies", [])
                if not replies:
                    break
                
                new_count = 0
                # 提取评论内容，用 rpid（评论唯一ID）去重
                for reply in replies:
                    rpid = reply.get("rpid")
                    content = reply.get("content", {}).get("message", "")
                    if content and rpid and rpid not in seen_rpids:
                        seen_rpids.add(rpid)
                        all_comments.append(content)
                        new_count += 1
                
                print(f"已爬取第{page}页，新增{new_count}条评论（本页共{len(replies)}条）")
                page += 1
            
            # 保存到数据库
            saved_count = await save_comments(bvid, all_comments)

            # 触发后台情感分析任务（不阻塞当前请求）
            asyncio.create_task(run_sentiment_analysis(bvid))
            print(f"[情感分析] 已为 {bvid} 启动后台分析任务")

            return {
                "status": "success",
                "bvid": bvid,
                "total_fetched": len(all_comments),
                "saved_count": saved_count,
                "msg": f"成功爬取并保存{saved_count}条评论，情感分析已在后台启动"
            }

        except httpx.RequestError as exc:
            raise HTTPException(status_code=400, detail=f"网络请求错误：{str(exc)}")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"爬取评论失败：{str(exc)}")


@app.get("/api/comments/{bvid}")
async def get_video_comments(bvid: str):
    """获取已保存的评论列表"""
    try:
        comments = await get_comments(bvid)
        return {
            "status": "success",
            "bvid": bvid,
            "total": len(comments),
            "comments": comments
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取评论失败：{str(exc)}")


@app.get("/api/sentiment-status/{bvid}")
async def get_sentiment_status(bvid: str):
    """查询情感分析进度"""
    try:
        stats = await get_sentiment_stats(bvid)
        total   = stats["total"]
        pending = stats["pending"]
        analyzed = total - pending
        return {
            "status": "success",
            "bvid": bvid,
            "total": total,
            "analyzed": analyzed,
            "finished": (pending == 0 and total > 0),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询进度失败：{str(exc)}")


@app.get("/api/sentiment/{bvid}")
async def get_sentiment_result(bvid: str):
    """获取情感分析统计结果与带标签的评论列表"""
    try:
        stats    = await get_sentiment_stats(bvid)
        comments = await get_comments(bvid)
        knowledge_effect = build_knowledge_effect_stats(comments, stats)
        return {
            "status": "success",
            "bvid": bvid,
            "stats": {
                "positive": stats["positive"],
                "neutral":  stats["neutral"],
                "negative": stats["negative"],
                "pending":  stats["pending"],
                "total":    stats["total"],
            },
            "knowledge_effect": knowledge_effect,
            "comments": comments,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取情感结果失败：{str(exc)}")


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "message": "B站视频分析系统运行正常",
        "content_analysis_worker_configured": bool(CONTENT_ANALYSIS_WORKER_URL),
    }


@app.get("/api/history")
async def get_analysis_history():
    """获取最近10条视频分析历史。"""
    try:
        items = await get_recent_analysis_history(limit=10)
        return {
            "status": "success",
            "items": items,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取分析历史失败：{str(exc)}")


if (FRONTEND_DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST_DIR / "assets"), name="frontend-assets")


if (FRONTEND_DIST_DIR / "index.html").exists():
    @app.get("/")
    async def serve_frontend_index():
        return FileResponse(FRONTEND_DIST_DIR / "index.html")


    @app.get("/{full_path:path}")
    async def serve_frontend_app(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="接口不存在")

        requested_path = FRONTEND_DIST_DIR / full_path
        if requested_path.is_file():
            return FileResponse(requested_path)

        return FileResponse(FRONTEND_DIST_DIR / "index.html")
