#!/bin/bash
# 确保在项目根目录运行
cd "$(dirname "$0")"

# 环境激活
source "/root/miniconda3/etc/profile.d/conda.sh" && conda activate geminiclaw || {
    echo "❌ 错误: 无法激活 Conda 环境 'geminiclaw'，请检查环境是否存在。"
    exit 1
}

# 显式指定 Node.js 版本（解决 gemini-cli 在 v18 环境下正则表达式报错问题）
# 我们发现系统存在 v24 版本，而 daemon 默认使用了包含错误的 v18
export PATH="/root/.nvm/versions/node/v24.12.0/bin:$PATH"

export PYTHONPATH=$PYTHONPATH:$(pwd)/skills

# 0. 前置清理：彻底清理旧进程，防止端口 8888 冲突导致的静默启动失败
echo "> 确认并清理旧进程以释放端口..."
pkill -9 -f "python src/run_daemon.py" 2>/dev/null || true
pkill -9 -f "python src/api.py" 2>/dev/null || true
pkill -9 -f "node.*/web/node_modules/.bin/next" 2>/dev/null || true
pkill -9 -f "node.*/gemini" 2>/dev/null || true

sleep 1

echo "> 检查并拆分 Markdown 配置模板 ..."
python src/init_env.py

echo "> 启动守护进程和API..."
# 启动守护进程
python src/run_daemon.py >> "/root/geminiclaw/logs/daemon.log" 2>&1 &
DAEMON_PID=$!

# 启动 API 服务 (已禁用 reload=True 以增强生产稳定性)
python src/api.py >> "/root/geminiclaw/logs/api.log" 2>&1 &
API_PID=$!

echo "Node version: $(node -v)"
echo "Daemon Started (PID: $DAEMON_PID) | API Started (PID: $API_PID)"

# 捕获退出信号：当 systemd 发起 Stop 或 Restart 时
trap "echo 'Systemd 信号捕获: 正在关闭子进程...'; kill -15 $DAEMON_PID $API_PID 2>/dev/null; sleep 1; kill -9 $DAEMON_PID $API_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# 健壮的阻塞监测机制：只要其中一个关键进程退出，脚本即退出，从而通知 systemd 服务状态异常
while true; do
  # 检查 Daemon
  if ! kill -0 $DAEMON_PID 2>/dev/null; then
    echo "警告: 守护进程 (PID $DAEMON_PID) 异常退出！"
    tail -n 10 /root/geminiclaw/logs/daemon.log
    exit 1
  fi
  
  # 检查 API
  if ! kill -0 $API_PID 2>/dev/null; then
    echo "警告: API 进程 (PID $API_PID) 异常退出！"
    tail -n 10 /root/geminiclaw/logs/api.log
    exit 1
  fi
  
  sleep 5
done
