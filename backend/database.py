import aiosqlite
import os
import datetime

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "comments.db")


async def init_db():
    """初始化数据库，创建评论表（含迁移逻辑）"""
    async with aiosqlite.connect(DB_PATH) as db:
        # 检查旧表是否存在且缺少 UNIQUE 约束，若是则重建
        cursor = await db.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='comments'"
        )
        row = await cursor.fetchone()
        if row and "UNIQUE" not in row[0]:
            # 旧表无 UNIQUE 约束，重建以支持去重
            print("检测到旧版 comments 表，正在迁移（重建以添加 UNIQUE 约束）...")
            await db.execute("DROP TABLE IF EXISTS comments")
            await db.execute("DROP INDEX IF EXISTS idx_bvid")

        # 创建表（含 UNIQUE 约束，防止同一视频下重复评论入库）
        await db.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bvid TEXT NOT NULL,
                content TEXT NOT NULL,
                sentiment TEXT DEFAULT NULL,
                UNIQUE(bvid, content)
            )
        """)
        # 创建索引加速查询
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_bvid ON comments(bvid)
        """)
        await db.commit()

        # 迁移：若表已存在但缺少 sentiment 字段，则补充添加
        cursor = await db.execute("PRAGMA table_info(comments)")
        columns = [col[1] for col in await cursor.fetchall()]
        if "sentiment" not in columns:
            print("检测到旧版 comments 表缺少 sentiment 字段，正在迁移...")
            await db.execute("ALTER TABLE comments ADD COLUMN sentiment TEXT DEFAULT NULL")
            await db.commit()

        await db.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bvid TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                cover TEXT DEFAULT '',
                pubdate TEXT DEFAULT '',
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                saved_comments_count INTEGER DEFAULT 0,
                composite_score REAL DEFAULT 0,
                composite_score_formatted TEXT DEFAULT '',
                stickiness_percent TEXT DEFAULT '',
                content_summary TEXT DEFAULT '',
                updated_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_history_updated_at
            ON analysis_history(updated_at DESC)
        """)
        await db.commit()

        cursor = await db.execute("PRAGMA table_info(analysis_history)")
        history_columns = [col[1] for col in await cursor.fetchall()]
        history_migrations = {
            "cover": "ALTER TABLE analysis_history ADD COLUMN cover TEXT DEFAULT ''",
            "pubdate": "ALTER TABLE analysis_history ADD COLUMN pubdate TEXT DEFAULT ''",
            "view_count": "ALTER TABLE analysis_history ADD COLUMN view_count INTEGER DEFAULT 0",
            "like_count": "ALTER TABLE analysis_history ADD COLUMN like_count INTEGER DEFAULT 0",
            "danmaku_count": "ALTER TABLE analysis_history ADD COLUMN danmaku_count INTEGER DEFAULT 0",
            "coin_count": "ALTER TABLE analysis_history ADD COLUMN coin_count INTEGER DEFAULT 0",
            "favorite_count": "ALTER TABLE analysis_history ADD COLUMN favorite_count INTEGER DEFAULT 0",
            "share_count": "ALTER TABLE analysis_history ADD COLUMN share_count INTEGER DEFAULT 0",
            "reply_count": "ALTER TABLE analysis_history ADD COLUMN reply_count INTEGER DEFAULT 0",
            "duration_seconds": "ALTER TABLE analysis_history ADD COLUMN duration_seconds INTEGER DEFAULT 0",
            "age_days": "ALTER TABLE analysis_history ADD COLUMN age_days INTEGER DEFAULT 0",
            "saved_comments_count": "ALTER TABLE analysis_history ADD COLUMN saved_comments_count INTEGER DEFAULT 0",
            "composite_score": "ALTER TABLE analysis_history ADD COLUMN composite_score REAL DEFAULT 0",
            "composite_score_formatted": "ALTER TABLE analysis_history ADD COLUMN composite_score_formatted TEXT DEFAULT ''",
            "stickiness_percent": "ALTER TABLE analysis_history ADD COLUMN stickiness_percent TEXT DEFAULT ''",
            "daily_views": "ALTER TABLE analysis_history ADD COLUMN daily_views REAL DEFAULT 0",
            "like_rate": "ALTER TABLE analysis_history ADD COLUMN like_rate REAL DEFAULT 0",
            "coin_rate": "ALTER TABLE analysis_history ADD COLUMN coin_rate REAL DEFAULT 0",
            "favorite_rate": "ALTER TABLE analysis_history ADD COLUMN favorite_rate REAL DEFAULT 0",
            "share_rate": "ALTER TABLE analysis_history ADD COLUMN share_rate REAL DEFAULT 0",
            "reply_rate": "ALTER TABLE analysis_history ADD COLUMN reply_rate REAL DEFAULT 0",
            "composite_interaction_rate": "ALTER TABLE analysis_history ADD COLUMN composite_interaction_rate REAL DEFAULT 0",
            "recognition_rate": "ALTER TABLE analysis_history ADD COLUMN recognition_rate REAL DEFAULT 0",
            "danmaku_density": "ALTER TABLE analysis_history ADD COLUMN danmaku_density REAL DEFAULT 0",
            "cognitive_feedback_ratio": "ALTER TABLE analysis_history ADD COLUMN cognitive_feedback_ratio REAL DEFAULT 0",
            "question_comment_ratio": "ALTER TABLE analysis_history ADD COLUMN question_comment_ratio REAL DEFAULT 0",
            "sentiment_polarization": "ALTER TABLE analysis_history ADD COLUMN sentiment_polarization REAL DEFAULT 0",
            "content_summary": "ALTER TABLE analysis_history ADD COLUMN content_summary TEXT DEFAULT ''",
            "updated_at": "ALTER TABLE analysis_history ADD COLUMN updated_at TEXT DEFAULT ''",
        }
        for column, sql in history_migrations.items():
            if column not in history_columns:
                await db.execute(sql)
        await db.commit()


def _history_timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def save_analysis_history(video_info: dict, content_summary: str | None = None):
    """写入或更新分析历史，仅保留最近10条。"""
    summary = content_summary
    if summary is None:
        summary = video_info.get("content_summary", "") or ""

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO analysis_history (
                bvid, url, title, author, cover, pubdate,
                view_count, like_count, danmaku_count, coin_count, favorite_count, share_count,
                reply_count, duration_seconds, age_days, saved_comments_count,
                composite_score, composite_score_formatted, stickiness_percent,
                daily_views, like_rate, coin_rate, favorite_rate, share_rate, reply_rate,
                composite_interaction_rate, recognition_rate, danmaku_density,
                content_summary, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(bvid) DO UPDATE SET
                url = excluded.url,
                title = excluded.title,
                author = excluded.author,
                cover = excluded.cover,
                pubdate = excluded.pubdate,
                view_count = excluded.view_count,
                like_count = excluded.like_count,
                danmaku_count = excluded.danmaku_count,
                coin_count = excluded.coin_count,
                favorite_count = excluded.favorite_count,
                share_count = excluded.share_count,
                reply_count = excluded.reply_count,
                duration_seconds = excluded.duration_seconds,
                age_days = excluded.age_days,
                saved_comments_count = excluded.saved_comments_count,
                composite_score = excluded.composite_score,
                composite_score_formatted = excluded.composite_score_formatted,
                stickiness_percent = excluded.stickiness_percent,
                daily_views = excluded.daily_views,
                like_rate = excluded.like_rate,
                coin_rate = excluded.coin_rate,
                favorite_rate = excluded.favorite_rate,
                share_rate = excluded.share_rate,
                reply_rate = excluded.reply_rate,
                composite_interaction_rate = excluded.composite_interaction_rate,
                recognition_rate = excluded.recognition_rate,
                danmaku_density = excluded.danmaku_density,
                content_summary = CASE
                    WHEN excluded.content_summary != '' THEN excluded.content_summary
                    ELSE analysis_history.content_summary
                END,
                updated_at = excluded.updated_at
            """,
            (
                video_info.get("bvid", ""),
                video_info.get("url", ""),
                video_info.get("title", "未知标题"),
                video_info.get("author", "未知UP主"),
                video_info.get("cover", ""),
                video_info.get("pubdate", ""),
                video_info.get("view", 0),
                video_info.get("like", 0),
                video_info.get("danmaku", 0),
                video_info.get("coin", 0),
                video_info.get("favorite", 0),
                video_info.get("share", 0),
                video_info.get("reply", 0),
                video_info.get("duration", 0),
                video_info.get("age_days", 0),
                video_info.get("saved_comments_count", 0),
                video_info.get("composite_score", 0),
                video_info.get("composite_score_formatted", ""),
                video_info.get("stickiness_percent", ""),
                video_info.get("daily_views", 0),
                video_info.get("like_rate", 0),
                video_info.get("coin_rate", 0),
                video_info.get("favorite_rate", 0),
                video_info.get("share_rate", 0),
                video_info.get("reply_rate", 0),
                video_info.get("composite_interaction_rate", 0),
                video_info.get("recognition_rate", 0),
                video_info.get("danmaku_density", 0),
                summary,
                _history_timestamp(),
            ),
        )
        await db.execute(
            """
            DELETE FROM analysis_history
            WHERE id NOT IN (
                SELECT id FROM analysis_history
                ORDER BY updated_at DESC, id DESC
                LIMIT 10
            )
            """
        )
        await db.commit()


