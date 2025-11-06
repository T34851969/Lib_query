"""从Excel文件创建数据库表"""

import pandas as pd
from core import LibraryDatabase


def import_excel(excel_file):

    print(f"正在从 {excel_file} 创建数据库...")
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file, dtype=str, engine='calamine')

        # 标准化列名：去除前后空格
        df.columns = [col.strip() for col in df.columns]

        # 重命名分类列（E-K列，索引4-10）
        for i in range(4, min(11, len(df.columns))):  # 避免列数不足时报错
            level_num = i - 3
            df = df.rename(columns={df.columns[i]: f"level_{level_num}"})

        with LibraryDatabase(path="图书馆详细馆藏.db") as conn:
            # 写入数据库
            df.to_sql('books', conn, if_exists='replace', index=False)

            # 题名索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON books(题名)")

            # 索书号切片索引
            for level in range(1, 8):
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_cn_level_{level} ON books(level_{level})")

            # 索书号索引
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_call_number ON books(索书号)")

            # ISBN标准号索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ISBN ON books(标准号)")

    except Exception as err:
        print(f"处理文件时遭遇错误：{err}")
