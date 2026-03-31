"""
scheduler.py — Runs the Anelo pipeline on a daily schedule.
Set PIPELINE_HOUR (0-23 UTC) to control when it runs. Default: 9am UTC.
"""
import os
import time
import subprocess
import sys
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [scheduler] %(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

PIPELINE_HOUR = int(os.environ.get("PIPELINE_HOUR", "9"))  # UTC hour to run


def run_pipeline():
    logger.info("Starting pipeline run...")
    result = subprocess.run(
        [sys.executable, "pipeline.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    if result.returncode == 0:
        logger.info("Pipeline completed successfully.")
    else:
        logger.error(f"Pipeline exited with code {result.returncode}")


def main():
    logger.info(f"Scheduler started. Pipeline runs daily at {PIPELINE_HOUR:02d}:00 UTC.")
    last_run_date = None

    while True:
        now = datetime.now(timezone.utc)
        today = now.date()

        if now.hour == PIPELINE_HOUR and last_run_date != today:
            last_run_date = today
            run_pipeline()

        time.sleep(60)  # check every minute


if __name__ == "__main__":
    main()
