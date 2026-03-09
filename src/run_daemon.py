import time
import datetime
import logging
import os
import json
import subprocess
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from engine import GeminiCliAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HeartbeatDaemon")

agent = GeminiCliAdapter()

def run_command(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except Exception as e:
        return f"Error: {str(e)}"

def skip_if_rate_limited(func):
    def wrapper(*args, **kwargs):
        if agent.is_rate_limited():
            logger.debug(f"Skipping {func.__name__} due to rate limit (429).")
            return
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__ # Preserve name for scheduler
    return wrapper

@skip_if_rate_limited
def heartbeat_task():
    """Trigger the agent proactively. If there are active bounties, prioritize them."""
    import sqlite3
    active_tasks = []
    try:
        conn = sqlite3.connect("memory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, platform FROM bounties WHERE status = 'IN_PROGRESS'")
        active_tasks = cursor.fetchall()
        conn.close()
    except:
        pass

    if active_tasks:
        task_list = ", ".join([f"{t[0]} ({t[1]})" for t in active_tasks])
        prompt = (
            f"HEARTBEAT_PRIORITY_TRIGGER: 当前时间是 {datetime.datetime.now().isoformat()}。\n"
            f"⚠️ 检测到有正在进行的任务: {task_list}。\n"
            "请立即恢复工作区 (workplace/) 的进度，尝试解决剩余问题并推进到提交阶段。\n"
            "完成后，更新数据库状态并汇报进度。"
        )
    else:
        prompt = (
            "HEARTBEAT_TRIGGER: 当前时间是 " + datetime.datetime.now().isoformat() + "。\n"
            "请检查系统状态、日志，以及回忆是否有什么任务需要现在执行？\n"
            "如果没有事情做，请简单回复 'All systems nominal.'\n"
            "如果要做事情，请自动调用你的内建终端工具完成。"
        )
    
    logger.info("Triggering Heartbeat (Active Tasks: %d)...", len(active_tasks))
    response = agent.chat(prompt)
    logger.info(f"Heartbeat Response: {response}")

@skip_if_rate_limited
def cleanup_and_reflect_task():
    """Run daily reflection to summarize logs and update MEMORY.md."""
    prompt = (
        "DAILY_REFLECTION_TRIGGER: 当前时间是 " + datetime.datetime.now().isoformat() + "。\n"
        "请读取过去24小时你在系统记录的日志（在 memory/ 目录下）。\n"
        "总结其中的高价值经验、事实，并将其追加或更新到项目根目录的 MEMORY.md 和 sqlite memory 数据库中。\n"
        "清理无关紧要的琐碎细节。"
    )
    logger.info("Triggering Daily Reflection...")
    response = agent.chat(prompt)
    logger.info(f"Reflection Response: {response}")

@skip_if_rate_limited
def bounty_scan_task():
    """Scan for new bounties and update the dashboard."""
    prompt = (
        "BOUNTY_SCAN_TRIGGER: 当前时间是 " + datetime.datetime.now().isoformat() + "。\n"
        "请启动自动化扫描程序，寻找适合你的 Solana 开发者任务（Bounty）。\n"
        "如果发现任务，请记录到数据库中并尝试执行（克隆代码、测试）。\n"
        "完成后，请汇报你的发现或处理进度。"
    )
    logger.info("Triggering Bounty Scan...")
    response = agent.chat(prompt)
    logger.info(f"Bounty Scan Response: {response}")

@skip_if_rate_limited
def nexus_pulse_task():
    """Execute Nexus Pulse and perform cross-dimensional strategic analysis."""
    logger.info("Triggering Nexus Pulse Task...")
    try:
        # 导入脚本逻辑
        import sys
        sys.path.append(os.path.join(os.getcwd(), "skills"))
        from nexus_pulse import pulse
        report_path = pulse()
        with open(report_path, "r") as f:
            report_content = f.read()
    except Exception as e:
        logger.error(f"Nexus Pulse script failed: {e}")
        return

    prompt = (
        f"NEXUS_PULSE_TRIGGER: 当前时间是 {datetime.datetime.now().isoformat()}。\n"
        f"这是我刚刚生成的全维度自治报告内容:\n{report_content}\n\n"
        "请作为一个具有前瞻性的自治 Agent，从以下四个维度进行深度分析：\n"
        "1. 情报: 有哪些 Solana 或 AI 的最新变动值得我立刻关注或集成？\n"
        "2. 资产: Gas 是否充足？是否需要申请 airdrop 或调整赏金策略？\n"
        "3. 名誉: 我的 PR 状态如何？我是否在 GitHub 上保持了活跃的开发者信誉？\n"
        "4. 进化: 针对系统错误，我需要做出哪些架构调整？\n"
        "5. 混沌实验: 随机选择一个 workplace/ 目录下的项目，尝试运行其测试套件并提出优化建议。\n"
        "分析完成后，请自动执行任何你认为高优先级的修复或研究行动。"
    )
    logger.info("Starting Autonomous Strategic Analysis...")
    response = agent.chat(prompt)
    logger.info(f"Pulse Analysis Response: {response}")

@skip_if_rate_limited
def trim_logs_task():
    limits = {"logs/daemon.log": 300, "logs/api.log": 500}
    for log_file, limit in limits.items():
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                if len(lines) > limit:
                    with open(log_file, "w", encoding="utf-8") as f:
                        f.writelines(lines[-limit:])
            except Exception as e:
                logger.error(f"Failed to trim {log_file}: {e}")

@skip_if_rate_limited
def daily_discovery_task():
    prompt = (
        "DAILY_DISCOVERY_TRIGGER: 当前时间是 " + datetime.datetime.now().isoformat() + "。\n"
        "请执行搜索并汇总有价值的信息到 memory/research/。\n"
    )
    logger.info("Triggering Daily Discovery...")
    agent.chat(prompt)

if __name__ == "__main__":
    logger.info("Starting Gemini-Claw Heartbeat Daemon...")
    scheduler = BackgroundScheduler(timezone=timezone('Asia/Shanghai'))
    
    from apscheduler.events import EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_JOB_MODIFIED, EVENT_JOB_EXECUTED

    def update_jobs_file(event=None):
        try:
            jobs = []
            for job in scheduler.get_jobs():
                next_run = getattr(job, "next_run_time", None)
                jobs.append({
                    "info": f"{job.name} (trigger: {job.trigger})",
                    "next_run": str(next_run) if next_run else "N/A"
                })
            os.makedirs("logs", exist_ok=True)
            with open("logs/jobs.json", "w", encoding="utf-8") as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to update jobs file: {e}")


    scheduler.add_job(heartbeat_task, 'interval', hours=1, name="heartbeat")
    scheduler.add_job(cleanup_and_reflect_task, 'cron', hour=3, minute=0, name="reflection")
    scheduler.add_job(trim_logs_task, 'interval', hours=1, name="trim_logs")
    scheduler.add_job(bounty_scan_task, 'interval', hours=6, name="bounty_scan")
    scheduler.add_job(nexus_pulse_task, 'cron', hour=9, minute=0, name="nexus_pulse")
    scheduler.add_job(daily_discovery_task, 'interval', hours=12, name="discovery")
    
    scheduler.add_listener(update_jobs_file, EVENT_JOB_ADDED | EVENT_JOB_REMOVED | EVENT_JOB_MODIFIED | EVENT_JOB_EXECUTED)
    scheduler.start()
    update_jobs_file()
    
    # 手动触发初次心跳以生成日志记录
    logger.info("Initializing system with first heartbeat...")
    heartbeat_task()
    
    try:
        while True:
            time.sleep(1)
            
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Daemon gracefully shut down.")
