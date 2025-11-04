"""数据库初始化与创建函数

在类内只声明方法签名以提高可读性，具体实现放在类定义之外。
实现以普通函数形式定义，随后赋值回类（LibraryDatabase.method = function）。
"""

import pandas as pd
import sqlite3
from pathlib import Path
from contextlib import contextmanager

class LibraryDatabase:
    def __init__(self, db_path: str = "图书馆详细馆藏.db"):
        """初始化数据库类实例。"""
        self.db_path = db_path
        self.conn = None

    # 类内声明
    # ————————————数据库接口函数————————————
    def openDb(self):  # 打开数据库连接
        pass
    def closeDb(self):  # 关闭数据库连接
        pass
    def connCtx(self):  # 上下文管理器，确保连接正确关闭
        pass
    def existsDb(self):  # 检查数据库是否存在
        pass
    def totalRecords(self):  # 获取总记录数
        pass
    def importExcel(self, excel_file):  # 从Excel文件创建数据库表
        pass
    # ————————————搜索函数————————————
    def searchTitle(self, keywords, fmt='excel'):  # 根据标题搜索书籍
        pass
    def searchCnPart(self, marking, fmt='excel'):  # 根据索书号切片筛选书籍
        pass
    def batchSearchCnPart(self, file_path, fmt='excel'):  # 从文件批量搜索索书号切片
        pass
    def searchCallNum(self, call_number, fmt='excel'):  # 根据完整索书号精确搜索
        pass
    def searchIsbn(self, ISBN, fmt='excel'):  # 根据标准号（如ISBN）精确搜索
        pass
    def batchSearchCallNum(self, callNumList, fmt='excel'):  # 批量根据完整索书号精确搜索
        pass
    def batchSearchIsbn(self, ISBN_list, fmt='excel'):  # 批量根据标准号精确搜索
        pass
# ————————————自定义方法————————————
def clean_name(filename, replace_char='_'):

    illegal_chars = '<>:"/\\|?*'
    trans_table = str.maketrans(illegal_chars, replace_char * len(illegal_chars))
    return filename.translate(trans_table)
# ————————————类外实现————————————

def openDb(self):
    """连接到数据库（驼峰名实现）"""
    self.conn = sqlite3.connect(self.db_path)
    self.conn.execute("PRAGMA cache_size = 100000")  # 增加缓存
    self.conn.execute("PRAGMA temp_store = MEMORY")  # 使用内存临时存储
    return self.conn


def closeDb(self):
    """关闭数据库连接（驼峰名实现）"""
    if self.conn:
        self.conn.close()


@contextmanager
def connCtx(self):
    """上下文管理器，确保连接正确关闭（驼峰名实现）"""
    conn = self.openDb()
    try:
        yield conn
    finally:
        conn.close()


def existsDb(self):
    """检查数据库是否存在（驼峰名实现）"""
    return Path(self.db_path).exists()


def totalRecords(self):
    """获取总记录数（驼峰名实现）"""
    with self.connCtx() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM books")
        return cursor.fetchone()[0]


def importExcel(self, excel_file):
    """从Excel文件创建数据库表（驼峰名实现）"""
    print(f"正在从 {excel_file} 创建数据库...")
    # 读取Excel文件
    df = pd.read_excel(excel_file, dtype=str)
    # 标准化列名：去除前后空格、转为小写
    df.columns = [col.strip().lower() for col in df.columns]
    # 强制重命名关键列（谨慎：依赖列数和列顺序）
    df = df.rename(columns={
        df.columns[1]: "标题",      # 原第二列
        df.columns[3]: "索书号",  # D列：索书号
        df.columns[12]: "标准号"  # M列：标准号（ISBN等）
    })
    # 重命名分类列（E-K列，索引4-10）
    for i in range(4, min(11, len(df.columns))):  # 避免列数不足时报错
        level_num = i - 3
        df = df.rename(columns={df.columns[i]: f"level_{level_num}"})

    # 写入数据库
    with self.connCtx() as conn:
        df.to_sql('books', conn, if_exists='replace', index=False)

    # 创建各个索引
    with self.connCtx() as conn:
        # 题名索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON books(标题)")
        # 索书号切割索引
        for level in range(1, 8):
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_level_{level} ON books(level_{level})")
        # 索书号索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_call_number ON books(索书号)")
        # ISBN标准号索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_standard_number ON books(标准号)")
        # 提交
        conn.commit()


