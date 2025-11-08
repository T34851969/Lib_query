"""应用程序主窗口"""

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from . import style_config
from lib_query.gui import title_tab, call_num_piece_tab, call_num_tab, isbn_tab


class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 图书馆 馆藏条目检索系统")
        self.root.geometry("1080x720")
        style_config.apply(self.root, theme=None)

        # 添加状态栏
        total_records = 0
        self.status_bar = ttk.Label(root, text=f"数据库已加载，共{total_records}条",
                                    relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 全局只读终端
        self.output_box = ScrolledText(
            root, height=22, wrap=tk.WORD, font=('Consolas', 9))
        self.output_box.pack(side=tk.BOTTOM, fill=tk.X,
                             expand=True, padx=10, pady=(0, 10))
        self.output_box.configure(state='disabled')  # 只读，外部通过方法写入

        # 主标签页
        self.tabControl = ttk.Notebook(root)
        self.tabControl.pack(expand=1, fill="both", padx=10, pady=10)

    def load_tab_modules(self):
        # 内置的模块名 -> 中文标题映射
        _modules = [
            (title_tab, '标题搜索'),
            (call_num_piece_tab, '索书号切片搜索'),
            (call_num_tab, '索书号搜索'),
            (isbn_tab, 'ISBN查询'),
        ]

        for mod, tab_title in _modules:
            # 注入属性
            try:
                setattr(mod, 'append_output', self.append_output)
                setattr(mod, 'app', self)
            except Exception:
                self.append_output(f"{mod.__name__}: 加载失败")
                continue

            frame = ttk.Frame(self.tabControl)
            self.tabControl.add(frame, text=tab_title)

            try:
                mod.create(app=self, parent=frame)
            except Exception as e:
                self.append_output(f"{mod.__name__}: 创建窗口失败: {e}")
                continue

    def append_output(self, text: str):
        """向输出框追加一行文本（只读）"""
        self.output_box.configure(state='normal')
        self.output_box.insert(tk.END, text + '\n')
        self.output_box.see(tk.END)
        self.output_box.configure(state='disabled')

    def clear_output(self):
        """清空输出框"""
        self.output_box.configure(state='normal')
        self.output_box.delete('1.0', tk.END)
        self.output_box.configure(state='disabled')
