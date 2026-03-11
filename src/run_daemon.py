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

DEFAULT_PROMPTS = {
    "heartbeat": {
        "prompt": "SYSTEM_HEARTBEAT: 当前时间 {time}。\n目前无紧急技术任务。请执行以下例行检查：\n1. 检查 workplace/ 下各项目的Git状态与待办事项。\n2. 检索 MEMORY.md 中的各矩阵记录，核对最近工作进展，并尝试推进未完成的分支与设定。\n3. 巡检系统日志，若一切正常，请回复 'All systems operational.' 并简述下一步计划。",
        "prompt_active": "SYSTEM_HEARTBEAT: 当前时间 {time}。\n检测到正在进行的任务: {active_tasks}。\n请作为核心开发工程师，优先推进 workplace/ 下的相关项目进度，确保高质量的代码实现。\n工作完成后，将技术突破沉淀至 MEMORY.md。"
    },
    "reflection": {
        "prompt": "DAILY_REFLECTION: 当前时间 {time}。\n请系统性地读取过去 24 小时 memory/ 目录下的所有研究与操作日志。\n任务目标：\n1. 提炼高价值技术经验与设计思路至 MEMORY.md。\n2. 更新当前各线项目的开发进度。\n3. 记录系统级基础事实。\n4. 归档冗余日志，保持系统简洁。"
    },
    "bounty_scan": {
        "prompt": "BOUNTY_SCAN_MODE: 当前时间 {time}。\n启动外部高价值任务扫描：重点关注与当前技术栈匹配的目标与协作项目。\n若发现目标，请立即记录并执行初步的可行性分析（环境要求、核心逻辑预览）。\n汇报扫描结果。"
    },
    "nexus_pulse": {
        "prompt": "NEXUS_PULSE_STRATEGY: 当前时间 {time}。\n系统状态汇总报告:\n{report_content}\n\n请从以下维度进行决策分析：\n1. 技术进化: 是否有值得集成的最佳实践、核心库或协议更新？\n2. 状态巡回: 检查子任务进度与系统的资源健康度。\n3. 产出复现: 如何通过高质量提交提升 workplace/ 下各项目的完善度？\n4. 规划构建: 根据系统现状，提出一个中长期探索任务或功能特性并记录。\n5. 混沌任务: 随机选取一个 workplace/ 项进行代码审计或文档补全。\n6. 提示词自调优: 评估当前调度提示词是否适配正在进行的核心方向？及时提出修改建议。"
    },
    "discovery": {
        "prompt": "DAILY_DISCOVERY_TRIGGER: 当前时间 {time}。\n请执行深度的资料研究并汇总相关技术动态、文档或者创意灵感到 memory/research/。"
    }
}

def get_prompt_from_jobs(job_id, prompt_key="prompt"):
    try:
        with open("logs/jobs.json", "r", encoding="utf-8") as f:
            jobs = json.load(f)
            for j in jobs:
                if j.get("id") == job_id:
                    if prompt_key in j and j[prompt_key]:
                        return j[prompt_key]
    except Exception:
        pass
    return DEFAULT_PROMPTS.get(job_id, {}).get(prompt_key, "")

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
    """定期唤醒 Agent，根据当前任务优先级推进工作。"""
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
        template = get_prompt_from_jobs("heartbeat", "prompt_active")
        prompt = template.replace("{time}", datetime.datetime.now().isoformat()).replace("{active_tasks}", task_list)
    else:
        template = get_prompt_from_jobs("heartbeat", "prompt")
        prompt = template.replace("{time}", datetime.datetime.now().isoformat())
    
    logger.info("Triggering System Heartbeat (Active Tasks: %d)...", len(active_tasks))
    response = agent.chat(prompt)
    logger.info(f"Heartbeat Response: {response}")

@skip_if_rate_limited
def cleanup_and_reflect_task():
    """每日回顾：总结日志，维护长期记忆文件。"""
    template = get_prompt_from_jobs("reflection", "prompt")
    prompt = template.replace("{time}", datetime.datetime.now().isoformat())
    logger.info("Triggering Daily Reflection...")
    response = agent.chat(prompt)
    logger.info(f"Reflection Response: {response}")

