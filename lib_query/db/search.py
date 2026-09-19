"""参数化检索实现：一套模板覆盖 题名/索书号/索书号切片/ISBN 四种检索。

旧版四份复制粘贴的 search 模块收敛为 SearchSpec 描述 + 通用实现。
"""
from __future__ import annotations

import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Optional

from .core import table_exists
from .exporter import ExportCancelled, HeadCapture, export_rows, format_preview

MODE_EXACT = "exact"    # 等值匹配（索书号 / ISBN）
MODE_PIECE = "piece"    # 索书号切片：按关键词长度定位 level_N 列
MODE_TITLE = "title"    # 题名模糊检索：FTS5 trigram，缺失时回退 LIKE

# 题名回退查询（FTS 不可用或关键词不足 3 字符时）
_LIKE_TITLE_SQL = 'SELECT * FROM books WHERE "题名" LIKE ? ESCAPE \'\\\''

# 单条 LIKE 导出过程中每 5000 行检查一次取消
CANCEL_CHECK_EVERY = 5000


@dataclass(frozen=True)
class SearchSpec:
    key: str              # 英文标识，如 'title'
    dir_name: str         # output 子目录名
    label: str            # 界面显示名
    mode: str             # exact / piece / title
    column: str = ""      # exact 模式的列名
    tip: str = ""         # 界面输入提示


def escape_like(word: str) -> str:
    """LIKE 模式转义（配合 ESCAPE '\\' 使用）。"""
    return word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def quote_fts_phrase(word: str) -> str:
    """包装为 FTS5 短语查询，双引号翻倍转义，其余字符按字面处理。"""
    return '"' + word.replace('"', '""') + '"'


def build_query(
    conn: sqlite3.Connection, spec: SearchSpec, keyword: str
) -> tuple[str, tuple, list[str]]:
    """构造 (sql, params, 附加提示)。"""
    kw = keyword.strip()
    if spec.mode == MODE_EXACT:
        sql = f'SELECT * FROM books WHERE "{spec.column}" = ?'
        return sql, (kw,), []

    if spec.mode == MODE_PIECE:
        # 沿用旧版定位规则：长度 >5 的切片按 level_(len-1) 精确匹配；
        # 5 位切片在 level_5 上做前缀匹配
        idx = len(kw)
        if idx > 5:
            idx -= 1
        col = f"level_{idx}"
        if col == "level_5" and len(kw) == 5:
            sql = 'SELECT * FROM books WHERE "level_5" LIKE ? ESCAPE \'\\\''
            return sql, (escape_like(kw) + "%",), []
        sql = f'SELECT * FROM books WHERE "{col}" = ?'
        return sql, (kw,), []

    if spec.mode == MODE_TITLE:
        notes: list[str] = []
        if len(kw) >= 3:
            if table_exists(conn, "books_fts"):
                sql = (
                    "SELECT b.* FROM books b JOIN books_fts f ON f.rowid = b.rowid "
                    "WHERE books_fts MATCH ?"
                )
                return sql, (quote_fts_phrase(kw),), notes
            notes.append(
                "提示：未检测到 books_fts 索引，题名检索回退全表扫描"
                "（可运行 scripts/rebuild_fts.py 补建索引）"
            )
        return _LIKE_TITLE_SQL, (f"%{escape_like(kw)}%",), notes

    raise ValueError(f"未知检索模式: {spec.mode}")


def search_one(
    conn: sqlite3.Connection,
    spec: SearchSpec,
    keyword: str,
    fmt: str,
    *,
    cancel_event=None,
) -> dict:
    """单关键词检索 + 流式导出，返回结构化结果（异常在内部捕获）。"""
    messages: list[str] = []
    result = {
        "keyword": keyword.strip(),
        "messages": messages,
        "preview": None,
        "output_file": None,
        "rows": 0,
        "cancelled": False,
        "error": None,
    }
    kw = keyword.strip()
    if not kw:
        messages.append("非法输入（空关键词）")
        return result

    try:
        sql, params, notes = build_query(conn, spec, kw)
        messages.extend(notes)
        messages.append(f"搜索: {kw}")

        cur = conn.execute(sql, params)
        columns = [d[0] for d in cur.description]
        cap = HeadCapture(cur)
        try:
            path, n, truncated = export_rows(
                fmt, spec.dir_name, kw, columns, cap,
                cancel_event=cancel_event, check_every=CANCEL_CHECK_EVERY,
            )
        except ExportCancelled:
            result["cancelled"] = True
            messages.append("已取消（部分结果未保存）")
            return result

        result["rows"] = n
        result["output_file"] = str(path)
        if truncated:
            messages.append(f"警告：结果超出 Excel 单表行数上限，已截断为 {n} 行")
        messages.append(f"搜索完成！找到 {n} 条记录")
        messages.append(f"结果已保存到: {path}")
        result["preview"] = format_preview(columns, cap.head)
        return result
    except ExportCancelled:
        raise
    except Exception as err:  # 单关键词失败不影响批量中的其余关键词
        result["error"] = str(err)
        messages.append(f"搜索失败: {err}")
        return result


def load_keywords(key: str | list[str], messages: list[str], label: str) -> Optional[list[str]]:
    """批量输入归一化：字符串按文件路径读取，列表直接使用。"""
    if isinstance(key, str):
        try:
            with open(key, "r", encoding="utf-8-sig") as f:
                kws = [line.strip() for line in f if line.strip()]
        except OSError as err:
            messages.append(f"读取文件时出错: {err}")
            return None
    elif isinstance(key, list):
        kws = [str(k).strip() for k in key if str(k).strip()]
    else:
        messages.append("出错：不支持的关键词类型")
        return None

    if not kws:
        messages.append("文件中无有效内容" if isinstance(key, str) else "无有效关键词")
        return None
    messages.append(f"加载 {len(kws)} 个 {label} 关键词")
    return kws


def search_batch(
    conn: sqlite3.Connection,
    spec: SearchSpec,
    key: str | list[str],
    fmt: str,
    *,
    progress: Optional[Callable[[int, int], None]] = None,
    cancel_event=None,
) -> dict:
    """批量检索：每个关键词一次索引查询 + 独立导出一个文件。

    返回 {"messages", "items", "cancelled", "error"}；
    progress(done, total) 在每个关键词完成后回调。
    """
    messages: list[str] = []
    result: dict = {"messages": messages, "items": [], "cancelled": False, "error": None}

    keywords = load_keywords(key, messages, spec.label)
    if keywords is None:
        result["error"] = "无有效输入"
        return result

    total = len(keywords)
    for i, kw in enumerate(keywords):
        if cancel_event is not None and cancel_event.is_set():
            result["cancelled"] = True
            messages.append(f"已取消：完成 {i}/{total} 个关键词")
            return result
        item = search_one(conn, spec, kw, fmt, cancel_event=cancel_event)
        result["items"].append(item)
        if item["cancelled"]:
            result["cancelled"] = True
            messages.append(f"已取消：完成 {i + 1}/{total} 个关键词")
            return result
        if progress is not None:
            progress(i + 1, total)
    return result
