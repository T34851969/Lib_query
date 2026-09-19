"""导出器测试：文件名清洗、xlsx 截断、预览捕获。"""
from pathlib import Path

from lib_query.db.exporter import clean_name, export_rows, format_preview


def test_clean_name():
    assert clean_name('a/b:c*?"<>|') == "a-b-c------"
    assert clean_name("正常关键词.xlsx") == "正常关键词.xlsx"
    assert clean_name("*") == "-"
    assert clean_name("x" * 300) == "x" * 100


def test_export_csv_and_preview(output_root):
    rows = iter([("题名A", "TP/1"), ("题名B", "TP/2")])
    path, n, truncated = export_rows(
        "csv", "题名", "测试词", ["题名", "索书号"], rows
    )
    assert not truncated and n == 2
    assert path == output_root / "题名" / "测试词.csv"
    content = path.read_text(encoding="utf-8-sig")
    assert content.splitlines()[0] == "题名,索书号"
    assert "题名A" in content


def test_export_xlsx_truncates(output_root, monkeypatch):
    import lib_query.db.exporter as exp

    monkeypatch.setattr(exp, "XLSX_MAX_ROWS", 5)
    rows = iter((f"row{i}",) for i in range(50))
    path, n, truncated = export_rows("xlsx", "题名", "trunc", ["题名"], rows)
    assert truncated and n == 5
    assert path.exists()


def test_format_preview():
    assert format_preview(["A", "B"], []) is None
    text = format_preview(["A", "B"], [("a", None)])
    assert text == "A | B\na | "
