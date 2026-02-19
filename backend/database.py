import aiosqlite
import os

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
