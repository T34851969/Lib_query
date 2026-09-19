"""GUI 冒烟测试（offscreen）：主窗口与全部检索页可实例化，后台任务框架可用。"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from lib_query.gui import MainWindow, apply_style  # noqa: E402
from lib_query.service import LibraryService  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_main_window_builds_all_tabs(app, synth_db_path, output_root):
    apply_style(app)
    window = MainWindow(LibraryService(synth_db_path))
    assert window.tab_widget.count() == 4
    tab_titles = [window.tab_widget.tabText(i) for i in range(4)]
    assert tab_titles == ["索书号切片检索", "索书号检索", "ISBN 检索", "题名检索"]


def test_worker_runs_job_and_emits_result(app, synth_db_path, output_root):
    from lib_query.gui.worker import TaskRunner

    runner = TaskRunner()
    results = []
    service = LibraryService(synth_db_path)
    from lib_query.db.search import MODE_EXACT, SearchSpec

    spec = SearchSpec(key="isbn", dir_name="ISBN", label="ISBN检索",
                      mode=MODE_EXACT, column="标准号")
    runner.start(
        lambda reporter, cancel: service.search_single(spec, "9787000000005", "csv",
                                                       cancel_event=cancel),
        on_finished=results.append,
        on_failed=lambda msg: results.append({"failed": msg}),
    )
    deadline = 5_000_000_000  # 最多等 5 秒
    import time

    ns = time.monotonic_ns()
    while runner.busy and time.monotonic_ns() - ns < deadline:
        app.processEvents()

    assert not runner.busy
    assert len(results) == 1
    assert results[0]["rows"] == 1