def searchTitle(self, keywords, fmt='excel'):
    """根据标题搜索书籍，单次搜索（驼峰名实现）"""
    if isinstance(keywords, str):
        keywords = [keywords]
    kws = [kw.strip() for kw in keywords if kw.strip()]
    if not kws:
        print("非法的关键词")
        return None
    print(f"搜索关键词: {kws}")
    with self.connCtx() as conn:
        # 构建SQL查询语句
        conditions = []
        params = []
        for kw in kws:
            conditions.append("标题 LIKE ?")
            params.append(f"%{kw}%")
        where_clause = " OR ".join(conditions)
        sql = f"SELECT * FROM books WHERE {where_clause}"
        print("正在执行搜索...")
        df = pd.read_sql_query(sql, conn, params=params)
        print(f"搜索完成！找到 {len(df)} 条记录")
        first_keyword = kws[0] if kws else "search"
        safe_keyword = first_keyword[:20] if len(first_keyword) > 20 else first_keyword
        final_key = clean_name(safe_keyword)
        keyword_count = len(kws)
        if fmt.lower() == 'csv':
            output_file = f"查询结果_{final_key}_{keyword_count}个关键词.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"结果已保存到: {output_file}")
        else:
            output_file = f"查询结果_{final_key}_{keyword_count}个关键词.xlsx"
            df.to_excel(output_file, index=False)
            print(f"结果已保存到: {output_file}")
        return df


def searchCnPart(self, part, fmt='excel'):
    """根据索书号的一部分筛选书籍，并导出结果（驼峰名实现）"""
    if not part.strip():
        print("非法输入")
        return None
    print(f"搜索: {part}")
    
    with self.connCtx() as conn:
        # 动态构建列名
        idx = len(part)
        if idx > 5:
            idx -= 1
        column_name = f"level_{idx}"
        # 构建特殊搜索请求
        if column_name == 'level_5' and len(part) == 5:
            sql = f'SELECT * FROM books WHERE "{column_name}" LIKE ?'
            params = [f"{part}%"]
        else:
            sql = f'SELECT * FROM books WHERE "{column_name}" = ?'
            params = [part]
        # 查询
        print("正在执行搜索...")
        df = pd.read_sql_query(sql, conn, params=params)
        print(f"搜索完成！找到 {len(df)} 条记录")
        safe_call_number = part[:20] if len(part) > 20 else part
        final_cn = clean_name(safe_call_number)
        if fmt.lower() == 'csv':
            output_file = f"{final_cn}.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"结果已保存到: {output_file}")
        else:
            output_file = f"{final_cn}.xlsx"
            df.to_excel(output_file, index=False)
            print(f"结果已保存到: {output_file}")
        return df


def batchSearchCnPart(self, file_path, fmt='excel'):
    """根据TXT文件中的索书号部分进行批量筛选，并导出结果（驼峰名实现）"""
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
        df_result = self.searchCnPart(part, fmt)
        if df_result is not None and not df_result.empty:
            found_any = True

    if not found_any:
        print("所有搜索均未找到匹配项")
        return

    print(f"批量搜索完成！")
    return


def searchCallNum(self, call_number, fmt='excel'):
    """根据完整的索书号精确搜索书籍，并导出结果"""
    if not call_number.strip():
        print("非法输入")
        return None
    
    print(f"精确搜索索书号: {call_number}")
    
    with self.connCtx() as conn:
        sql = 'SELECT * FROM books WHERE 索书号 = ?'
        params = [call_number]
        print("正在执行搜索...")
        df = pd.read_sql_query(sql, conn, params=params)
        print(f"搜索完成！找到 {len(df)} 条记录")
        safeCallNum = call_number[:20] if len(call_number) > 20 else call_number
        safeCallNum = clean_name(safeCallNum)
        if fmt.lower() == 'csv':
            output_file = f"结果{safeCallNum}.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"结果已保存到: {output_file}")
        else:
            output_file = f"结果{safeCallNum}.xlsx"
            df.to_excel(output_file, index=False)
            print(f"结果已保存到: {output_file}")
        return df


def searchIsbn(self, ISBN, fmt='excel'):
    """根据标准号（如ISBN）精确搜索书籍，并导出结果（驼峰名实现）"""
    if not ISBN.strip():
        print("非法输入")
        return None
    print(f"搜索标准号: {ISBN}")
    with self.connCtx() as conn:
        sql = 'SELECT * FROM books WHERE 标准号 = ?'
        params = [ISBN]
        print("正在执行搜索...")
        df = pd.read_sql_query(sql, conn, params=params)
        print(f"搜索完成！找到 {len(df)} 条记录")
        if fmt.lower() == 'csv':
            file_out = f"{ISBN}.csv"
            df.to_csv(file_out, index=False, encoding='utf-8-sig')
            print(f"结果已保存到: {file_out}")
        else:
            file_out = f"{ISBN}.xlsx"
            df.to_excel(file_out, index=False)
            print(f"结果已保存到: {file_out}")
        return df


