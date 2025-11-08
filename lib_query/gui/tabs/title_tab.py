import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

class TitleTab:
    TAB_NAME: str = "title_tab"
    TAB_TITLE: str = "标题搜索"

    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self._build_ui()

    def _build_ui(self):
        # 标题
        title_label = ttk.Label(self.parent, text="标题搜索", style='Header.TLabel')
        title_label.grid(column=0, row=0, columnspan=4,
                         padx=10, pady=(10, 20), sticky=tk.W)

        # 单次搜索部分
        ttk.Label(self.parent, text="请输入关键词：").grid(
            column=0, row=1, padx=10, pady=5, sticky=tk.W)
        self.keyword_entry = ttk.Entry(self.parent, width=40, font=('Arial', 10))
        self.keyword_entry.grid(column=1, row=1, padx=5,
                               pady=5, sticky=tk.EW, columnspan=2)
        search_btn = ttk.Button(self.parent, text="开始搜索",
                               command=self.on_title_search)
        search_btn.grid(column=3, row=1, padx=5, pady=5)

        # 输出格式选择（单次）
        ttk.Label(self.parent, text="选择输出格式:").grid(
            column=0, row=2, padx=10, pady=5, sticky=tk.W)
        self.fmt = tk.StringVar(value="excel")
        format_frame = ttk.Frame(self.parent)
        format_frame.grid(column=1, row=2, padx=5, pady=2, sticky=tk.W)
        ttk.Radiobutton(format_frame, text=".xlsx", variable=self.fmt,
                        value="excel").pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(format_frame, text=".csv", variable=self.fmt,
                        value="csv").pack(side=tk.LEFT, padx=4)

        # 分隔线
        separator = ttk.Separator(self.parent, orient='horizontal')
        separator.grid(row=3, column=0, columnspan=4,
                       sticky="ew", padx=10, pady=5)

        # 批量搜索部分：文件导入 + 多行输入
        ttk.Label(self.parent, text="从文件导入或粘贴多行\n下方选择输出格式").grid(
            column=0, row=4, padx=10, pady=5, sticky=tk.W)

        load_batch_btn = ttk.Button(
            self.parent, text="选择文件", command=self.on_load_title_batch_file)
        load_batch_btn.grid(column=1, row=4, padx=0, pady=0)

        # 多行输入框

        self.title_batch_text = ScrolledText(
            self.parent, height=6, wrap=tk.WORD, font=('Arial', 10))
        self.title_batch_text.grid(column=1, row=6, columnspan=3,
                               padx=(0, 10), pady=(0, 10), sticky=tk.EW)

        self.batch_fmt = tk.StringVar(value="excel")
        batch_format_frame = ttk.Frame(self.parent)
        batch_format_frame.grid(column=0, row=5, padx=2, pady=1, sticky=tk.W)
        ttk.Radiobutton(batch_format_frame, text=".xlsx",
                        variable=self.batch_fmt, value="excel").pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(batch_format_frame, text=".csv",
                        variable=self.batch_fmt, value="csv").pack(side=tk.LEFT, padx=4)

        # 批量搜索按钮
        batch_search_btn = ttk.Button(
            self.parent, text="开始搜索（批量）", command=self.on_title_batch_search, state='normal')
        batch_search_btn.grid(
            column=2, row=4, padx=5, pady=2, columnspan=2)

        # 配置列权重
        self.parent.columnconfigure(1, weight=1)

        # 添加说明
        info_label2 = ttk.Label(self.parent, text="每次输入一个或批量导入/粘贴\n每行一个关键词",
                                foreground='gray')
        info_label2.grid(column=0, row=6, columnspan=4,
                         padx=10, pady=2, sticky=tk.W)

    def on_title_search(self):
        title = self.keyword_entry.get()
        fmt = self.fmt.get()
        result = self.app.ctrl.on_title_single(title, fmt)
        self.app.append_output('\n'.join(result.get('messages', [])))

    def on_load_title_batch_file(self):
        self.app.load_file()

    def on_title_batch_search(self):
        values = self.title_batch_text.get('1.0', tk.END).strip().splitlines()
        fmt = self.batch_fmt.get()
        result = self.app.ctrl.on_title_batch(values, fmt)
        self.app.append_output('\n'.join(result.get('messages', [])))


def create(app, parent):
    """标签页创建入口，供 LibraryApp.load_tab_modules 调用"""
    return TitleTab(app, parent)
