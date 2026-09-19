"""Excel → SQLite 建库：calamine 读取、books 表重建、索引与 FTS5 trigram 题名索引。

列布局沿用旧版约定：第 1~4 列保持原列名（题名/索书号/标准号等），
第 5~11 列按位置重命名为 level_1..level_7。
"""
from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from python_calamine import CalamineWorkbook

from .core import DB_PATH

CHUNK_ROWS = 5000  # 分批写入，兼顾内存与提交频率

_INDEX_SQL = [
    'CREATE INDEX IF NOT EXISTS idx_title ON books("题名")',
    *[
        f"CREATE INDEX IF NOT EXISTS idx_cn_level_{i} ON books(\"level_{i}\")"
        for i in range(1, 8)
    ],
    'CREATE INDEX IF NOT EXISTS idx_call_number ON books("索书号")',
    'CREATE INDEX IF NOT EXISTS idx_ISBN ON books("标准号")',
]

_FTS_DDL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5("
    '"题名", content=\'books\', content_rowid=\'rowid\', tokenize=\'trigram\')'
)

_TRIGGER_SQL = [
    """
    CREATE TRIGGER IF NOT EXISTS books_fts_ai AFTER INSERT ON books BEGIN
        INSERT INTO books_fts(rowid, "题名") VALUES (new.rowid, new."题名");
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS books_fts_ad AFTER DELETE ON books BEGIN
        INSERT INTO books_fts(books_fts, rowid, "题名") VALUES ('delete', old.rowid, old."题名");
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS books_fts_au AFTER UPDATE OF "题名" ON books BEGIN
        INSERT INTO books_fts(books_fts, rowid, "题名") VALUES ('delete', old.rowid, old."题名");
        INSERT INTO books_fts(rowid, "题名") VALUES (new.rowid, new."题名");
    END
    """,
]


def _to_str(value) -> Optional[str]:
    """单元格统一转文本；整数化浮点去掉小数尾巴（如 Excel 数值格式的 ISBN）。"""
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def create_indexes_and_fts(conn: sqlite3.Connection, progress: Optional[Callable[[str], None]] = None) -> None:
    """在 books 表上建立常规索引与 FTS5 外部内容索引（幂等，可对存量库调用）。"""
    for sql in _INDEX_SQL:
        conn.execute(sql)
    conn.execute(_FTS_DDL)
    for ddl in _TRIGGER_SQL:
        conn.execute(ddl)
    if progress is not None:
        progress("正在构建 FTS5 题名索引（大库约需 1~2 分钟）...")
    conn.execute("INSERT INTO books_fts(books_fts) VALUES('rebuild')")
    conn.commit()


def import_excel(
    excel_file: str | Path,
    db_path: str | Path = DB_PATH,
    progress: Optional[Callable[[str], None]] = None,
) -> dict:
    """读取 Excel 首个工作表，整体重建 books 表并建立索引/FTS。

    返回 {"rows", "columns", "seconds"}。该操作为破坏性重建（先删后建）。
    """
    t0 = time.monotonic()
    workbook = CalamineWorkbook.from_path(str(excel_file))
    rows = workbook.get_sheet_by_index(0).to_python(skip_empty_area=False)
    if not rows:
        raise ValueError("Excel 首个工作表为空")

    header = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
    for i in range(4, min(11, len(header))):
        header[i] = f"level_{i - 3}"
    data = rows[1:]

    conn = sqlite3.connect(str(db_path))
    try:
        # 顺序敏感：先删 FTS（外部内容表悬空会报错），再删内容表
        conn.execute("DROP TABLE IF EXISTS books_fts")
        conn.execute("DROP TABLE IF EXISTS books")
        cols_sql = ", ".join(f'"{c}" TEXT' for c in header)
        conn.execute(f"CREATE TABLE books ({cols_sql})")

        placeholders = ", ".join("?" for _ in header)
        insert_sql = f"INSERT INTO books VALUES ({placeholders})"
        inserted = 0
        for start in range(0, len(data), CHUNK_ROWS):
            chunk = []
            for row in data[start:start + CHUNK_ROWS]:
                cells = [_to_str(v) for v in row[:len(header)]]
                cells.extend(None for _ in range(len(header) - len(cells)))
                chunk.append(tuple(cells))
            conn.executemany(insert_sql, chunk)
            conn.commit()
            inserted += len(chunk)
            if progress is not None:
                progress(f"已写入 {inserted}/{len(data)} 行")

        create_indexes_and_fts(conn, progress=progress)
    finally:
        conn.close()

    return {
        "rows": inserted,
        "columns": header,
        "seconds": round(time.monotonic() - t0, 1),
    }
