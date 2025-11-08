"""应用/重载全局 ttk 样式。可被多次调用以切换主题。"""

import tkinter as tk
from tkinter import ttk

class StyleConfig:
    DEFAULT_THEME = 'clam'
    FONT_FAMILY = 'Arial'
    FONT_SIZES = {
        'title': 20,
        'header': 15,
        'normal': 10,
    }

    @classmethod
    def apply(cls, root: tk.Tk, theme: str = None):
        style = ttk.Style(root)
        theme = theme or cls.DEFAULT_THEME
        try:
            style.theme_use(theme)
        except Exception:
            style.theme_use(cls.DEFAULT_THEME)

        # 标签样式
        style.configure('Title.TLabel', font=(cls.FONT_FAMILY, cls.FONT_SIZES['title'], 'bold'),
                        foreground="#093E55")
        style.configure('Header.TLabel', font=(cls.FONT_FAMILY, cls.FONT_SIZES['header'], 'bold'),
                        foreground="#093E55")

        # 按钮 / 单选 / 输入样式
        style.configure('TButton', font=(
            cls.FONT_FAMILY, cls.FONT_SIZES['normal']), padding=6)
        style.configure('Accent.TButton', font=(cls.FONT_FAMILY, cls.FONT_SIZES['normal']), padding=6,
                        foreground='#ffffff', background="#23BCDE")
        style.configure('TRadiobutton', font=(cls.FONT_FAMILY, cls.FONT_SIZES['normal']))
        style.configure('TEntry', padding=5)
