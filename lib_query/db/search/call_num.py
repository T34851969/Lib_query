"""根据完整的索书号精确搜索书籍，并导出结果"""

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


def search(call_number, fmt='excel') -> Optional[pd.DataFrame]:
    if not call_number.strip():
        print("非法输入")
        return None

    print(f"精确搜索索书号: {call_number}")

    with LibraryDatabase(db_path="图书馆详细馆藏.db") as conn:
        sql = 'SELECT * FROM books WHERE 索书号=? ESCAPE "\\"'
        params = escape(call_number)

        print("正在执行搜索...")
        df = pd.read_sql_query(sql, conn, params=params)

        print(f"搜索完成！找到 {len(df)} 条记录")

        safe_Num = call_number[:20] if len(call_number) > 20 else call_number
        safe_Num = clean_name(safe_Num)

        output_dir = Path('output') / '索书号切片搜索结果'
        output_dir.mkdir(parents=True, exist_ok=True)

        if fmt.lower() == 'csv':
            output_file = output_dir / f"{safe_Num}.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"结果已保存到: {output_file}")
        else:
            output_file = output_dir / f"{safe_Num}.xlsx"
            df.to_excel(output_file, index=False, engine='calamine')
            print(f"结果已保存到: {output_file}")
        return df.head()


def batch_search(file_path, fmt='excel'):
    # 根据TXT文件中的索书号进行批量筛选，并导出结果
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            call_num = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

    if not call_num:
        print("文件中无有效内容")
        return None

    print(f"从文件加载 {len(call_num)} 个索书号: {call_num}")

    found_any = False
    for part in call_num:
        df_result = search(part, fmt)
        if df_result is not None and not df_result.empty:
            found_any = True

    if not found_any:
        print("所有搜索均未找到匹配项")
        return
    else:
        print(f"批量搜索完成！")
        if df_result is not None:
            return df_result.head()
