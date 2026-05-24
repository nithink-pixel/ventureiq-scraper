# VentureIQ — AI Startup Intelligence Platform

> An automated VC research tool that discovers, scores, and ranks startups every week using professional investment frameworks and AI.

**Live Dashboard → [nithink-pixel.github.io/ventureiq-scraper/dashboard.html](https://nithink-pixel.github.io/ventureiq-scraper/dashboard.html)**

---

## What it does

Every week, VentureIQ automatically:

1. **Scrapes** Product Hunt (official API) and Y Combinator company directory
2. **Scores** each startup across 9 professional VC dimensions using Claude AI
3. **Ranks** companies by conviction score (0–100)
4. **Calculates** Kelly criterion portfolio allocation — safe / moderate / aggressive
5. **Saves** a ranked CSV report and displays top 10 on the dashboard

---

## Scoring framework

Built on frameworks used by Sequoia, a16z, and Bessemer:

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Market size & timing | 15% | TAM, secular tailwinds, why now |
| Product–market fit | 15% | Retention, referrals, customer love |
| Business model quality | 12% | Gross margin, LTV:CAC, recurring revenue |
| Competitive moat | 12% | Network effects, switching costs, proprietary data |
| Team quality | 12% | Founder-market fit, domain expertise, execution |
| Growth velocity | 12% | MoM growth, hiring velocity, traction signals |
| Unit economics | 10% | CAC payback, burn multiple, path to profitability |
| Technology depth | 7% | Proprietary IP, novel architecture, data moat |
| Capital efficiency | 5% | Runway, burn rate, clean cap table |

---

## Investment allocation model

Uses the **Kelly Criterion** adapted for startup portfolios:

- **Safe** (20% fractional Kelly) — conservative investor
- **Moderate** (35% fractional Kelly) — balanced investor  
- **Aggressive** (50% fractional Kelly) — risk-tolerant investor

Shows exact dollar amounts at $50k, $250k, and $1M portfolio sizes.

---

## Sample output
=== VentureIQ Weekly Report — 2026-05-23 ===
80 companies  |  1 invest signal  |  avg conviction 45
#1  Spellar 3.0     Score: 65  Invest   Medium risk   Product Hunt
#2  Indemni         Score: 61  Watch    Medium risk   YC W25
#3  Blacksmith      Score: 61  Watch    Medium risk   YC S24
#4  Reprompt        Score: 59  Watch    Medium risk   YC W25
#5  Open Wearables  Score: 56  Watch    Medium risk   Product Hunt

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| AI scoring | Anthropic Claude API (claude-sonnet-4-5) |
| Scraping | Product Hunt API v2, YC public directory |
| HTTP | Python requests + BeautifulSoup |
| Data | Pandas, CSV |
| Database | Supabase (optional) |
| Dashboard | Vanilla HTML/CSS/JS |
| Automation | Python schedule / cron |

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/nithink-pixel/ventureiq-scraper.git
cd ventureiq-scraper

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API keys
cp .env.example .env
# Edit .env and add:
# ANTHROPIC_API_KEY=sk-ant-...
# PH_API_KEY=ph_...  (free from producthunt.com/v2/oauth/applications)

# 4. Run your first scan
python scheduler/weekly_job.py
```

---

## Project structure
ventureiq-scraper/
├── scrapers/
│   ├── producthunt.py     # Product Hunt API scraper
│   ├── ycombinator.py     # YC company directory scraper
│   ├── indiehackers.py    # Indie Hackers scraper
│   └── wellfound.py       # Wellfound hiring signals
├── scoring/
│   ├── vc_framework.py    # 9-dimension VC scoring framework
│   ├── scorer.py          # Claude API integration
│   └── report.py          # CSV + Supabase report builder
├── scheduler/
│   └── weekly_job.py      # Weekly pipeline orchestrator
├── dashboard.html          # Live top-10 dashboard
└── data/                  # Weekly CSV reports (gitignored)

---

## Automate weekly

```bash
# Run on a loop (stays running)
python scheduler/weekly_job.py --loop

# Or add to crontab (runs every Monday 8am)
# 0 8 * * 1 cd /path/to/ventureiq-scraper && python scheduler/weekly_job.py
```

---

Built by **Nithin Krishna** · MSBA @ UMass Amherst  
[GitHub](https://github.com/nithink-pixel) · [Dashboard](https://nithink-pixel.github.io/ventureiq-scraper/dashboard.html)
