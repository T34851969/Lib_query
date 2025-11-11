"""lib_query.gui 包公共接口
导出：
- LibraryApp: 主应用类（位于 core_tab.py）
- apply_style: 样式应用函数（来自 style_config）
- create_app: 便利工厂函数，创建并可选地加载所有标签模块
"""
from typing import Optional
import tkinter as tk

from .core_tab import LibraryApp
from lib_query.gui.style_config import StyleConfig

def apply_style(root, theme: str='clam'):
  return StyleConfig.apply(root, theme)

__all__ = ["LibraryApp", "apply_style", "create_app"]


def create_app(root: tk.Tk, *, ctrl=None, load_tabs: bool = True, theme: Optional[str] = None) -> LibraryApp:
    """
    创建 LibraryApp 实例并（可选）加载包内的标签模块。

    参数:
      root: 已创建的 tk.Tk 或 tk.Toplevel 对象。
      ctrl: 可选，传入的控制器实例（如 CentreCrtl），用于全局共享。
      load_tabs: 是否在创建后自动调用 app.load_tab_modules()。
      theme: 如果提供，则在创建前应用该主题（会调用 apply_style）。

    返回:
      已初始化并（可选）加载好标签的 LibraryApp 实例。
    """
    if theme is not None:
        apply_style(root, theme=theme)
    app = LibraryApp(root, ctrl=ctrl)  # 传递 ctrl 实例
    if load_tabs:
        app.load_tab_modules()
    return app