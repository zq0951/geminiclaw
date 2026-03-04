#!/bin/bash
# stop.sh - 平滑终止所有 Gemini-Claw 相关后台服务

cd "$(dirname "$0")"

# 系统类型判断
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
echo "   [Gemini-Claw] 终止序列开始 (OS: $OS_TYPE) "
echo "==============================================="

stop_process() {
    PID_FILE=$1
    PROCESS_MARK=${2:-""}

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "终止服务 PID: $PID (对应记录: $PID_FILE) ..."
        if [ "$OS_TYPE" = "Windows" ]; then
            # Windows 下可能需要 taskkill，但 Git Bash 下 kill 经常也是有效的
            kill -15 $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        else
            kill -15 $PID 2>/dev/null
            sleep 1
            kill -9 $PID 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    else
        echo "未找到 $PID_FILE，尝试根据进程特征 ($PROCESS_MARK) 关闭..."
        pkill -f "python src/$PROCESS_MARK" 2>/dev/null || true
    fi
}

# 停止 daemon
stop_process "run_daemon.pid" "run_daemon.py"

# 停止 api
stop_process "api.pid" "api.py"

# 如果配置了 Systemd 服务，给出提示
if [ "$OS_TYPE" = "Linux" ]; then
    if systemctl is-active --quiet geminiclaw.service 2>/dev/null; then
        echo "-----------------------------------------------"
        echo "警告: 检测到 systemd 服务正在运行！"
        echo "若要彻底停止服务，请使用: sudo systemctl stop geminiclaw"
        echo "-----------------------------------------------"
    fi
fi

echo "==============================================="
echo "所有本项目的后台进程已被清理。"
echo "==============================================="
