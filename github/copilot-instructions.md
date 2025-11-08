# Lib_query 项目 Copilot 指南

## 项目架构总览

- **主包结构**：`lib_query/` 下分为 `gui`（图形界面）、`db`（数据库相关）、`ctrl.py`（控制中心）。
- **主入口**：`main.py`，创建 Tkinter GUI 应用，调用 [`lib_query.gui.create_app`](lib_query/gui/__init__.py)。
- **GUI 设计**：所有标签页（如标题检索、索书号检索等）在 `lib_query/gui/tabs/` 下实现，每个 tab 通过 `create(app, parent)` 入口函数注册到主界面。
- **数据库交互**：通过 [`LibraryDatabase`](lib_query/db/core.py) 类实现，支持上下文管理（with 语句），所有查询均在 `lib_query/db/search/` 下实现为类（如 [`TitleSearch`](lib_query/db/search/title.py)）。
- **控制中心**：[`CentreCrtl`](lib_query/ctrl.py) 负责统一调度数据库操作，供 GUI 层调用。

## 关键开发流程

- **构建/运行**：直接运行 `main.py` 启动 GUI，无需额外构建步骤。
    ```sh
    python main.py
    ```
- **数据库初始化**：通过 [`import_excel`](lib_query/db/impoter.py) 从 Excel 文件导入数据，自动建表并创建索引。
- **输出结果**：所有检索结果自动保存到 `output/` 目录下的对应子文件夹（如 `标题搜索结果/`），文件名会自动清理非法字符。

## 项目约定与模式

- **面向对象范式**：所有检索逻辑均以类实现，继承 [`SearchBase`](lib_query/db/search/search_base.py)。
- **样式统一**：GUI 样式通过 [`apply`](lib_query/gui/style_config.py) 统一设置，可动态切换主题。
- **Tab 注册**：每个 tab 需实现 `create(app, parent)`，由 [`LibraryApp.load_tab_modules`](lib_query/gui/core_tab.py) 自动加载。
- **输出格式**：支持 `.xlsx` 和 `.csv`，由界面单选按钮选择，底层统一调用 `SearchBase.output`。
- **错误处理**：所有数据库操作均捕获异常，返回结构化 dict，包含 `messages` 字段用于界面输出。

## 依赖与集成

- **依赖**：主要依赖 `pandas`、`tkinter`，Excel 导入用 `calamine` 引擎。
- **外部数据**：仅通过 Excel 文件导入，未集成外部 API。
- **扩展性**：新增检索类型需在 `db/search/` 下实现新类，并在 `gui/tabs/` 下添加对应 tab。

## 重要文件/目录

- [`main.py`](main.py)：主程序入口
- [`lib_query/gui/core_tab.py`](lib_query/gui/core_tab.py)：主窗口与 tab 管理
- [`lib_query/ctrl.py`](lib_query/ctrl.py)：控制中心，统一数据库操作
- [`lib_query/db/core.py`](lib_query/db/core.py)：数据库连接与工具
- [`lib_query/db/search/`](lib_query/db/search/)：所有检索逻辑
- [`lib_query/gui/tabs/`](lib_query/gui/tabs/)：所有 GUI 标签页

---

如有不清楚或遗漏的部分，请反馈，我会进一步完善说明！
