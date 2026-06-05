"""
Market Intelligence Report Generator
======================================
Analyzes the entire weekly batch of scored + memo'd companies
and produces a market-level intelligence report.

This is what separates a startup tracker from a VC research tool.
Output mirrors what an analyst would present at a Monday morning
partners meeting — sector trends, emerging themes, white space.
"""

import os
import json
import anthropic
from dotenv import load_dotenv
from datetime import date

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-5"


def generate_market_report(companies: list[dict], week_of: date = None) -> dict:
    """
    Takes the full scored + memo'd company list.
    Returns a market intelligence report dict.
    """
    if week_of is None:
        week_of = date.today()

    print(f"[Market Intel] Analyzing {len(companies)} companies for market patterns...")

    # Build company summary for analysis
    company_summaries = _build_summaries(companies)

    # Generate report via Claude
    report = _generate_report(company_summaries, week_of)

    # Print to console
    _print_report(report, week_of)

    return report


def _build_summaries(companies: list[dict]) -> list[dict]:
    """Extract key fields for market analysis."""
    summaries = []
    for c in companies:
        summaries.append({
            "name": c.get("name", ""),
            "category": c.get("category", ""),
            "tagline": c.get("tagline", ""),
            "recommendation": c.get("recommendation", ""),
            "conviction_score": c.get("conviction_score", 0),
            "stage": c.get("stage", ""),
            "business_model": c.get("business_model", ""),
            "source": c.get("source", ""),
            "moat_strength": c.get("moat_strength", ""),
            "market_size": c.get("market_size", ""),
        })
    return summaries


def _generate_report(summaries: list[dict], week_of: date) -> dict:
    prompt = f"""You are a Partner at a top VC fund presenting your weekly market intelligence briefing.

You have just reviewed {len(summaries)} startups from Product Hunt and Y Combinator this week.

Here is the full list:
{json.dumps(summaries, indent=2)}

Analyze this batch as a whole and produce a market intelligence report.
Think like a VC partner — what patterns do you see? What's heating up? What's crowded? What's the next wave?

Return ONLY valid JSON (no markdown):
{{
  "headline": "<one punchy sentence summarizing this week's most important trend>",
  "sector_breakdown": [
    {{"sector": "<name>", "count": <int>, "pct": <int>, "trend": "Rising|Stable|Declining"}},
    {{"sector": "<name>", "count": <int>, "pct": <int>, "trend": "Rising|Stable|Declining"}},
    {{"sector": "<name>", "count": <int>, "pct": <int>, "trend": "Rising|Stable|Declining"}},
    {{"sector": "<name>", "count": <int>, "pct": <int>, "trend": "Rising|Stable|Declining"}},
    {{"sector": "<name>", "count": <int>, "pct": <int>, "trend": "Rising|Stable|Declining"}}
  ],
  "emerging_themes": [
    {{"theme": "<theme name>", "signal": "<one sentence why this matters now>", "companies": ["<name>", "<name>"]}},
    {{"theme": "<theme name>", "signal": "<one sentence>", "companies": ["<name>", "<name>"]}},
    {{"theme": "<theme name>", "signal": "<one sentence>", "companies": ["<name>", "<name>"]}}
  ],
  "crowded_markets": [
    {{"market": "<market name>", "why": "<one sentence — why it is overcrowded>", "advice": "<what to look for to stand out>"}},
    {{"market": "<market name>", "why": "<one sentence>", "advice": "<advice>"}}
  ],
  "white_space": [
    {{"opportunity": "<opportunity name>", "thesis": "<2 sentences — why this is underserved and interesting>"}},
    {{"opportunity": "<opportunity name>", "thesis": "<2 sentences>"}}
  ],
  "hidden_gems": [
    {{"name": "<company name>", "why": "<one sentence — why this is underrated>"}},
    {{"name": "<company name>", "why": "<one sentence>"}},
    {{"name": "<company name>", "why": "<one sentence>"}}
  ],
  "top_opportunities": ["<company 1>", "<company 2>", "<company 3>", "<company 4>", "<company 5>"],
  "partner_note": "<3-4 sentences written as if a senior partner is summarizing this week to the rest of the partnership. Opinionated, direct, actionable. What should the team focus on this week?>"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    report = json.loads(text)
    report["week_of"] = week_of.isoformat()
    return report


def _print_report(report: dict, week_of: date):
    w = 65
    print(f"\n{'═'*w}")
    print(f"  VENTUREIQ MARKET INTELLIGENCE — {week_of.isoformat()}")
    print(f"{'═'*w}")
    print(f"\n  HEADLINE: {report.get('headline','')}")

    print(f"\n{'─'*w}")
    print(f"  SECTOR BREAKDOWN")
    print(f"{'─'*w}")
    for s in report.get("sector_breakdown", []):
        bar = "█" * (s.get("pct", 0) // 5)
        trend = {"Rising": "↑", "Stable": "→", "Declining": "↓"}.get(s.get("trend",""), "")
        print(f"  {s.get('sector',''):<28} {bar:<12} {s.get('pct',0)}% {trend}")

    print(f"\n{'─'*w}")
    print(f"  EMERGING THEMES")
    print(f"{'─'*w}")
    for t in report.get("emerging_themes", []):
        print(f"  ▶ {t.get('theme','')}")
        print(f"    {t.get('signal','')}")
        print(f"    Companies: {', '.join(t.get('companies',[]))}\n")

    print(f"{'─'*w}")
    print(f"  CROWDED MARKETS (avoid)")
    print(f"{'─'*w}")
    for m in report.get("crowded_markets", []):
        print(f"  ✗ {m.get('market','')}: {m.get('why','')}")

    print(f"\n{'─'*w}")
    print(f"  WHITE SPACE (opportunity)")
    print(f"{'─'*w}")
    for o in report.get("white_space", []):
        print(f"  ★ {o.get('opportunity','')}")
        print(f"    {o.get('thesis','')}\n")

    print(f"{'─'*w}")
    print(f"  HIDDEN GEMS")
    print(f"{'─'*w}")
    for g in report.get("hidden_gems", []):
        print(f"  💎 {g.get('name','')}: {g.get('why','')}")

    print(f"\n{'─'*w}")
    print(f"  PARTNER NOTE")
    print(f"{'─'*w}")
    print(f"  {report.get('partner_note','')}")
    print(f"\n{'═'*w}\n")


if __name__ == "__main__":
    # Test with sample data
    test_companies = [
        {"name": "Blacksmith", "category": "Dev Tools", "tagline": "Faster GitHub Actions", "recommendation": "Monitor", "conviction_score": 61, "stage": "Seed", "business_model": "SaaS", "source": "yc"},
        {"name": "Indemni", "category": "Fintech", "tagline": "AI insurance automation", "recommendation": "Monitor", "conviction_score": 61, "stage": "Seed", "business_model": "SaaS", "source": "yc"},
        {"name": "Spellar 3.0", "category": "AI Tools", "tagline": "AI meeting assistant", "recommendation": "Invest", "conviction_score": 65, "stage": "Seed", "business_model": "Subscription", "source": "producthunt"},
        {"name": "Kelviq", "category": "B2B SaaS", "tagline": "B2B sales intelligence", "recommendation": "Monitor", "conviction_score": 58, "stage": "Pre-seed", "business_model": "SaaS", "source": "producthunt"},
        {"name": "Patched", "category": "Dev Tools", "tagline": "AI code review automation", "recommendation": "Monitor", "conviction_score": 56, "stage": "Seed", "business_model": "SaaS", "source": "yc"},
    ]
    generate_market_report(test_companies)
