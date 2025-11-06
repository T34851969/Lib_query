TAB_NAME: str = "title_tab"

"""创建标签页：标题搜索"""

import tkinter as tk
from tkinter import ttk


def create(self):
    # 标题
    title_label = ttk.Label(self.tab1, text="标题搜索", style='Header.TLabel')
    title_label.grid(column=0, row=0, columnspan=3,
                     padx=10, pady=(10, 20), sticky=tk.W)

    # 关键词输入
    ttk.Label(self.tab1, text="请输入关键词：").grid(
        column=0, row=1, padx=10, pady=5, sticky=tk.W)
    self.title_keywords_entry = ttk.Entry(
        self.tab1, width=50, font=('Arial', 10))
    self.title_keywords_entry.grid(
        column=1, row=1, padx=10, pady=5, sticky=tk.EW, columnspan=2)

    # 输出格式选择
    ttk.Label(self.tab1, text="选择输出格式：").grid(
        column=0, row=2, padx=10, pady=5, sticky=tk.W)
    self.title_format_var = tk.StringVar(value="excel")
    excel_rb = ttk.Radiobutton(
        self.tab1, text=".xlsx", variable=self.title_format_var, value="excel")
    csv_rb = ttk.Radiobutton(
        self.tab1, text=".csv", variable=self.title_format_var, value="csv")
    excel_rb.grid(column=1, row=2, padx=5, pady=5, sticky=tk.W)
    csv_rb.grid(column=2, row=2, padx=5, pady=5, sticky=tk.W)

    # 搜索按钮
    search_btn = ttk.Button(self.tab1, text="🔍 开始搜索", command=self.on_title_search,
                            style='Accent.TButton')
    search_btn.grid(column=1, row=3, padx=10, pady=20)

    # 配置列权重，使输入框可以扩展
    self.tab1.columnconfigure(1, weight=1)

    # 添加说明
    info_label = ttk.Label(self.tab1, text="💡 提示：单关键词搜索",
                           foreground='gray')
    info_label.grid(column=0, row=4, columnspan=3,
                    padx=10, pady=5, sticky=tk.W)
