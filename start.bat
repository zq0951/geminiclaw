@echo off
setlocal
cd /d "%~dp0"

echo ===============================================
echo    [Gemini-Claw] Start Sequence (Windows)
echo ===============================================

if not exist logs mkdir logs

echo ^> Checking environment configuration...
set "ACTIVATE_CMD=conda activate geminiclaw"
call %ACTIVATE_CMD% >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if exist "venv\Scripts\activate.bat" (
        set "ACTIVATE_CMD=call venv\Scripts\activate.bat"
    ) else if exist ".venv\Scripts\activate.bat" (
        set "ACTIVATE_CMD=call .venv\Scripts\activate.bat"
    ) else (
        set ACTIVATE_CMD=
        echo [INFO] Conda or Virtualenv not found. Using system default Python.
    )
)

python src\init_env.py

if "%ACTIVATE_CMD%"=="" (
    set "EXEC_DAEMON=python src\run_daemon.py >> logs\daemon.log 2>&1"
    set "EXEC_API=python src\api.py >> logs\api.log 2>&1"
) else (
    set "EXEC_DAEMON=%ACTIVATE_CMD% & python src\run_daemon.py >> logs\daemon.log 2>&1"
    set "EXEC_API=%ACTIVATE_CMD% & python src\api.py >> logs\api.log 2>&1"
)

echo Set objArgs = WScript.Arguments > run_hidden.vbs
echo Set WshShell = CreateObject("WScript.Shell") >> run_hidden.vbs
echo WshShell.Run "cmd /c """ ^& objArgs(0) ^& """", 0, False >> run_hidden.vbs

echo ^> Starting run_daemon.py in background...
cscript //nologo run_hidden.vbs "%EXEC_DAEMON%"

echo ^> Starting api.py (Web Dashboard) in background...
cscript //nologo run_hidden.vbs "%EXEC_API%"

del run_hidden.vbs

echo ===============================================
echo [SUCCESS] Services are now running silently in the background!
echo - Please check logs\api.log or logs\daemon.log for details.
echo - Web Dashboard is available at http://127.0.0.1:8888
echo 
echo Run stop.bat whenever you want to stop these processes.
echo ===============================================
endlocal
