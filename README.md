# Project Gemini-Claw

**Gemini-Claw** 是一个极轻量级、全天候运行 (7x24)、跨平台 (Headless) 环境下的本地自治 AI Agent。它巧妙绕过了繁重的本地大模型部署和高昂的 API 计费，完全利用原生的 `gemini` CLI 来桥接逻辑池，具备主动任务调度、长期进化记忆以及可无限拓展的动态技能执行系统。

## 🌟 核心理念与特性

- **7\*24 永远在线 (Always-On)**: 基于 `APScheduler` 的后台守护进程，支持主动触发 Cron 调度任务（如：定时早报获取、系统巡检、记忆流反思清理），无需外界人工干预。
- **跨平台与环境自适应 (Cross-platform)**: 完美的平台级自适应脚本，支持 Linux Systemd 守护进程、macOS 及 Windows cmd 后台运行。自动嗅探 Conda 或 venv 隔离环境。
- **单通道纯文本强控规则**: `.md` 即系统！项目利用 `GEMINI.md` 作为顶级配置代理文件，级联阅读工作空间 (`AGENTS.md`)、核心机制 (`SOUL.md`) 等防击穿设定。
- **模型热切换与流式呈现**: 支持前端控制台一键切换多种 Gemini 模型 (`pro`, `flash`, `lite` 或 `auto` 默认)，数据流式呈现，内置 Markdown 高级渲染 (图片查看器，语法高亮等)。
- **开源插件化技能与媒体库 (Dynamic Skills & Media)**: `skills/` 目录下的 Python 脚本会自动识别为 Agent 可调用的原生工具 (如：ffmpeg 传感器捕捉、Web Search)。所有生成的多媒体资源均存放于 `media/`，前后端完全静态解耦。

---

## 🚀 快速启动

本仓库推荐使用 Conda 或 venv 虚拟环境以隔离您的纯净服务器。

### 1. 环境准备

```bash
# 全局环境依赖（如需要）并确保 gemini cli 已成功安装可用
conda create -n geminiclaw python=3.10 -y
conda activate geminiclaw
pip install -r requirements.txt
```

### 2. 编译 Dashboard 前端 (首次运行必须执行)

为了保证前端面板能正常加载，**首次运行前必须手动通过 Node.js 构建并打包一次**前端产物供后端托管：

```bash
cd web
npm install
npm run build
cd ..
```

### 3. 本地快捷启动与停止 (Dev & Testing)

系统能自动检测您的系统环境和 Python 虚拟环境，使用最稳妥的方式将任务挂起至后台。

- **Linux / macOS**:
  ```bash
  chmod +x start.sh stop.sh
  ./start.sh
  ```
- **Windows**:
  直接双击 `start.bat` 运行，停止时运行 `stop.bat`。

一旦所有后台进程苏醒：

- **Web UI 界面**: 请访问 `http://127.0.0.1:8888`
- **默认登录密码**: 初始化时使用的 Access Code 默认为 `claw` (定义于项目根目录 `config.json` 中)
- **系统日志监控**:
  - `tail -f logs/api.log` (FastAPI 桥接)
  - `tail -f logs/daemon.log` (核心心跳生命体)

### 4. Linux 生产环境 (Systemd 服务模式)

如果您希望在 Ubuntu/Debian 主机上长期稳定运行且支持开机自启，请使用提供的专门脚本：

```bash
./install_service.sh -y
```

安装后，您可以通过标准指令管理 Agent：
`sudo systemctl start geminiclaw` | `stop` | `restart` | `status`

---

## 🗂️ 核心架构速写目录

```text
gemini-claw/
├── config.json             # 环境与鉴权口令配置 (Access Code)
├── SYSTEM_PROMPTS_TEMPLATE.md # 💡 模板 (通过 init_env.py 拆分为以下配置)
│   ├── GEMINI.md           # 被 CLI 读取的强入口
│   ├── AGENTS.md           # 工作空间规则与生存指南
│   ├── SOUL.md             # 底线与核心准则
│   └── MEMORY.md           # 长期事实记忆库
├── start.sh / .bat         # ▶️ 跨平台启动机制
├── stop.sh / .bat          # ⏹️ 跨平台终止机制
├── install_service.sh      # 🐧 Linux Systemd 守护配置工具
├── memory/                 # 📂 每日流水账纯文本与 memory.db 持久化数据表
├── media/                  # 📂 独立解耦的公共媒体池 (图片/视频)，前后端共享挂载
├── src/                    # 📂 Python API 与引擎工作流
│   ├── init_env.py         # 增强型模板加载与环境校验器
│   ├── engine.py           # 稳定处理 CLI 寻址/模型参数注入与 Session 保持
│   ├── api.py              # WebSocket / REST 网关（内置 HMAC Token 防线）
│   ├── memory.py           # SQLite 长效记忆系统
│   └── run_daemon.py       # 后台心跳起搏器 (APScheduler)
├── skills/                 # 📂 安全的降级容错插件集 (system/camera/web_search)
└── web/                    # 📂 React + Tailwind 开发的响应式流控仪表盘 (Dashboard)
```

## ⚖️ 知识声明

本项目赋予了 Agent 执行本地脚本、终端命令和文件系统探针探索的极大自由裁量权。如果将此 Agent 接入公网环境，务必修改默认的鉴权密钥，并设置好反向代理或 WAF。请始终保持 `SOUL.md` 控制其破坏性行为的威慑力以策万全。
