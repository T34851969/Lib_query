"""应用程序主窗口"""

import tkinter as tk
import importlib
from importlib import resources
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
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
        self.output_box = ScrolledText(
            root, height=8, wrap=tk.WORD, font=('Consolas', 12))
        self.output_box.pack(side=tk.BOTTOM, fill=tk.x,
                             expand=False, padx=10, pady=(0, 10))
        self.output_box.configure(state='disabled')  # 只读，外部通过方法写入

        # 主标签页
        self.tabControl = ttk.Notebook(root)
        self.tabControl.pack(expand=1, fill="both", padx=10, pady=10)

    def load_tab_modules(self):
        package_name = 'lib_query.gui'
        try:
            pkg = importlib.import_module(package_name)
        except Exception as e:
            self.append_output(f"无法导入包 {package_name}: {e}")
            return

        # 在导入子模块前先把 append_output/app 注入到包对象，保证子模块导入时可用
        setattr(pkg, 'append_output', self.append_output)
        setattr(pkg, 'app', self)

        try:
            # 列举包内的 .py 文件
            pkg_files = resources.files(package_name)
        except Exception as e:
            self.append_output(f"无法通过读取包 {package_name}: {e}")
            return

        try:
            for entry in pkg_files.iterdir():
                # 只处理 .py 文件（忽略包目录/子包、非源码文件）
                try:
                    if not entry.is_file() or entry.suffix != '.py':
                        continue
                except Exception:
                    # 某些 Traversable 实现可能不支持 is_file/suffix，跳过不可识别项
                    continue

                name = entry.stem
                if name.startswith('_') or name in ('core_tab', '__init__'):
                    continue

                try:
                    mod = importlib.import_module(f"{package_name}.{name}")
                    # 再注入到子模块，保证后续调用可用
                    setattr(mod, 'append_output', self.append_output)
                    setattr(mod, 'app', self)

                    tab_title = getattr(mod, 'TAB_NAME', name)
                    frame = ttk.Frame(self.tabControl)
                    self.tabControl.add(frame, text=tab_title)

                    if hasattr(mod, 'create') and callable(mod.create):
                        try:
                            mod.create(app=self, parent=frame)
                        except Exception as e:
                            self.append_output(f"{name}: 创建窗口失败: {e}")
                    else:
                        self.append_output(f"{name}: 未找到创建进程")
                    self.append_output(f"已加载标签: {name} -> {tab_title}")
                except Exception as e:
                    self.append_output(f"加载模块 {name} 出错: {e}")
        except Exception as e:
            self.append_output(f"遍历包 {package_name} 时出错: {e}")
            return

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
