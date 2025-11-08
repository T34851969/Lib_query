"""应用程序主窗口"""

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from .style_config import StyleConfig
from lib_query.gui.tabs import TAB_MODULES
from tkinter import filedialog


class LibraryApp:
    def __init__(self, root, ctrl=None):
        self.root = root
        self.root.title("📚 图书馆 馆藏条目检索系统")
        self.root.geometry("1080x720")
        StyleConfig.apply(self.root, theme=None)
        self.ctrl = ctrl

        # 添加状态栏
        total_records = self.ctrl.get_recs()
        self.status_bar = ttk.Label(self.root, text=f"数据库已加载，共 {total_records} 条",
                                    relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 全局只读终端
        self.output_box = ScrolledText(
            self.root, height=22, wrap=tk.WORD, font=('Consolas', 9))
        self.output_box.pack(side=tk.BOTTOM, fill=tk.X,
                             expand=False, padx=10, pady=(0, 10))
        self.output_box.configure(state='disabled')  # 只读，外部通过方法写入

        # 主标签页
        self.tabControl = ttk.Notebook(self.root)
        self.tabControl.pack(expand=1, fill="both", padx=10, pady=10)

    def load_tab_modules(self):
        """
        加载所有标签页模块，并注入控制中心实例（CentreCrtl）及输出方法。
        每个 tab 可通过 app.ctrl 访问所有事件 handler。
        """

        for tab_info in TAB_MODULES:
            tab_title = tab_info['title']
            frame = ttk.Frame(self.tabControl)
            self.tabControl.add(frame, text=tab_title)
            try:
                tab_info['create'](app=self, parent=frame)
            except Exception as e:
                self.append_output(f"{tab_info['name']}: 创建窗口失败: {e}")
                continue

    def load_file():
        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title="请选择TXT文件",
                filetypes=[("TXT文件", "*.txt"), ("全部（不保证支持）", "*.*")]
            )
            root.destroy()
        except Exception as e:
            print(f"文件选择对话框异常: {e}")
            return False
        
        if not file_path:
            print("未选择文件。")
            return False
        
        return file_path

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
