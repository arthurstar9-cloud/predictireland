"""Generate TikTok captions using OpenAI gpt-4o-mini."""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You write TikTok captions for @predictireland, an Irish prediction market page "
    "targeting 18-35 year olds who use Paddy Power and Bet365. "
    "Tone is conversational, punchy, slightly sarcastic about bookies. "
    "Never cringe. Never corporate. Max 300 chars before hashtags."
)

HASHTAGS = (
    "#polymarket #predictionmarket #ireland #irishfinance "
    "#crypto #paddypower #politics #makemoney #sidehustle #irishpolitics"
)


def _get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _call_openai(user_prompt: str) -> str:
    client = _get_client()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=400,
        temperature=0.8,
    )
    return resp.choices[0].message.content.strip()


def write_pillar1_caption(market_title: str, probability: int,
                           bookie_name: str, overround: float) -> str:
    """Generate caption for Pillar 1 (bookie comparison)."""
    prompt = (
        f"Write a TikTok carousel caption for a post comparing {bookie_name} to Polymarket.\n"
        f"Market: {market_title}\n"
        f"Polymarket probability: {probability}%\n"
        f"{bookie_name} overround: {overround:.1f}%\n\n"
        f"Structure:\n"
        f"Line 1: Hook — provocative statement or question about bookies, no emoji\n"
        f"Lines 2-3: 2 punchy lines about this specific market and the overround gap\n"
        f"Line 4: 'Link in bio to trade this 👇'\n\n"
        f"Do NOT include hashtags. Max 300 characters total."
    )
    caption = _call_openai(prompt)
    return f"{caption}\n\n{HASHTAGS}"


def write_pillar2_caption(markets: list[dict]) -> str:
    """Generate caption for Pillar 2 (weekly roundup)."""
    market_lines = []
    for m in markets:
        prices = m.get("prices", [0])
        prob = int(prices[0] * 100) if prices else 0
        market_lines.append(f"- {m['title']}: {prob}% (vol: ${m.get('volume', 0):,.0f})")

    prompt = (
        f"Write a TikTok carousel caption for a weekly prediction market roundup.\n"
        f"Markets featured:\n" + "\n".join(market_lines) + "\n\n"
        f"Structure:\n"
        f"Line 1: Hook — something about what the smart money/crowd thinks this week, no emoji\n"
        f"Lines 2-3: 2 punchy lines teasing the most interesting markets\n"
        f"Line 4: 'Link in bio to trade this 👇'\n\n"
        f"Do NOT include hashtags. Max 300 characters total."
    )
    caption = _call_openai(prompt)
    return f"{caption}\n\n{HASHTAGS}"


def write_pillar3_caption(topic: dict) -> str:
    """Generate caption for Pillar 3 (educational)."""
    template = topic.get("caption_template", "")
    if template:
        # Use template as base but let OpenAI refine it
        prompt = (
            f"Rewrite this TikTok caption to sound natural and punchy. "
            f"Keep the same message but make it feel less templated:\n\n"
            f"{template}\n\n"
            f"Rules:\n"
            f"- Max 300 characters before hashtags\n"
            f"- End with 'Link in bio to...' + 👇\n"
            f"- No emoji except the 👇 at the end\n"
            f"- Do NOT include hashtags"
        )
    else:
        prompt = (
            f"Write a TikTok caption about: {topic['title']}\n"
            f"Hook: {topic['hook']}\n\n"
            f"Structure:\n"
            f"Line 1: Hook, no emoji\n"
            f"Lines 2-3: 2 punchy lines explaining this concept\n"
            f"Line 4: 'Link in bio...' + 👇\n\n"
            f"Do NOT include hashtags. Max 300 characters."
        )
    caption = _call_openai(prompt)
    return f"{caption}\n\n{HASHTAGS}"


def write_market_commentary(market_title: str, probability: int) -> str:
    """Generate a 1-line commentary for a market card."""
    prompt = (
        f"Write ONE short punchy sentence (max 15 words) commenting on this prediction market:\n"
        f"Market: {market_title}\n"
        f"Current probability: {probability}%\n\n"
        f"Be conversational and slightly opinionated. Irish audience. "
        f"No emoji. No hashtags. Just one sentence."
    )
    return _call_openai(prompt)
