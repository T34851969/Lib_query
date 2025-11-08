# Lib_query

图书检索工具，支持多种检索方式，基于Tkinter和pandas。

## 项目结构

Lib_query                           # 项目根目录
├── lib_query                           # 主包，包含核心代码
│   ├── __init__.py                         # 包初始化文件
│   ├── ctrl.py                             # 控制器
│   ├── gui                                 # 图形界面相关模块
│   │   ├── __init__.py                         # GUI子包初始化
│   │   ├── style_config.py                    # 统一应用个性化设置
│   │   ├── core_tab.py                         # 主界面Tab逻辑
│   │   ├── title_tab.py                        # 题名检索Tab
│   │   ├── call_num_piece_tab.py               # 索书号切片检索Tab
│   │   ├── call_num_tab.py                     # 索书号检索Tab
│   │   └── isbn_tab.py                         # ISBN检索Tab
│   └── db                            # 数据库相关模块
│       ├── __init__.py                     # DB子包初始化
│       ├── core.py                         # 数据库连接、事务、公共工具
│       ├── importer.py                     # Excel导入/建表逻辑
│       └── search                          # 搜索函数子包
│           ├── __init__.py                     # 子包初始化
│           ├── base_search.py                  # 包抽象入口
│           ├── title.py                        # 题名检索 searchTitle
│           ├── call_num_piece.py               # 索书号分段检索 searchCnPart
│           ├── call_num.py                     # 索书号检索 searchCallNum
│           └── isbn.py                         # ISBN检索 searchIsbn
├── main.py                         # 主程序
├── output                              # 输出结果文件夹
│   ├── title_result                    # 题名检索结果
│   ├── call_num_piece_result           # 索书号分段检索结果
│   ├── call_num_result                 # 索书号检索结果
│   └── isbn                            # ISBN检索结果
├── pyproject.toml                  # Python项目配置
├── requirements.txt                # 依赖包列表
└── README.md                       # 项目说明文档

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

## 依赖

- pandas
- tkinter

