"""应用程序主窗口"""

import importlib
import sys
import tkinter as tk
from importlib import resources
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog
from . import style_config


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

        # 全局只读终端（始终显示在所有标签页下方）
        # 增大高度并使用更清晰的等宽字体以便阅读日志
        self.output_box = ScrolledText(
            root, height=22, wrap=tk.WORD, font=('Consolas', 9))
        self.output_box.pack(side=tk.BOTTOM, fill=tk.X,
                             expand=True, padx=10, pady=(0, 10))
        self.output_box.configure(state='disabled')  # 只读，外部通过方法写入

        # 主标签页
        self.tabControl = ttk.Notebook(root)
        self.tabControl.pack(expand=1, fill="both", padx=10, pady=10)

    def load_tab_modules(self):
        package_name = 'lib_query.gui'

        try:
            pkg_files = resources.files(package_name)
        except Exception as e:
            self.append_output(f"无法通过读取包 {package_name}: {e}")
            return

        # 内置的模块名 -> 中文标题映射（可按需扩充）
        _title_map = {
            'title_tab': '标题搜索',
            'call_num_piece_tab': '索书号切片搜索',
            'call_num_tab': '索书号搜索',
            'isbn_tab': 'ISBN查询',
        }

        try:
            for entry in pkg_files.iterdir():
                # 过滤器
                try:
                    if not entry.is_file() or entry.suffix != '.py':
                        continue
                except Exception as err:
                    self.append_output(f"加载时发生错误：{err}")
                    continue

                name = entry.stem
                if name.startswith('_') or name in ('core_tab', '__init__'):
                    continue

                # 先尝试导入模块
                try:
                    mod = importlib.import_module(f"{package_name}.{name}")
                except Exception as e:
                    self.append_output(f"导入模块 {name} 失败: {e}")
                    continue

                # 注入属性
                try:
                    setattr(mod, 'append_output', self.append_output)
                    setattr(mod, 'app', self)
                except Exception:
                    pass

                # 跳过非标签页
                if not hasattr(mod, 'create') or not callable(mod.create):
                    continue
                
                # 映射为中文
                tab_title = getattr(mod, 'TAB_TITLE', None)
                tab_title = _title_map.get(tab_title, tab_title)

                frame = ttk.Frame(self.tabControl)
                self.tabControl.add(frame, text=tab_title)

                try:
                    mod.create(app=self, parent=frame)
                except Exception as e:
                    self.append_output(f"{name}: 创建窗口失败: {e}")
                    # 继续加载其他模块，不中断循环
                    continue

        except Exception as e:
            self.append_output(f"遍历包 {package_name} 时出错: {e}")
            return

    def reload_tabs(self):
        """清除 Notebook 中现有 tab 并重新加载包内的标签模块。

        会从 sys.modules 中删除以 "lib_query.gui." 开头的已加载子模块（除 core_tab 本身），
        以便下一次 import 时能重新导入最新代码。
        """
        try:
            # 移除所有已添加的 tab（安全地遍历副本）
            for tab_id in list(self.tabControl.tabs()):
                try:
                    self.tabControl.forget(tab_id)
                except Exception:
                    pass
        except Exception:
            pass

        # 清理 gui 子模块缓存（保留 core_tab 本身与包根）
        prefix = "lib_query.gui."
        to_del = [name for name in list(sys.modules.keys()) if name.startswith(prefix) and name not in (prefix + "core_tab", "lib_query.gui")]
        for name in to_del:
            try:
                del sys.modules[name]
            except Exception:
                pass

        # 重新加载标签模块
        try:
            self.load_tab_modules()
            self.append_output("UI 热重载完成")
        except Exception as e:
            self.append_output(f"reload_tabs 出错: {e}")

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

    def load_cn_batch_file(self):
        """允许用户选择批量文件，更新状态并启用批量按钮"""

        path = filedialog.askopenfilename(
            filetypes=[("文本文件", "*.txt"), ("CSV 文件", "*.csv"), ("所有文件", "*")]
        )
        if path:
            try:
                self.cn_batch_file_path_var.set(path)
            except Exception:
                pass
            try:
                self.append_output(f"已选择批量文件: {path}")
            except Exception:
                pass
            try:
                self.cn_batch_search_btn.configure(state='normal')
            except Exception:
                pass

    def on_cn_part_search(self):
        """单次索书号切片搜索占位实现"""
        self.append_output("on_cn_part_search: 未实现（占位）")

    def on_cn_batch_search(self):
        """批量切片搜索占位实现"""
        # 优先读取多行输入，否则尝试从已选文件读取
        try:
            text = ''
            if hasattr(self, 'cn_batch_text'):
                text = self.cn_batch_text.get('1.0', 'end').strip()
            if text:
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                self.append_output(f"准备批量搜索 {len(lines)} 行（占位）")
            else:
                fp = getattr(self, 'cn_batch_file_path_var', None)
                if fp is not None and fp.get() and fp.get() != "未选择文件":
                    self.append_output(f"准备从文件批量搜索: {fp.get()} （占位）")
                else:
                    self.append_output("未提供输入")
        except Exception as e:
            self.append_output(f"出错: {e}")

    def on_title_search(self):
        self.append_output("on_title_search: 未实现（占位）")

    def load_batch_input(self):
        self.append_output("load_batch_input: 未实现（占位）")

    def on_precise_batch_search(self):
        self.append_output("on_precise_batch_search: 未实现（占位）")
