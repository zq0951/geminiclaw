# Project Gemini-Claw

**Gemini-Claw** 是一个极轻量级、全天候运行 (7x24)、纯无头 (Headless) 环境下的本地自治 AI Agent。它巧妙绕过了繁重的本地大模型部署和高昂的 API 计费，完全利用原生的 `gemini cli` 来桥接逻辑池，具备主动任务调度、长期进化记忆以及可无限拓展的动态技能执行系统。

## 🌟 核心理念与特性

- **7\*24 永远在线 (Always-On)**: 基于 `APScheduler` 的后台守护进程，支持主动触发 Cron 调度任务（如：定时早报获取、系统巡检、记忆流反思清理），无需外界人工干预。
- **极低资源依赖 (Lightweight & Headless)**: 不依赖重量级编排框架，通过 Python `subprocess` 与原生 `gemini cli` 交互，实现无头会话保持 (Session Continuity)。
- **单通道纯文本强控规则**: `.md` 即系统！项目利用 `GEMINI.md` 作为顶级配置代理文件，级联阅读人设 (`IDENTITY.md`)、核心机制 (`SOUL.md`) 以及机器信息 (`USER.md`)。
- **动态记忆层 (Evolutionary Memory)**: 摒弃沉重的数据库，结合 SQLite 与纯文本，实现每日日志 (Daily Logs)、核心记忆 (MEMORY.md) 与主动内省机制。
- **现代化 Web Dashboard**: 随附一个全栈编译的基于 React + TailwindCSS 的前端控制面板。WebSocket 数据管道实时为您投射大模型的内部状态与决策意图，并已集成基于 Token 的身份验证以加强 API 接口安全。
- **开源插件化技能 (Dynamic Skills)**: `skills/` 目录下的 Python 脚本会被自动识别并转化为 Agent 可调用的原生工具，随时通过文件挂载实现能力拓展。

---

## 🚀 快速启动

本仓库推荐使用 Conda 虚拟环境以隔离您的纯净服务器（特别是避免 Ubuntu 等系统的 PIP 墙）。

### 1. 环境准备

```bash
# 全局环境依赖（如需要）并确保 gemini cli 已成功安装可用
conda create -n geminiclaw python=3.10 -y
conda activate geminiclaw
pip install -r requirements.txt
```

### 2. 编译 Dashboard 前端 (首次运行必须执行)

为了保证前端面板能正常加载，**首次运行前必须手动通过 Node.js 构建并打包一次**前端产物供后端托管。之后若有前端二次修改，亦需重新运行此步骤：

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

- **Web UI 界面**: 请访问 `http://<服务器IP或本地>:8000` (如果配置了鉴权，请使用系统生成的 Token 登录)
- **系统日志监控**:
  - `tail -f logs/api.log` (FastAPI 桥接)
  - `tail -f logs/daemon.log` (核心心跳生命体)

如果需要关闭实验，请直接运行同目录下的 `./stop.sh` 脚本优雅停止。

---

## 🗂️ 核心架构速写目录

```text
gemini-claw/
├── .env                    # 环境与鉴权配置 (含 API Token 设定)
├── SYSTEM_PROMPTS_TEMPLATE.md # 💡 系统唯一初始模板 (首次运行将一键拆分为以下配置文件)
│   ├── GEMINI.md           # 被 CLI 读取的强入口
│   ├── SOUL.md             # 底线与核心准则
│   ├── IDENTITY.md         # 你的身份定义
│   ├── USER.md             # 主人个人偏好
│   ├── MEMORY.md           # 长期事实记忆库
│   └── TOOLS.md            # 可用插件集概览
├── start.sh / stop.sh      # ▶️ 一键进入后台与停止系统脚本
├── memory/                 # 📂 每日流水账流式纯文本与持久化数据表目录
├── src/                    # 📂 Python API 与引擎工作流
│   ├── init_env.py         # 自动拆分 Markdown 模板的初始化程序
│   ├── engine.py           # CLI Session 并发保持
│   ├── api.py              # WebSocket / REST 网关（具备 Token 安全防线）
│   ├── memory.py           # SQLite 长效记忆增删改与防遗忘系统
│   └── run_daemon.py       # 后台的心跳起搏器 (APScheduler 注册)
├── skills/                 # 📂 标准化 Agent 操作能力集，放入.py全自动读取
└── web/                    # 📂 基于 React/Tailwind 开发的高级流式视觉监控台
```

## ⚖️ 知识声明

本项目由于允许执行本地脚本、终端命令以及外置功能模块，因而被赋予了极大的向外自由裁量权。如果将此 Agent 接入公网环境使用，务必保障服务器与 Web 界面的基础访问防护。请始终妥善编写与保留 `SOUL.md` 控制其破坏性行为以策万全。
