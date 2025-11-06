"""根据标题搜索书籍，单次搜索"""

import pandas as pd
from ..core import LibraryDatabase
from pathlib import Path
from typing import Optional


def clean_name(filename: str, replace_char: str = '-') -> str:
    illegal_chars = '<>:"/\\|?*'
    trans_table = str.maketrans(
        illegal_chars, replace_char * len(illegal_chars))
    return filename.translate(trans_table)


def escape(word: str) -> str:
    return word.replace('%', '[%]').replace('_', '[_]')


def search_title(keyword: str, fmt: str = 'excel') -> Optional[pd.DataFrame]:
    if not keyword:
        print("请输入关键词")
        return None

    raw_keyword = keyword.strip()
    escaped_keyword = escape(raw_keyword)
    print(f"搜索关键词: {raw_keyword}")

    sql = "SELECT * FROM books WHERE 题名 LIKE ? ESCAPE '\\'"
    params = f"%{escaped_keyword}%"

    with LibraryDatabase(db_path='图书馆详细馆藏.db') as conn:
        print("正在搜索...")
        df = pd.read_sql_query(sql, conn, params=params)
        print(f"搜索完成！找到 {len(df)} 条记录")

        # 构建输出路径
        output_dir = Path('output') / '标题搜索结果'
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_keyword = clean_name(raw_keyword[:20])
        count = len(df)
        if fmt.lower().strip() == 'csv':
            output_file = output_dir / f"查询：{safe_keyword}——{count}个结果.csv"
            try:
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"结果已保存到: {output_file}")
            except Exception as e:
                print(f"保存CSV文件时出错: {e}")
        else:
            output_file = output_dir / f"查询：{safe_keyword}——{count}个结果.xlsx"
            try:
                df.to_excel(output_file, index=False, engine='calamine')
                print(f"结果已保存到: {output_file}")
            except Exception as e:
                print(f"保存Excel文件时出错: {e}")
        return df
