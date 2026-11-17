#!/usr/bin/env bash
# LibQuery 在 x99（Arch + nix dotnet-sdk_10）上的构建入口。
# 用法: scripts/x99-build.sh [test|bench|publish|all]
# 机器约定：
#   - SDK 经 home-manager（dotnet-sdk_10），无全局 dotnet → 显式前置 ~/.nix-profile/bin
#   - GB 级状态只在 /data（AGENTS.md 规则 4）→ NUGET_PACKAGES / DOTNET_CLI_HOME 重定向
set -euo pipefail

export PATH="$HOME/.nix-profile/bin:$PATH"
export NUGET_PACKAGES=/data/toolchains/nuget-packages
export DOTNET_CLI_HOME=/data/toolchains/dotnet-cli-home
export DOTNET_NOLOGO=1
export DOTNET_CLI_TELEMETRY_OPTOUT=1

cd "$(dirname "$0")/.."

TEST_PROJ="tests/LibQuery.Core.Tests/LibQuery.Core.Tests.csproj"

case "${1:-test}" in
  test)
    dotnet test "$TEST_PROJ" -c Release
    ;;
  bench)
    dotnet run -c Release --project bench/LibBench
    ;;
  publish)
    rm -rf dist
    dotnet publish src/LibQuery/LibQuery.csproj -c Release -o dist \
      -p:DebugType=none -p:DebugSymbols=false
    ls -lh dist/
    ;;
  all)
    dotnet test "$TEST_PROJ" -c Release
    rm -rf dist
    dotnet publish src/LibQuery/LibQuery.csproj -c Release -o dist \
      -p:DebugType=none -p:DebugSymbols=false
    ls -lh dist/
    ;;
  *)
    echo "unknown target: $1 (test|bench|publish|all)" >&2
    exit 2
    ;;
esac
