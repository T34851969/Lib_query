"""创建标签页：索书号切片搜索"""

import tkinter as tk
from tkinter import ttk


def create(self):
    # 标题
    title_label = ttk.Label(
        self.tab2, text="索书号切片搜索", style='Header.TLabel')
    title_label.grid(column=0, row=0, columnspan=4,
                     padx=10, pady=(10, 20), sticky=tk.W)

    # 单次搜索部分
    ttk.Label(self.tab2, text="单次搜索:").grid(
        column=0, row=1, padx=10, pady=5, sticky=tk.W)
    self.cn_part_entry = ttk.Entry(self.tab2, width=40, font=('Arial', 10))
    self.cn_part_entry.grid(column=1, row=1, padx=5,
                            pady=5, sticky=tk.EW, columnspan=2)
    single_search_btn = ttk.Button(self.tab2, text="🔍 开始搜索",
                                   command=self.on_cn_part_search)
    single_search_btn.grid(column=3, row=1, padx=5, pady=5)

    # 输出格式选择 (单次搜索)
    ttk.Label(self.tab2, text="单次输出格式:").grid(
        column=0, row=2, padx=10, pady=5, sticky=tk.W)
    self.cn_part_format_var = tk.StringVar(value="excel")
    excel_rb = ttk.Radiobutton(
        self.tab2, text=".xlsx", variable=self.cn_part_format_var, value="excel")
    csv_rb = ttk.Radiobutton(
        self.tab2, text=".csv", variable=self.cn_part_format_var, value="csv")
    excel_rb.grid(column=1, row=2, padx=5, pady=5, sticky=tk.W)
    csv_rb.grid(column=2, row=2, padx=5, pady=5, sticky=tk.W)

    # 分隔线
    separator = ttk.Separator(self.tab2, orient='horizontal')
    separator.grid(row=3, column=0, columnspan=4,
                   sticky="ew", padx=10, pady=10)

    # 批量搜索部分
    ttk.Label(self.tab2, text="批量搜索 - 从文件导入:").grid(
        column=0, row=4, padx=10, pady=5, sticky=tk.W)

    self.cn_batch_file_path_var = tk.StringVar(value="未选择文件")
    file_label = ttk.Label(
        self.tab2, textvariable=self.cn_batch_file_path_var, relief="sunken", anchor="w")
    file_label.grid(column=1, row=4, padx=5, pady=5,
                    sticky=tk.EW, columnspan=2)

    load_batch_btn = ttk.Button(
        self.tab2, text="📄 选择文件", command=self.load_cn_batch_file)
    load_batch_btn.grid(column=3, row=4, padx=5, pady=5)

    # 输出格式选择 (批量搜索)
    ttk.Label(self.tab2, text="批量输出格式:").grid(
        column=0, row=5, padx=10, pady=5, sticky=tk.W)
    self.cn_batch_format_var = tk.StringVar(value="excel")
    batch_excel_rb = ttk.Radiobutton(
        self.tab2, text=".xlsx", variable=self.cn_batch_format_var, value="excel")
    batch_csv_rb = ttk.Radiobutton(
        self.tab2, text=".csv", variable=self.cn_batch_format_var, value="csv")
    batch_excel_rb.grid(column=1, row=5, padx=5, pady=5, sticky=tk.W)
    batch_csv_rb.grid(column=2, row=5, padx=5, pady=5, sticky=tk.W)

    # 批量搜索按钮
    self.cn_batch_search_btn = ttk.Button(
        self.tab2, text="🔍 批量开始搜索", command=self.on_cn_batch_search, state=tk.DISABLED)
    self.cn_batch_search_btn.grid(
        column=1, row=6, padx=10, pady=20, columnspan=2)

    # 配置列权重
    self.tab2.columnconfigure(1, weight=1)
    # 添加说明
    info_label = ttk.Label(self.tab2, text="💡 提示1：单次搜索 - 输入索书号部分进行匹配",
                           foreground='gray')
    info_label.grid(column=0, row=7, columnspan=4,
                    padx=10, pady=2, sticky=tk.W)
    info_label2 = ttk.Label(self.tab2, text="💡 提示2：批量搜索 - 导入.txt/.csv文件，要求文件中每行一个",
                            foreground='gray')
    info_label2.grid(column=0, row=8, columnspan=4,
                     padx=10, pady=2, sticky=tk.W)
