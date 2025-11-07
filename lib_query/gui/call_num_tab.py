from tkinter import ttk
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

TAB_NAME: str = "call_num_tab"
TAB_TITLE: str = "索书号搜索"
"""创建标签页：索书号搜索"""


def create(app, parent):
    # 标题
    title_label = ttk.Label(parent, text="索书号搜索", style='Header.TLabel')
    title_label.grid(column=0, row=0, columnspan=4,
                     padx=10, pady=(10, 20), sticky=tk.W)

    # 单次搜索部分
    ttk.Label(parent, text="单次搜索:").grid(
        column=0, row=1, padx=10, pady=5, sticky=tk.W)
    app.cn_part_entry = ttk.Entry(parent, width=40, font=('Arial', 10))
    app.cn_part_entry.grid(column=1, row=1, padx=5,
                           pady=5, sticky=tk.EW, columnspan=2)
    single_search_btn = ttk.Button(parent, text="开始搜索",
                                   command=app.on_cn_part_search)
    single_search_btn.grid(column=3, row=1, padx=5, pady=5)

    # 输出格式选择 (单次搜索)
    ttk.Label(parent, text="单次输出格式:").grid(
        column=0, row=2, padx=10, pady=5, sticky=tk.W)
    app.cn_part_format_var = tk.StringVar(value="excel")
    # 使用内嵌 frame 紧凑排列单选按钮
    format_frame = ttk.Frame(parent)
    format_frame.grid(column=1, row=2, padx=5, pady=2, sticky=tk.W)
    # 紧凑排列单选按钮
    ttk.Radiobutton(format_frame, text=".xlsx", variable=app.cn_part_format_var,
                    value="excel").pack(side=tk.LEFT, padx=4)
    ttk.Radiobutton(format_frame, text=".csv", variable=app.cn_part_format_var,
                    value="csv").pack(side=tk.LEFT, padx=4)

    # 分隔线
    separator = ttk.Separator(parent, orient='horizontal')
    separator.grid(row=3, column=0, columnspan=4,
                   sticky="ew", padx=10, pady=5)

# 批量搜索部分：文件导入 + 多行输入
    ttk.Label(parent, text="从文件导入或粘贴多行\n下方选择输出格式").grid(
        column=0, row=4, padx=10, pady=5, sticky=tk.W)

    load_batch_btn = ttk.Button(
        parent, text="选择文件", command=app.load_cn_batch_file)
    load_batch_btn.grid(column=1, row=4, padx=0, pady=0)

    # 多行输入框（支持直接粘贴/编辑多条索书号）
    app.cn_batch_text = ScrolledText(
        parent, height=6, wrap=tk.WORD, font=('Arial', 10))
    app.cn_batch_text.grid(column=1, row=6, columnspan=3,
                           padx=(0, 10), pady=(0, 10), sticky=tk.EW)
    app.cn_batch_format_var = tk.StringVar(value="excel")
    batch_format_frame = ttk.Frame(parent)
    batch_format_frame.grid(column=0, row=5, padx=2, pady=1, sticky=tk.W)
    ttk.Radiobutton(batch_format_frame, text=".xlsx",
                    variable=app.cn_batch_format_var, value="excel").pack(side=tk.LEFT, padx=4)
    ttk.Radiobutton(batch_format_frame, text=".csv",
                    variable=app.cn_batch_format_var, value="csv").pack(side=tk.LEFT, padx=4)

    # 批量搜索按钮
    app.cn_batch_search_btn = ttk.Button(
        parent, text="开始搜索（批量）", command=app.on_cn_batch_search, state='normal')
    app.cn_batch_search_btn.grid(
        column=2, row=4, padx=5, pady=2, columnspan=2)

    # 配置列权重
    parent.columnconfigure(1, weight=1)
    
    # 添加说明
    info_label2 = ttk.Label(parent, text="每次输入一个\n或导入.txt/.csv文件\n或在右边粘贴\n每行一个",
                            foreground='gray')
    info_label2.grid(column=0, row=6, columnspan=4,
                     padx=10, pady=2, sticky=tk.W)
