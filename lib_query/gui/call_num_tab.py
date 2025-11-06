import tkinter as tk
from tkinter import ttk, messagebox, filedialog

def create(self):
    # 标题
    title_label = ttk.Label(
        self.tab3, text="精确/批量查询", style='Header.TLabel')
    title_label.grid(column=0, row=0, columnspan=5,
                     padx=10, pady=(10, 20), sticky=tk.W)

    # 选择查询类型
    ttk.Label(self.tab3, text="选择查询类型:").grid(
        column=0, row=1, padx=10, pady=5, sticky=tk.W)
    self.query_type_var = tk.StringVar(value="标准号")

    # 查询类型按钮
    frame_types = ttk.Frame(self.tab3)
    frame_types.grid(column=1, row=1, columnspan=4,
                     padx=10, pady=5, sticky=tk.W)

    ttk.Radiobutton(frame_types, text="标准号", variable=self.query_type_var,
                    value="标准号").pack(side=tk.LEFT, padx=2)
    ttk.Radiobutton(frame_types, text="完整索书号", variable=self.query_type_var,
                    value="完整索书号").pack(side=tk.LEFT, padx=2)

    # 输入框
    ttk.Label(self.tab3, text="输入内容:").grid(
        column=0, row=2, padx=10, pady=5, sticky=tk.W)
    self.precise_input_entry = ttk.Entry(
        self.tab3, width=50, font=('Arial', 10))
    self.precise_input_entry.grid(
        column=1, row=2, columnspan=2, padx=10, pady=5, sticky=tk.EW)

    # 批量输入按钮
    ttk.Button(self.tab3, text="📄 批量导入", command=self.load_batch_input).grid(
        column=3, row=2, padx=10, pady=5)

    # 输出格式
    ttk.Label(self.tab3, text="选择输出格式:").grid(
        column=0, row=3, padx=10, pady=5, sticky=tk.W)
    self.precise_format_var = tk.StringVar(value="excel")
    format_frame = ttk.Frame(self.tab3)
    format_frame.grid(column=1, row=3, padx=10, pady=5, sticky=tk.W)
    ttk.Radiobutton(format_frame, text=".xlsx", variable=self.precise_format_var,
                    value="excel").pack(side=tk.LEFT, padx=2)
    ttk.Radiobutton(format_frame, text=".csv", variable=self.precise_format_var,
                    value="csv").pack(side=tk.LEFT, padx=2)

    # 开始搜索按钮
    search_btn = ttk.Button(self.tab3, text="🔍 开始搜索",
                            command=self.on_precise_batch_search)
    search_btn.grid(column=1, row=4, padx=10, pady=20)

    # 配置列权重
    self.tab3.columnconfigure(1, weight=1)

    # 添加说明
    info_label1 = ttk.Label(self.tab3, text="💡 提示：批量查询时，多个条目用逗号分隔",
                            foreground='gray')
    info_label1.grid(column=0, row=5, columnspan=5,
                     padx=10, pady=2, sticky=tk.W)
    info_label2 = ttk.Label(self.tab3, text="💡 文件导入：支持.txt/.csv格式，每行一个条目",
                            foreground='gray')
    info_label2.grid(column=0, row=6, columnspan=5,
                     padx=10, pady=2, sticky=tk.W)
