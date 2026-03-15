"""Fetch markets from Polymarket Gamma API and scrape bookie odds from Oddschecker."""

import requests
import logging
import json
import re

logger = logging.getLogger(__name__)

GAMMA_API = "https://gamma-api.polymarket.com"


def fetch_top_markets(limit: int = 50) -> list[dict]:
    """Fetch top markets by volume from Polymarket Gamma API."""
    try:
        resp = requests.get(
            f"{GAMMA_API}/markets",
            params={
                "limit": limit,
                "active": True,
                "closed": False,
                "order": "volume",
                "ascending": False,
            },
            timeout=15,
        )
        resp.raise_for_status()
        markets = resp.json()
        logger.info(f"Fetched {len(markets)} markets from Gamma API")
        return markets
    except Exception as e:
        logger.error(f"Failed to fetch markets: {e}")
        return []


def fetch_market_by_slug(slug: str) -> dict | None:
    """Fetch a single market by its slug."""
    try:
        resp = requests.get(f"{GAMMA_API}/markets", params={"slug": slug}, timeout=15)
        resp.raise_for_status()
        markets = resp.json()
        return markets[0] if markets else None
    except Exception as e:
        logger.error(f"Failed to fetch market {slug}: {e}")
        return None


def _parse_string_or_list(val, convert=None):
    """Parse a value that might be a JSON array string, CSV string, or list."""
    if isinstance(val, list):
        items = val
    elif isinstance(val, str) and val.strip():
        try:
            items = json.loads(val)
        except (json.JSONDecodeError, ValueError):
            items = [v.strip().strip('"') for v in val.split(",") if v.strip().strip('"')]
    else:
        return []
    if convert:
        return [convert(x) for x in items]
    return [str(x).strip().strip('"') for x in items]


def parse_market(raw: dict) -> dict:
    """Normalize a Gamma API market into a clean dict."""
    outcomes = _parse_string_or_list(raw.get("outcomes", ""))
    prices = _parse_string_or_list(raw.get("outcomePrices", ""), convert=float)

    return {
        "id": raw.get("id", ""),
        "slug": raw.get("slug", ""),
        "title": raw.get("question", raw.get("title", "")),
        "description": raw.get("description", ""),
        "outcomes": outcomes,
        "prices": prices,
        "volume": float(raw.get("volume", 0)),
        "volume_24h": float(raw.get("volume24hr", 0)),
        "liquidity": float(raw.get("liquidity", 0)),
        "end_date": raw.get("endDate", ""),
        "image": raw.get("image", ""),
        "url": f"https://polymarket.com/event/{raw.get('slug', '')}",
    }


def get_top_parsed_markets(limit: int = 50) -> list[dict]:
    """Fetch and parse top markets."""
    raw_markets = fetch_top_markets(limit)
    return [parse_market(m) for m in raw_markets]


async def scrape_oddschecker_odds(event_url: str) -> dict | None:
    """Scrape odds from an Oddschecker event page using Playwright.

    Returns dict with: {outcome: {bookie: decimal_odds, ...}, ...}
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed")
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await ctx.new_page()
            await page.goto(event_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)

            odds_data = await page.evaluate("""() => {
                const rows = document.querySelectorAll('tr[data-bname]');
                const result = {};
                rows.forEach(row => {
                    const name = row.getAttribute('data-bname');
                    const cells = row.querySelectorAll('td[data-odig]');
                    const bookieOdds = {};
                    cells.forEach(cell => {
                        const bookie = cell.getAttribute('data-bk');
                        const odds = cell.getAttribute('data-odig');
                        if (bookie && odds) {
                            bookieOdds[bookie] = parseFloat(odds);
                        }
                    });
                    if (Object.keys(bookieOdds).length > 0) {
                        result[name] = bookieOdds;
                    }
                });
                return result;
            }""")

            await browser.close()
            return odds_data if odds_data else None

    except Exception as e:
        logger.error(f"Oddschecker scrape failed: {e}")
        return None


def calculate_overround(odds: dict[str, float]) -> float:
    """Calculate overround from decimal odds for a set of outcomes.

    Args:
        odds: {outcome_name: decimal_odds, ...}
    Returns:
        Overround as a percentage (100% = fair, >100% = bookie margin)
    """
    if not odds:
        return 0.0
    return sum(1.0 / o for o in odds.values()) * 100


def get_paddy_power_overround(odds_data: dict) -> tuple[float, dict]:
    """Extract Paddy Power odds and calculate overround.

    Args:
        odds_data: Output from scrape_oddschecker_odds
    Returns:
        (overround_pct, {outcome: odds})
    """
    if not odds_data:
        return 0.0, {}

    pp_odds = {}
    for outcome, bookies in odds_data.items():
        # Look for Paddy Power specifically
        for bookie_key in ["PP", "PB", "Paddy Power", "paddypower"]:
            if bookie_key in bookies:
                pp_odds[outcome] = bookies[bookie_key]
                break
        # Fallback: use best odds from any bookie
        if outcome not in pp_odds and bookies:
            pp_odds[outcome] = min(bookies.values())

    overround = calculate_overround(pp_odds)
    return overround, pp_odds


def scrape_paddy_power_direct(market_url: str) -> dict | None:
    """Direct scrape of Paddy Power odds using Playwright.

    Fallback if Oddschecker doesn't have the market.
    Returns: {outcome: decimal_odds, ...}
    """
    # This is a placeholder — Paddy Power's site structure changes frequently.
    # In practice you'd adapt selectors to their current DOM.
    logger.warning("Direct Paddy Power scraping not yet implemented — use Oddschecker")
    return None