@skip_if_rate_limited
def bounty_scan_task():
    """自动化搜寻：寻找符合技术栈的 Solana 赏金任务。"""
    template = get_prompt_from_jobs("bounty_scan", "prompt")
    prompt = template.replace("{time}", datetime.datetime.now().isoformat())
    logger.info("Triggering Bounty Scan...")
    response = agent.chat(prompt)
    logger.info(f"Bounty Scan Response: {response}")

@skip_if_rate_limited
def nexus_pulse_task():
    """全维度战略分析与执行决策。"""
    logger.info("Triggering Strategic Nexus Pulse...")
    try:
        import sys
        sys.path.append(os.path.join(os.getcwd(), "skills"))
        from nexus_pulse import pulse
        report_path = pulse()
        with open(report_path, "r") as f:
            report_content = f.read()
    except Exception as e:
        logger.error(f"Nexus Pulse failed: {e}")
        return

    template = get_prompt_from_jobs("nexus_pulse", "prompt")
    prompt = template.replace("{time}", datetime.datetime.now().isoformat()).replace("{report_content}", report_content)
    logger.info("Starting Autonomous Strategic Analysis...")
    response = agent.chat(prompt)
    logger.info(f"Nexus Pulse Response: {response}")

@skip_if_rate_limited
def trim_logs_task():
    """清理日志文件，增加文件锁保护以避免与重定向冲突。"""
    lock_fd = None
    try:
        # 借用引擎锁来确保清理日志时没有后台任务正在高频写入
        lock_fd = agent._acquire_lock_sync()
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
    finally:
        if lock_fd:
            agent._release_lock(lock_fd)

@skip_if_rate_limited
def daily_discovery_task():
    template = get_prompt_from_jobs("discovery", "prompt")
    prompt = template.replace("{time}", datetime.datetime.now().isoformat())
    logger.info("Triggering Daily Discovery...")
    agent.chat(prompt)

if __name__ == "__main__":
    logger.info("Starting Gemini-Claw Heartbeat Daemon...")
    scheduler = BackgroundScheduler(timezone=timezone('Asia/Shanghai'))
    
    from apscheduler.events import EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_JOB_MODIFIED, EVENT_JOB_EXECUTED

    def update_jobs_file(event=None):
        try:
            existing_jobs = {}
            if os.path.exists("logs/jobs.json"):
                with open("logs/jobs.json", "r", encoding="utf-8") as f:
                    try:
                        for j in json.load(f):
                            existing_jobs[j.get("id")] = j
                    except:
                        pass
            
            jobs = []
            for job in scheduler.get_jobs():
                next_run = getattr(job, "next_run_time", None)
                job_data = {
                    "id": job.name,
                    "info": f"{job.name} (trigger: {job.trigger})",
                    "next_run": str(next_run) if next_run else "N/A"
                }
                
                # keep existing props
                if job.name in existing_jobs:
                    for k, v in existing_jobs[job.name].items():
                        if k not in job_data:
                            job_data[k] = v

                # inject defaults if missing
                if job.name in DEFAULT_PROMPTS:
                    for pk, pv in DEFAULT_PROMPTS[job.name].items():
                        if pk not in job_data:
                            job_data[pk] = pv
                            
                jobs.append(job_data)

            os.makedirs("logs", exist_ok=True)
            with open("logs/jobs.json", "w", encoding="utf-8") as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to update jobs file: {e}")


    scheduler.add_job(heartbeat_task, 'interval', hours=1, name="heartbeat", jitter=60)
    scheduler.add_job(cleanup_and_reflect_task, 'cron', hour=3, minute=0, name="reflection")
    scheduler.add_job(trim_logs_task, 'interval', hours=1, name="trim_logs", jitter=60)
    scheduler.add_job(bounty_scan_task, 'interval', hours=6, name="bounty_scan", jitter=120)
    scheduler.add_job(nexus_pulse_task, 'cron', hour=9, minute=0, name="nexus_pulse")
    scheduler.add_job(daily_discovery_task, 'interval', hours=12, name="discovery", jitter=300)
    
    scheduler.add_listener(update_jobs_file, EVENT_JOB_ADDED | EVENT_JOB_REMOVED | EVENT_JOB_MODIFIED | EVENT_JOB_EXECUTED)
    scheduler.start()
    update_jobs_file()
    
    # 手动触发初次心跳
    logger.info("Initializing system with first heartbeat...")
    heartbeat_task()
    
    try:
        while True:
            time.sleep(1)
            
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Daemon gracefully shut down.")
