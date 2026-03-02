# 项目计划书：轻量级全天候 Gemini 自治代理 (Project Gemini-Claw)

## 1. 项目愿景与目标 (Vision & Goals)

本项目旨在利用您拥有的 **Google Pro/Gemini API 额度**，构建一个**极其轻量、纯后端的纯无头 (Headless)** 自治 AI Agent。它借鉴了 OpenClaw 的核心理念，提供 7\*24 小时的后台不间断运行能力，支持任务定时调度与自我规划，并具备可无限迭代的长期记忆系统。

**核心能力：**

1. **7\*24 小时存活 (Always-On)**：通过守护进程或后台任务，系统保持永不休眠，或处于事件监听状态。
2. **主动计划与执行 (Cron/Schedule)**：不仅能被动响应，还能基于时钟 (`cron`) 定期主动触发任务（如：每日新闻总结、清理日志、定时巡检）。
3. **长期记忆与内省 (Local Persisted Memory)**：不再受限于单个上下文窗口，具备记忆写入、检索记忆、反思提炼（Reflection）的能力。
4. **极低资源依赖 (Lightweight)**：无需显卡算力，完全依赖 Gemini Cloud API 执行思考。

---

## 2. 核心架构设计 (Architecture)

整体系统架构秉持 **“最小集（Minimalist）”** 和 **“原子化（Atomic）”** 原则。主要包含四大模块：

### 2.1 引擎核心层 (Core Engine & IO)

- **事件总线 (Event Loop)**：基于 Python `asyncio`，处理所有异步任务和并发。
- **触发器 (Triggers)**：
- **事件总线 (Event Loop)**：基于 Python `asyncio`，处理所有异步任务和并发。
- **触发器 (Triggers)**：
  - _CLI Command_: 命令行手动交互 / 唤醒。
  - _Cron Scheduler_: 解析标准的 Cron 表达式（如 `0 8 * * *`），主动触发 Agent 处理预设或它自己给自己安排的任务。
  - _Webhook / System Events_:（可选扩展）通过 HTTP 或系统监控触发。

### 2.2 动态技能层 (Dynamic Skills)

- **开源插件化架构**：为了保证本项目的独立性与开源友好度，将引入一套极简的 Skills 挂载规范。任何第三方开发者（或大模型自己）只需按照规范在 `skills/` 下放入单个 Python 脚本或 `yaml` 配置，即可被宿主识别并转化为 Agent 可调用的工具。
- **高度向下兼容**：这套机制设计上将完美兼容 `local-jarvis` 现已沉淀的成熟技能生态（例如 HA 智能家居、系统控制等），使用者可以通过文件拷贝或软链接（`ln -s`）实现零成本迁移与平替。
- **动态执行引擎**：由于 `gemini cli` 内置执行本地代码的能力，外围代码甚至无需做复杂的 AST 或者 Import Hook，只需在系统提示词侧将 `skills/` 目录能力列表作为 Prompt 灌入，让模型自行决策执行什么命令。

### 2.3 LLM 接口层 (Headless CLI Wrapper)

- **无头会话保持 (Session Continuity)**：摒弃传统 API SDK，转而使用 Python `subprocess`。首条初始激活消息使用 `gemini -p "<prompt>" -y -o json` 运行，获取 CLI 返回的 JSON 结构并提取出新会话的 `Session ID`。后续的心跳轮询、定时任务均使用 `gemini -r <Session ID> -p "<prompt>" -y -o json` 继续在**同一个对话上下文**内交流。这完美解决了短期工作记忆连贯性的问题。
- **内置原生工具链 (Native OS Tools)**：最新的 `gemini cli` 已经原生内置了执行 Shell 命令、全量文件读写的能力。使用 `--approval-mode yolo` 或 `-y` 参数，可以使大模型免确认自动执行这些内置动作（如直接搜索系统日志、调用本地 Python 代码）。
- **系统配置与入口路由 (Root Context Entry)**：利用 `gemini cli` 会默认自动读取宿主目录 `GEMINI.md` 的特性。我们在项目根目录下维护 `GEMINI.md` 作为唯一的 **Root Prompt 注入点**。在 `GEMINI.md` 内部，刻入明确指令：_"启动初始化时，请立即读取并遵循本目录下的 `SOUL.md` (行为底线)、`IDENTITY.md` (助手人设)、`USER.md` (主人偏好) 以及 `MEMORY.md`"_。通过这种“单点启动、级联拉取”的方式，实现 0 代码文本控制整个复杂生态。

