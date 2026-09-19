"""导入器测试：calamine 读取、列重命名、类型规整、FTS 构建。"""
import sqlite3

import pytest
import xlsxwriter

from lib_query.db.importer import import_excel

HEADER = ["题名", "索书号", "标准号", "出版年", "分级一", "分级二", "分级三",
          "分级四", "分级五", "分级六", "分级七"]


@pytest.fixture()
def sample_excel(tmp_path):
    """构造一个与馆藏格式一致的 Excel：前 4 列保留原名，后 7 列将被按位置重命名。"""
    path = tmp_path / "馆藏.xlsx"
    wb = xlsxwriter.Workbook(str(path))
    ws = wb.add_worksheet()
    ws.write_row(0, 0, HEADER)
    data = [
        ["数据结构教程", "TP311.13/1", "9787030123456", "2019",
         "T", "TP", "TP3", "TP31", "TP311.13", "TP311.13", "TP311.13/1"],
        ["古代文学史", "I209/2", "9787100100000", "2013",
         "I", "I2", "I20", "I209", "I209", "I209", "I209/2"],
        # 数值格式的 ISBN（Excel 中未按文本存储的典型情况）
        ["操作系统导论", "TP316/3", 9787111544937, "2016",
         "T", "TP", "TP3", "TP31", "TP316", "TP316", "TP316/3"],
    ]
    for r, row in enumerate(data, start=1):
        ws.write_row(r, 0, row)
    wb.close()
    return path


def test_import_excel_rebuilds_books_and_fts(sample_excel, tmp_path):
    db = tmp_path / "imported.db"
    messages = []
    summary = import_excel(sample_excel, db, progress=messages.append)

    assert summary["rows"] == 3
    assert summary["columns"][4] == "level_1"
    assert summary["columns"][10] == "level_7"
    assert any("FTS5" in m for m in messages)

    conn = sqlite3.connect(db)
    try:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(books)")]
        assert cols[4:] == [f"level_{i}" for i in range(1, 8)]
        assert conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 3

        # 数值 ISBN 被规整为无小数尾巴的文本
        isbn = conn.execute(
            'SELECT "标准号" FROM books WHERE "题名" = ?', ("操作系统导论",)
        ).fetchone()[0]
        assert isbn == "9787111544937"

        # FTS 索引可查
        hits = conn.execute(
            "SELECT COUNT(*) FROM books_fts WHERE books_fts MATCH ?", ('"数据结构"',)
        ).fetchone()[0]
        assert hits == 1
    finally:
        conn.close()


def test_import_is_destructive_rebuild(sample_excel, tmp_path):
    """重复导入不残留旧数据/旧索引。"""
    db = tmp_path / "reimport.db"
    import_excel(sample_excel, db)
    import_excel(sample_excel, db)
    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM books_fts").fetchone()[0] == 3
    finally:
        conn.close()


def test_import_empty_sheet(tmp_path):
    from lib_query.db.importer import import_excel as imp

    path = tmp_path / "empty.xlsx"
    wb = xlsxwriter.Workbook(str(path))
    wb.add_worksheet()
    wb.close()
    with pytest.raises(ValueError):
        imp(path, tmp_path / "x.db")
