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
                UNIQUE(bvid, content)
            )
        """)
        # 创建索引加速查询
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_bvid ON comments(bvid)
        """)
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