### 2.4 动态记忆层 (Evolutionary Memory)

完全对标原味 OpenClaw 的记忆隔离策略，摒弃沉重的数据库，回归纯文本力量：

- **每日流水账 (Daily Logs)**：按天生成的纯文本日志（如 `memory/2026-03-03.md`），代理在日常对话与后台任务中的原始动作、临时思考都会记录在此。
- **核心记忆 (MEMORY.md)**：专属于主人的长期精炼记忆。代理通过内省，将有价值的事实从 Daily Logs 中提取出来，沉淀进 `MEMORY.md`。
- **环境备忘录 (TOOLS.md)**：存放诸如本地服务器内网IP、特定设备的配置备注，将“怎么做”和“工具细节”与主记忆脱离。
- **主动心跳与内省 (Heartbeat & Reflection)**：引入定期推送的 `HEARTBEAT` 提示词。“心跳”触发时，提醒代理查看日常邮件、系统状态，并在每天空闲时汇总流水账，自我修剪 `MEMORY.md`。

### 2.5 Web 前端交互层 (Web Dashboard)

为满足直观的监控与交互需求，项目将配备一个轻量级、现代化的 Web 前端应用页面：

- **状态大屏 (Dashboard)**：动态实时展示 Agent 当前的生存状态、近期日志、正在规划与执行的定时任务 (Cron Jobs) 以及与 API 交互流。
- **记忆管理视图 (Memory Viewer)**：可视化查看和检索每日流水与核心 `MEMORY.md`，允许用户手动修正、补充先验知识点。
- **即时指令与干预 (Chat / Command Box)**：通过 WebSocket 或轻量 HTTP 接口接入，随时从浏览器下发最高优先级指令，甚至人工中断/干预工作流。

---

## 3. 技术栈建议 (Tech Stack)

| 领域             | 推荐技术/库                 | 说明                                                                  |
| :--------------- | :-------------------------- | :-------------------------------------------------------------------- |
| **编程语言**     | `Python 3.10+`              | 生态最完善，适合快速起步                                              |
| **大模型接口**   | `pexpect` / `subprocess`    | 用来拉起并控制 `gemini cli`，捕获模型输出，实现**无头免额度**通信     |
| **服务端 API**   | `FastAPI` / `AIOHTTP`       | 用于支撑前端与 Agent 事件总线的轻量级异步接口和 WebSocket 交互        |
| **Web UI 前端**  | 原生 HTML+JS / Vue / React  | 极简现代化 UI（流式终端响应式大屏、流畅动画等），提升主控视觉心智负荷 |
| **定时调度**     | `APScheduler`               | 支持 cron、interval、date 多种调度方式，纯后台 Python 运行            |
| **记忆与持久化** | `SQLite3` + 纯文本          | 降低运维复杂度，避免起沉重的数据库；可选使用 `sqlite-vec` 处理向量    |
| **守护进程管理** | `systemd` 或 `PM2` / `tmux` | 在 Linux 环境下实现宕机重启与 7\*24 持续运行                          |

---

## 4. 实施路线图 (Roadmap)

### 阶段 1：核心代理与 Gemini CLI 无头封装 (Week 1)

- **目标**：不使用官方 API，攻克 `gemini cli` 的无头并发调用、Session 继承与原生工具自动化。
- **任务**：
  1.  提炼 `gemini cli` 的调用参数，特别是 `-p`（无头模式）、`-y`（跳过确认自动动作）与 `-o json`（结构化输出）。
  2.  实现 `GeminiCliAdapter` 类封装：初次调用捕获输出 JSON 拿到 `Session ID`，通过注入 `-r <Session ID>` 机制做到同一对话不中断的无限轮转。
  3.  验证模型在本地免授权执行终端命令能力，证明其可以自动调用 `date` 甚至自主读取项目里的 `SOUL.md` 等身份文件。

### 阶段 2：长程记忆库 (OpenClaw-like Memory) 构建 (Week 1-2)

2.  设计记忆数据库表结构（`Memories: id, content, importance, timestamp, category`）。
3.  赋予 Agent 新工具：`search_memory`, `add_memory`, `update_core_preference`。
4.  **优化提示词**：在每次 System Prompt 注入当前时刻和最新最热的 Memory 摘要。

### 阶段 3：自主时钟与 Cron 调度 (Week 2)