def batchSearchCallNum(self, callNumList, fmt='excel'):
    """批量根据完整的索书号精确搜索书籍，并导出结果（驼峰名实现）"""
    if not callNumList or not any(cn.strip() for cn in callNumList):
        print("非法输入列表")
        return None
    valid_ = [cn.strip() for cn in callNumList if cn.strip()]
    if not valid_:
        print("非法输入列表（无有效索书号）")
        return None

    print(f"批量搜索索书号: {valid_}")
    
    with self.connCtx() as conn:
        placeholders = ','.join('?' * len(valid_))
        sql = f'SELECT * FROM books WHERE 索书号 IN ({placeholders})'
        print("正在执行批量搜索...")
        df = pd.read_sql_query(sql, conn, params=valid_)
        print(f"批量搜索完成！找到 {len(df)} 条记录")
        theFirst = valid_[0]
        if fmt.lower() == 'csv':
            file_out = f"{theFirst}.csv"
            df.to_csv(file_out, index=False, encoding='utf-8-sig')
            print(f"结果已保存到: {file_out}")
        else:
            file_out = f"{theFirst}.xlsx"
            df.to_excel(file_out, index=False)
            print(f"结果已保存到: {file_out}")
        return df


def batchSearchIsbn(self, ISBN_list, fmt='excel'):
    """批量根据标准号（如ISBN）精确搜索书籍，并导出结果（驼峰名实现）"""
    if not ISBN_list or not any(sn.strip() for sn in ISBN_list):
        print("非法输入列表")
        return None

    valid_ = [sn.strip() for sn in ISBN_list if sn.strip()]
    if not valid_:
        print("无有效标准号")
        return None

    print(f"批量搜索标准号: {valid_}")
    with self.connCtx() as conn:
        placeholders = ','.join('?' * len(valid_))
        sql = f'SELECT * FROM books WHERE 标准号 IN ({placeholders})'
        print("正在执行批量搜索...")
        df = pd.read_sql_query(sql, conn, params=valid_)
        print(f"批量搜索完成！找到 {len(df)} 条记录")
        first_ISBN = valid_[0]
        first_ISBN = first_ISBN[:15] if len(first_ISBN) > 15 else first_ISBN
        if fmt.lower() == 'csv':
            file_out = f"{first_ISBN}.csv"
            df.to_csv(file_out, index=False, encoding='utf-8-sig')
            print(f"结果已保存到: {file_out}")
        else:
            file_out = f"{first_ISBN}.xlsx"
            df.to_excel(file_out, index=False)
            print(f"结果已保存到: {file_out}")
        return df


# 将实现赋值回类（驼峰名绑定），并保留 snake_case 别名以兼容历史调用
LibraryDatabase.openDb = openDb
LibraryDatabase.open_db = openDb

LibraryDatabase.closeDb = closeDb
LibraryDatabase.close_db = closeDb

LibraryDatabase.connCtx = connCtx
LibraryDatabase.conn_ctx = connCtx

LibraryDatabase.existsDb = existsDb
LibraryDatabase.exists_db = existsDb

LibraryDatabase.totalRecords = totalRecords
LibraryDatabase.total_records = totalRecords

LibraryDatabase.importExcel = importExcel
LibraryDatabase.import_excel = importExcel

LibraryDatabase.searchTitle = searchTitle
LibraryDatabase.search_title = searchTitle

LibraryDatabase.searchCnPart = searchCnPart
LibraryDatabase.search_cn_part = searchCnPart

LibraryDatabase.batchSearchCnPart = batchSearchCnPart
LibraryDatabase.batch_search_cn_part = batchSearchCnPart
LibraryDatabase.batch_s_cn_p = batchSearchCnPart

LibraryDatabase.searchCallNum = searchCallNum
LibraryDatabase.search_callnum = searchCallNum
LibraryDatabase.search_cn = searchCallNum

LibraryDatabase.searchIsbn = searchIsbn
LibraryDatabase.search_isbn = searchIsbn
LibraryDatabase.search_ISBN = searchIsbn

LibraryDatabase.batchSearchCallNum = batchSearchCallNum
LibraryDatabase.batch_search_callnum = batchSearchCallNum
LibraryDatabase.batch_s_cn = batchSearchCallNum

LibraryDatabase.batchSearchIsbn = batchSearchIsbn
LibraryDatabase.batch_search_isbn = batchSearchIsbn
LibraryDatabase.batch_s_ISBN = batchSearchIsbn
