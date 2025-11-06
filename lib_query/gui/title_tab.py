from tkinter import ttk
import tkinter as tk
TAB_NAME: str = "title_tab"
"""创建标签页：标题搜索"""


def create(app, parent):
    # 标题
    title_label = ttk.Label(parent, text="标题搜索", style='Header.TLabel')
    title_label.grid(column=0, row=0, columnspan=3,
                     padx=10, pady=(10, 20), sticky=tk.W)

    # 关键词输入
    ttk.Label(parent, text="请输入关键词：").grid(
        column=0, row=1, padx=10, pady=5, sticky=tk.W)
    app.title_keywords_entry = ttk.Entry(
        parent, width=50, font=('Arial', 10))
    app.title_keywords_entry.grid(
        column=1, row=1, padx=10, pady=5, sticky=tk.EW, columnspan=2)

    # 输出格式选择
    ttk.Label(parent, text="选择输出格式：").grid(
        column=0, row=2, padx=10, pady=5, sticky=tk.W)
    app.title_format_var = tk.StringVar(value="excel")
    excel_rb = ttk.Radiobutton(
        parent, text=".xlsx", variable=app.title_format_var, value="excel")
    csv_rb = ttk.Radiobutton(
        parent, text=".csv", variable=app.title_format_var, value="csv")
    excel_rb.grid(column=1, row=2, padx=5, pady=5, sticky=tk.W)
    csv_rb.grid(column=2, row=2, padx=5, pady=5, sticky=tk.W)

    # 搜索按钮
    search_btn = ttk.Button(parent, text="🔍 开始搜索", command=app.on_title_search,
                            style='Accent.TButton')
    search_btn.grid(column=1, row=3, padx=10, pady=20)

    # 配置列权重，使输入框可以扩展
    parent.columnconfigure(1, weight=1)

    # 添加说明
    info_label = ttk.Label(parent, text="💡 提示：单关键词搜索",
                           foreground='gray')
    info_label.grid(column=0, row=4, columnspan=3,
                    padx=10, pady=5, sticky=tk.W)
