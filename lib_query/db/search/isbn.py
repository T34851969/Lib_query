"""根据 ISBN 精确搜索书籍，并导出结果 (类封装版)"""

import pandas as pd
from typing import Optional
from .search_base import SearchBase


class ISBNSearch(SearchBase):
    def search(self, conn, ISBN: str, fmt: str = 'excel') -> Optional[dict]:
        msg = []
        if not ISBN or not ISBN.strip():
            msg.append("非法输入")
            return {"df": None, "messages": msg, "output_file": None}

        raw_isbn = ISBN.strip()
        msg.append(f"搜索标准号: {raw_isbn}")

        try:
            isbn = self.escape(raw_isbn)
            sql = 'SELECT * FROM books WHERE 标准号=?'
            params = (isbn,)

            msg.append("正在执行搜索...")
            df = pd.read_sql_query(sql, conn, params=params) # pyright: ignore[reportArgumentType]
            msg.append(f"搜索完成！找到 {len(df)} 条记录")

            return self.output(raw_isbn, df, fmt, 3, msg) # pyright: ignore[reportArgumentType]

        except Exception as e:
            msg.append(f"搜索失败: {e}")
            return {"df": None, "messages": msg, "output_file": None}

    def batch_search(self, conn, key, fmt: str = 'excel'):
        msg = []
        isbns = self.import_input(key, msg, 3)

        if isinstance(isbns, dict):
            return isbns

        found_any = False

        try:
            for isbn in isbns:
                raw_isbn = isbn.strip()
                if not raw_isbn:
                    continue
                msg.append(f"搜索标准号: {raw_isbn}")

                isbn_ = self.escape(raw_isbn)
                sql = 'SELECT * FROM books WHERE 标准号=?'
                params = (isbn_,)

                msg.append("正在执行搜索...")
                try:
                    df = pd.read_sql_query(sql, conn, params=params) # type: ignore
                except Exception as e:
                    msg.append(f"查询出错（{raw_isbn}）: {e}")
                    df = pd.DataFrame()

                msg.append(f"搜索完成！找到 {len(df)} 条记录")

                result = self.output(raw_isbn, df, fmt, 3, msg) # type: ignore
                if result and result.get("df") is not None:
                    found_any = True

        except Exception as e:
            msg.append(f"搜索失败: {e}")
            return {"df": None, "messages": msg, "output_file": None}

        if not found_any:
            msg.append("所有搜索均未找到匹配项")
            return {"df": None, "messages": msg, "output_file": None}
        else:
            msg.append("批量搜索完成！")
            return result
