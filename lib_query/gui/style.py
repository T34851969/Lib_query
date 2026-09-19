"""全局 QSS 样式（延续旧版 Tkinter 配色）。"""

QSS = """
QLabel#headerLabel {
    color: #093E55;
    font-size: 15px;
    font-weight: bold;
}
QLabel#tipLabel { color: gray; }
QPushButton { padding: 5px 14px; }
QPlainTextEdit#logPanel {
    font-family: "Consolas", "Courier New", monospace;
}
"""


def apply_style(app) -> None:
    """对 QApplication 应用全局样式。"""
    app.setStyleSheet(QSS)
