from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import re

app = FastAPI(title="B站视频分析系统")

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

# 响应模型
class VideoInfo(BaseModel):
    status: str
    bvid: str
    title: str
    author: str
    author_face: str
    cover: str
    desc: str
    view: int          # 播放量
    danmaku: int       # 弹幕数
    like: int          # 点赞数
    coin: int          # 投币数
    favorite: int      # 收藏数
    share: int         # 分享数
    reply: int         # 评论数
    duration: int      # 时长（秒）
    pubdate: str       # 发布时间
    msg: str


def extract_bvid(url: str) -> str:
    """从B站URL中提取BV号"""
    # 匹配各种B站链接格式
    patterns = [
        r'BV[a-zA-Z0-9]+',  # 直接匹配BV号
        r'bilibili\.com/video/(BV[a-zA-Z0-9]+)',  # 标准视频链接
        r'b23\.tv/([a-zA-Z0-9]+)',  # 短链接
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            bvid = match.group(0) if 'BV' in match.group(0) else match.group(1)
            if bvid.startswith('BV'):
                return bvid
            # 处理短链接情况，需要重定向获取真实BV号
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
    
    # 伪装浏览器请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 处理短链接，获取重定向后的真实URL
            if 'b23.tv' in url:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                url = str(resp.url)
                print(f"短链接重定向到：{url}")
            
            # 提取BV号
            bvid = extract_bvid(url)
            if not bvid:
                raise HTTPException(status_code=400, detail="无法从链接中提取BV号，请检查链接格式")
            
            print(f"提取到BV号：{bvid}")
            
            # 调用B站官方API获取视频信息
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            response = await client.get(api_url, headers=headers)
            data = response.json()
            
            # 检查API返回状态
            if data.get("code") != 0:
                error_msg = data.get("message", "未知错误")
                raise HTTPException(status_code=400, detail=f"B站API返回错误：{error_msg}")
            
            video_data = data.get("data", {})
            stat = video_data.get("stat", {})
            owner = video_data.get("owner", {})
            
            # 格式化发布时间
            import datetime
            pubdate_timestamp = video_data.get("pubdate", 0)
            pubdate = datetime.datetime.fromtimestamp(pubdate_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                "status": "success",
                "bvid": bvid,
                "title": video_data.get("title", "未知标题"),
                "author": owner.get("name", "未知UP主"),
                "author_face": owner.get("face", ""),
                "cover": video_data.get("pic", ""),
                "desc": video_data.get("desc", "暂无简介"),
                "view": stat.get("view", 0),
                "view_formatted": format_number(stat.get("view", 0)),
                "danmaku": stat.get("danmaku", 0),
                "danmaku_formatted": format_number(stat.get("danmaku", 0)),
                "like": stat.get("like", 0),
                "like_formatted": format_number(stat.get("like", 0)),
                "coin": stat.get("coin", 0),
                "coin_formatted": format_number(stat.get("coin", 0)),
                "favorite": stat.get("favorite", 0),
                "favorite_formatted": format_number(stat.get("favorite", 0)),
                "share": stat.get("share", 0),
                "share_formatted": format_number(stat.get("share", 0)),
                "reply": stat.get("reply", 0),
                "reply_formatted": format_number(stat.get("reply", 0)),
                "duration": video_data.get("duration", 0),
                "duration_formatted": format_duration(video_data.get("duration", 0)),
                "pubdate": pubdate,
                "msg": "✅ 成功访问B站视频！"
            }
            
        except httpx.RequestError as exc:
            raise HTTPException(status_code=400, detail=f"网络请求错误：{str(exc)}")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(exc)}")


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "B站视频分析系统运行正常"}
