@echo off
setlocal
cd /d "%~dp0"

echo ===============================================
echo    [Gemini-Claw] Terminating Services (Windows)
echo ===============================================

echo ^> Stopping Daemon and API processes...

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and ($_.CommandLine -match 'src[\\/]run_daemon\.py' -or $_.CommandLine -match 'src[\\/]api\.py') } | ForEach-Object { taskkill /F /T /PID $_.ProcessId }"

if exist run_daemon.pid del run_daemon.pid
if exist api.pid del api.pid

echo ===============================================
echo All background processes related to Gemini-Claw are stopped.
echo ===============================================
endlocal
