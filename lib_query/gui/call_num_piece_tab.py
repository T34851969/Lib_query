from tkinter import ttk
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

TAB_NAME: str = "call_num_piece_tab"
TAB_TITLE: str = "索书号切片搜索"
"""创建标签页：索书号切片搜索"""


def create(app, parent):
    # 标题
    title_label = ttk.Label(parent, text="索书号切片搜索", style='Header.TLabel')
    title_label.grid(column=0, row=0, columnspan=4,
                     padx=10, pady=(10, 20), sticky=tk.W)

    # 单次搜索部分
    ttk.Label(parent, text="单次搜索:").grid(
        column=0, row=1, padx=10, pady=5, sticky=tk.W)
    app.cn_part_entry = ttk.Entry(parent, width=40, font=('Arial', 10))
    app.cn_part_entry.grid(column=1, row=1, padx=5,
                           pady=5, sticky=tk.EW, columnspan=2)
    single_search_btn = ttk.Button(parent, text="🔍 开始搜索",
                                   command=app.on_cn_part_search)
    single_search_btn.grid(column=3, row=1, padx=5, pady=5)

    # 输出格式选择 (单次搜索)
    ttk.Label(parent, text="单次输出格式:").grid(
        column=0, row=2, padx=10, pady=5, sticky=tk.W)
    app.cn_part_format_var = tk.StringVar(value="excel")
    # 紧凑排列单选按钮
    format_frame = ttk.Frame(parent)
    format_frame.grid(column=1, row=2, padx=5, pady=5, sticky=tk.W)
    ttk.Radiobutton(format_frame, text=".xlsx", variable=app.cn_part_format_var, value="excel").pack(side=tk.LEFT, padx=4)
    ttk.Radiobutton(format_frame, text=".csv", variable=app.cn_part_format_var, value="csv").pack(side=tk.LEFT, padx=4)

    # 分隔线
    separator = ttk.Separator(parent, orient='horizontal')
    separator.grid(row=3, column=0, columnspan=4,
                   sticky="ew", padx=10, pady=10)

    # 批量搜索部分：文件导入 + 多行输入
    ttk.Label(parent, text="批量搜索 - 从文件导入或粘贴多行:").grid(
        column=0, row=4, padx=10, pady=5, sticky=tk.W)

    app.cn_batch_file_path_var = tk.StringVar(value="未选择文件")
    file_label = ttk.Label(
        parent, textvariable=app.cn_batch_file_path_var, relief="sunken", anchor="w")
    file_label.grid(column=1, row=5, padx=5, pady=5,
                    sticky=tk.EW, columnspan=2)

    load_batch_btn = ttk.Button(
        parent, text="📄 选择文件", command=app.load_cn_batch_file)
    load_batch_btn.grid(column=3, row=5, padx=5, pady=5)

    # 多行输入框（支持直接粘贴/编辑多条索书号切片）
    app.cn_batch_text = ScrolledText(
        parent, height=6, wrap=tk.WORD, font=('Arial', 10))
    app.cn_batch_text.grid(column=1, row=6, columnspan=3,
                           padx=10, pady=(0, 10), sticky=tk.EW)
    ttk.Label(parent, text="在此粘贴每行一个切片：").grid(
        column=0, row=6, padx=10, pady=(0, 10), sticky=tk.NW)

    # 输出格式选择 (批量搜索)
    ttk.Label(parent, text="批量输出格式:").grid(
        column=0, row=7, padx=10, pady=5, sticky=tk.W)
    app.cn_batch_format_var = tk.StringVar(value="excel")
    batch_format_frame = ttk.Frame(parent)
    batch_format_frame.grid(column=1, row=7, padx=5, pady=5, sticky=tk.W)
    ttk.Radiobutton(batch_format_frame, text=".xlsx", variable=app.cn_batch_format_var, value="excel").pack(side=tk.LEFT, padx=4)
    ttk.Radiobutton(batch_format_frame, text=".csv", variable=app.cn_batch_format_var, value="csv").pack(side=tk.LEFT, padx=4)

    # 批量搜索按钮
    app.cn_batch_search_btn = ttk.Button(
        parent, text="🔍 批量开始搜索", command=app.on_cn_batch_search, state=tk.DISABLED)
    app.cn_batch_search_btn.grid(
        column=1, row=8, padx=10, pady=20, columnspan=2)

    # 配置列权重
    parent.columnconfigure(1, weight=1)
    # 添加说明
    info_label = ttk.Label(parent, text="💡 提示1：单次搜索 - 输入索书号部分进行匹配",
                           foreground='gray')
    info_label.grid(column=0, row=9, columnspan=4,
                    padx=10, pady=2, sticky=tk.W)
    info_label2 = ttk.Label(parent, text="💡 提示2：批量搜索 - 导入.txt/.csv文件或在上方粘贴，每行一个",
                            foreground='gray')
    info_label2.grid(column=0, row=10, columnspan=4,
                     padx=10, pady=2, sticky=tk.W)
