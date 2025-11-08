"""根据索书号的一部分筛选书籍，并导出结果"""

import turtle
import pandas as pd
from typing import Optional
from .search_base import SearchBase


class CallNumberPieceSearch(SearchBase):

    def search(self, conn, part: str, fmt: str = 'excel') -> Optional[dict]:
        msg: list = []
        if not part or not part.strip():
            msg.append("非法输入")
            return {"df": None, "messages": msg, "output_file": None}

        raw_part = part.strip()
        msg.append(f"搜索: {raw_part}")

        try:
            # 动态构建列名
            idx = len(raw_part)
            if idx > 5:
                idx -= 1
            column_name = f"level_{idx}"
            part_escaped = self.escape(raw_part)

            # 构建特殊搜索请求
            params: tuple = ()
            if column_name == 'level_5' and len(part_escaped) == 5:
                sql = f"SELECT * FROM books WHERE level_5 LIKE ?"
                params = (f"{part_escaped}%",)
            else:
                sql = f'SELECT * FROM books WHERE "level_{idx}" = ?'
                params = (part_escaped,)

            # 搜索
            msg.append("正在执行搜索...")
            df = pd.read_sql_query(sql, conn, params=params)
            msg.append(f"搜索完成！找到 {len(df)} 条记录")

            return self.output(raw_part, df, fmt, 1, msg)

        except Exception as e:
            msg.append(f"搜索失败: {e}")
            return {"df": None, "messages": msg, "output_file": None}

    def batch_search(self, conn, key, fmt: str = 'excel'):
        msg = []
        parts = self.import_input(key, msg, 1)

        if isinstance(parts, dict):
            return parts

        found_any = False
        try:
            for part in parts:
                raw_part = part.strip()
                if not raw_part:
                    continue

                idx = len(raw_part)
                if idx > 5:
                    idx -= 1
                column_name = f"level_{idx}"
                part_escaped = self.escape(raw_part)

                params: tuple = ()
                if column_name == 'level_5' and len(part_escaped) == 5:
                    sql = f"SELECT * FROM books WHERE level_5 LIKE ?"
                    params = (f"{part_escaped}%",)
                else:
                    sql = f'SELECT * FROM books WHERE "level_{idx}" = ?'
                    params = (part_escaped,)

                msg.append(f"正在执行搜索: {raw_part} ...")
                try:
                    df = pd.read_sql_query(sql, conn, params=params)
                except Exception as e:
                    msg.append(f"查询出错 {raw_part} : {e}")
                    df = pd.DataFrame()

                msg.append(f"搜索完成！找到 {len(df)} 条记录")

                result = self.output(raw_part, df, fmt, 1, msg)
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
