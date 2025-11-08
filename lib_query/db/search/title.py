"""根据书名筛选书籍，并导出结果"""

import pandas as pd
from typing import Optional
from .search_base import SearchBase


class TitleSearch(SearchBase):

    def search(self, conn, title: str, fmt: str = 'excel') -> Optional[dict]:
        msg: list = []
        if not title or not title.strip():
            msg.append("非法输入")
            return {"df": None, "messages": msg, "output_file": None}

        raw_title = title.strip()
        msg.append(f"搜索: {raw_title}")

        try:
            sql = 'SELECT * FROM books WHERE "题名" LIKE ?'
            params = [f"%{raw_title}%"]

            msg.append("正在执行搜索...")
            df = pd.read_sql_query(sql, conn, params=params)
            msg.append(f"搜索完成！找到 {len(df)} 条记录")

            return self.output(raw_title, df, fmt, 4, msg)

        except Exception as e:
            msg.append(f"搜索失败: {e}")
            return {"df": None, "messages": msg, "output_file": None}

    def batch_search(self, conn, key, fmt: str = 'excel'):
        msg = []
        titles = self.import_input(key, msg, 1)

        if isinstance(titles, dict):
            return titles

        found_any = False
        try:
            for title in titles:
                raw_title = title.strip()
                if not raw_title:
                    continue

                sql = 'SELECT * FROM books WHERE "题名" LIKE ?'
                params = [f"%{raw_title}%"]

                msg.append(f"正在执行搜索: {raw_title} ...")
                try:
                    df = pd.read_sql_query(sql, conn, params=params)
                except Exception as e:
                    msg.append(f"查询出错（{raw_title}）: {e}")
                    df = pd.DataFrame()

                msg.append(f"搜索完成！找到 {len(df)} 条记录")

                result = self.output(raw_title, df, fmt, 4, msg)
                if result and result.get("df") is not None:
                    found_any = True

        except Exception as e:
            msg.append(f"批量搜索时数据库连接出错: {e}")
            return {"df": None, "messages": msg, "output_file": None}

        if not found_any:
            msg.append("所有搜索均未找到匹配项\n")
            return {"df": None, "messages": msg, "output_file": None}
        else:
            msg.append("批量搜索完成！\n")
            return result
