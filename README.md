# @predictireland — TikTok Prediction Market Content Agent

Autonomous TikTok photo carousel posting agent for an Irish Polymarket affiliate page.

## What it does

Generates and posts TikTok photo carousels across 3 content pillars:

1. **Bookie Comparison** — Paddy Power overround vs Polymarket's 0% margin
2. **Weekly Roundup** — Top prediction markets relevant to Irish audiences
3. **Educational** — Evergreen explainers about prediction markets

Posts 4x/week at peak Irish TikTok times (IST):
- Tuesday 19:30 → Pillar 1
- Thursday 19:30 → Pillar 2
- Saturday 20:00 → Pillar 3
- Sunday 19:00 → Pillar 1 or 2

## Setup

### 1. Install dependencies

```bash
cd predictireland
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required keys:
- `OPENAI_API_KEY` — for caption generation (gpt-4o-mini)
- `TIKTOK_ACCESS_TOKEN` — for TikTok Content Posting API (optional, falls back to local save)

### 3. TikTok Content Posting API

To post directly to TikTok:

1. Go to [TikTok Developer Portal](https://developers.tiktok.com/)
2. Create an app and request **Content Posting API** access
3. Your app needs these scopes: `video.publish`, `video.upload`
4. Complete the review process (takes a few days)
5. Generate an access token and add to `.env`

**Without TikTok API**: The agent saves carousels to `output/` with images + caption.txt for manual upload.

## Usage

### Run a single post

```bash
# Auto-select pillar based on day of week
python run.py

# Force a specific pillar
python run.py 1  # Bookie comparison
python run.py 2  # Weekly roundup
python run.py 3  # Educational
```

### Run the scheduler

```bash
python scheduler.py
```

Runs continuously, posting at the scheduled times.

### Run tests

```bash
python -m pytest tests/ -v
```

## Project structure

```
predictireland/
├── run.py              # Single entry point — full pipeline
├── scheduler.py        # Schedule wrapper for automated posting
├── scraper.py          # Gamma API + Oddschecker scraping
├── market_selector.py  # Irish relevance scoring + pillar assignment
├── screenshotter.py    # Playwright HTML→PNG pipeline
├── caption_writer.py   # OpenAI caption generation
├── poster.py           # TikTok API + local fallback
├── db.py               # SQLite post log + deduplication
├── topics.json         # Pillar 3 evergreen topic bank
├── templates/          # HTML slide templates (1080×1920)
├── output/             # Generated carousels (local fallback)
├── logs/               # Timestamped run logs
└── tests/              # Unit tests
```

## Slide templates

All slides render at 1080×1920px (TikTok portrait) with:
- Dark background (#0d0d0d)
- Polymarket green accents (#00c16e)
- @predictireland watermark
- Slide number indicators

Templates: `intro_slide`, `market_card`, `comparison_card`, `stat_card`, `cta_slide`
