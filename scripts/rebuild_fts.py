"""为存量数据库补建 FTS5 trigram 题名索引（直接从现有 books 表构建，无需重导 Excel）。

用法：
    python scripts/rebuild_fts.py [数据库路径]
    python scripts/rebuild_fts.py --force [数据库路径]   # 已有索引时删除重建

100 万行库首次构建约需 1~2 分钟。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from lib_query.db.core import DB_PATH, connect, table_exists  # noqa: E402
from lib_query.db.importer import create_indexes_and_fts  # noqa: E402


def main(argv: list[str]) -> int:
    force = "--force" in argv
    args = [a for a in argv if not a.startswith("--")]
    db_path = Path(args[0]) if args else DB_PATH

    if not db_path.exists():
        print(f"数据库不存在: {db_path}")
        return 1

    conn = connect(db_path)
    try:
        if not table_exists(conn, "books"):
            print("数据库中没有 books 表，请先通过程序导入馆藏 Excel。")
            return 1
        if table_exists(conn, "books_fts"):
            if not force:
                print("已存在 books_fts 索引；如需重建请加 --force。")
                return 0
            conn.execute("DROP TABLE IF EXISTS books_fts")

        t0 = time.monotonic()
        create_indexes_and_fts(conn, progress=print)
        print(f"FTS5 题名索引构建完成，耗时 {time.monotonic() - t0:.1f} 秒")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
