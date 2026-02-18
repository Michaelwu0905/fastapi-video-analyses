from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx
import re
import datetime
import sys
import os

# 确保能找到同目录下的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, save_comments, get_comments, get_comment_count


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
            
            return {
                "status": "success",
                "bvid": bvid,
                "total_fetched": len(all_comments),
                "saved_count": saved_count,
                "msg": f"成功爬取并保存{saved_count}条评论"
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


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "B站视频分析系统运行正常"}