- **目标**：让 Agent 具备主动苏醒的生物钟。
- **任务**：
  1.  引入 `APScheduler`。
  2.  实现底层的任务注册接口，比如注册一个 `cron: "0 8 * * *", task: "每日早间简报检索与总结"`。
  3.  开放 `SchedulerTool` 供 Agent 自身调用，使其可以对自己说：“_这件事明天下午提醒我再跟进_”并写入定时队列。

### 阶段 4：系统“内省”与闭环 (Week 3)

- **目标**：实现记忆自清理，防止长期运行上下文溢出。
- **任务**：
  1.  建立特殊守护任务：**System Cleanup / Reflection**。
  2.  当闲置或特定时间 (如凌晨 3 点)，系统自动拉取前一天的日志。
  3.  调起一次大上下文 Gemini 总结，提炼成长期 Fact，覆盖进 Core Profile，并删除繁杂的底层事件日志。

### 阶段 5：构建开源标准 Skills 架构 (Week 4)

- **目标**：确立开源向的“即插即用”技能库，赋予模型自我进化的创造力。
- **任务**：
  1.  建立规范的 `skills/` 提供标准工具加载器（`loader.py`）以及至少 2 个基础开源示范（如 `system.py`, `web_search.py`）。
  2.  设计能力说明书（`TOOLS.md`），使得大模型一眼看懂每个代码文件对应的能力与可用参数。
  3.  通过文档预设，无缝打通或软链接（`ln -s`）导入你已有的 `jarvis-core` 强大插件库，展现其超高兼容性。
  4.  _(进阶)_ 提供 `CodeExecutor` 或类似于 `Computer Use` 的能力，并结合 `write_file` 准许 Agent 根据自己的需求自己撰写并挂载新的 Python Skill，达成针对本地化环境的常驻进化。

### 阶段 6：Web 前端交互页面开发 (Week 5)

- **目标**：打造极具现代感、响应式的可视化监控与交互控制面板。
- **任务**：
  1.  利用 `FastAPI` 建立 API 服务，向外暴露 REST 接口与 WebSocket 服务，打通底层的事件总线。
  2.  开发前端监控页面 (Web UI Dashboard)，重点设计暗黑模式、动态终端输出视觉效果与调度看板。
  3.  增加状态穿透功能，支持用户通过 Web 页面直观下发临时指令与任务，甚至覆盖/修改当前的记忆点与 Cron 设置。

---

## 5. 项目结构初稿设计

```text
gemini-claw/
├── .env                    # 可能用到的辅助配置
├── GEMINI.md               # 💡 系统唯一强入口 (默认被 CLI 读取，负责调度下方文件)
├── SOUL.md                 # 💡 底线与核心准则 (被 GEMINI.md 会话初期级联读取)
├── IDENTITY.md             # 💡 你的身份定义 (e.g. Jarvis)
├── USER.md                 # 💡 主人你的个人偏好 (小鹏, Timezone 等)
├── MEMORY.md               # 💡 高纯度的长期事实记忆库
├── TOOLS.md                # 💡 本地服务器备忘与 Skills 能力说明书
├── run_daemon.py           # 守护进程入口 (Heartbeat 触发器)
├── memory/
│   └── 2026-03-03.md       # 每日流水账，原始日志
├── src/
│   ├── engine.py           # 无头 CLI 拉起套件、JSON 解析与 Session 延续逻辑
│   └── api.py              # (New) 轻量后端 API 路由与 WebSocket 推送服务
├── web/                    # 📂 (New) Web 前端 UI 源码展现层
│   ├── index.html          # 控制台入口文件大屏
│   ├── css/                # 极简全局现代样式与动画定义
│   └── js/                 # 交互生命周期与 WebSocket 对接层
└── skills/                 # 📂 标准化可插拔开源技能模块
    ├── loader.py           # (可选) Skill 加载或描述提取器
    ├── iot_home.py         # 示例：智能家居控制 (可复用 jarvis-core)
    └── get_weather.py      # 示例：获取天气
```

## 6. 下一步操作建议 (Next Steps)

如果你确认此计划满足需求，我们可以按照 **阶段 1** 立即开始：

1. 我会在你的当前环境下创建一个独立的文件夹（比如 `/root/gemini-claw/`）。
2. 构建基础的 `requirements.txt`。
3. 编写 `engine.py` 测试一下您的 Gemini 接口连通性和基础工具调用。
   请告诉我是否需要对上述设计进行微调，或者是否直接进入代码开发阶段？
