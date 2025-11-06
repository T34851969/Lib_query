"""主函数入口"""

import tkinter as tk
from tkinter import ttk

from gui import LibraryApp


def main_func():
    """主函数（入口）"""
    root = tk.Tk()
    root.style = ttk.Style()
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap('library_icon.ico')  # 如果有图标文件
    except Exception:
        pass
    app = LibraryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main_func()
