"""Render HTML templates with live data and screenshot at 1080x1920 using Playwright."""

import os
import io
import base64
import asyncio
import logging
import qrcode
from pathlib import Path

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
REFERRAL_LINK = os.getenv("REFERRAL_LINK", "https://polymarket.com?via=arthur-cussen-0ebv")


def _render_template(template_name: str, replacements: dict) -> str:
    """Load an HTML template and replace placeholders."""
    path = os.path.join(TEMPLATES_DIR, template_name)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    for key, value in replacements.items():
        safe_val = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = html.replace(f"{{{{{key}}}}}", safe_val)
    return html


def _generate_qr_base64() -> str:
    """Generate QR code as base64 data URI for embedding in HTML."""
    qr = qrcode.QRCode(version=1, box_size=20, border=2,
                        error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(REFERRAL_LINK)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00c16e", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def _format_volume(vol: float) -> str:
    """Format volume as $1.2M, $340K, etc."""
    if vol >= 1_000_000:
        return f"${vol / 1_000_000:.1f}M"
    elif vol >= 1_000:
        return f"${vol / 1_000:.0f}K"
    else:
        return f"${vol:.0f}"


async def _screenshot_html(html: str, output_path: str):
    """Render HTML string and take a screenshot at 1080x1920."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})
        # Encode as ASCII with HTML entities to avoid charset issues
        html_ascii = html.encode("ascii", "xmlcharrefreplace").decode("ascii")
        await page.set_content(html_ascii, wait_until="networkidle")
        # Allow local file:// images to load
        await page.wait_for_timeout(500)
        await page.screenshot(path=output_path, full_page=False)
        await browser.close()

    logger.info(f"Screenshot saved: {output_path}")


async def screenshot_intro(output_dir: str, headline: str, subheadline: str,
                            pillar_tag: str, slide_num: int, total_slides: int) -> str:
    """Render and screenshot intro slide."""
    html = _render_template("intro_slide.html", {
        "HEADLINE": headline,
        "SUBHEADLINE": subheadline,
        "PILLAR_TAG": pillar_tag,
        "SLIDE_NUM": str(slide_num),
        "TOTAL_SLIDES": str(total_slides),
    })
    path = os.path.join(output_dir, f"slide_{slide_num}_intro.png")
    await _screenshot_html(html, path)
    return path


async def screenshot_market_card(output_dir: str, market: dict, commentary: str,
                                   slide_num: int, total_slides: int) -> str:
    """Render and screenshot a market card."""
    prices = market.get("prices", [0])
    probability = int(prices[0] * 100) if prices else 0
    outcomes = market.get("outcomes", ["Yes"])
    direction_color = "#00c16e" if probability >= 50 else "#ff4444"

    html = _render_template("market_card.html", {
        "MARKET_TITLE": market.get("title", ""),
        "PROBABILITY": str(probability),
        "OUTCOME_LABEL": f"{outcomes[0]} is leading" if len(outcomes) > 0 else "",
        "DIRECTION_COLOR": direction_color,
        "VOLUME_24H": _format_volume(market.get("volume_24h", 0)),
        "TOTAL_VOLUME": _format_volume(market.get("volume", 0)),
        "LIQUIDITY": _format_volume(market.get("liquidity", 0)),
        "COMMENTARY": commentary,
        "SLIDE_NUM": str(slide_num),
        "TOTAL_SLIDES": str(total_slides),
    })
    path = os.path.join(output_dir, f"slide_{slide_num}_market.png")
    await _screenshot_html(html, path)
    return path


async def screenshot_comparison(output_dir: str, bookie_name: str,
                                  bookie_overround: float,
                                  market_title: str, probability: int,
                                  slide_num: int, total_slides: int) -> str:
    """Render and screenshot comparison card with euro return example.

    Shows what you'd get back on a 10 euro winning bet on each platform.
    """
    # Calculate returns on a 10 euro bet
    # Fair odds from probability (what Polymarket gives)
    if probability > 0 and probability < 100:
        fair_decimal = 100.0 / probability
        poly_return = round(10 * fair_decimal, 2)
        # Bookie odds: fair odds reduced by overround
        bookie_decimal = fair_decimal / (1 + bookie_overround / 100)
        bookie_return = round(10 * bookie_decimal, 2)
    else:
        poly_return = 20.0
        bookie_return = 18.0

    bookie_lost = round(poly_return - bookie_return, 2)
    poly_extra = bookie_lost

    # Short market title for the bet example (max ~30 chars)
    market_short = market_title if len(market_title) <= 35 else market_title[:32] + "..."

    html = _render_template("comparison_card.html", {
        "BOOKIE_NAME": bookie_name,
        "BOOKIE_OVERROUND": f"{bookie_overround:.1f}",
        "MARKET_SHORT": market_short,
        "BOOKIE_RETURN": f"{bookie_return:.2f}",
        "BOOKIE_LOST": f"{bookie_lost:.2f}",
        "POLY_RETURN": f"{poly_return:.2f}",
        "POLY_EXTRA": f"{poly_extra:.2f}",
        "SLIDE_NUM": str(slide_num),
        "TOTAL_SLIDES": str(total_slides),
    })
    path = os.path.join(output_dir, f"slide_{slide_num}_comparison.png")
    await _screenshot_html(html, path)
    return path


async def screenshot_stat_card(output_dir: str, step_label: str, headline: str,
                                body: str, source: str,
                                slide_num: int, total_slides: int) -> str:
    """Render and screenshot stat/educational card."""
    html = _render_template("stat_card.html", {
        "STEP_LABEL": step_label,
        "HEADLINE": headline,
        "BODY": body,
        "SOURCE": source,
        "SLIDE_NUM": str(slide_num),
        "TOTAL_SLIDES": str(total_slides),
    })
    path = os.path.join(output_dir, f"slide_{slide_num}_stat.png")
    await _screenshot_html(html, path)
    return path


async def screenshot_cta(output_dir: str, slide_num: int, total_slides: int) -> str:
    """Render and screenshot CTA slide with QR code."""
    qr_uri = _generate_qr_base64()

    html = _render_template("cta_slide.html", {
        "QR_PATH": qr_uri,
        "SLIDE_NUM": str(slide_num),
        "TOTAL_SLIDES": str(total_slides),
    })
    path = os.path.join(output_dir, f"slide_{slide_num}_cta.png")
    await _screenshot_html(html, path)
    return path


# --- Full carousel builders per pillar ---

async def build_pillar1_carousel(output_dir: str, market: dict,
                                   bookie_name: str, bookie_overround: float,
                                   commentary: str) -> list[str]:
    """Build full Pillar 1 carousel: intro → market → comparison → CTA."""
    os.makedirs(output_dir, exist_ok=True)
    total = 4
    slides = []

    slides.append(await screenshot_intro(
        output_dir,
        headline=f"Your bookie is taking {bookie_overround:.0f}%",
        subheadline=f"{market['title']} — same market, different odds",
        pillar_tag="Bookie Exposed",
        slide_num=1, total_slides=total,
    ))
    slides.append(await screenshot_market_card(
        output_dir, market, commentary,
        slide_num=2, total_slides=total,
    ))
    prob = int(market["prices"][0] * 100) if market.get("prices") else 50
    slides.append(await screenshot_comparison(
        output_dir, bookie_name, bookie_overround,
        market_title=market["title"], probability=prob,
        slide_num=3, total_slides=total,
    ))
    slides.append(await screenshot_cta(output_dir, slide_num=4, total_slides=total))
    return slides


async def build_pillar2_carousel(output_dir: str, markets: list[dict],
                                   commentaries: list[str]) -> list[str]:
    """Build full Pillar 2 carousel: intro → market cards → CTA."""
    os.makedirs(output_dir, exist_ok=True)
    total = 2 + len(markets)  # intro + markets + CTA
    slides = []

    slides.append(await screenshot_intro(
        output_dir,
        headline="What Ireland is betting on this week",
        subheadline="The top prediction markets for Irish audiences",
        pillar_tag="Weekly Roundup",
        slide_num=1, total_slides=total,
    ))

    for i, (market, comment) in enumerate(zip(markets, commentaries)):
        slides.append(await screenshot_market_card(
            output_dir, market, comment,
            slide_num=i + 2, total_slides=total,
        ))

    slides.append(await screenshot_cta(output_dir, slide_num=total, total_slides=total))
    return slides


async def build_pillar3_carousel(output_dir: str, topic: dict) -> list[str]:
    """Build full Pillar 3 carousel: intro → stat cards → CTA."""
    os.makedirs(output_dir, exist_ok=True)
    topic_slides = topic.get("slides", [])
    total = 2 + len(topic_slides)  # intro + slides + CTA
    slides = []

    slides.append(await screenshot_intro(
        output_dir,
        headline=topic["hook"],
        subheadline=topic["title"],
        pillar_tag="Learn",
        slide_num=1, total_slides=total,
    ))

    for i, s in enumerate(topic_slides):
        slides.append(await screenshot_stat_card(
            output_dir,
            step_label=f"Part {i + 1}",
            headline=s["headline"],
            body=s["body"],
            source="polymarket.com",
            slide_num=i + 2, total_slides=total,
        ))

    slides.append(await screenshot_cta(output_dir, slide_num=total, total_slides=total))
    return slides
