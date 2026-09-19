"""检索编排层：连接生命周期与单次/批量检索入口。

本层方法均设计为可在工作线程中调用；每次调用自建连接、用完即关。
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
from typing import Callable, Optional

from .db.core import DB_PATH, connect, table_exists
from .db.importer import import_excel
from .db.search import SearchSpec, search_batch, search_one


class LibraryService:
    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = Path(db_path)

    def exists(self) -> bool:
        return self.db_path.exists()

    def record_count(self) -> int:
        if not self.exists():
            return 0
        with closing(connect(self.db_path)) as conn:
            return conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]

    def has_fts(self) -> bool:
        if not self.exists():
            return False
        with closing(connect(self.db_path)) as conn:
            return table_exists(conn, "books_fts")

    def import_excel(self, excel_path: str | Path, progress: Optional[Callable[[str], None]] = None) -> dict:
        return import_excel(excel_path, self.db_path, progress=progress)

    def search_single(self, spec: SearchSpec, keyword: str, fmt: str, *, cancel_event=None) -> dict:
        if not self.exists():
            return self._no_db_result()
        with closing(connect(self.db_path)) as conn:
            return search_one(conn, spec, keyword, fmt, cancel_event=cancel_event)

    def search_batch(
        self,
        spec: SearchSpec,
        key: str | list[str],
        fmt: str,
        *,
        progress: Optional[Callable[[int, int], None]] = None,
        cancel_event=None,
    ) -> dict:
        if not self.exists():
            return self._no_db_result()
        with closing(connect(self.db_path)) as conn:
            return search_batch(conn, spec, key, fmt, progress=progress, cancel_event=cancel_event)

    @staticmethod
    def _no_db_result() -> dict:
        msg = "数据库不存在，请先导入馆藏 Excel 文件。"
        return {
            "messages": [msg],
            "error": msg,
            "items": [],
            "preview": None,
            "output_file": None,
            "rows": 0,
            "cancelled": False,
        }
