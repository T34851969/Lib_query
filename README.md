# Lib_query

基于 **PySide6（Qt 6）** 与 **SQLite FTS5** 的馆藏图书检索工具。支持题名、索书号、索书号切片、ISBN 四种检索方式，单次或批量执行，结果导出为 .xlsx / .csv。

为图书馆采编/典藏场景设计：百万行级馆藏库，检索毫秒级响应，批量任务后台执行、界面不卡顿、随时可取消。

---

## 功能特性

- **四种检索方式**：题名模糊检索（FTS 索引）、索书号精确检索、索书号切片检索、ISBN 精确检索
- **单次 / 批量**：批量支持文本框逐行输入或从 TXT 文件导入，每个关键词独立输出一个结果文件
- **后台执行**：所有检索与导入均在后台线程运行，界面始终响应；批量任务有进度条，可随时取消
- **流式导出**：结果逐行写入 .xlsx（`constant_memory` 模式）或 .csv，内存占用恒定，不随结果集大小膨胀
- **一键建库**：首次启动引导选择馆藏 Excel，自动建表、建索引、建 FTS5 题名索引
- **旧库兼容**：老版本生成的数据库可直接使用，一条命令补建 FTS 索引（无需重导 Excel）

## 环境要求

| 项目 | 要求 |
|---|---|
| Python | ≥ 3.10 |
| SQLite | ≥ 3.34（需编译 FTS5 与 trigram 分词器；程序启动时自动检查） |
| 操作系统 | Windows / Linux / macOS（Qt 支持的桌面环境均可） |

## 发行版下载（免装 Python）

