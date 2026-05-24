# VentureIQ Scraper — Weekly Startup Discovery Engine

Scrapes Product Hunt, YC, Indie Hackers, and Wellfound every week, scores each company
using the Claude API, and saves a ranked investment report to Supabase (or a local CSV).

## Project structure

```
ventureiq-scraper/
├── scrapers/
│   ├── producthunt.py     # Scrapes Product Hunt trending
│   ├── ycombinator.py     # Scrapes YC company directory
│   ├── indiehackers.py    # Scrapes Indie Hackers products
│   └── wellfound.py       # Scrapes Wellfound job listings (hiring = growth signal)
├── scoring/
│   ├── scorer.py          # Sends companies to Claude API, gets JSON scores
│   └── report.py          # Builds ranked weekly report (CSV + Supabase)
├── scheduler/
│   └── weekly_job.py      # Orchestrator — runs all scrapers then scorer
├── data/                  # Local output (CSV reports saved here)
├── requirements.txt
├── .env.example
└── README.md
```

## Quickstart

```bash
# 1. Clone and install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Copy env file and fill in your keys
cp .env.example .env

# 3. Run a one-off scan right now
python scheduler/weekly_job.py

# 4. (Optional) Schedule weekly via cron
# Add to crontab: runs every Monday at 8am
# 0 8 * * 1 /usr/bin/python3 /path/to/scheduler/weekly_job.py
```

## Environment variables (.env)

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `SUPABASE_URL` | Supabase project URL (optional) |
| `SUPABASE_KEY` | Supabase anon key (optional) |
| `OUTPUT_DIR` | Where to save CSV reports (default: `./data`) |

## Output

Each weekly run produces:
- `data/startups_YYYY-MM-DD.csv` — full scored list
- Supabase `startups` table rows (if configured)
- Console summary with top 5 by conviction score

## Supabase schema (optional)

```sql
create table startups (
  id uuid default gen_random_uuid() primary key,
  week_of date not null,
  name text,
  source text,
  url text,
  tagline text,
  category text,
  stage text,
  business_model text,
  market_size text,
  risk_level text,
  conviction_score int,
  moat_strength text,
  investment_verdict text,
  growth_signal text,
  allocation_suggestion text,
  comparable_to text,
  top_strength text,
  top_risk text,
  analysis_note text,
  created_at timestamptz default now()
);
```
