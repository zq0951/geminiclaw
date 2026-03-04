#!/bin/bash
# start.sh - 一键启动所有 Gemini-Claw 相关后台服务

# 确保切换到项目根目录
cd "$(dirname "$0")"

# 1. 系统类型判断
OS_TYPE="Unknown"
case "$OSTYPE" in
  linux*)   OS_TYPE="Linux" ;;
  darwin*)  OS_TYPE="macOS" ;;
  msys*|cygwin*|win32*) OS_TYPE="Windows" ;;
  *)
    if uname -a | grep -iq "mingw\|cygwin\|windows"; then
      OS_TYPE="Windows"
    fi
    ;;
esac

echo "==============================================="
echo "   [Gemini-Claw] 启动序列开始 (OS: $OS_TYPE) "
echo "==============================================="

# 2. 尝试拉起虚拟环境 (Conda / venv)
if command -v conda >/dev/null 2>&1 && conda env list | grep -q "geminiclaw"; then
    CONDA_BASE=$(conda info --base 2>/dev/null)
    if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        source "$CONDA_BASE/etc/profile.d/conda.sh"
        conda activate geminiclaw 2>/dev/null
    fi
elif [ -f "venv/bin/activate" ]; then
    source "venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
else
    echo "💡 提示: 未检测到特定 conda (geminiclaw) / venv，将使用找到的环境 Python 执行。"
fi

# 确保存放日志的目录存在
mkdir -p logs

# 执行初次运行配置（如果模板存在且配置不存在）
echo "> 检查并拆分 Markdown 配置模板 ..."
python src/init_env.py

# 3. 启动底层后台心跳和反思守护进程
echo "> 启动 run_daemon.py ..."
nohup python src/run_daemon.py > logs/daemon.log 2>&1 &
DAEMON_PID=$!
echo $DAEMON_PID > run_daemon.pid
echo "   Daemon PID: $DAEMON_PID"

# 4. 启动与前端交互的 FastAPI 层
echo "> 启动 api.py (Web Dashboard) ..."
nohup python src/api.py > logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > api.pid
echo "   API PID: $API_PID"

echo "==============================================="
echo "所有核心服务均已转入后台运行！"
echo "- 控制台日志可通过查看 logs/api.log 或 logs/daemon.log 实时获取。"
echo "- Frontend 大屏可访问 http://127.0.0.1:8888"
echo "你可以运行 ./stop.sh 优雅关闭这些服务。"

if [ "$OS_TYPE" = "Linux" ]; then
    echo "-----------------------------------------------"
    echo "💡 提示: 您在 Ubuntu/Linux 下，如果希望开机自启且作为服务长期运行，"
    echo "建议运行 ./install_service.sh 将其注册为 systemd 守护服务。"
fi
echo "==============================================="
