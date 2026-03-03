import time
import schedule
import datetime
import logging
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from engine import GeminiCliAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HeartbeatDaemon")

agent = GeminiCliAdapter()

def heartbeat_task():
    """Trigger the agent proactively to check if there are tasks to perform or logs to reflect on."""
    prompt = (
        "HEARTBEAT_TRIGGER: 当前时间是 " + datetime.datetime.now().isoformat() + "。\n"
        "请检查系统状态、日志，以及回忆是否有什么任务需要现在执行？\n"
        "如果没有事情做，请简单回复 'All systems nominal.'\n"
        "如果要做事情，请自动调用你的内建终端工具完成。"
    )
    logger.info("Triggering Heartbeat...")
    response = agent.chat(prompt)
    logger.info(f"Heartbeat Response: {response}")

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

if __name__ == "__main__":
    logger.info("Starting Gemini-Claw Heartbeat Daemon...")
    # Explicitly set timezone to avoid deprecated /etc/timezone warning
    scheduler = BackgroundScheduler(timezone=timezone('Asia/Shanghai'))
    
    # Run the heartbeat every 30 minutes
    scheduler.add_job(heartbeat_task, 'interval', minutes=30)
    
    # Run daily reflection at 3:00 AM
    scheduler.add_job(cleanup_and_reflect_task, 'cron', hour=3, minute=0)
    
    scheduler.start()
    
    try:
        # Initial boot check 
        prompt = (
            "SYSTEM_BOOT: Agent 以守护进程模式苏醒。\n"
            "这是你的初始心跳，请读取你的所有身份配置 (GEMINI.md 以及级联文件)。并熟悉 skills/ 下的可用工具。"
            "最后自我介绍说明你当前的状态并返回 JSON 结构结果。"
        )
        logger.info("Booting Agent...")
        logger.info(agent.chat(prompt))

        while True:
            time.sleep(1)
            
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Daemon gracefully shut down.")
