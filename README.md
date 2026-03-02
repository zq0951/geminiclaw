# Project Gemini-Claw

**Gemini-Claw** 是一个旨在构建极轻量级、全天候运行 (7x24)、纯无头 (Headless) 环境下的本地自治 AI Agent。它巧妙绕过了繁重的本地大模型部署和高昂的 API 计费，完全利用原生的 `gemini cli` 来桥接逻辑池，具备长期记忆、自我反思以及通过 `local-jarvis` 高度兼容的技能执行系统。

## 🌟 核心理念与特性

- **7\*24 永远在线**: 基于 `APScheduler` 的后台守护进程，无论是定时早报获取、系统巡检，还是每日的记忆流反思清理，都不需要外界人工拉起。
- **Agent 降本增益 (Headless)**: 不依赖 `langchain` / `smolagents` 或任何复杂的重型调用编排框架。模型的所有系统工具能力源自内置的 CLI 并直接穿透您的系统外壳进行交互。
- **单通道纯文本强控规则**: `.md` 即系统！项目利用 `GEMINI.md` 作为顶级配置代理文件，级联阅读人设 (`IDENTITY`)、核心机制 (`SOUL`) 以及机器信息 (`USER.md`)。
- **现代化 Web Dashboard**: 摆脱纯命令行的认知负荷，我们随附了一个全栈编译的基于 React + TailwindCSS 的流式黑客面版。WebSocket 数据管道实时为您投射大模型的内部状态与决策意图。

---

## 🚀 快速启动

本仓库推荐并严格要求使用 Conda 虚拟环境以隔离您的纯净服务器（特别是避免 Ubuntu 等系统的 PIP 墙）。

### 1. 环境准备

```bash
# 全局环境依赖（如需要）并确保 gemini cli 已成功安装可用
conda create -n geminiclaw python=3.10 -y
conda activate geminiclaw
pip install -r requirements.txt
```

### 2. 编译 Dashboard 前端 (若需二次开发)

该项目已包含编译完成的产物供后端托管，若您需要调整：

```bash
cd web
npm install
npm run build
cd ..
```

### 3. 一键挂载守护系统与 API 面板

启动前，确保本系统能正常免密读写所有需要操作的目录。

```bash
# 在项目根目录下执行脚本
chmod +x start.sh stop.sh
./start.sh
```

一旦所有后台进程苏醒：

- **Web UI 界面**: 请访问 `http://<服务器IP或本地>:8000`
- **系统日志监控**:
  - `tail -f logs/api.log` (FastAPI 桥接)
  - `tail -f logs/daemon.log` (核心心跳生命体)

如果需要关闭实验，请直接运行同目录下的 `./stop.sh` 脚本优雅停止。

---

## 🗂️ 核心架构速写目录

```text
gemini-claw/
├── GEMINI.md               # 💡 系统唯一强入口 (默认被 CLI 读取，负责调度下方文件)
├── SOUL.md                 # 💡 底线与核心准则 (被 GEMINI.md 会话初期级联读取)
├── IDENTITY.md             # 💡 你的身份定义 (e.g. Jarvis)
├── USER.md                 # 💡 主人你的个人偏好 (时区, 环境 等)
├── MEMORY.md               # 💡 长期事实记忆库（会由内部心跳主动更新）
├── TOOLS.md                # 💡 可用插件集概览，由 system 自动生成
├── start.sh                # ▶️ 一键进入后台运转
├── src/                    # Python API 与引擎脚手架
│   ├── engine.py           # CLI Session 并发保持
│   ├── api.py              # WebSocket / REST 网关
│   ├── memory.py           # SQLite 长效记忆增删改与防遗忘系统
│   └── run_daemon.py       # 后台的心跳起搏器 (APScheduler 注册)
├── skills/                 # Agent 操作能力，放进去的所有.py会自动组装
└── web/                    # 基于 React/Tailwind 开发的高级流式视觉监控台
```

## ⚖️ 知识声明

本项目专为与 `local-jarvis` 的跨生态适配而构筑极大的向外自由裁量权，允许高级命令工具挂载。请始终保留 `SOUL.md` 控制其破坏性行为。
