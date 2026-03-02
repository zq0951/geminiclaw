#!/bin/bash
# start.sh - 一键启动所有 Gemini-Claw 相关后台服务

# 确保切换到项目根目录
cd "$(dirname "$0")"

# 尝试通过 conda base 路径拉起系统
source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate geminiclaw

echo "==============================================="
echo "   [Gemini-Claw] 启动序列开始 "
echo "==============================================="

# 确保存放日志的目录存在
mkdir -p logs

# 启动底层后台心跳和反思守护进程
echo "> 启动 run_daemon.py ..."
nohup python src/run_daemon.py > logs/daemon.log 2>&1 &
DAEMON_PID=$!
echo $DAEMON_PID > run_daemon.pid
echo "   Daemon PID: $DAEMON_PID"

# 启动与前端交互的 FastAPI 层
echo "> 启动 api.py (Web Dashboard) ..."
nohup python src/api.py > logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > api.pid
echo "   API PID: $API_PID"

echo "==============================================="
echo "所有核心服务均已转入后台运行！"
echo "- 控制台日志可通过查看 logs/api.log 或 logs/daemon.log 实时获取。"
echo "- Frontend 大屏可访问 http://<SERVER_IP>:8000"
echo "你可以运行 ./stop.sh 优雅关闭这些服务。"
echo "==============================================="
