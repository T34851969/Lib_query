"""图形化界面"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from db import LibraryDatabase
from utils import find_excel


class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 图书馆馆藏条目检索系统")
        self.root.geometry("800x400")

        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')

        # 自定义样式
        style.configure('Title.TLabel', font=(
            'Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=(
            'Arial', 12, 'bold'), foreground='#34495e')
        style.configure('TButton', font=('Arial', 10), padding=6)
        style.configure('TRadiobutton', font=('Arial', 10))
        style.configure('TEntry', padding=5)

        self.db = LibraryDatabase()

        # 初始化数据库
        if not self.db.exists_db():
            print("未找到数据库文件，正在从Excel文件创建数据库...")
            excel_file = find_excel()
            if excel_file is None:
                messagebox.showerror("错误", "未找到Excel文件，程序无法启动。")
                root.quit()
                return
            self.db.import_excel(excel_file)
            total_records = self.db.total_records()
            print(f"已创建新数据库，条目总计: {total_records}")
        else:
            total_records = self.db.total_records()
            print(f"已连接现有数据库，总记录数: {total_records}")

        # 创建主标签页控件
        self.tabControl = ttk.Notebook(root)

        # 标签页1: 标题搜索
        self.tab1 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab1, text='🔍 标题搜索')
        self.create_title_search_tab()

        # 标签页2: 索书号部分搜索
        self.tab2 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab2, text='🏷️ 索书号部分搜索')
        self.create_call_number_search_tab()

        # 标签页3: 标准号/完整索书号精确/批量查询
        self.tab3 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab3, text='🎯 精确/批量查询')
        self.create_precise_batch_search_tab()

        self.tabControl.pack(expand=1, fill="both", padx=10, pady=10)

        # 添加状态栏
        self.status_bar = ttk.Label(root, text=f"数据库已加载，总记录数: {total_records}",
                                    relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_title_search_tab(self):
        # 标题
        title_label = ttk.Label(self.tab1, text="标题搜索", style='Header.TLabel')
        title_label.grid(column=0, row=0, columnspan=3,
                         padx=10, pady=(10, 20), sticky=tk.W)

        # 关键词输入
        ttk.Label(self.tab1, text="请输入关键词（多个关键词用逗号分隔）:").grid(
            column=0, row=1, padx=10, pady=5, sticky=tk.W)
        self.title_keywords_entry = ttk.Entry(
            self.tab1, width=50, font=('Arial', 10))
        self.title_keywords_entry.grid(
            column=1, row=1, padx=10, pady=5, sticky=tk.EW, columnspan=2)

        # 输出格式选择
        ttk.Label(self.tab1, text="选择输出格式:").grid(
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
        info_label = ttk.Label(self.tab1, text="💡 提示：支持多关键词搜索，关键词之间用逗号分隔",
                               foreground='gray')
        info_label.grid(column=0, row=4, columnspan=3,
                        padx=10, pady=5, sticky=tk.W)

    def create_call_number_search_tab(self):
        # 标题
        title_label = ttk.Label(
            self.tab2, text="索书号部分搜索", style='Header.TLabel')
        title_label.grid(column=0, row=0, columnspan=4,
                         padx=10, pady=(10, 20), sticky=tk.W)

        # 单次搜索部分
        ttk.Label(self.tab2, text="单次搜索 - 输入索书号（或一部分）:").grid(
            column=0, row=1, padx=10, pady=5, sticky=tk.W)
        self.cn_part_entry = ttk.Entry(self.tab2, width=40, font=('Arial', 10))
        self.cn_part_entry.grid(column=1, row=1, padx=5, pady=5, sticky=tk.EW, columnspan=2)
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
        separator.grid(row=3, column=0, columnspan=4, sticky="ew", padx=10, pady=10)

        # 批量搜索部分
        ttk.Label(self.tab2, text="批量搜索 - 从文件导入索书号片段:").grid(
            column=0, row=4, padx=10, pady=5, sticky=tk.W)
        
        self.cn_batch_file_path_var = tk.StringVar(value="未选择文件")
        file_label = ttk.Label(self.tab2, textvariable=self.cn_batch_file_path_var, relief="sunken", anchor="w")
        file_label.grid(column=1, row=4, padx=5, pady=5, sticky=tk.EW, columnspan=2)
        
        load_batch_btn = ttk.Button(self.tab2, text="📄 选择文件", command=self.load_cn_batch_file)
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
        self.cn_batch_search_btn = ttk.Button(self.tab2, text="🔍 批量开始搜索", command=self.on_cn_batch_search, state=tk.DISABLED)
        self.cn_batch_search_btn.grid(column=1, row=6, padx=10, pady=20, columnspan=2)

        # 配置列权重
        self.tab2.columnconfigure(1, weight=1)
        # 添加说明
        info_label = ttk.Label(self.tab2, text="💡 提示1：单次搜索 - 输入索书号的前缀部分进行模糊匹配",
                               foreground='gray')
        info_label.grid(column=0, row=7, columnspan=4, padx=10, pady=2, sticky=tk.W)
        info_label2 = ttk.Label(self.tab2, text="💡 提示2：批量搜索 - 选择包含多个索书号片段的.txt/.csv文件，每行一个",
                               foreground='gray')
        info_label2.grid(column=0, row=8, columnspan=4, padx=10, pady=2, sticky=tk.W)

    def create_precise_batch_search_tab(self):
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
        ttk.Radiobutton(frame_types, text="标准号(批量)", variable=self.query_type_var,
                        value="标准号(批量)").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(frame_types, text="完整索书号(批量)", variable=self.query_type_var,
                        value="完整索书号(批量)").pack(side=tk.LEFT, padx=2)

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

    def on_title_search(self):
        keywords_input = self.title_keywords_entry.get().strip()
        if not keywords_input:
            messagebox.showwarning("⚠️ 输入错误", "请输入关键词。")
            return
        keywords = [kw.strip()
                    for kw in keywords_input.split(',') if kw.strip()]
        if not keywords:
            messagebox.showwarning("⚠️ 输入错误", "关键词无效。")
            return
        try:
            results = self.db.search_title(
                keywords, self.title_format_var.get())
            if results is not None and len(results) > 0:
                messagebox.showinfo("✅ 搜索完成", f"找到 {len(results)} 条记录，结果已保存。")
                print("前5条结果:")
                print(results.head())
            else:
                messagebox.showinfo("ℹ️ 搜索完成", "未找到匹配项。")
        except Exception as e:
            messagebox.showerror("❌ 搜索出错", f"搜索出错: {str(e)}")

    def on_cn_part_search(self):
        marking = self.cn_part_entry.get().strip()
        if not marking:
            messagebox.showwarning("⚠️ 输入错误", "请输入索书号的一部分。")
            return
        try:
            results = self.db.search_cn_part(
                marking, self.cn_part_format_var.get())
            if results is not None and len(results) > 0:
                messagebox.showinfo("✅ 搜索完成", f"找到 {len(results)} 条记录，结果已保存。")
                print("前五条：")
                print(results.head())
            else:
                messagebox.showinfo("ℹ️ 搜索完成", "未找到匹配项。")
        except Exception as e:
            messagebox.showerror("❌ 搜索出错", f"搜索出错: {str(e)}")

    def load_batch_input(self):
        file_path = filedialog.askopenfilename(
            title="选择包含输入内容的文件",
            filetypes=[("Text files", "*.txt"),
                       ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # 假设文件每行一个输入
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                # 过滤掉空白行并合并为逗号分隔的字符串
                inputs = [line.strip() for line in lines if line.strip()]
                if inputs:
                    self.precise_input_entry.delete(0, tk.END)
                    self.precise_input_entry.insert(0, ','.join(inputs))
                    messagebox.showinfo(
                        "✅ 导入成功", f"成功从文件导入 {len(inputs)} 个条目。")
                else:
                    messagebox.showwarning("⚠️ 导入失败", "文件中未找到有效内容。")
            except Exception as e:
                messagebox.showerror("❌ 导入失败", f"读取文件时出错: {str(e)}")

    def on_precise_batch_search(self):
        query_type = self.query_type_var.get()
        input_text = self.precise_input_entry.get().strip()
        if not input_text:
            messagebox.showwarning("⚠️ 输入错误", "请输入查询内容。")
            return

        if "批量" in query_type:
            # 批量模式
            inputs = [item.strip()
                      for item in input_text.split(',') if item.strip()]
            if not inputs:
                messagebox.showwarning("⚠️ 输入错误", "批量输入无效。")
                return
            try:
                if query_type == "标准号(批量)":
                    results = self.db.batch_search_isbn(
                        inputs, self.precise_format_var.get())
                elif query_type == "完整索书号(批量)":
                    results = self.db.batch_search_callnum(
                        inputs, self.precise_format_var.get())
            except Exception as e:
                messagebox.showerror("❌ 搜索出错", f"批量搜索出错: {str(e)}")
                return
        else:
            # 单个模式
            try:
                if query_type == "标准号":
                    results = self.db.search_isbn(
                        input_text, self.precise_format_var.get())
                elif query_type == "完整索书号":
                    results = self.db.search_callnum(
                        input_text, self.precise_format_var.get())
            except Exception as e:
                messagebox.showerror("❌ 搜索出错", f"搜索出错: {str(e)}")
                return

        if results is not None and len(results) > 0:
            messagebox.showinfo("✅ 搜索完成", f"找到 {len(results)} 条记录，结果已保存。")
            print("前5条结果:")
            print(results.head())
        else:
            messagebox.showinfo("ℹ️ 搜索完成", "未找到匹配项。")
            
    def load_cn_batch_file(self):
        """为索书号部分批量搜索加载文件"""
        file_path = filedialog.askopenfilename(
            title="选择包含索书号片段的文件",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.cn_batch_file_path_var.set(os.path.basename(file_path))
            self.cn_batch_file_path = file_path # 存储文件路径供后续使用
            self.cn_batch_search_btn.config(state=tk.NORMAL) # 启用批量搜索按钮
            print(f"已选择批量文件: {file_path}")
        else:
            # 如果取消选择，重置状态
            self.cn_batch_file_path_var.set("未选择文件")
            self.cn_batch_file_path = None
            self.cn_batch_search_btn.config(state=tk.DISABLED)

    def on_cn_batch_search(self):
        """处理索书号部分批量搜索事件"""
        if not hasattr(self, 'cn_batch_file_path') or not self.cn_batch_file_path:
            messagebox.showwarning("⚠️ 文件错误", "请先选择一个批量查询文件。")
            return

        try:
            # 调用数据库的批量搜索方法
            results = self.db.batch_search_cn_part(
                self.cn_batch_file_path, self.cn_batch_format_var.get()
            )
            if results is not None: # 修改判断条件，只要函数执行完毕（即使无结果）也算完成
                messagebox.showinfo("✅ 批量搜索完成", f"批量搜索任务已执行完毕。结果已按单次逻辑分别保存。")
            else:
                messagebox.showinfo("ℹ️ 批量搜索完成", "批量搜索任务已执行，但未找到任何匹配项。")
        except Exception as e:
            messagebox.showerror("❌ 批量搜索出错", f"批量搜索出错: {str(e)}")
        finally:
            # 重置文件选择状态
            self.cn_batch_file_path_var.set("未选择文件")
            self.cn_batch_file_path = None
            self.cn_batch_search_btn.config(state=tk.DISABLED)
