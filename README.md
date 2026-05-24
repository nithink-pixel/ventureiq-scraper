# VentureIQ — AI Startup Intelligence Platform

An automated venture capital research tool that scrapes Product Hunt and Y Combinator weekly, scores every company across 9 professional VC dimensions using Claude AI, and generates ranked investment reports with Kelly criterion portfolio allocation.

## What it does

- Scrapes Product Hunt (via official API) and YC company directory weekly
- Scores each startup across 9 dimensions: market size, PMF, business model, moat, team, growth, unit economics, tech depth, capital efficiency
- Calculates conviction score (0–100) using weighted VC framework (Sequoia, a16z, Bessemer)
- Generates Kelly criterion portfolio allocation — safe / moderate / aggressive %
- Saves ranked CSV report + prints top 10 to console

## Tech stack

Python · Anthropic Claude API · BeautifulSoup · Product Hunt API · Pandas · Supabase (optional)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY and PH_API_KEY
python scheduler/weekly_job.py
```

## Sample output

| Rank | Company | Score | Verdict | Risk |
|------|---------|-------|---------|------|
| 1 | Spellar 3.0 | 65 | Invest | Medium |
| 2 | Indemni | 61 | Watch | Medium |
| 3 | Blacksmith | 61 | Watch | Medium |

Built by Nithin Krishna · MSBA @ UMass Amherst
