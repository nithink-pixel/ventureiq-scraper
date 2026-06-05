"""
Founder Intelligence Layer
===========================
Pulls founder signals for every startup and scores
founder quality — one of the strongest predictors of
venture outcomes.

VCs obsess over founders more than products because
products pivot but great founders figure it out.

Signals collected:
- Technical vs business founder
- Previous startup experience
- Previous exits
- FAANG / top company background
- Domain expertise match
- Academic background signals
- YC / top accelerator alumni

Output per company:
- founder_score (0-10)
- founder_signals (list of positive signals)
- founder_risks (list of concerns)
- founder_summary (one paragraph)
"""

import os
import json
import time
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-5"

# Top companies that signal strong founder pedigree
TIER1_COMPANIES = [
    "Google", "Meta", "Apple", "Microsoft", "Amazon", "OpenAI",
    "Stripe", "Airbnb", "Uber", "Lyft", "Twitter", "LinkedIn",
    "Palantir", "Snowflake", "Databricks", "Figma", "Notion",
    "Coinbase", "Robinhood", "Plaid", "Brex", "Rippling",
    "Scale AI", "Anthropic", "DeepMind", "Tesla", "SpaceX"
]

# Top academic institutions
TIER1_SCHOOLS = [
    "MIT", "Stanford", "Harvard", "Carnegie Mellon", "Berkeley",
    "Caltech", "Princeton", "Yale", "Columbia", "Oxford", "Cambridge"
]


def add_founder_intelligence(companies: list[dict]) -> list[dict]:
    """
    Adds founder intelligence to each company.
    For YC companies we have more signal — uses batch info.
    For Product Hunt we infer from available signals.
    """
    results = []
    total = len(companies)

    print(f"[Founder Intel] Analyzing founders for {total} companies...")

    for i, company in enumerate(companies):
        print(f"[Founder Intel] {i+1}/{total} — {company.get('name')}")
        try:
            intel = _analyze_founder(company)
            merged = {**company, **intel}
            results.append(merged)
        except Exception as e:
            print(f"[Founder Intel] Failed for {company.get('name')}: {e}")
            results.append(company)
        if i < total - 1:
            time.sleep(0.4)

    scored = len([r for r in results if "founder_score" in r])
    print(f"[Founder Intel] Complete — {scored}/{total} analyzed")
    return results


def _analyze_founder(company: dict) -> dict:
    prompt = _build_prompt(company)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    return json.loads(text)


def _build_prompt(company: dict) -> str:
    name = company.get("name", "")
    tagline = company.get("tagline", "")
    category = company.get("category", "")
    stage = company.get("stage", "")
    source = company.get("source", "")
    batch = company.get("batch", "")
    url = company.get("url", "")
    memo = company.get("memo", "")

    yc_context = f"This is a YC {batch} company." if batch else ""
    ph_context = "This launched on Product Hunt." if source == "producthunt" else ""

    return f"""You are a VC partner assessing founder quality for an investment decision.

COMPANY:
Name: {name}
Tagline: {tagline}
Category: {category}
Stage: {stage}
Source: {source}
{yc_context}
{ph_context}
Website: {url}
Memo: {memo}

Based on everything you know about this company — its name, category, product,
YC batch if applicable, and any public information — assess the likely founder profile.

For YC companies especially, use your knowledge of who typically founds companies
in this category and what YC batches typically look like.

Be realistic and calibrated. Most founders are first-time founders without FAANG
backgrounds. Only assign high scores when there are genuine signals.

Tier 1 company backgrounds: {", ".join(TIER1_COMPANIES[:10])}
Tier 1 schools: {", ".join(TIER1_SCHOOLS[:6])}

Return ONLY valid JSON (no markdown):
{{
  "founder_score": <float 1.0-10.0>,
  "founder_type": "Technical|Business|Mixed",
  "experience_level": "First-time|Repeat|Serial",
  "likely_background": "<one sentence describing likely founder background based on company type and category>",
  "positive_signals": [
    "<signal 1 e.g. YC backing suggests strong technical foundation>",
    "<signal 2>",
    "<signal 3>"
  ],
  "risk_signals": [
    "<risk 1 e.g. No public founder information available>",
    "<risk 2>"
  ],
  "domain_expertise_match": "Strong|Moderate|Weak",
  "founder_market_fit": "<one sentence — why this founder type is or isn't right for this market>",
  "founder_summary": "<2 sentences — overall founder assessment a VC partner would give>"
}}"""


if __name__ == "__main__":
    test = [
        {
            "name": "Blacksmith",
            "tagline": "Faster GitHub Actions with persistent runner cache",
            "category": "Dev Tools",
            "stage": "Seed",
            "source": "yc",
            "batch": "W24",
            "memo": "Blacksmith solves CI/CD performance with measurable ROI."
        },
        {
            "name": "Indemni",
            "tagline": "AI-powered insurance automation",
            "category": "Fintech",
            "stage": "Seed",
            "source": "yc",
            "batch": "W25",
            "memo": "Indemni automates insurance workflows end to end."
        },
        {
            "name": "Spellar 3.0",
            "tagline": "AI meeting assistant with real-time coaching",
            "category": "AI Tools",
            "stage": "Seed",
            "source": "producthunt",
            "memo": "Spellar improves meeting quality with AI coaching."
        }
    ]
    results = add_founder_intelligence(test)
    for r in results:
        print(f"\n{'='*55}")
        print(f"  {r['name']} — Founder Intelligence")
        print(f"{'─'*55}")
        print(f"  Score:      {r.get('founder_score')}/10")
        print(f"  Type:       {r.get('founder_type')}")
        print(f"  Experience: {r.get('experience_level')}")
        print(f"  Domain fit: {r.get('domain_expertise_match')}")
        print(f"\n  Background: {r.get('likely_background')}")
        print(f"\n  Signals:")
        for s in r.get("positive_signals", []):
            print(f"    ✓ {s}")
        print(f"\n  Risks:")
        for s in r.get("risk_signals", []):
            print(f"    ✗ {s}")
        print(f"\n  Summary: {r.get('founder_summary')}")
