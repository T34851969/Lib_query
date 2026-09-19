"""结果流式导出：sqlite 游标逐行写出 xlsx/csv，内存占用恒定。

写入过程中支持取消：取消时删除半成品文件并抛出 ExportCancelled。
"""
from __future__ import annotations

import csv
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Optional

import xlsxwriter

from .core import OUTPUT_DIR

# Excel 单工作表数据行上限（不含表头）
XLSX_MAX_ROWS = 1_048_575

_ILLEGAL = '<>:"/\\|?*'
_TRANS = str.maketrans(_ILLEGAL, '-' * len(_ILLEGAL))


class ExportCancelled(RuntimeError):
    """导出过程被用户取消。"""


def clean_name(name: str, limit: int = 100) -> str:
    """关键词转安全文件名：非法字符替换为 '-'，超长截断。"""
    cleaned = name.translate(_TRANS).strip() or "未命名"
    return cleaned[:limit]


class HeadCapture:
    """包装行迭代器，顺带保留前 N 行用于界面预览。"""

    def __init__(self, rows: Sequence[Sequence], limit: int = 5):
        self._it = iter(rows)
        self._limit = limit
        self.head: list[tuple] = []

    def __iter__(self) -> Iterator[tuple]:
        return self

    def __next__(self) -> tuple:
        row = next(self._it)
        if len(self.head) < self._limit:
            self.head.append(row)
        return row


def _check_cancel(cancel_event, n: int, check_every: int) -> bool:
    return cancel_event is not None and n % check_every == 0 and cancel_event.is_set()


def export_rows(
    fmt: str,
    directory: str,
    filename: str,
    columns: Sequence[str],
    rows: Sequence[Sequence],
    *,
    out_root: Optional[Path] = None,
    cancel_event=None,
    check_every: int = 5000,
) -> tuple[Path, int, bool]:
    """将行迭代器流式写入 output/<directory>/<filename>.<ext>。

    返回 (输出路径, 行数, 是否因 Excel 行数上限截断)。取消时抛 ExportCancelled。
    """
    root = out_root or OUTPUT_DIR
    out_dir = Path(root) / directory
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = "csv" if fmt == "csv" else "xlsx"
    path = out_dir / f"{clean_name(filename)}.{ext}"

    n = 0
    truncated = False
    cancelled = False
    cap = rows if isinstance(rows, HeadCapture) else HeadCapture(rows)

    if ext == "csv":
        with path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(columns)
            try:
                for row in cap:
                    writer.writerow(["" if v is None else v for v in row])
                    n += 1
                    if _check_cancel(cancel_event, n, check_every):
                        cancelled = True
                        break
            finally:
                fh.close()
    else:
        wb = xlsxwriter.Workbook(str(path), {"constant_memory": True})
        ws = wb.add_worksheet()
        ws.write_row(0, 0, list(columns))
        try:
            for row in cap:
                ws.write_row(n + 1, 0, list(row))
                n += 1
                if n >= XLSX_MAX_ROWS:
                    truncated = True
                    break
                if _check_cancel(cancel_event, n, check_every):
                    cancelled = True
                    break
        finally:
            wb.close()

    if cancelled:
        path.unlink(missing_ok=True)
        raise ExportCancelled(f"导出已取消（已处理 {n} 行）")
    return path, n, truncated


def format_preview(columns: Sequence[str], head: list[tuple]) -> Optional[str]:
    """前几行结果的文本预览（用于界面日志显示）。"""
    if not head:
        return None
    lines = [" | ".join(columns)]
    lines.extend(" | ".join("" if v is None else str(v) for v in row) for row in head)
    return "\n".join(lines)
