"""Score markets for Irish relevance and assign content pillars."""

import logging
import re
from db import was_market_used

logger = logging.getLogger(__name__)

# Keywords and their relevance weights for Irish audience
IRISH_KEYWORDS = {
    # Direct Ireland
    "ireland": 10, "irish": 10, "dublin": 8, "taoiseach": 10,
    "sinn fein": 9, "sinn féin": 9, "fianna fail": 9, "fianna fáil": 9,
    "fine gael": 9, "coalition": 6, "dáil": 10, "dail": 10,
    # UK / close neighbours
    "uk": 5, "united kingdom": 5, "britain": 4, "british": 4,
    "keir starmer": 4, "labour": 3, "conservative": 3, "brexit": 6,
    "northern ireland": 8, "stormont": 7,
    # EU / Europe
    "eu": 5, "european union": 5, "ecb": 6, "european central bank": 6,
    "euro": 4, "eurozone": 5, "brussels": 4,
    # Economics (relevant to Irish audience)
    "inflation": 4, "recession": 4, "interest rate": 5, "fed": 3,
    "federal reserve": 3, "tariff": 4, "trade war": 3,
    # US politics (high engagement)
    "trump": 5, "biden": 4, "us election": 4, "president": 3,
    "republican": 2, "democrat": 2, "congress": 2, "senate": 2,
    # Sport
    "gaa": 10, "hurling": 10, "gaelic football": 10,
    "six nations": 9, "rugby": 7, "rugby world cup": 8,
    "premier league": 6, "champions league": 5, "world cup": 6,
    "formula 1": 3, "f1": 3, "golf": 4, "ryder cup": 6,
    # Tech / crypto (audience interest)
    "bitcoin": 3, "ethereum": 3, "crypto": 3, "ai": 3,
    "openai": 3, "chatgpt": 3, "apple": 2, "meta": 2,
    # Culture / pop
    "eurovision": 5, "oscar": 3, "grammys": 2,
}

MIN_RELEVANCE_SCORE = 3
MIN_PROBABILITY = 5      # Skip markets below 5% — not interesting content
MAX_PROBABILITY = 97     # Skip near-certain markets — no tension


def score_market(market: dict) -> int:
    """Score a market for Irish audience relevance (0-100)."""
    text = f"{market.get('title', '')} {market.get('description', '')}".lower()
    score = 0
    matched = []

    for keyword, weight in IRISH_KEYWORDS.items():
        if keyword.lower() in text:
            score += weight
            matched.append(keyword)

    if matched:
        logger.debug(f"Market '{market.get('title', '')[:50]}' scored {score} "
                      f"(matched: {', '.join(matched)})")
    return score


def assign_pillar(market: dict) -> int | None:
    """Suggest which content pillar a market fits best.

    Returns 1, 2, or None (Pillar 3 is topic-based, not market-based).
    """
    title = market.get("title", "").lower()
    desc = market.get("description", "").lower()
    text = f"{title} {desc}"

    # Pillar 1 candidates: markets that map to traditional betting events
    betting_signals = [
        "win", "winner", "champion", "election", "next president",
        "premier league", "champions league", "world cup", "six nations",
        "grand national", "cheltenham", "rugby", "match", "fight",
    ]
    is_bettable = any(sig in text for sig in betting_signals)

    if is_bettable:
        return 1
    # Everything else goes to Pillar 2 (weekly roundup)
    return 2


def select_markets_for_pillar(markets: list[dict], pillar: int,
                               count: int = 4, allow_reuse: bool = False) -> list[dict]:
    """Select best markets for a given pillar.

    Args:
        markets: List of parsed market dicts from scraper
        pillar: 1 or 2
        count: Number of markets to select
        allow_reuse: If False, skip markets already used

    Returns:
        Sorted list of top markets for this pillar
    """
    candidates = []

    for m in markets:
        # Dedup check
        if not allow_reuse and was_market_used(m["id"]):
            continue

        # Skip dead or near-certain markets
        prices = m.get("prices", [])
        if prices:
            prob = int(prices[0] * 100)
            if prob < MIN_PROBABILITY or prob > MAX_PROBABILITY:
                continue

        relevance = score_market(m)
        if relevance < MIN_RELEVANCE_SCORE:
            continue

        suggested_pillar = assign_pillar(m)
        if suggested_pillar != pillar:
            continue

        candidates.append({
            **m,
            "relevance_score": relevance,
        })

    # Sort by relevance first, then by volume as tiebreaker
    candidates.sort(key=lambda x: (x["relevance_score"], x["volume"]), reverse=True)

    selected = candidates[:count]
    logger.info(f"Selected {len(selected)} markets for Pillar {pillar}: "
                f"{[m['title'][:40] for m in selected]}")
    return selected


def select_for_pillar1(markets: list[dict]) -> dict | None:
    """Select best single market for Pillar 1 (bookie comparison)."""
    selected = select_markets_for_pillar(markets, pillar=1, count=1)
    return selected[0] if selected else None


def select_for_pillar2(markets: list[dict], count: int = 4) -> list[dict]:
    """Select markets for Pillar 2 (weekly roundup)."""
    # For Pillar 2, include both pillar 1 and 2 candidates
    candidates = []
    for m in markets:
        if was_market_used(m["id"]):
            continue
        prices = m.get("prices", [])
        if prices:
            prob = int(prices[0] * 100)
            if prob < MIN_PROBABILITY or prob > MAX_PROBABILITY:
                continue
        relevance = score_market(m)
        if relevance < MIN_RELEVANCE_SCORE:
            continue
        candidates.append({**m, "relevance_score": relevance})

    candidates.sort(key=lambda x: (x["relevance_score"], x["volume"]), reverse=True)
    return candidates[:count]
