"""主程序：PySide6 图形界面入口。

命令行参数：
    --selfcheck    无界面自检（SQLite 版本与 FTS5 trigram 支持），CI 冒烟用
"""
from __future__ import annotations

import sqlite3
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from lib_query.db.core import sqlite_supports_trigram
from lib_query.gui import MainWindow, apply_style
from lib_query.service import LibraryService


def main() -> int:
    if "--selfcheck" in sys.argv:
        # 不创建 QApplication，无显示环境亦可运行
        ok = sqlite_supports_trigram()
        print(f"Lib_query 自检: sqlite={sqlite3.sqlite_version} fts5_trigram={ok}")
        return 0 if ok else 1

    app = QApplication(sys.argv)
    apply_style(app)

    if not sqlite_supports_trigram():
        QMessageBox.critical(
            None,
            "环境不满足",
            "当前 Python 的 SQLite 缺少 FTS5/trigram 支持"
            f"（检测到 {__import__('sqlite3').sqlite_version}，需 ≥ 3.34）。"
            "题名检索索引无法使用，程序退出。",
        )
        return 1

    service = LibraryService()
    window = MainWindow(service)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
