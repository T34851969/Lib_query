@echo off
REM Build helper for LibQuery on ws2025 VM.
REM Usage: ws2025-build.cmd test|publish|selftest|bench|clean
setlocal
cd /d "%~dp0.."
set "DOTNET=C:\Users\Administrator\Desktop\dotnet\dotnet.exe"
if not exist "%DOTNET%" set "DOTNET=dotnet.exe"

if /i "%~1"=="test"     goto test
if /i "%~1"=="publish"  goto publish
if /i "%~1"=="selftest" goto selftest
if /i "%~1"=="bench"    goto bench
if /i "%~1"=="clean"    goto clean
echo Usage: ws2025-build.cmd test^|publish^|selftest^|bench^|clean
exit /b 2

:test
"%DOTNET%" test LibQuery.sln -c Release --nologo -p:NuGetAudit=false
exit /b %errorlevel%

:publish
"%DOTNET%" publish src\LibQuery -c Release -p:NuGetAudit=false -o dist --nologo
exit /b %errorlevel%

:selftest
if not exist dist\LibQuery.exe echo dist\LibQuery.exe not found - run publish first & exit /b 1
dist\LibQuery.exe --selftest
exit /b %errorlevel%

:bench
"%DOTNET%" run -c Release --project bench\LibBench --nologo
exit /b %errorlevel%

:clean
git clean -xdq -e dist
exit /b %errorlevel%
