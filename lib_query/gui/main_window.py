"""主窗口：检索页容器、只读日志面板与状态栏。

首次使用时引导导入馆藏 Excel；导入、检索等耗时操作全部经 TaskRunner 后台执行。
"""
from __future__ import annotations

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from lib_query.service import LibraryService

from .style import QSS
from .tabs import build_tabs
from .worker import TaskRunner


class MainWindow(QMainWindow):
    def __init__(self, service: LibraryService):
        super().__init__()
        self.service = service
        self.count_runner = TaskRunner(self)
        self.import_runner = TaskRunner(self)

        self.setWindowTitle("📚 图书馆 馆藏条目检索系统")
        self.resize(1080, 720)

        central = QWidget()
        layout = QVBoxLayout(central)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget, stretch=1)

        self.import_progress = QProgressBar()
        self.import_progress.setRange(0, 0)
        self.import_progress.setVisible(False)
        layout.addWidget(self.import_progress)

        self.log_panel = QPlainTextEdit(objectName="logPanel")
        self.log_panel.setReadOnly(True)
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(9)
        self.log_panel.setFont(font)
        self.log_panel.setMinimumHeight(150)
        layout.addWidget(self.log_panel)

        self.setCentralWidget(central)

        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label, stretch=1)

        self._setup_database()
        for title, tab in build_tabs(service, self.log):
            self.tab_widget.addTab(tab, title)

    # ---------- 日志 ----------

    def log(self, text: str) -> None:
        self.log_panel.appendPlainText(text)

    # ---------- 数据库初始化与状态 ----------

    def _setup_database(self):
        if self.service.exists():
            self._refresh_count()  # 状态栏文案会附带 FTS 缺失提示
            return

        answer = QMessageBox.question(
            self, "初始化", "未找到数据库，是否现在选择馆藏 Excel 文件导入？"
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.status_label.setText("未加载数据库：检索功能不可用")
            self.log("已跳过导入；后续可通过重新启动程序完成初始化。")
            return
        self._pick_and_import()

    def _pick_and_import(self):
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, "请选择Excel文件", "", "Excel文件 (*.xlsx)")
        if not path:
            self.status_label.setText("未加载数据库：检索功能不可用")
            return
        self.import_progress.setVisible(True)
        self.import_runner.start(
            lambda reporter, cancel: self.service.import_excel(path, progress=reporter.message),
            on_message=self.log,
            on_finished=self._on_import_finished,
            on_failed=self._on_import_failed,
        )

    def _on_import_finished(self, summary: dict):
        self.import_progress.setVisible(False)
        self.log(
            f"导入成功：{summary['rows']} 行，{len(summary['columns'])} 列，"
            f"耗时 {summary['seconds']} 秒"
        )
        self._refresh_count()

    def _on_import_failed(self, message: str):
        self.import_progress.setVisible(False)
        self.log(f"数据库初始化失败: {message}")
        self.status_label.setText("未加载数据库：检索功能不可用")

    def _refresh_count(self):
        self.status_label.setText("正在统计数据量…")
        self.count_runner.start(
            lambda reporter, cancel: self.service.record_count(),
            on_finished=self._on_count,
            on_failed=lambda msg: self.status_label.setText(f"数据量统计失败: {msg}"),
        )

    def _on_count(self, count: int):
        suffix = "" if self.service.has_fts() else "（题名检索未建 FTS 索引）"
        self.status_label.setText(f"数据库已加载，共 {count:,} 条{suffix}")
