"""pytest 公共夹具：合成馆藏数据库（与正式库同构：books + 索引 + FTS5）。"""
import sqlite3
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from lib_query.db.importer import create_indexes_and_fts  # noqa: E402

COLUMNS = ["题名", "索书号", "标准号", "出版年"] + [f"level_{i}" for i in range(1, 8)]


def _synth_rows(n: int):
    """构造可预测的合成数据：索书号分段规律、题名/ISBN 覆盖各检索路径。"""
    classes = ["TP311.13", "I247.5", "O13", "K207"]
    titles = ["数据结构教程", "计算机网络自顶向下", "操作系统导论", "数据库系统原理",
              "机器学习实战", "中国通史纲要", "高等数学（第二版）", "西方经济学"]
    rows = []
    for i in range(n):
        cls = classes[i % len(classes)]
        title = f"{titles[i % len(titles)]}·第{i % 40 + 1}册"
        call_no = f"{cls}/{i + 1}"
        isbn = f"9787{i:09d}"
        year = str(1980 + i % 45)
        rows.append((
            title, call_no, isbn, year,
            cls[0], cls[:2], cls[:3], cls[:4], cls, call_no.split("/")[0], call_no,
        ))
    return rows


def make_db(path: Path, n: int = 200, *, with_fts: bool = True) -> Path:
    conn = sqlite3.connect(path)
    try:
        cols_sql = ", ".join(f'"{c}" TEXT' for c in COLUMNS)
        conn.execute(f"CREATE TABLE books ({cols_sql})")
        conn.executemany(
            f"INSERT INTO books VALUES ({', '.join('?' for _ in COLUMNS)})",
            _synth_rows(n),
        )
        if with_fts:
            create_indexes_and_fts(conn)
        conn.commit()
    finally:
        conn.close()
    return path


@pytest.fixture()
def synth_db_path(tmp_path):
    return make_db(tmp_path / "synth.db", n=200)


@pytest.fixture()
def output_root(tmp_path, monkeypatch):
    """将导出根目录指向临时目录，避免污染项目 output/。"""
    root = tmp_path / "output"
    monkeypatch.setattr("lib_query.db.exporter.OUTPUT_DIR", root)
    return root
