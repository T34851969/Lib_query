# Lib_query

图书检索工具，支持多种检索方式，基于Tkinter和pandas。

## 项目结构

| 路径/文件                          | 说明                         |
|------------------------------------|------------------------------|
| lib_query/                         | 主包，包含核心代码           |
| ├── __init__.py                    | 包初始化文件                 |
| ├── ctrl.py                        | 控制器                       |
| ├── gui/                           | 图形界面相关模块             |
| │   ├── __init__.py                | GUI子包初始化                |
| │   ├── style_config.py            | 统一应用个性化设置           |
| │   ├── core_tab.py                | 主界面Tab逻辑                |
| │   ├── title_tab.py               | 题名检索Tab                  |
| │   ├── call_num_piece_tab.py      | 索书号切片检索Tab            |
| │   ├── call_num_tab.py            | 索书号检索Tab                |
| │   └── isbn_tab.py                | ISBN检索Tab                  |
| └── db/                            | 数据库相关模块               |
|     ├── __init__.py                | DB子包初始化                 |
|     ├── core.py                    | 数据库连接、事务、公共工具   |
|     ├── importer.py                | Excel导入/建表逻辑           |
|     └── search/                    | 搜索函数子包                 |
|         ├── __init__.py            | 子包初始化                   |
|         ├── base_search.py         | 包抽象入口                   |
|         ├── title.py               | 题名检索 searchTitle         |
|         ├── call_num_piece.py      | 索书号分段检索 searchCnPart  |
|         ├── call_num.py            | 索书号检索 searchCallNum     |
|         └── isbn.py                | ISBN检索 searchIsbn          |
| main.py                            | 主程序                       |
| output/                            | 输出结果文件夹               |
| ├── title_result                   | 题名检索结果                 |
| ├── call_num_piece_result          | 索书号分段检索结果           |
| ├── call_num_result                | 索书号检索结果               |
| └── isbn                           | ISBN检索结果                 |
| pyproject.toml                     | Python项目配置               |
| requirements.txt                   | 依赖包列表                   |
| README.md                          | 项目说明文档                 |

## 主要功能

- 题名检索
- 索书号检索/分段检索
- ISBN检索
- Excel导入/导出
- 多格式结果输出（.xlsx/.csv）

## 运行方法

```bash
python main.py
```

## 依赖与引擎说明

- pandas：数据处理与分析
- tkinter：图形界面
- xlsxwriter：Excel 文件写入（pip install xlsxwriter）
- python-calamine：Excel 文件读写（pip install python-calamine）

## 主要引擎用途

- xlsxwriter 用于将检索结果导出为 .xlsx 文件，支持多样化格式和大数据量写入。
- python-calamine 用于读取 Excel 文件，兼容多种 Excel 格式，适合批量数据导入。

## 安装方法

推荐使用 pip 安装所有依赖：

```bash
pip install -r requirements.txt
```

或使用 poetry：

```bash
poetry install
```

## 典型用法示例

### 1. 启动主程序

```bash
python main.py
```

### 2. 检索流程

- 在 GUI 中选择检索类型（题名、索书号、ISBN），输入条件，点击检索。
- 检索结果自动保存至 output/ 对应子目录，格式为 .xlsx/.csv。

### 3. 数据导入

- 支持 Excel 文件批量导入，入口在 db/importer.py。

## 测试与开发流程

- 单元测试脚本：`test_db_module.py`，可用 VSCode 任务“Run db module unit tests”运行。
- 新增检索类型：在 db/search 新建 xxx.py，定义 searchXxx，并在 gui/tabs 新建对应 Tab 文件。
- 扩展结果输出：修改 db 层相关函数，确保写入 output/ 下新目录。
- 所有界面样式配置集中在 gui/style_config.py。

## 参考文档

- `.github/copilot-instructions.md`：AI 代码助手开发约定
- `requirements.txt`、`pyproject.toml`：依赖管理

---
如需补充特殊约定或遇到不明确的开发流程，请反馈以便完善本说明。
