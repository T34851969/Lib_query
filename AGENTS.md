# AGENTS.md — Lib_query 仓 Agent 约定

> 本文件面向任何接手本仓的 Agent。事实源在机器，文档只辅助——动手前先在机器上验证。

## 仓库定位

- 图书馆藏条目检索系统，**C#/.NET 10 + WinForms 重构版**（原 PySide6 版存于 git 历史 v0.2.0 及更早）
- 红线：**不新建仓库，一切变更推回本仓**（T34851969/Lib_query，public）

## 源码真源与构建

| 机器 | 角色 | 入口 |
|---|---|---|
| ws2025 VM（10.0.0.50） | 源码真源 + 全量构建/测试/发布 | `ssh ws2025` → `C:\Users\Administrator\Desktop\Lib_query` → `scripts\ws2025-build.cmd test|publish|selftest` |
| x99（Arch） | Linux 侧单测 + 交叉编译验证 | `/data/work/Lib_query` → `scripts/x99-build.sh test|publish`（SDK 经 home-manager dotnet-sdk_10） |

- ws2025 SDK：`C:\Users\Administrator\Desktop\dotnet`（10.0.404，机器 PATH）；Git 为 Git for Windows
- x99：`~/.nix-profile/bin/dotnet`；NUGET_PACKAGES/DOTNET_CLI_HOME 重定向 /data/toolchains（脚本内已钉）

## CI/CD

- **Runner**：ws2025 第三 self-hosted runner（仅注册到本仓），目录 `C:\Program Files\actions-runner-libq`，
  服务 `actions.runner.T34851969-Lib_query.LCARS-WIN-SERVE`（SYSTEM、延迟自启），label **`libq`**
  ——与 ISBN_query 仓 runner（actions-runner-isbnq）和 Proj 仓 runner（actions-runner）互不相干，勿动后两者
- `build.yml`：push main → 单测 30 → publish → `--selftest` → exe 工件 → **自动转正发行包**
  （读最新稳定 tag，patch+1，标记 Latest，--generate-notes；用户裁定：每次 Actions 跑完必须出
  发行包，且**不打预备发行标签，直接转正**）
- `release.yml`：`v*` 标签 → 同上全流程 → 自检报告文件判定（`selftest_result.txt`，WinExe 无控制台）→
  `LibQuery-windows-x64.zip` 上正式 Release；调试附件失败时回传 Release、成功后清理

## 工程红线

1. **Schema 兼容**：`books` 列布局（1~4 列原名 + 5~11 列 level_1~7）、`books_fts`（trigram, content='books'）、
   索引命名——与 Python 版旧库互通的根基，不得更改
2. **零镜像**：CI/构建一律官方上游（nuget.org）；高校/第三方镜像 = 政治脆弱面（x99 ai-ops ADR-0031）
3. **线程铁律**：耗时操作必须经 TaskRunner 后台执行；UI 更新只经 Progress/BeginInvoke 封送
4. **编码**：bat 必须 CRLF+ASCII；C# 源 UTF-8；`--selftest` 报告写 CWD 的 `selftest_result.txt`（双判定：报告内容 + 退出码）
5. **单文件发布**：net10.0-windows + PublishSingleFile + IncludeNativeLibrariesForSelfExtract；
   x99 交叉编译依赖 `EnableWindowsTargeting=true`，勿删
6. **变更必回写**：本仓变更若涉及 ws2025 机器面（runner/SDK/服务），同步登记到维护机 `~/AGENTS.md` 公共知识索引
