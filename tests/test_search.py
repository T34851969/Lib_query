"""检索实现测试：四种模式、FTS 索引路径、回退路径、单次与批量。"""
from contextlib import closing

import pytest

from lib_query.db.core import connect, table_exists
from lib_query.db.search import (
    MODE_EXACT,
    MODE_PIECE,
    MODE_TITLE,
    SearchSpec,
    build_query,
    search_batch,
    search_one,
)
from lib_query.service import LibraryService

TITLE_SPEC = SearchSpec(key="title", dir_name="题名", label="题名检索", mode=MODE_TITLE)
ISBN_SPEC = SearchSpec(key="isbn", dir_name="ISBN", label="ISBN检索",
                       mode=MODE_EXACT, column="标准号")
CALLNUM_SPEC = SearchSpec(key="call_num", dir_name="索书号", label="索书号检索",
                          mode=MODE_EXACT, column="索书号")
PIECE_SPEC = SearchSpec(key="call_num_piece", dir_name="索书号切片", label="索书号切片检索",
                        mode=MODE_PIECE)


def test_title_query_uses_fts_index(synth_db_path):
    with closing(connect(synth_db_path)) as conn:
        sql, params, notes = build_query(conn, TITLE_SPEC, "计算机网络")
        plan = "\n".join(
            row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql, params)
        )
        # M1 = FTS 虚表按 MATCH 约束走索引，而非全表扫描
        assert "VIRTUAL TABLE INDEX 0:M1" in plan
        assert notes == []


def test_title_short_keyword_falls_back_to_like(synth_db_path):
    with closing(connect(synth_db_path)) as conn:
        sql, params, notes = build_query(conn, TITLE_SPEC, "数")
        assert "LIKE" in sql
        rows = conn.execute(sql, params).fetchall()
        assert len(rows) > 0


def test_title_without_fts_warns_and_falls_back(tmp_path):
    from tests.conftest import make_db
    db = make_db(tmp_path / "nofts.db", n=50, with_fts=False)
    with closing(connect(db)) as conn:
        sql, params, notes = build_query(conn, TITLE_SPEC, "计算机网络")
        assert "LIKE" in sql
        assert any("rebuild_fts" in n for n in notes)


def test_title_search_finds_seeded_rows(synth_db_path, output_root):
    service = LibraryService(synth_db_path)
    result = service.search_single(TITLE_SPEC, "计算机网络", "csv")
    assert result["error"] is None
    assert result["rows"] == 25  # 8 种题名循环 200 行，含该词的题名占 1/8
    assert result["preview"] and "计算机网络" in result["preview"]
    assert (output_root / "题名" / "计算机网络.csv").exists()


def test_title_search_fts_phrase_with_quotes(synth_db_path, output_root):
    """关键词含双引号时不 crash，且短语转义正确。"""
    service = LibraryService(synth_db_path)
    result = service.search_single(TITLE_SPEC, '导"论', "csv")
    assert result["error"] is None


def test_isbn_exact_search(synth_db_path, output_root):
    service = LibraryService(synth_db_path)
    result = service.search_single(ISBN_SPEC, "9787000000005", "csv")
    assert result["rows"] == 1
    assert "9787000000005" in result["preview"]


def test_call_num_exact_search(synth_db_path, output_root):
    service = LibraryService(synth_db_path)
    result = service.search_single(CALLNUM_SPEC, "TP311.13/1", "csv")
    assert result["rows"] == 1


def test_piece_search(synth_db_path, output_root):
    service = LibraryService(synth_db_path)
    # 'I247'（4 位）→ level_4 等值匹配
    result = service.search_single(PIECE_SPEC, "I247", "csv")
    assert result["rows"] == 50  # 200 行中每 4 行一个分类
    # 'I247.5'（6 位）→ level_5 等值匹配（len>5 时 idx-1=5）
    result2 = service.search_single(PIECE_SPEC, "I247.5", "csv")
    assert result2["rows"] == 50


def test_single_empty_keyword(synth_db_path):
    service = LibraryService(synth_db_path)
    result = service.search_single(TITLE_SPEC, "   ", "csv")
    assert "非法输入" in result["messages"][0]


def test_batch_writes_one_file_per_keyword(synth_db_path, output_root):
    service = LibraryService(synth_db_path)
    progress_log = []

    result = service.search_batch(
        ISBN_SPEC, ["9787000000000", "9787000000001", ""], "csv",
        progress=lambda done, total: progress_log.append((done, total)),
    )
    assert result["error"] is None
    assert len(result["items"]) == 2  # 空关键词被过滤
    assert progress_log == [(1, 2), (2, 2)]
    assert (output_root / "ISBN" / "9787000000000.csv").exists()
    assert (output_root / "ISBN" / "9787000000001.csv").exists()


def test_batch_from_file(tmp_path, synth_db_path, output_root):
    key_file = tmp_path / "keys.txt"
    key_file.write_text("9787000000000\n\n9787000000001\n", encoding="utf-8")
    service = LibraryService(synth_db_path)
    result = service.search_batch(ISBN_SPEC, str(key_file), "csv")
    assert result["error"] is None
    assert len(result["items"]) == 2


def test_batch_cancel(synth_db_path, output_root):
    import threading

    service = LibraryService(synth_db_path)
    cancel = threading.Event()
    cancel.set()  # 预先置位：立即取消

    result = service.search_batch(
        ISBN_SPEC, ["9787000000000", "9787000000001"], "csv", cancel_event=cancel
    )
    assert result["cancelled"] is True
    assert result["items"] == []


def test_search_cancel_during_export(tmp_path, output_root):
    """导出中途取消：半成品文件被清理。"""
    import threading

    from lib_query.db.exporter import ExportCancelled

    from tests.conftest import make_db

    db = make_db(tmp_path / "big.db", n=20000)
    cancel = threading.Event()
    seen = {"rows": 0}

    class CancellingRows:
        """逐行产出，并在第 6000 行触发取消。"""

        def __init__(self):
            with closing(connect(db)) as conn:
                self._rows = conn.execute("SELECT * FROM books").fetchall()

        def __iter__(self):
            return self

        def __next__(self):
            row = self._rows[seen["rows"]]
            seen["rows"] += 1
            if seen["rows"] >= 6000:
                cancel.set()
            return row

    from lib_query.db.exporter import export_rows

    with pytest.raises(ExportCancelled):
        export_rows("csv", "题名", "cancel-test", ["题名"], CancellingRows(),
                    cancel_event=cancel, check_every=1000)
    assert not (output_root / "题名" / "cancel-test.csv").exists()
