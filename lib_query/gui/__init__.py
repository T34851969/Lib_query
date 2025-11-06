"""lib_query.gui 包的公共接口。

导出：
- LibraryApp: 主应用类（位于 core_tab.py）
- apply_style: 样式应用函数（来自 style_config）
- create_app: 便利工厂函数，创建并可选地加载所有标签模块
"""
from typing import Optional
import tkinter as tk

from .core_tab import LibraryApp
from .style_config import apply as apply_style

__all__ = ["LibraryApp", "apply_style", "create_app"]


def create_app(root: tk.Tk, *, load_tabs: bool = True, theme: Optional[str] = None) -> LibraryApp:
    """
    创建 LibraryApp 实例并（可选）加载包内的标签模块。

    参数:
      root: 已创建的 tk.Tk 或 tk.Toplevel 对象。
      load_tabs: 是否在创建后自动调用 app.load_tab_modules()。
      theme: 如果提供，则在创建前应用该主题（会调用 apply_style）。

    返回:
      已初始化并（可选）加载好标签的 LibraryApp 实例。
    """
    if theme is not None:
        apply_style(root, theme=theme)
    # LibraryApp __init__ 也会调用 style_config.apply；这里允许外部覆盖主题
    app = LibraryApp(root)
    if load_tabs:
        app.load_tab_modules()
    return app