async def update_analysis_history_summary(bvid: str, content_summary: str):
    """更新某条历史记录的内容摘要。"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE analysis_history
            SET content_summary = ?, updated_at = ?
            WHERE bvid = ?
            """,
            (content_summary, _history_timestamp(), bvid),
        )
        await db.commit()


async def update_analysis_history_knowledge_effect(bvid: str, knowledge_effect: dict):
    """更新某条历史记录的知识传播效果相关指标。"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE analysis_history
            SET
                cognitive_feedback_ratio = ?,
                question_comment_ratio = ?,
                sentiment_polarization = ?,
                updated_at = ?
            WHERE bvid = ?
            """,
            (
                knowledge_effect.get("cognitive_feedback_ratio", 0),
                knowledge_effect.get("question_comment_ratio", 0),
                knowledge_effect.get("sentiment_polarization", 0),
                _history_timestamp(),
                bvid,
            ),
        )
        await db.commit()


async def get_recent_analysis_history(limit: int = 10) -> list[dict]:
    """获取最近分析历史。"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                bvid, url, title, author, cover, pubdate,
                view_count, like_count, saved_comments_count,
                composite_score, composite_score_formatted,
                stickiness_percent, content_summary, updated_at
            FROM analysis_history
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_analysis_history_item(bvid: str) -> dict | None:
    """获取单条分析历史。"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM analysis_history WHERE bvid = ?",
            (bvid,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_analysis_history_samples(limit: int = 100) -> list[dict]:
    """获取用于评价模型计算的历史样本。"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM analysis_history
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def save_comments(bvid: str, comments: list[str]):
    """保存评论到数据库（先清除该视频的旧评论，再批量写入，重复内容自动忽略）"""
    async with aiosqlite.connect(DB_PATH) as db:
        # 清除该视频的旧评论
        await db.execute("DELETE FROM comments WHERE bvid = ?", (bvid,))
        # 批量插入新评论，INSERT OR IGNORE 保证重复内容不报错
        await db.executemany(
            "INSERT OR IGNORE INTO comments (bvid, content) VALUES (?, ?)",
            [(bvid, comment) for comment in comments]
        )
        await db.commit()
        return len(comments)


async def get_comments(bvid: str) -> list[dict]:
    """获取指定视频的评论列表（含情感标签）"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, content, sentiment FROM comments WHERE bvid = ? ORDER BY id",
            (bvid,)
        )
        rows = await cursor.fetchall()
        return [
            {"index": idx + 1, "content": row["content"], "sentiment": row["sentiment"]}
            for idx, row in enumerate(rows)
        ]


