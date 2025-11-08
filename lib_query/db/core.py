"""数据库核心函数"""

import pandas as pd
import tkinter as tk
from tkinter import filedialog
import sqlite3
from pathlib import Path


class LibraryDatabase:

    PATH = "图书馆详细馆藏.db"

    def __init__(self):
        # 初始化数据库类实例
        self.db_path = LibraryDatabase.PATH
        self.conn = None
        if not self.is_exists():
            success = ExcelImporter.select()
            if not success:
                raise FileNotFoundError("数据库初始化失败，未能导入Excel。")

    def __enter__(self):
        # 连接到数据库
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA cache_size = 100000")  # 增加缓存
        self.conn.execute("PRAGMA temp_store = MEMORY")  # 使用内存临时存储
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 关闭数据库连接
        if self.conn:
            self.conn.close()

    def is_exists(self) -> bool:
        # 检查数据库是否存在
        return Path(self.db_path).exists()

    def all_records(self) -> int:
        # 获取总记录数
        with self as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM books")
            return cursor.fetchone()[0]

    @staticmethod
    def return_path():
        return LibraryDatabase.PATH


class ExcelImporter:
    @classmethod
    def select(cls):
        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title="请选择Excel文件",
                filetypes=[("Excel文件", "*.xlsx")]
            )
            root.destroy()
        except Exception as e:
            print(f"文件选择对话框异常: {e}")
            return False
        if not file_path:
            print("未选择文件。")
            return False
        return cls.import_excel(file_path)

    @classmethod
    def import_excel(cls, excel_file):

        print(f"正在从 {excel_file} 创建数据库...")
        try:
            df = pd.read_excel(excel_file, dtype=str, engine='calamine')
            df.columns = [col.strip() for col in df.columns]
            for i in range(4, min(11, len(df.columns))):
                level_num = i - 3
                df = df.rename(columns={df.columns[i]: f"level_{level_num}"})

            conn = sqlite3.connect(LibraryDatabase.PATH)
            df.to_sql('books', conn, if_exists='replace', index=False)

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_title ON books(题名)")
            for level in range(1, 8):
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_cn_level_{level} ON books(level_{level})")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_call_number ON books(索书号)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ISBN ON books(标准号)")
            print("导入成功！")
            return True

        except Exception as err:
            print(f"处理文件时遭遇错误：{err}")
            return False
