"""Schedule automated posts at peak Irish TikTok times (IST)."""

import os
import time
import logging
import asyncio
import schedule
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from run import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_pillar(pillar: int):
    """Wrapper to run async pipeline from sync scheduler."""
    logger.info(f"Scheduler triggered: Pillar {pillar}")
    try:
        asyncio.run(run(pillar))
    except Exception as e:
        logger.error(f"Scheduled run failed (Pillar {pillar}): {e}", exc_info=True)


def setup_schedule():
    """Set up posting schedule at peak Irish TikTok times.

    All times are IST (Irish Standard Time = UTC+0 winter / UTC+1 summer).
    The schedule library uses local system time, so adjust if server
    is not in IST timezone.

    Schedule:
    - Tuesday 19:30 IST → Pillar 1 (bookie comparison)
    - Thursday 19:30 IST → Pillar 2 (weekly roundup)
    - Saturday 20:00 IST → Pillar 3 (educational)
    - Sunday 19:00 IST → Pillar 2 (or 1 depending on news)
    """
    schedule.every().tuesday.at("19:30").do(run_pillar, pillar=1)
    schedule.every().thursday.at("19:30").do(run_pillar, pillar=2)
    schedule.every().saturday.at("20:00").do(run_pillar, pillar=3)
    schedule.every().sunday.at("19:00").do(run_pillar, pillar=2)

    logger.info("Schedule configured:")
    logger.info("  Tue 19:30 → Pillar 1 (Bookie Comparison)")
    logger.info("  Thu 19:30 → Pillar 2 (Weekly Roundup)")
    logger.info("  Sat 20:00 → Pillar 3 (Educational)")
    logger.info("  Sun 19:00 → Pillar 2 (Weekly Roundup)")


def main():
    setup_schedule()
    logger.info("Scheduler running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
