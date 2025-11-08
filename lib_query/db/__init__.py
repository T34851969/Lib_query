"""db 包初始化：导出数据库类、导入器及搜索子模块的便捷接口。"""

from .core import LibraryDatabase
from . import search

__all__ = [
    "LibraryDatabase",
    "search",
    "all_records",
    "return_path"
]