打包好的程序发布在 [GitHub Releases](https://github.com/T34851969/Lib_query/releases)，每次推送 `v*` 标签时由 GitHub Actions 自动构建：

| 文件 | 平台 | 使用方式 |
|---|---|---|
| `Lib_query-windows-x64.zip` | Windows 10/11 x64 | 解压后双击 `Lib_query.exe`；首次运行可能触发 SmartScreen 提示，选择"仍要运行" |
| `Lib_query-linux-x64.tar.gz` | Linux x64（glibc ≥ 2.35，Ubuntu 22.04 基准构建） | 解压后运行 `./Lib_query/Lib_query`；缺 `libGL/libEGL` 时用包管理器安装 |

**注意**：数据库（`图书馆详细馆藏.db`）与 `output/` 生成在程序目录旁——请解压到**可写目录**使用，不要放在 `C:\Program Files` 等受限路径下。

## 快速开始

```bash
# 1. 安装依赖
python -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip install -r requirements.txt

# 2. 启动
.venv/bin/python main.py
```

首次启动若未找到 `图书馆详细馆藏.db`，程序会引导选择馆藏 Excel 文件完成建库。

**馆藏 Excel 格式约定**（沿用 v0.1 的列布局）：

- 读取第一个工作表，首行为表头；
- 第 1~4 列保留原列名（`题名`、`索书号`、`标准号` 等，程序按列名建索引）；
- 第 5~11 列按位置重命名为 `level_1` ~ `level_7`（索书号分级，供切片检索使用）；
- 所有单元格按文本入库；Excel 中以数值格式存储的 ISBN 会自动去除小数尾巴（如 `9787030123456.0` → `9787030123456`）。

## 老版本数据库升级

v0.1 生成的 `.db` 文件可以直接使用。缺 FTS 索引时题名检索自动回退全表扫描（功能不受影响，仅速度慢）；运行一次以下脚本即可补建：

```bash
.venv/bin/python scripts/rebuild_fts.py                # 默认路径
.venv/bin/python scripts/rebuild_fts.py /path/to/库.db  # 指定路径
.venv/bin/python scripts/rebuild_fts.py --force /path/to/库.db  # 已有索引时强制重建
```

100 万行库首次构建约需 1~2 分钟，构建完成前程序仍可正常使用其他检索类型。

## 检索行为说明

| 检索类型 | 匹配规则 | 索引 |
|---|---|---|
| 题名检索 | 关键词出现在题名中即命中 | ≥3 字符走 FTS5 trigram 索引；1~2 字符回退 LIKE 全表扫描（trigram 最小单元为 3 字符，属正常现象） |
| 索书号检索 | 完整索书号等值匹配 | idx_call_number |
| 索书号切片 | 按关键词长度定位 `level_N` 列：长度 ≤5 匹配 `level_长度`；长度 >5 匹配 `level_(长度-1)`；5 位切片在 `level_5` 上做前缀匹配 | idx_cn_level_1~7 |
| ISBN 检索 | 完整标准号等值匹配 | idx_ISBN |

**导出规则**：

- 单次检索：结果预览写入日志面板，完整结果导出至 `output/<检索类型>/<关键词>.xlsx|csv`
- 批量检索：每个关键词独立输出一个文件；文件名中的非法字符（`\ / : * ? " < > |`）自动替换为 `-`，超长截断至 100 字符
- .xlsx 单表超过 1,048,575 行自动截断并在日志提示；.csv 无上限
- 编码：csv 使用 `utf-8-sig`（Excel 直接打开不乱码）

## 性能基准

以下为 `scripts/build_synth_db.py` 生成的 **100 万行合成库**实测数据（Python 3.13 / SQLite 3.46）：

| 场景 | v0.1（pandas + LIKE 全表扫描） | v0.2（FTS + 流式导出） |
|---|---|---|
| 题名检索（低频词，命中 200 行） | ~206 ms 仅查询，另加 pandas 全量转换 | **0.7 ms** 含导出 23 ms |
| 批量 100 个 ISBN + 逐词导出 xlsx | 逐条查询 + 每词 pandas 转换 | **306 ms** 全程 |
| Excel 导入建库（20 万行实测外推） | — | 100 万行约 30~40 s，峰值内存 ~1.5 GB |
| 导出内存占用 | 随结果集线性膨胀 | 恒定（流式写入） |

> v0.1 的题名检索在主线程执行同样的全表扫描，期间界面完全冻结——这是重构要解决的核心问题。

## 架构

```
main.py
  └─ MainWindow ──────────────────── 主线程：窗口 / 日志面板 / 状态栏
       ├─ SearchTab × 4（SearchSpec 声明式配置，四个检索页共用一套模板）
       │    └─ TaskRunner（gui/worker.py）
       │         └─ QThread 后台线程
       │              └─ LibraryService（service.py，连接生命周期）
       │                   ├─ db/search.py    参数化检索（题名/索书号/切片/ISBN）
       │                   └─ db/exporter.py  流式导出 xlsx / csv
       └─ 状态更新仅经 Qt 信号（progress / message / finished / failed）回主线程
```

- **线程模型**：每页一个 TaskRunner，任务运行期间禁用该页按钮、启用取消；取消经 `threading.Event` 传递，导出循环每 5000 行响应一次
- **FTS5 索引**：外部内容表（`content='books'`）+ 三触发器同步，导入时一次性 `rebuild` 构建

## 项目结构

| 路径 | 说明 |
|---|---|
| `main.py` | 程序入口（QApplication + MainWindow，启动时检查 FTS5 能力） |
| `lib_query/service.py` | 检索编排层：连接生命周期、单次/批量入口（线程安全） |
| `lib_query/gui/worker.py` | 后台任务框架：QThread + Worker（进度 / 消息 / 结果 / 失败 / 取消） |
| `lib_query/gui/main_window.py` | 主窗口：检索页容器、日志面板、状态栏、首启导入引导 |
| `lib_query/gui/search_tab.py` | 检索页基类：单次 + 批量 UI 与任务编排 |
| `lib_query/gui/tabs.py` | 四个检索页的声明式配置（`SEARCH_SPECS`） |
| `lib_query/gui/style.py` | 全局 QSS 样式 |
| `lib_query/db/core.py` | 连接管理、项目根路径解析、FTS5 能力检查 |
| `lib_query/db/importer.py` | Excel 导入建库（python-calamine）+ 索引 + FTS5 |
| `lib_query/db/search.py` | 参数化检索实现与批量编排 |
| `lib_query/db/exporter.py` | 流式导出 xlsx / csv（恒定内存、支持取消、行数上限保护） |
| `scripts/rebuild_fts.py` | 存量库补建 FTS 索引 |
| `scripts/build_synth_db.py` | 生成合成馆藏库（默认 100 万行），用于性能压测 |
| `.github/workflows/` | 打包流水线：Windows / Linux 发行版构建与发布 |
| `tests/` | pytest 测试套件（检索 / 导入 / 导出正确性 + GUI 冒烟） |

## 开发指南

**新增检索类型**：在 `lib_query/gui/tabs.py` 的 `SEARCH_SPECS` 中追加一条 `SearchSpec`（指定匹配模式与输出目录）；如需新的匹配语义，在 `lib_query/db/search.py` 的 `build_query()` 增加一个 mode 分支。无需新建文件、无需改动界面代码。

**运行测试**：

```bash
.venv/bin/pip install pytest
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -v
```

**性能压测**：

```bash
.venv/bin/python scripts/build_synth_db.py --rows 1000000 --output /tmp/perf.db
```

**本地打包**（与 CI 同流程）：

```bash
.venv/bin/pip install -e ".[build]"
.venv/bin/pyinstaller --clean --noconfirm --windowed --name Lib_query main.py   # Linux 去掉 --windowed
./dist/Lib_query/Lib_query --selfcheck    # 验证捆绑的 SQLite 支持 FTS5
```

**持续集成**：`.github/workflows/` 下有两个打包工作流（`release-windows.yml` / `release-linux.yml`），推送 `v*` 标签时自动构建并发布到 Releases；也可在 Actions 页面手动触发（workflow_dispatch），产物在构建工件里下载。两个工作流均先跑 `--selfcheck` 冒烟（校验捆绑 Python 的 SQLite 带 FTS5）再发布。

**开发红线**：

- 任何耗时操作（检索 / 导入 / 导出）禁止在主线程执行，必须经 `gui/worker.py` 的 `TaskRunner`
- 界面更新只能来自 Qt 信号回调，后台线程不得直接触碰任何 QWidget
- 数据库与输出路径以项目根为基准（`db/core.py`），不要引入对进程工作目录的依赖

## 常见问题

**Q：题名搜索 1~2 个字时明显变慢？**
trigram 分词器最小索引单元是 3 个字符，短关键词自动回退 LIKE 全表扫描。这是索引机制的固有限制，百万行库约 200 ms，属正常现象。

**Q：导入时提示某列变成 level_N 了？**
列布局约定第 5~11 列按位置重命名为 `level_1`~`level_7`（供切片检索）。若你的 Excel 列序有变，请调整表头使其匹配约定，或修改 `db/importer.py` 中的重命名规则。

**Q：启动时提示"SQLite 缺少 FTS5/trigram 支持"？**
系统的 Python SQLite 编译时未启用 FTS5。Linux 发行版自带的 SQLite 通常已启用；若为自编译版本，需加 `--enable-fts5` 重新编译。

**Q：结果文件在哪里？**
`output/<检索类型>/` 目录下，以关键词命名。该目录及数据库文件均固定在项目根目录，与启动时的工作目录无关。
