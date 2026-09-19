"""四个检索页的声明式配置（顺序沿用旧版 TAB_MODULES）。"""
from __future__ import annotations

from lib_query.db.search import (
    MODE_EXACT,
    MODE_PIECE,
    MODE_TITLE,
    SearchSpec,
)
from lib_query.service import LibraryService

from .search_tab import SearchTab

SEARCH_SPECS = [
    SearchSpec(
        key="call_num_piece",
        dir_name="索书号切片",
        label="索书号切片检索",
        mode=MODE_PIECE,
        tip="输入索书号切片（1~6 位），如 I247.5；5 位切片按前缀匹配",
    ),
    SearchSpec(
        key="call_num",
        dir_name="索书号",
        label="索书号检索",
        mode=MODE_EXACT,
        column="索书号",
        tip="输入完整索书号，精确匹配",
    ),
    SearchSpec(
        key="isbn",
        dir_name="ISBN",
        label="ISBN 检索",
        mode=MODE_EXACT,
        column="标准号",
        tip="输入完整标准号（ISBN），精确匹配",
    ),
    SearchSpec(
        key="title",
        dir_name="题名",
        label="题名检索",
        mode=MODE_TITLE,
        tip="输入题名关键词；≥3 字符走 FTS 索引，更短的关键词回退全表扫描",
    ),
]


def build_tabs(service: LibraryService, log) -> list[tuple[str, SearchTab]]:
    """按配置生成全部检索页，返回 (页签名, 页面) 列表。"""
    return [(spec.label, SearchTab(service, spec, log)) for spec in SEARCH_SPECS]
