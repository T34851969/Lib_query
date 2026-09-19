"""数据库连接、路径与能力检查。

所有路径以项目根（main.py 所在目录）为基准，不依赖进程工作目录。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

# core.py 位于 <项目根>/lib_query/db/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "图书馆详细馆藏.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

REQUIRED_SQLITE_MIN = (3, 34)  # FTS5 trigram tokenizer 的最低版本


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """打开一个配置好 PRAGMA 的连接。每次任务新建连接，用完即关。"""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA cache_size = 100000")
    conn.execute("PRAGMA temp_store = MEMORY")
    return conn


def sqlite_supports_trigram() -> bool:
    """当前 sqlite 是否支持 FTS5 及 trigram 分词器。"""
    if sqlite3.sqlite_version_info < REQUIRED_SQLITE_MIN:
        return False
    try:
        with sqlite3.connect(":memory:") as conn:
            conn.execute("CREATE VIRTUAL TABLE _probe USING fts5(x, tokenize='trigram')")
        return True
    except sqlite3.Error:
        return False


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
        (name,),
    ).fetchone()
    return row is not None