async def get_comment_count(bvid: str) -> int:
    """获取指定视频的评论数量"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM comments WHERE bvid = ?",
            (bvid,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_pending_comments(bvid: str) -> list[dict]:
    """获取尚未进行情感分析的评论（sentiment IS NULL）"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, content FROM comments WHERE bvid = ? AND sentiment IS NULL ORDER BY id",
            (bvid,)
        )
        rows = await cursor.fetchall()
        return [{"id": row["id"], "content": row["content"]} for row in rows]


async def update_sentiments(results: list[dict]):
    """
    批量更新评论的情感标签。
    results: [{"id": int, "sentiment": str}, ...]
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            "UPDATE comments SET sentiment = ? WHERE id = ?",
            [(r["sentiment"], r["id"]) for r in results]
        )
        await db.commit()


async def get_sentiment_stats(bvid: str) -> dict:
    """
    统计指定视频的情感分布。
    返回: {"positive": int, "neutral": int, "negative": int, "pending": int, "total": int}
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive,
                SUM(CASE WHEN sentiment = 'neutral'  THEN 1 ELSE 0 END) AS neutral,
                SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative,
                SUM(CASE WHEN sentiment IS NULL       THEN 1 ELSE 0 END) AS pending
            FROM comments WHERE bvid = ?
            """,
            (bvid,)
        )
        row = await cursor.fetchone()
        if not row or row[0] == 0:
            return {"total": 0, "positive": 0, "neutral": 0, "negative": 0, "pending": 0}
        return {
            "total":    row[0] or 0,
            "positive": row[1] or 0,
            "neutral":  row[2] or 0,
            "negative": row[3] or 0,
            "pending":  row[4] or 0,
        }
