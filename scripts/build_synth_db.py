"""生成合成馆藏数据库，用于性能压测（默认 100 万行）。

用法：
    python scripts/build_synth_db.py [--rows 1000000] [--output 路径]

生成的库结构与正式库一致（books + 索引 + FTS5 trigram），
可用于对比 FTS 前后的题名检索耗时。
"""
from __future__ import annotations

import argparse
import random
import sqlite3
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from lib_query.db.importer import create_indexes_and_fts  # noqa: E402

COLUMNS = ["题名", "索书号", "标准号", "出版年"] + [f"level_{i}" for i in range(1, 8)]

TITLE_HEADS = ["数据结构", "计算机网络", "操作系统", "数据库系统", "机器学习", "古代文学",
               "西方经济学", "中国通史", "分子生物学", "电磁场理论", "高等数学", "法学概论"]
TITLE_TAILS = ["教程", "导论", "（第二版）", "习题解析", "案例研究", "原理与实践", "", "（影印版）"]
CLASSES = ["TP311.13", "I247.5", "O13", "K207", "Q5", "TN911", "F016", "D922"]
PUBLISHERS = ["清华大学出版社", "高等教育出版社", "商务印书馆", "科学出版社"]


def _random_rows(n: int, rng: random.Random):
    for i in range(n):
        cls = rng.choice(CLASSES)
        title = rng.choice(TITLE_HEADS) + rng.choice(TITLE_TAILS)
        call_no = f"{cls}/{i % 997 + 1}"
        isbn = f"9787{rng.randint(10 ** 6, 10 ** 7 - 1)}{rng.randint(10 ** 3, 10 ** 4 - 1)}"
        year = str(rng.randint(1978, 2024))
        level_1 = cls[0]
        level_2 = cls[:2]
        level_3 = cls[:3]
        level_4 = cls[:4]
        level_5 = cls
        level_6 = call_no.split("/")[0]
        level_7 = call_no
        yield (title, call_no, isbn, year,
               level_1, level_2, level_3, level_4, level_5, level_6, level_7)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--output", default=str(PROJECT_ROOT / "synthetic_馆藏.db"))
    args = parser.parse_args(argv)

    out = Path(args.output)
    if out.exists():
        out.unlink()

    conn = sqlite3.connect(out)
    t0 = time.monotonic()
    cols_sql = ", ".join(f'"{c}" TEXT' for c in COLUMNS)
    conn.execute(f"CREATE TABLE books ({cols_sql})")
    conn.executemany(
        f"INSERT INTO books VALUES ({', '.join('?' for _ in COLUMNS)})",
        _random_rows(args.rows, random.Random(42)),
    )
    conn.commit()
    print(f"数据写入完成：{args.rows} 行，耗时 {time.monotonic() - t0:.1f} 秒")

    t1 = time.monotonic()
    create_indexes_and_fts(conn, progress=print)
    print(f"索引与 FTS 构建完成，耗时 {time.monotonic() - t1:.1f} 秒；总计 {time.monotonic() - t0:.1f} 秒")
    conn.close()
    print(f"输出: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
