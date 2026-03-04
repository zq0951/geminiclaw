@echo off
setlocal
cd /d "%~dp0"

echo ===============================================
echo    [Gemini-Claw] Terminating Services (Windows)
echo ===============================================

echo ^> Stopping Daemon and API processes...

for /f "tokens=2 delims==" %%I in ('wmic process where "name='python.exe' and commandline like '%%src\\\\run_daemon.py%%'" get processid /value 2^>nul') do (
    if "%%I" NEQ "" (
        echo Killing run_daemon.py ^(PID: %%I^)
        taskkill /PID %%I /F /T >nul 2>&1
    )
)

for /f "tokens=2 delims==" %%I in ('wmic process where "name='python.exe' and commandline like '%%src\\\\api.py%%'" get processid /value 2^>nul') do (
    if "%%I" NEQ "" (
        echo Killing api.py ^(PID: %%I^)
        taskkill /PID %%I /F /T >nul 2>&1
    )
)

if exist run_daemon.pid del run_daemon.pid
if exist api.pid del api.pid

echo ===============================================
echo All background processes related to Gemini-Claw are stopped.
echo ===============================================
endlocal
