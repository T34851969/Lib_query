"""应用程序主窗口"""

import tkinter as tk
import importlib
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 图书馆 馆藏条目检索系统")
        self.root.geometry("1080x720")


        # 主标签页控件
        self.tabControl = ttk.Notebook(root)

        # 终端输出
        self.tabControl.pack(expand=1, fill="both", padx=10, pady=10)

        # 全局只读输出区（始终显示在所有标签页下方）
        self.output_box = ScrolledText(root, height=8, wrap=tk.WORD, font=('Consolas', 12))
        self.output_box.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))
        self.output_box.configure(state='disabled')  # 只读，外部通过方法写入

        # 添加状态栏
        total_records = 0
        self.status_bar = ttk.Label(root, text=f"数据库已加载，总记录数: {total_records}",
                                    relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def load_tab_modules(self):
        """使用 importlib.resources 遍历包内模块（支持 zip/包资源）"""
        package_name = 'lib_query.gui'
        try:
            pkg = importlib.import_module(package_name)
        except Exception as e:
            self.append_output(f"无法导入包 {package_name}: {e}")
            return

        try:
            from importlib import resources
            for entry in resources.files(package_name).iterdir():
                # 跳过非 py 文件和私有模块
                if entry.name.startswith('_'):
                    continue
                if entry.is_dir():
                    name = entry.name
                elif entry.suffix == '.py':
                    name = entry.stem
                else:
                    continue
                if name == 'core_tab':
                    continue
                try:
                    mod = importlib.import_module(f"{package_name}.{name}")
                    tab_title = getattr(mod, 'TAB_NAME', name)
                    frame = ttk.Frame(self.tabControl)
                    self.tabControl.add(frame, text=tab_title)
                    if hasattr(mod, 'create') and callable(mod.create):
                        try:
                            mod.create(self)
                        except Exception as e:
                            self.append_output(f"{name}: 调用 create 失败: {e}")
                    else:
                        self.append_output(f"{name}: 未找到 create 函数")
                    self.append_output(f"已加载标签: {name} -> {tab_title}")
                except Exception as e:
                    self.append_output(f"加载模块 {name} 出错: {e}")
        except Exception as e:
            # 万一 resources 不可用或出错，降级
            self.append_output(f"resources 遍历失败，回退到 pkgutil: {e}")
            import pkgutil
            for _, name, _ in pkgutil.iter_modules(pkg.__path__):
                 if name.startswith('_') or name == 'core_tab':
                     continue
                 try:
                     mod = importlib.import_module(f"{package_name}.{name}")
                     tab_title = getattr(mod, 'TAB_NAME', name)
                     frame = ttk.Frame(self.tabControl)
                     self.tabControl.add(frame, text=tab_title)
                     if hasattr(mod, 'create') and callable(mod.create):
                         try:
                             mod.create(self)
                         except Exception as e:
                             self.append_output(f"{name}: 调用 create 失败: {e}")
                     else:
                         self.append_output(f"{name}: 未找到 create 函数")
                     self.append_output(f"已加载标签(回退): {name} -> {tab_title}")
                 except Exception as e:
                     self.append_output(f"加载模块 {name} 出错: {e}")
                
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