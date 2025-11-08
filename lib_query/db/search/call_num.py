"""根据完整的索书号精确搜索书籍，并导出结果"""

import pandas as pd
from typing import Optional
from .search_base import SearchBase


class CallNumberSearch(SearchBase):

    def search(self, conn, call_number: str, fmt: str = 'excel') -> Optional[dict]:
        msg: list = []
        if not call_number or not call_number.strip():
            msg.append("非法输入")
            return {"df": None, "messages": msg, "output_file": None}

        raw_cn = call_number.strip()
        msg.append(f"搜索: {raw_cn}")

        try:
            sql = 'SELECT * FROM books WHERE "索书号" = ?'
            params = (self.escape(raw_cn),)

            msg.append("正在执行搜索...")
            df = pd.read_sql_query(sql, conn, params=params)
            msg.append(f"搜索完成！找到 {len(df)} 条记录")

            return self.output(raw_cn, df, fmt, 2, msg)

        except Exception as e:
            msg.append(f"搜索失败: {e}")
            return {"df": None, "messages": msg, "output_file": None}

    def batch_search(self, conn, key, fmt: str = 'excel'):
        msg = []
        call_numbers = self.import_input(key, msg, 2)

        if isinstance(call_numbers, dict):
            return call_numbers

        found_any = False
        try:
            for call_number in call_numbers:
                raw_cn = call_number.strip()
                if not raw_cn:
                    continue

                sql = 'SELECT * FROM books WHERE "索书号" = ?'
                params = (self.escape(raw_cn),)

                msg.append(f"正在执行搜索: {raw_cn} ...")
                try:
                    df = pd.read_sql_query(sql, conn, params=params)
                except Exception as e:
                    msg.append(f"查询出错（{raw_cn}）: {e}")
                    df = pd.DataFrame()

                msg.append(f"搜索完成！找到 {len(df)} 条记录")

                result = self.output(raw_cn, df, fmt, 2, msg)
                if result and result.get("df") is not None:
                    found_any = True

        except Exception as e:
            msg.append(f"批量搜索时数据库连接出错: {e}")
            return {"df": None, "messages": msg, "output_file": None}

        if not found_any:
            msg.append("所有搜索均未找到匹配项")
            return {"df": None, "messages": msg, "output_file": None}
        else:
            msg.append("批量搜索完成！")
            return result
