"""应用/重载全局 ttk 样式。可被多次调用以切换主题。"""

import tkinter as tk
from tkinter import ttk

DEFAULT_THEME = 'clam'
FONT_FAMILY = 'Arial'
FONT_SIZES = {
    'title': 20,
    'header': 15,
    'normal': 10,
}


def apply(root: tk.Tk, theme: str = None):

    style = ttk.Style(root)
    theme = theme or DEFAULT_THEME
    try:
        style.theme_use(theme)
    except Exception:
        # 主题不可用时回退为默认
        style.theme_use(DEFAULT_THEME)

    # 标签样式
    style.configure('Title.TLabel', font=(FONT_FAMILY, FONT_SIZES['title'], 'bold'),
                    foreground="#093E55")
    style.configure('Header.TLabel', font=(FONT_FAMILY, FONT_SIZES['header'], 'bold'),
                    foreground="#093E55")

    # 按钮 / 单选 / 输入样式
    style.configure('TButton', font=(
        FONT_FAMILY, FONT_SIZES['normal']), padding=6)
    style.configure('Accent.TButton', font=(FONT_FAMILY, FONT_SIZES['normal']), padding=6,
                    foreground='#ffffff', background='#0a84ff')
    style.configure('TRadiobutton', font=(FONT_FAMILY, FONT_SIZES['normal']))
    style.configure('TEntry', padding=5)
