#!/bin/bash
# stop.sh - 平滑终止所有 Gemini-Claw 相关后台服务

echo "==============================================="
echo "   [Gemini-Claw] 终止序列开始 "
echo "==============================================="

cd "$(dirname "$0")"

if [ -f "run_daemon.pid" ]; then
    DAEMON_PID=$(cat run_daemon.pid)
    echo "终止后台心跳总线 (run_daemon.py) PID: $DAEMON_PID"
    kill $DAEMON_PID 2>/dev/null
    rm run_daemon.pid
else
    echo "未找到后台心跳记录文件 (run_daemon.pid)，尝试强制 pkill"
    pkill -f "python src/run_daemon.py"
fi

if [ -f "api.pid" ]; then
    API_PID=$(cat api.pid)
    echo "终止后台接口服务 (api.py) PID: $API_PID"
    kill $API_PID 2>/dev/null
    rm api.pid
else
    echo "未找到后台接口服务文件 (api.pid)，尝试强制 pkill"
    pkill -f "python src/api.py"
fi

echo "==============================================="
echo "所有本项目的后台进程已被清理。"
echo "==============================================="
