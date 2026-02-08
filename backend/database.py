import aiosqlite
import os

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "comments.db")


async def init_db():
    """初始化数据库，创建评论表"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bvid TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        # 创建索引加速查询
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_bvid ON comments(bvid)
        """)
        await db.commit()


async def save_comments(bvid: str, comments: list[str]):
    """保存评论到数据库（先清除该视频的旧评论）"""
    async with aiosqlite.connect(DB_PATH) as db:
        # 清除该视频的旧评论
        await db.execute("DELETE FROM comments WHERE bvid = ?", (bvid,))
        # 批量插入新评论
        await db.executemany(
            "INSERT INTO comments (bvid, content) VALUES (?, ?)",
            [(bvid, comment) for comment in comments]
        )
        await db.commit()
        return len(comments)


async def get_comments(bvid: str) -> list[dict]:
    """获取指定视频的评论列表"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, content FROM comments WHERE bvid = ? ORDER BY id",
            (bvid,)
        )
        rows = await cursor.fetchall()
        # 返回带有递增索引的评论列表
        return [{"index": idx + 1, "content": row["content"]} for idx, row in enumerate(rows)]


async def get_comment_count(bvid: str) -> int:
    """获取指定视频的评论数量"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM comments WHERE bvid = ?",
            (bvid,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

