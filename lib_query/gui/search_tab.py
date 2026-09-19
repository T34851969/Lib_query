"""检索页基类：单次 + 批量检索的共用 UI 与任务编排。

四个检索页仅由 tabs.py 的 SearchSpec 配置差异化，不再各自复制一份代码。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from lib_query.db.search import SearchSpec
from lib_query.service import LibraryService

from .worker import TaskRunner


class SearchTab(QWidget):
    def __init__(self, service: LibraryService, spec: SearchSpec, log, parent=None):
        super().__init__(parent)
        self.service = service
        self.spec = spec
        self._log = log  # 主窗口日志面板回调
        self._file_path = ""
        self.runner = TaskRunner(self)
        self.runner.busy_changed.connect(self._on_busy_changed)
        self._build_ui()

    # ---------- UI ----------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QLabel(self.spec.label, objectName="headerLabel")
        layout.addWidget(header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        grid.addWidget(QLabel("请输入关键词："), 0, 0)
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText(self.spec.tip)
        self.keyword_edit.returnPressed.connect(self._on_single)
        grid.addWidget(self.keyword_edit, 0, 1, 1, 2)
        self.single_btn = QPushButton("开始搜索")
        self.single_btn.clicked.connect(self._on_single)
        grid.addWidget(self.single_btn, 0, 3)

        grid.addWidget(QLabel("输出格式："), 1, 0)
        fmt_box = QHBoxLayout()
        self._single_fmt = self._add_fmt_radios(fmt_box, default_xlsx=True)
        grid.addLayout(fmt_box, 1, 1, 1, 2)

        layout.addLayout(grid)

        separator = QFrame(frameShape=QFrame.Shape.HLine, frameShadow=QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        batch_head = QHBoxLayout()
        batch_head.addWidget(QLabel("批量检索（每行一个关键词，\n或从文件导入）："))
        batch_head.addStretch(1)
        self.file_btn = QPushButton("选择文件…")
        self.file_btn.clicked.connect(self._on_pick_file)
        batch_head.addWidget(self.file_btn)
        self.batch_btn = QPushButton("开始搜索（批量）")
        self.batch_btn.clicked.connect(self._on_batch)
        batch_head.addWidget(self.batch_btn)
        layout.addLayout(batch_head)

        self.batch_edit = QPlainTextEdit()
        self.batch_edit.setFixedHeight(110)
        self.batch_edit.setPlaceholderText("每行一个关键词；留空时使用已选择的文件")
        layout.addWidget(self.batch_edit)

        batch_fmt_box = QHBoxLayout()
        batch_fmt_box.addWidget(QLabel("批量输出格式："))
        self._batch_fmt = self._add_fmt_radios(batch_fmt_box, default_xlsx=True)
        batch_fmt_box.addStretch(1)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.runner.cancel)
        batch_fmt_box.addWidget(self.cancel_btn)
        layout.addLayout(batch_fmt_box)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress)

        tip = QLabel(self.spec.tip, objectName="tipLabel")
        layout.addWidget(tip)
        layout.addStretch(1)

    @staticmethod
    def _add_fmt_radios(box: QHBoxLayout, *, default_xlsx: bool) -> QRadioButton:
        radio_xlsx = QRadioButton(".xlsx")
        radio_csv = QRadioButton(".csv")
        (radio_xlsx if default_xlsx else radio_csv).setChecked(True)
        box.addWidget(radio_xlsx)
        box.addWidget(radio_csv)
        return radio_xlsx

    # ---------- 任务执行 ----------

    def _fmt_of(self, radio: QRadioButton) -> str:
        """radio 为 .xlsx 单选钮：选中返回 xlsx，否则 csv。"""
        return "xlsx" if radio.isChecked() else "csv"

    def _start(self, job):
        self.progress.setRange(0, 0)  # 先显示忙碌；批量收到进度后切换为确定区间
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.runner.start(
            job,
            on_progress=self._on_progress,
            on_message=self._log,
            on_finished=self._on_finished,
            on_failed=self._on_failed,
        )

    def _on_progress(self, done: int, total: int):
        if total > 0 and self.progress.maximum() != total:
            self.progress.setRange(0, total)
        self.progress.setValue(done)

    def _on_finished(self, result: dict):
        self._log(self._format_result(result))
        self.progress.setVisible(False)

    def _on_failed(self, message: str):
        self._log(f"任务失败: {message}")
        self.progress.setVisible(False)

    def _on_busy_changed(self, busy: bool):
        self.single_btn.setEnabled(not busy)
        self.batch_btn.setEnabled(not busy)
        self.file_btn.setEnabled(not busy)
        self.keyword_edit.setEnabled(not busy)
        self.cancel_btn.setEnabled(busy)
        if not busy:
            self.progress.setVisible(False)

    # ---------- 动作 ----------

    def _on_single(self):
        keyword = self.keyword_edit.text().strip()
        if not keyword:
            self._log("请输入关键词。")
            return
        fmt = self._fmt_of(self._single_fmt)
        self._start(
            lambda reporter, cancel: self.service.search_single(
                self.spec, keyword, fmt, cancel_event=cancel
            )
        )

    def _on_batch(self):
        lines = [ln.strip() for ln in self.batch_edit.toPlainText().splitlines() if ln.strip()]
        if lines:
            key = lines
        elif self._file_path:
            key = self._file_path
        else:
            self._log("请先输入关键词或选择文件。")
            return
        fmt = self._fmt_of(self._batch_fmt)
        self._start(
            lambda reporter, cancel: self.service.search_batch(
                self.spec, key, fmt, progress=reporter.progress, cancel_event=cancel
            )
        )

    def _on_pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "请选择TXT文件", "", "TXT文件 (*.txt);;所有文件 (*)"
        )
        if path:
            self._file_path = path
            self._log(f"已选择文件：{path}")

    # ---------- 结果展示 ----------

    def _format_result(self, result: dict) -> str:
        lines = list(result.get("messages", []))
        if "items" in result:  # 批量结果：每关键词一行摘要
            for item in result.get("items", []):
                if item.get("error"):
                    lines.append(f"✗ {item['keyword']}: {item['error']}")
                else:
                    lines.append(
                        f"✓ {item['keyword']}: {item['rows']} 条"
                        f" → {item.get('output_file') or '（无输出）'}"
                    )
            if result.get("cancelled"):
                lines.append("（任务已取消）")
        else:  # 单次结果
            if result.get("preview"):
                lines.append(result["preview"])
            if result.get("output_file"):
                lines.append(f"输出文件: {result['output_file']}")
        return "\n".join(lines)
