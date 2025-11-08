import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

class IsbnTab:
    TAB_NAME: str = "isbn_tab"
    TAB_TITLE: str = "ISBN查询"

    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self._build_ui()

    def _build_ui(self):
        # 标题
        title_label = ttk.Label(self.parent, text="ISBN搜索", style='Header.TLabel')
        title_label.grid(column=0, row=0, columnspan=4,
                         padx=10, pady=(10, 20), sticky=tk.W)

        # 单次搜索部分
        ttk.Label(self.parent, text="单次搜索:").grid(
            column=0, row=1, padx=10, pady=5, sticky=tk.W)
        self.cn_part_entry = ttk.Entry(self.parent, width=40, font=('Arial', 10))
        self.cn_part_entry.grid(column=1, row=1, padx=5,
                               pady=5, sticky=tk.EW, columnspan=2)
        single_search_btn = ttk.Button(self.parent, text="开始搜索",
                                       command=self.on_cn_part_search)
        single_search_btn.grid(column=3, row=1, padx=5, pady=5)

        # 输出格式选择 (单次搜索)
        ttk.Label(self.parent, text="单次输出格式:").grid(
            column=0, row=2, padx=10, pady=5, sticky=tk.W)
        self.cn_part_format_var = tk.StringVar(value="excel")
        format_frame = ttk.Frame(self.parent)
        format_frame.grid(column=1, row=2, padx=5, pady=2, sticky=tk.W)
        ttk.Radiobutton(format_frame, text=".xlsx", variable=self.cn_part_format_var,
                        value="excel").pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(format_frame, text=".csv", variable=self.cn_part_format_var,
                        value="csv").pack(side=tk.LEFT, padx=4)

        # 分隔线
        separator = ttk.Separator(self.parent, orient='horizontal')
        separator.grid(row=3, column=0, columnspan=4,
                       sticky="ew", padx=10, pady=5)

        # 批量搜索部分：文件导入 + 多行输入
        ttk.Label(self.parent, text="从文件导入或粘贴多行\n下方选择输出格式").grid(
            column=0, row=4, padx=10, pady=5, sticky=tk.W)

        load_batch_btn = ttk.Button(
            self.parent, text="选择文件", command=self.on_load_cn_batch_file)
        load_batch_btn.grid(column=1, row=4, padx=0, pady=0)

        # 多行输入框
        self.cn_batch_text = ScrolledText(
            self.parent, height=6, wrap=tk.WORD, font=('Arial', 10))
        self.cn_batch_text.grid(column=1, row=6, columnspan=3,
                               padx=(0, 10), pady=(0, 10), sticky=tk.EW)

        self.cn_batch_format_var = tk.StringVar(value="excel")
        batch_format_frame = ttk.Frame(self.parent)
        batch_format_frame.grid(column=0, row=5, padx=2, pady=1, sticky=tk.W)
        ttk.Radiobutton(batch_format_frame, text=".xlsx",
                        variable=self.cn_batch_format_var, value="excel").pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(batch_format_frame, text=".csv",
                        variable=self.cn_batch_format_var, value="csv").pack(side=tk.LEFT, padx=4)

        # 批量搜索按钮
        batch_search_btn = ttk.Button(
            self.parent, text="开始搜索（批量）", command=self.on_cn_batch_search, state='normal')
        batch_search_btn.grid(
            column=2, row=4, padx=5, pady=2, columnspan=2)

        # 配置列权重
        self.parent.columnconfigure(1, weight=1)

        # 添加说明
        info_label2 = ttk.Label(self.parent, text="每次输入一个\n或导入.txt/.csv文件\n或在右边粘贴\n每行一个",
                                foreground='gray')
        info_label2.grid(column=0, row=6, columnspan=4,
                         padx=10, pady=2, sticky=tk.W)

    def on_cn_part_search(self):
        value = self.cn_part_entry.get()
        fmt = self.cn_part_format_var.get()
        result = self.app.ctrl.on_isbn_single(value, fmt)
        self.app.append_output('\n'.join(result.get('messages', [])))

    def on_load_cn_batch_file(self):
        self.app.load_cn_batch_file()

    def on_cn_batch_search(self):
        values = self.cn_batch_text.get('1.0', tk.END).strip().splitlines()
        fmt = self.cn_batch_format_var.get()
        result = self.app.ctrl.on_isbn_batch(values, fmt)
        self.app.append_output('\n'.join(result.get('messages', [])))

def create(app, parent):
    """标签页创建入口，供 LibraryApp.load_tab_modules 调用"""
    return IsbnTab(app, parent)
