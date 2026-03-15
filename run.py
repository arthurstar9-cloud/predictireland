"""Single entry point — runs the full pipeline for one post."""

import os
import sys
import json
import asyncio
import logging
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from scraper import (
    get_top_parsed_markets, scrape_oddschecker_odds, get_paddy_power_overround,
    search_oddschecker,
)
from market_selector import select_for_pillar1, select_for_pillar2
from screenshotter import (
    build_pillar1_carousel, build_pillar2_carousel, build_pillar3_carousel,
)
from caption_writer import (
    write_pillar1_caption, write_pillar2_caption, write_pillar3_caption,
    write_market_commentary,
)
from poster import post_carousel
from db import mark_market_used, log_post, log_run_start, log_run_end

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "logs",
                         f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        ),
    ],
)
logger = logging.getLogger(__name__)

TOPICS_PATH = os.path.join(os.path.dirname(__file__), "topics.json")


def _load_topics() -> list[dict]:
    with open(TOPICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_work_dir(pillar: int) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    d = os.path.join(os.path.dirname(__file__), "output", f"_work_{ts}_p{pillar}")
    os.makedirs(d, exist_ok=True)
    return d


async def run_pillar1():
    """Pillar 1: Bookie comparison post."""
    logger.info("=== PILLAR 1: Bookie Comparison ===")
    run_id = log_run_start(1)

    try:
        markets = get_top_parsed_markets(50)
        market = select_for_pillar1(markets)
        if not market:
            logger.warning("No suitable Pillar 1 market found")
            log_run_end(run_id, "skipped", "No suitable market")
            return

        logger.info(f"Selected market: {market['title']}")

        # Try scraping live bookie odds — fall back to estimated overround
        bookie_name = "Paddy Power"
        bookie_overround = 8.5  # Default estimate if scraping fails

        try:
            import re as _re
            # Clean the market title into a search query
            search_query = market["title"]
            search_query = _re.sub(r"\b(Will|will|Does|does|Is|is|the|The)\b", "", search_query)
            search_query = _re.sub(r"[?!.,;:'\"()]", "", search_query)
            search_query = _re.sub(r"\s+", " ", search_query).strip()
            logger.info(f"Searching Oddschecker for: '{search_query}'")

            oc_url = await search_oddschecker(search_query)
            if oc_url:
                logger.info(f"Found Oddschecker URL: {oc_url}")
                odds_data = await scrape_oddschecker_odds(oc_url)
                if odds_data:
                    overround_pct, pp_odds = get_paddy_power_overround(odds_data)
                    if overround_pct > 100.0:
                        bookie_overround = round(overround_pct - 100.0, 2)
                        logger.info(
                            f"Live overround from Oddschecker: {bookie_overround}% "
                            f"({len(pp_odds)} outcomes)"
                        )
                    else:
                        logger.warning(
                            f"Oddschecker overround looks invalid ({overround_pct}%), "
                            f"using default {bookie_overround}%"
                        )
                else:
                    logger.warning("Oddschecker returned no odds data, using default overround")
            else:
                logger.warning("No Oddschecker match found, using default overround")
        except Exception as e:
            logger.warning(f"Oddschecker scraping failed ({e}), using default {bookie_overround}%")

        # Generate commentary
        prob = int(market["prices"][0] * 100) if market.get("prices") else 50
        commentary = write_market_commentary(market["title"], prob)

        # Build carousel
        work_dir = _get_work_dir(1)
        slides = await build_pillar1_carousel(
            work_dir, market, bookie_name, bookie_overround, commentary,
        )

        # Generate caption
        caption = write_pillar1_caption(market["title"], prob, bookie_name, bookie_overround)
        logger.info(f"Caption: {caption[:100]}...")

        # Post
        tiktok_id, local_dir = post_carousel(slides, caption, pillar=1)

        # Log
        mark_market_used(market["id"], market["slug"], market["title"])
        log_post(1, [market["id"]], caption, slides, tiktok_id, "posted" if tiktok_id else "local")
        log_run_end(run_id, "success")
        logger.info(f"Pillar 1 complete. Output: {local_dir}")

    except Exception as e:
        logger.error(f"Pillar 1 failed: {e}", exc_info=True)
        log_run_end(run_id, "error", str(e))


async def run_pillar2():
    """Pillar 2: Weekly roundup post."""
    logger.info("=== PILLAR 2: Weekly Roundup ===")
    run_id = log_run_start(2)

    try:
        markets = get_top_parsed_markets(50)
        selected = select_for_pillar2(markets, count=4)
        if not selected:
            logger.warning("No suitable Pillar 2 markets found")
            log_run_end(run_id, "skipped", "No suitable markets")
            return

        logger.info(f"Selected {len(selected)} markets for roundup")

        # Generate commentaries
        commentaries = []
        for m in selected:
            prob = int(m["prices"][0] * 100) if m.get("prices") else 50
            commentaries.append(write_market_commentary(m["title"], prob))

        # Build carousel
        work_dir = _get_work_dir(2)
        slides = await build_pillar2_carousel(work_dir, selected, commentaries)

        # Generate caption
        caption = write_pillar2_caption(selected)
        logger.info(f"Caption: {caption[:100]}...")

        # Post
        tiktok_id, local_dir = post_carousel(slides, caption, pillar=2)

        # Log
        market_ids = []
        for m in selected:
            mark_market_used(m["id"], m["slug"], m["title"])
            market_ids.append(m["id"])
        log_post(2, market_ids, caption, slides, tiktok_id, "posted" if tiktok_id else "local")
        log_run_end(run_id, "success")
        logger.info(f"Pillar 2 complete. Output: {local_dir}")

    except Exception as e:
        logger.error(f"Pillar 2 failed: {e}", exc_info=True)
        log_run_end(run_id, "error", str(e))


async def run_pillar3():
    """Pillar 3: Educational content post."""
    logger.info("=== PILLAR 3: Educational ===")
    run_id = log_run_start(3)

    try:
        topics = _load_topics()
        # Pick a random topic (could be smarter with tracking used topics)
        topic = random.choice(topics)
        logger.info(f"Selected topic: {topic['title']}")

        # Build carousel
        work_dir = _get_work_dir(3)
        slides = await build_pillar3_carousel(work_dir, topic)

        # Generate caption
        caption = write_pillar3_caption(topic)
        logger.info(f"Caption: {caption[:100]}...")

        # Post
        tiktok_id, local_dir = post_carousel(slides, caption, pillar=3)

        # Log
        log_post(3, [topic["id"]], caption, slides, tiktok_id, "posted" if tiktok_id else "local")
        log_run_end(run_id, "success")
        logger.info(f"Pillar 3 complete. Output: {local_dir}")

    except Exception as e:
        logger.error(f"Pillar 3 failed: {e}", exc_info=True)
        log_run_end(run_id, "error", str(e))


async def run(pillar: int | None = None):
    """Run the pipeline for a specific pillar, or auto-select based on day."""
    if pillar is None:
        # Auto-select based on day of week
        day = datetime.now().strftime("%A")
        pillar_map = {
            "Tuesday": 1,
            "Thursday": 2,
            "Saturday": 3,
            "Sunday": 2,  # or 1 depending on news cycle
        }
        pillar = pillar_map.get(day)
        if pillar is None:
            logger.info(f"No post scheduled for {day}")
            return

    runners = {1: run_pillar1, 2: run_pillar2, 3: run_pillar3}
    runner = runners.get(pillar)
    if runner:
        await runner()
    else:
        logger.error(f"Unknown pillar: {pillar}")


def main():
    pillar = None
    if len(sys.argv) > 1:
        try:
            pillar = int(sys.argv[1])
        except ValueError:
            print(f"Usage: python run.py [pillar_number]")
            print(f"  pillar_number: 1, 2, or 3 (omit for auto-select by day)")
            sys.exit(1)

    asyncio.run(run(pillar))


if __name__ == "__main__":
    main()
