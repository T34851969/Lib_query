"""根据索书号的一部分筛选书籍，并导出结果"""
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


def search(part: str, fmt='excel', db_path="图书馆详细馆藏.db") -> Optional[pd.DataFrame]:
    if not part.strip():
        print("非法输入")
        return None
    print(f"搜索: {part}")

    with LibraryDatabase() as conn:
        # 动态构建列名
        idx = len(part)
        if idx > 5:
            idx -= 1
        column_name = f"level_{idx}"

        part = escape(part.strip())

        # 构建特殊搜索请求
        if column_name == 'level_5' and len(part) == 5:
            sql = f"SELECT * FROM books WHERE level_5 LIKE ?"
            params = [f"{part}%"]
        else:
            sql = f'SELECT * FROM books WHERE "level_{idx}" = ?'
            params = [part]

        # 查询
        print("正在执行搜索...")
        df = pd.read_sql_query(sql, conn, params=params)
        print(f"搜索完成！找到 {len(df)} 条记录")

        output_dir = Path('output') / '索书号切片搜索结果'
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_call_number = part[:20] if len(part) > 20 else part
        final_cn = clean_name(safe_call_number)

        if fmt.lower() == 'csv':
            output_file = output_dir / f"{final_cn}.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"结果已保存到: {output_file}")
        else:
            output_file = output_dir / f"{final_cn}.xlsx"
            df.to_excel(output_file, index=False, engine='xlsxwriter')
            print(f"结果已保存到: {output_file}")
        return df.head()


def batch_search(file_path, fmt='excel', db_path="图书馆详细馆藏.db"):
    # 根据 TXT 文件中的索书号部分进行批量筛选，并导出结果
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            parts = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

    if not parts:
        print("文件中无有效内容")
        return None

    print(f"从文件加载 {len(parts)} 个索书号片段: {parts}")

    found_any = False
    for part in parts:
        df_result = search(part, fmt, db_path)
        if df_result is not None and not df_result.empty:
            found_any = True

    if not found_any:
        print("所有搜索均未找到匹配项")
    else:
        print(f"批量搜索完成！")
