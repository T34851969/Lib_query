"""主程序：PySide6 图形界面入口。

命令行参数：
    --selfcheck    无界面自检（SQLite/FTS5 能力 + GUI 依赖导入），CI 冒烟用
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def _selfcheck() -> int:
    """逐项自检并生成报告。

    --windowed 打包无控制台（stdout 为 None，print 为静默 no-op），
    因此报告同时写入 selfcheck_result.txt 供 CI 读取。
    GUI 依赖导入与 SQLite 检查分项执行并各自捕获异常，便于定位打包问题。
    """
    import sqlite3

    lines: list[str] = []
    ok = True

    # 先落"已启动"标记：与最终报告区分"exe 未运行"与"运行到一半崩溃"
    try:
        Path("selfcheck_result.txt").write_text("selfcheck started\n", encoding="utf-8")
    except Exception:
        pass

    try:
        from lib_query.db.core import sqlite_supports_trigram

        fts = sqlite_supports_trigram()
        lines.append(f"sqlite={sqlite3.sqlite_version} fts5_trigram={fts}")
        ok = ok and fts
    except Exception as err:
        lines.append(f"sqlite check FAILED: {type(err).__name__}: {err}")
        ok = False

    try:
        import lib_query.gui  # noqa: F401  完整 GUI 依赖链（PySide6/Qt）导入

        lines.append("gui imports OK")
    except Exception as err:
        lines.append(f"gui import FAILED: {type(err).__name__}: {err}")
        ok = False

    report = "Lib_query 自检: " + " | ".join(lines)
    try:
        print(report)
    except Exception:
        pass  # 无 stdout 时静默跳过
    try:
        Path("selfcheck_result.txt").write_text(report + "\n", encoding="utf-8")
    except Exception:
        pass
    return 0 if ok else 1


def main() -> int:
    if "--selfcheck" in sys.argv:
        # 自检路径不导入 GUI 顶层依赖，导入问题也能被分项报告
        return _selfcheck()

    from PySide6.QtWidgets import QApplication, QMessageBox

    from lib_query.db.core import sqlite_supports_trigram
    from lib_query.gui import MainWindow, apply_style
    from lib_query.service import LibraryService

    app = QApplication(sys.argv)
    apply_style(app)

    if not sqlite_supports_trigram():
        QMessageBox.critical(
            None,
            "环境不满足",
            "当前 Python 的 SQLite 缺少 FTS5/trigram 支持"
            f"（检测到 {sqlite3.sqlite_version}，需 ≥ 3.34）。"
            "题名检索索引无法使用，程序退出。",
        )
        return 1

    service = LibraryService()
    window = MainWindow(service)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
