@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ===============================================
echo    [Gemini-Claw] 终止序列开始 (Windows)
echo ===============================================

echo 尝试终止 daemon 与 API 进程...
:: 在 Windows 中由于缺乏良好的 PID 记录供脱离的 cmd 窗口使用，最快捷的方式是通过 Window Title 或者进程模块。
:: 如果使用 start 启动了窗口，它们可能在运行 python，我们尝试杀掉带参数的 python

echo ^> 正在寻找并终止 Python 进程 (run_daemon.py / api.py)...

:: 通过 wmic 查询命令行并终止 (此方法很稳健，只杀属于本项目的脚本)
for /f "tokens=2 delims==" %%I in ('wmic process where "name='python.exe' and commandline like '%%src\\\\run_daemon.py%%'" get processid /value 2^>nul') do (
    if "%%I" NEQ "" (
        echo 终止 run_daemon.py (PID: %%I)
        taskkill /PID %%I /F /T >nul 2>&1
    )
)

for /f "tokens=2 delims==" %%I in ('wmic process where "name='python.exe' and commandline like '%%src\\\\api.py%%'" get processid /value 2^>nul') do (
    if "%%I" NEQ "" (
        echo 终止 api.py (PID: %%I)
        taskkill /PID %%I /F /T >nul 2>&1
    )
)

:: 顺便清理一下可能会残留在 git bash 下用的 pid 文件
if exist run_daemon.pid del run_daemon.pid
if exist api.pid del api.pid

echo ===============================================
echo 所有本项目的后台进程已被清理。
echo ===============================================
endlocal
