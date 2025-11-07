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


def title(self, keyword: str, fmt: str = 'excel') -> Optional[pd.DataFrame]:
    messages = []
    if not keyword:
        messages.append("请输入关键词")
        return {"df": None, "messages": messages, "output_file": None}

    raw_keyword = keyword.strip()
    escaped_keyword = self.escape(raw_keyword)
    messages.append(f"搜索关键词: {raw_keyword}")

    sql = "SELECT * FROM books WHERE 题名 LIKE ?"
    params = (f"%{escaped_keyword}%",)

    try:
        with LibraryDatabase() as conn:
            messages.append("正在搜索...")
            df = pd.read_sql_query(sql, conn, params=params)
            messages.append(f"搜索完成！找到 {len(df)} 条记录")

            output_dir = Path('output') / '标题搜索结果'
            output_dir.mkdir(parents=True, exist_ok=True)

            safe_keyword = self.clean_name(raw_keyword[:20])
            count = len(df)
            output_file = None

            if fmt.lower().strip() == 'csv':
                output_file = output_dir / f"查询：{safe_keyword}——{count}个结果.csv"
                try:
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                    messages.append(f"结果已保存到: {str(output_file)}")
                except Exception as e:
                    messages.append(f"保存CSV文件时出错: {e}")
            else:
                output_file = output_dir / \
                    f"查询：{safe_keyword}——{count}个结果.xlsx"
                try:
                    df.to_excel(output_file, index=False, engine='xlsxwriter')
                    messages.append(f"结果已保存到: {str(output_file)}")
                except Exception as e:
                    messages.append(f"保存Excel文件时出错: {e}")

            return {"df": df.head().to_string(index=False), "messages": messages,
                    "output_file": str(output_file) if output_file else None}

    except Exception as e:
        messages.append(f"搜索失败: {e}")
        return {"df": None, "messages": messages, "output_file": None}
