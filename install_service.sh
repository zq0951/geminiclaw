#!/bin/bash
# install_service.sh - (仅限 Linux systemd) 将 Gemini-Claw 注册为系统后台服务

cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)
USER_NAME=$(whoami)

echo "==============================================="
echo "     Gemini-Claw Systemd 服务安装脚本"
echo "==============================================="

# 确保在 Linux 下且支持 systemctl
if ! command -v systemctl >/dev/null 2>&1; then
    echo "❌ 错误：当前系统不支持 systemd (例如处于 Windows / macOS 或者是 WSL1)。"
    echo "无法注册为 systemd 常规服务。"
    exit 1
fi

PYTHON_EXEC="python"
ACTIVATE_CMD=""

# 1. 寻找 Conda 路径并推断是否含有对应环境
if command -v conda >/dev/null 2>&1; then
    CONDA_BASE=$(conda info --base 2>/dev/null)
    if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        if conda env list | grep -q "geminiclaw"; then
            ACTIVATE_CMD="source \"$CONDA_BASE/etc/profile.d/conda.sh\" && conda activate geminiclaw"
            echo "✅ 检测到 Conda 环境 geminiclaw"
        fi
    fi
fi

# 2. 回退机制：检查本目录下的 venv，或者直接采用系统 python
if [ -z "$ACTIVATE_CMD" ]; then
    if [ -f "venv/bin/activate" ]; then
        ACTIVATE_CMD="source venv/bin/activate"
        echo "✅ 检测到虚拟环境 venv (venv/bin/activate)"
    elif [ -f ".venv/bin/activate" ]; then
        ACTIVATE_CMD="source .venv/bin/activate"
        echo "✅ 检测到虚拟环境 .venv (.venv/bin/activate)"
    else
        PYTHON_EXEC=$(which python3 2>/dev/null || which python 2>/dev/null)
        if [ -z "$PYTHON_EXEC" ]; then
            echo "❌ 错误：未能找到 Python 执行文件，请确认已安装 Python。"
            exit 1
        fi
        echo "💡 提示: 未检测到特定 conda (geminiclaw) / venv，将使用找到的环境 Python: $PYTHON_EXEC"
    fi
fi

# 确保存放日志的目录存在
mkdir -p "$PROJECT_DIR/logs"

# 3. 生成单一 wrapper 启动脚本 service_start_all.sh
USER_PATH="$PATH"

cat <<EOF > service_start_all.sh
#!/bin/bash
cd "${PROJECT_DIR}"

# 注入当前用户的环境变量 PATH，特别是针对 .nvm 或 .npm-global 等路径
export PATH="${USER_PATH}"

${ACTIVATE_CMD}

echo "> 检查并拆分 Markdown 配置模板 ..."
${PYTHON_EXEC} src/init_env.py

echo "> 启动守护进程和API..."
# 在后台分别启动 daemon 和 api，日志写入各自文件以便区分
${PYTHON_EXEC} src/run_daemon.py >> "${PROJECT_DIR}/logs/daemon.log" 2>&1 &
DAEMON_PID=\$!

${PYTHON_EXEC} src/api.py >> "${PROJECT_DIR}/logs/api.log" 2>&1 &
API_PID=\$!

# 设置退出清理机制：当 systemd 停止此服务 (发 SIGTERM) 时，将连带终止子进程
trap "kill -15 \$DAEMON_PID \$API_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# 阻塞等待子进程 (必须阻塞，否则 service 脚本会立刻终止)
wait \$DAEMON_PID \$API_PID
EOF
chmod +x service_start_all.sh

echo "✅ 完成启动包装脚本生成: service_start_all.sh"
echo "正在请求 sudo 权限以写入 /etc/systemd/system/ ..."

# 4. 制作单一的 geminiclaw.service
cat <<EOF | sudo tee /etc/systemd/system/geminiclaw.service > /dev/null
[Unit]
Description=Gemini-Claw Unified Service (Daemon & API)
After=network.target

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/service_start_all.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 成功生成 systemd 守护配置。"
echo "正在重新加载 systemd 并启用开机自启服务..."
sudo systemctl daemon-reload
sudo systemctl enable geminiclaw.service

# 支持非交互模式 (-y 自动启动, -n 不启动)
START_NOW="ask"
while getopts "yn" opt; do
  case $opt in
    y) START_NOW="y" ;;
    n) START_NOW="n" ;;
  esac
done

if [ "$START_NOW" = "ask" ]; then
    read -p "是否现在立即启动/重启 Systemd 后台服务？(y/N) " choice
    case "$choice" in 
      y|Y ) START_NOW="y" ;;
      * ) START_NOW="n" ;;
    esac
fi

if [ "$START_NOW" = "y" ]; then
    sudo systemctl restart geminiclaw
    echo "✅ 服务已运行。可通过 systemctl status geminiclaw 查看状态。"
else
    echo "💡 您稍后可以使用命令启动: sudo systemctl start geminiclaw"
fi

echo "==============================================="
echo "🎉 安装完成！统一的系统服务已就绪 (Ubuntu/Linux模式)"
echo "-----------------------------------------------"
echo "  启动服务: sudo systemctl start geminiclaw"
echo "  停止服务: sudo systemctl stop geminiclaw"
echo "  重载服务: sudo systemctl restart geminiclaw"
echo "  查看状态: sudo systemctl status geminiclaw"
echo "  查看日志: tail -f logs/api.log logs/daemon.log"
echo "==============================================="
