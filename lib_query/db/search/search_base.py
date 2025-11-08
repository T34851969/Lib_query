from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import pandas


class SearchBase(ABC):
    mod_dict = {
        1: '索书号切片',
        2: '索书号',
        3: 'ISBN',
        4: '题名',
    }

    @staticmethod
    def clean_name(filename: str, replace_char: str = '-') -> str:
        illegal_chars = '<>:"/\\|?*'
        trans_table = str.maketrans(
            illegal_chars, replace_char * len(illegal_chars))
        return filename.translate(trans_table)

    @staticmethod
    def escape(word: str) -> str:
        return word.replace('%', '[%]').replace('_', '[_]')

    @staticmethod
    def import_input(key, msg: list, t: int):
        res = []
        if isinstance(key, str):
            try:
                with open(key, 'r', encoding='utf-8') as f:
                    res = [line.strip()
                           for line in f.readlines() if line.strip()]
            except Exception as e:
                msg.append(f"读取文件时出错: {e}")
                return {"df": None, "messages": msg, "output_file": None}
        elif isinstance(key, list):
            res = key

        else:
            msg.append("出错")
            return {"df": None, "messages": msg, "output_file": None}

        if not res:
            msg.append("文件中无有效内容")
            return {"df": None, "messages": msg, "output_file": None}

        msg.append(f"从文件加载 {len(res)} 个 {SearchBase.mod_dict[t]} : {res}")
        return res

    @staticmethod
    def output(key: str, df: pandas.DataFrame, fmt: str, t: int, msg: dict) -> Optional[dict]:

        # 准备输出
        output_dir = Path('output') / SearchBase.mod_dict[t]
        output_dir.mkdir(parents=True, exist_ok=True)
        final_name = SearchBase.clean_name(key)

        # 按格式输出
        if fmt == 'csv':
            output_file = output_dir / f"{final_name}.csv"
            try:
                df.to_csv(output_file, index=False,
                          encoding='utf-8-sig')
                msg.append(f"结果已保存到: {output_file}")
            except Exception as e:
                msg.append(f"保存CSV文件时出错: {e}")
        else:
            output_file = output_dir / f"{final_name}.xlsx"
            try:
                df.to_excel(output_file, index=False,
                            engine='xlsxwriter')
                msg.append(f"结果已保存到: {output_file}")
            except Exception as e:
                msg.append(f"保存Excel文件时出错: {e}")

        # 返回结果
        return {"df": df.head().to_string(index=False) if not df.empty else None,
                "messages": msg,
                "output_file": str(output_file) if output_file else None}

    @abstractmethod
    def search(conn, keyword: str, fmt: str):
        pass

    @abstractmethod
    def batch_search(conn, file_path: str, fmt: str):
        pass
