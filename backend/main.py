from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Any
import httpx
import re
import datetime
import asyncio

from database import (
    init_db, save_comments, get_comments, get_comment_count,
    get_pending_comments, update_sentiments, get_sentiment_stats
)
from sentiment import analyze_batch_async
from content_analysis.pipeline import run_demo


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


def get_content_analysis_task(bvid: str) -> dict[str, Any]:
    return CONTENT_ANALYSIS_TASKS.setdefault(
        bvid,
        {
            "status": "idle",
            "message": "尚未开始内容分析",
            "content_analysis": None,
            "error": None,
        },
    )


async def run_real_content_analysis_task(bvid: str, url: str):
    task = get_content_analysis_task(bvid)
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


# 通用请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com"
}


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

    task = get_content_analysis_task(bvid)
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
    asyncio.create_task(run_real_content_analysis_task(bvid, url))
    return {
        "status": "accepted",
        "bvid": bvid,
        "task_status": "queued",
        "message": task["message"],
    }


@app.get("/api/content-analysis/status/{bvid}")
async def get_video_content_analysis_status(bvid: str):
    """查询真实视频内容分析任务状态。"""
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
            
            return {
                "status": "success",
                "bvid": bvid,
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
                "saved_comments_count": saved_count,  # 已保存的评论数
                # 传播力指标
                "composite_score": round(composite_score, 2),
                "composite_score_formatted": format_number(round(composite_score, 2)),
                "stickiness": round(stickiness, 4),
                "stickiness_percent": f"{stickiness * 100:.2f}%",
                "msg": "成功访问B站视频"
            }
            
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
            "comments": comments,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取情感结果失败：{str(exc)}")


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "B站视频分析系统运行正常"}
