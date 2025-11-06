"""根据 ISBN 精确搜索书籍，并导出结果"""

import pandas as pd
from pathlib import Path
from typing import Optional
from ..core import LibraryDatabase


def clean_name(filename: str, replace_char: str = '-') -> str:
    illegal_chars = '<>:"/\\|?*'
    trans_table = str.maketrans(
        illegal_chars, replace_char * len(illegal_chars))
    return filename.translate(trans_table)


def escape(word: str) -> str:
    return word.replace('%', '[%]').replace('_', '[_]')


def search(ISBN: str, fmt: str = 'excel') -> Optional[pd.DataFrame]:
    if not ISBN.strip():
        print("非法输入")
        return None
    print(f"搜索标准号: {ISBN}")

    with LibraryDatabase() as conn:
        isbn = escape(ISBN.strip())
        sql = 'SELECT * FROM books WHERE 标准号=?'
        params = [isbn]

        print("正在执行搜索...")
        df = pd.read_sql_query(sql, conn, params=params)
        print(f"搜索完成！找到 {len(df)} 条记录")

        output_dir = Path('output') / '标准号搜索结果'
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_isbn = isbn[:20] if len(isbn) > 20 else isbn
        final_name = clean_name(safe_isbn)

        if fmt.lower() == 'csv':
            output_file = output_dir / f"{final_name}.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"结果已保存到: {output_file}")
        else:
            output_file = output_dir / f"{final_name}.xlsx"
            df.to_excel(output_file, index=False, engine='xlsxwriter')
            print(f"结果已保存到: {output_file}")

        return df.head()


def batch_search(file_path, fmt: str = 'excel'):
    # 根据 TXT 文件中的ISBN逐行批量搜索，并导出结果
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            isbns = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

    if not isbns:
        print("文件中无有效内容")
        return None

    print(f"从文件加载 {len(isbns)} 个标准号: {isbns}")

    found_any = False
    for isbn in isbns:
        df_result = search(isbn, fmt).head()
        if df_result is not None and not df_result.empty:
            found_any = True

    if not found_any:
        print("所有搜索均未找到匹配项")
    else:
        print(f"批量搜索完成！")
