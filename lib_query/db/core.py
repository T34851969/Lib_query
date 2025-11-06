"""数据库核心函数"""
import sqlite3
from pathlib import Path


class LibraryDatabase:
    def __init__(self, db_path: str = "图书馆详细馆藏.db"):
        # 初始化数据库类实例
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        # 连接到数据库
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA cache_size = 100000")  # 增加缓存
        self.conn.execute("PRAGMA temp_store = MEMORY")  # 使用内存临时存储
        return self.conn

    def __exit__(self):
        # 关闭数据库连接
        if self.conn:
            self.conn.close()

    def is_exists(self):
        # 检查数据库是否存在
        return Path(self.db_path).exists()

    def all_records(self):
        # 获取总记录数
        with LibraryDatabase(path="图书馆详细馆藏.db") as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM books")
            return cursor.fetchone()[0]
