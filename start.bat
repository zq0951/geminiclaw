@echo off
:: Set UTF-8 encoding as early as possible to prevent parsing misalignment
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ===============================================
echo    [Gemini-Claw] 启动序列开始 (Windows)
echo ===============================================

:: 检查日志目录
if not exist "logs" mkdir logs

:: 尝试运行环境初始化
echo ^> 检查环境配置 ...
set ACTIVATE_CMD=conda activate geminiclaw
call %ACTIVATE_CMD% 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "venv\Scripts\activate.bat" (
        set ACTIVATE_CMD=venv\Scripts\activate.bat
        call %ACTIVATE_CMD%
    ) else if exist ".venv\Scripts\activate.bat" (
        set ACTIVATE_CMD=.venv\Scripts\activate.bat
        call %ACTIVATE_CMD%
    ) else (
        set ACTIVATE_CMD=
        echo [提示] 未找到 conda geminiclaw 环境或 venv 目录，将采用当前终端默认 Python。
    )
)

python src\init_env.py

:: 使用 start /b 在后台执行并不弹新窗口
:: 判断如果有激活命令则连带执行，如果没有则直接执行 python
if "%ACTIVATE_CMD%"=="" (
    set EXEC_DAEMON=python src\run_daemon.py ^>^> logs\daemon.log 2^>^&1
    set EXEC_API=python src\api.py ^>^> logs\api.log 2^>^&1
) else (
    set EXEC_DAEMON=%ACTIVATE_CMD% ^& python src\run_daemon.py ^>^> logs\daemon.log 2^>^&1
    set EXEC_API=%ACTIVATE_CMD% ^& python src\api.py ^>^> logs\api.log 2^>^&1
)

echo ^> 启动 run_daemon.py ...
start /b cmd /c "%EXEC_DAEMON%"

echo ^> 启动 api.py (Web Dashboard) ...
start /b cmd /c "%EXEC_API%"

echo ===============================================
echo 🚀 服务已在后台隐式启动成功！
echo - 控制台日志可通过查看 logs\api.log 或 logs\daemon.log 获取。
echo - Frontend 大屏可访问 http://127.0.0.1:8888
echo 你可以运行 stop.bat 优雅关闭这些服务。
echo 若要在 Windows 下作为自启服务，可将 start.bat 的快捷方式放入"启动"文件夹。
echo ===============================================
endlocal
