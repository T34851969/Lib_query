# Lib_query（图书馆馆藏条目检索系统，C# 重构版）

基于 **.NET 10 + WinForms + SQLite FTS5** 的馆藏图书检索工具，Windows 专用。
由 PySide6（Qt 6）版本（本仓 v0.2.0 及更早，见 [Releases](https://github.com/T34851969/Lib_query/releases) 与历史标签）重构而来：
发布形态改为**自包含单文件 exe**（免安装、无 Python 依赖），数据库结构与检索行为与 Python 版完全兼容。

## 功能特性

- **四种检索方式**：题名模糊检索（FTS 索引）、索书号精确检索、索书号切片检索、ISBN 精确检索
- **单次 / 批量**：批量支持文本框逐行输入或从 TXT 文件导入，每个关键词独立输出一个结果文件
- **后台执行**：所有检索与导入均在后台线程运行，界面始终响应；批量任务有进度条，可随时取消
- **流式导出**：结果逐行写入 .xlsx 或 .csv，内存占用恒定，不随结果集大小膨胀
- **一键建库**：首次启动引导选择馆藏 Excel，自动建表、建索引、建 FTS5 题名索引
- **旧库兼容**：Python 版生成的数据库（含老版本无 FTS 的库）可直接使用；`--rebuild-fts` 一键补建索引（无需重导 Excel）

## 环境要求

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 10/11 x64 |
| 安装 | 免安装（自包含单文件；首次启动会把内嵌原生库解压到 `%TEMP%\.net`，属预期行为） |

## 发行版下载

打包好的程序发布在 [GitHub Releases](https://github.com/T34851969/Lib_query/releases)，每次推送 `v*` 标签时由
**self-hosted runner（ws2025 Windows VM，label `libq`）** 自动构建：

| 文件 | 说明 |
|---|---|
| `LibQuery-windows-x64.zip` | 解压后双击 `LibQuery.exe`；首次运行可能触发 SmartScreen 提示，选择"仍要运行" |

**注意**：数据库（`图书馆详细馆藏.db`）与 `output/` 生成在程序目录旁——请解压到**可写目录**使用，不要放在 `C:\Program Files` 等受限路径下。

旧 Python 版发行版（`Lib_query-windows-x64.zip` / `Lib_query-linux-x64.tar.gz`，v0.2.0 及更早）仍可从 Releases 下载；Linux 版自 v0.3.0 起不再提供（本重构为 Windows 专用）。

## 快速开始

1. 双击 `LibQuery.exe`
2. 首次启动若未找到 `图书馆详细馆藏.db`，程序会引导选择馆藏 Excel 文件完成建库
3. CLI 附加模式：`LibQuery.exe --selftest`（无界面自检）；`LibQuery.exe --rebuild-fts [--force] [数据库路径]`（补建 FTS 索引）

**馆藏 Excel 格式约定**（沿用 v0.1 的列布局）：

- 读取第一个工作表，首行为表头；
- 第 1~4 列保留原列名（`题名`、`索书号`、`标准号` 等，程序按列名建索引）；
- 第 5~11 列按位置重命名为 `level_1` ~ `level_7`（索书号分级，供切片检索使用）；
- 所有单元格按文本入库；Excel 中以数值格式存储的 ISBN 会自动去除小数尾巴（如 `9787030123456.0` → `9787030123456`）。

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

## 与 Python 版（v0.2.0）的兼容性

- **数据库完全兼容**：表结构（`books` + 全部索引名）、FTS5 虚表（`books_fts`，`content='books'` 外部内容 + 三触发器）、切片定位规则逐条对齐；Python 版生成的 `.db` 直接放到 exe 目录即可使用
- **差异点**：
  - Excel 导入改为流式逐块写库（内存恒定），进度按块回报"已写入 N 行"（Python 版整表物化后带总数回报）
  - 存量库补建索引由 `LibQuery.exe --rebuild-fts` 取代 `scripts/rebuild_fts.py`
  - Linux 发行版停止（Windows 专用）

## 架构

```
Program.cs ── --selftest / --rebuild-fts CLI 分支
  └─ MainForm ────────────────────── UI 线程：标签页容器 / 日志面板 / 状态栏
       ├─ SearchTab × 4（SearchSpecs 声明式配置，四个检索页共用一套模板）
       │    └─ TaskRunner（Task.Run + IProgress + CancellationToken）
       │         └─ LibraryService（连接生命周期，每次调用自建连接）
       │              ├─ Searcher.cs     参数化检索（题名/索书号/切片/ISBN）
       │              └─ Exporter.cs     流式导出 xlsx / csv（MiniExcel DataReader 通道）
       └─ 状态更新经 Progress<T>/BeginInvoke 封送回 UI 线程
```

- **线程模型**：每页一个 TaskRunner，任务运行期间禁用该页按钮、启用取消；取消经 `CancellationToken` 传递，导出循环每 5000 行响应一次
- **FTS5 索引**：外部内容表（`content='books'`）+ 三触发器同步，导入时一次性 `rebuild` 构建
- **xlsx 流式写出**：MiniExcel 的 DataReader 通道（表头取自游标列名，空结果也有表头行）；`CancellableReader` 包装游标实现预览捕获、行数截断与取消检查

## 项目结构

| 路径 | 说明 |
|---|---|
| `src/LibQuery/Program.cs` | 入口（`--selftest` / `--rebuild-fts` CLI 分支 + WinForms 启动） |
| `src/LibQuery/MainForm.cs` | 主窗口：检索页容器、日志面板、状态栏、首启导入引导 |
| `src/LibQuery/SearchTab.cs` | 检索页：单次 + 批量 UI 与任务编排 |
| `src/LibQuery/TaskRunner.cs` | 后台任务框架（Task.Run + Progress 封送 + busy 锁定 + 取消） |
| `src/LibQuery.Core/LibraryService.cs` | 检索编排层：连接生命周期、单次/批量入口（线程安全）+ `RebuildFts` |
| `src/LibQuery.Core/Searcher.cs` | 参数化检索实现与批量编排（四种模式） |
| `src/LibQuery.Core/SearchSpecs.cs` | 四个检索页的声明式配置 |
| `src/LibQuery.Core/Exporter.cs` | 流式导出 xlsx/csv（恒定内存、取消、行数上限保护）+ `CancellableReader` |
| `src/LibQuery.Core/Importer.cs` | Excel 导入建库（ExcelDataReader 流式）+ 索引 + FTS5 |
| `src/LibQuery.Core/Db.cs` | 连接管理、路径、FTS5 trigram 能力探测 |
| `src/LibQuery.Core/SelfTest.cs` | `--selftest` 无 UI 冒烟（报告写 `selftest_result.txt`，CI 用） |
| `src/LibQuery.Core/SynthDb.cs` | 合成馆藏库生成器（tests/bench/自检共用） |
| `bench/LibBench/` | 合成大库压测（默认 100 万行） |
| `tests/LibQuery.Core.Tests/` | xUnit 测试套件（检索/导入/导出正确性 + 取消/兼容路径） |
| `scripts/ws2025-build.cmd` | ws2025 构建入口（test/publish/selftest/bench/clean） |
| `scripts/x99-build.sh` | x99 Linux 构建/测试入口（交叉编译发布） |
| `.github/workflows/build.yml` | CI：push → 全量测试 + 发布 + 自检 + exe 工件 |
| `.github/workflows/release.yml` | CD：`v*` 标签 → 测试 + 发布 + 自检 → Release |

## 开发指南

**源码真源**：ws2025 Windows VM `C:\Users\Administrator\Desktop\Lib_query`（维护机经 `ssh ws2025` 直连）。
SDK 为 Windows 版 .NET 10（`C:\Users\Administrator\Desktop\dotnet`，已进机器 PATH）；x99（Arch）经 home-manager
`dotnet-sdk_10` 可跑 Linux 侧单元测试与交叉编译发布（`scripts/x99-build.sh`）。

**新增检索类型**：在 `src/LibQuery.Core/SearchSpecs.cs` 的 `All` 数组中追加一条 `SearchSpec`（指定匹配模式与输出目录）；如需新的匹配语义，在 `Searcher.BuildQuery` 增加一个 mode 分支。无需新建文件、无需改动界面代码。

**运行测试 / 构建**（ws2025）：

```bat
scripts\ws2025-build.cmd test
scripts\ws2025-build.cmd publish
scripts\ws2025-build.cmd selftest
```

**性能压测**：

```bat
dotnet run -c Release --project bench\LibBench -- --rows 1000000 --output D:\perf.db
```

**持续集成 / 部署**：CI 在 self-hosted runner（label `libq`，ws2025 VM 第三 runner，服务
`actions.runner.T34851969-Lib_query.LCARS-WIN-SERVE`）上运行，**每次全绿构建自动出发行包**：
- `build.yml`：push 到 main → 30 项单测 → 单文件发布 → `--selftest` 冒烟 → exe 工件（保留 14 天）
  → **滚动预发行 [nightly](https://github.com/T34851969/Lib_query/releases/tag/nightly)**（`LibQuery-windows-x64.zip` 同名刷新，下载链接恒定，Notes 记录 commit 与构建记录）
- `release.yml`：推送 `v*` 标签（或手动 dispatch）→ 同上全流程 → 自检报告文件判定通过后压缩上传**正式 Release**

**开发红线**：

- 任何耗时操作（检索 / 导入 / 导出）禁止在 UI 线程执行，必须经 `TaskRunner`
- 界面更新只能来自 Progress/BeginInvoke 回调，后台线程不得直接触碰任何控件
- 数据库与输出路径以 exe 所在目录为基准（`AppPaths`），不要引入对进程工作目录的依赖
- **Schema 兼容红线**：不得更改 `books` 列布局约定、`books_fts` 外部内容结构与索引命名——这是与 Python 版旧库互通的根基
- CI 关键路径一律官方上游（nuget.org），不得引入第三方镜像源（镜像政治脆弱面，见 x99 ai-ops ADR-0031）

## 常见问题

**Q：题名搜索 1~2 个字时明显变慢？**
trigram 分词器最小索引单元是 3 个字符，短关键词自动回退 LIKE 全表扫描。这是索引机制的固有限制，百万行库约 200 ms，属正常现象。

**Q：导入时提示某列变成 level_N 了？**
列布局约定第 5~11 列按位置重命名为 `level_1`~`level_7`（供切片检索）。若你的 Excel 列序有变，请调整表头使其匹配约定，或修改 `Importer.cs` 中的重命名规则。

**Q：启动时提示"SQLite 缺少 FTS5/trigram 支持"？**
C# 版内嵌 SQLite（Microsoft.Data.Sqlite / e_sqlite3 3.53.x）自带 FTS5 与 trigram，正常不会出现该提示；若自检报此错请附上 `--selftest` 的 `selftest_result.txt`。

**Q：结果文件在哪里？**
`output/<检索类型>/` 目录下，以关键词命名。该目录及数据库文件均固定在 exe 所在目录，与启动时的工作目录无关。
