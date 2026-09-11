"""
Scheduler for Daily Current Affairs Agent.
Triggers daily bulletin curation and dispatch at a configured morning time.
"""

import logging
import sys
import time
from pathlib import Path
import schedule

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DISPATCH_CHANNEL, SCHEDULE_TIME, TARGET_EXAM

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def start_scheduler(exam_type: str = TARGET_EXAM, channel: str = DISPATCH_CHANNEL, run_time: str = SCHEDULE_TIME):
    """Starts the daily schedule loop."""
    from main import run_agent

    def job():
        logger.info(f"Triggering scheduled daily digest for {exam_type} via {channel}...")
        run_agent(exam_type=exam_type, channel=channel)

    schedule.every().day.at(run_time).do(job)
    logger.info(f"📅 Scheduler initialized. Daily current affairs will run every day at {run_time} (System Time).")
    logger.info("Press Ctrl+C to stop the scheduler.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")


if __name__ == "__main__":
    start_scheduler()
