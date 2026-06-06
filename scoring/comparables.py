"""
Comparable Company Analysis
=============================
For every startup, finds 3-5 similar companies that have already
raised funding, been acquired, or gone public.

This is core VC work — understanding valuation context and
what similar companies achieved gives investors a framework
for thinking about potential outcomes.

Output per company:
- 3-5 comparable companies with outcomes
- Implied valuation corridor
- Strategic acquirer candidates
- Most likely exit path
"""

import os
import json
import time
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-5"


def add_comparables(companies: list[dict]) -> list[dict]:
    """
    Takes scored + memo'd companies.
    Adds comparable analysis to each.
    Processes top 20 by conviction score — comparables
    matter most for the strongest opportunities.
    """
    # Sort by conviction score, process top 20
    sorted_companies = sorted(
        companies,
        key=lambda x: int(x.get("conviction_score") or 0),
        reverse=True
    )

    top = sorted_companies[:20]
    rest = sorted_companies[20:]

    print(f"[Comparables] Analyzing top {len(top)} companies...")

    results = []
    for i, company in enumerate(top):
        print(f"[Comparables] {i+1}/{len(top)} — {company.get('name')}")
        try:
            comp_data = _get_comparables(company)
            merged = {**company, **comp_data}
            results.append(merged)
        except Exception as e:
            print(f"[Comparables] Failed for {company.get('name')}: {e}")
            results.append(company)
        if i < len(top) - 1:
            time.sleep(0.5)

    # Add rest without comparables
    results.extend(rest)

    scored = len([r for r in results[:20] if "comparable_companies" in r])
    print(f"[Comparables] Complete — {scored}/{len(top)} analyzed")
    return results


def _get_comparables(company: dict) -> dict:
    prompt = _build_prompt(company)

    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
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
    model = company.get("business_model", "")
    market = company.get("market_size", "")
    memo = company.get("memo", "")
    recommendation = company.get("recommendation", "")
    score = company.get("conviction_score", 0)

    return f"""You are a senior VC analyst specializing in comparable company analysis.

COMPANY:
Name: {name}
Tagline: {tagline}
Category: {category}
Stage: {stage}
Business Model: {model}
Market Size: {market}
Recommendation: {recommendation}
Conviction Score: {score}/100
Memo Summary: {memo}

Find the most relevant comparable companies — real companies that investors would
reference when evaluating this deal. Include a mix of:
- Direct competitors that raised funding
- Adjacent companies in the same space
- Successful exits in this category
- One aspirational comparable (best case)

Return ONLY valid JSON (no markdown):
{{
  "comparable_companies": [
    {{
      "name": "<real company name>",
      "description": "<one sentence what they do>",
      "outcome": "<e.g. Acquired by Salesforce for $1.9B (2021) / Raised $50M Series B at $400M valuation / IPO at $2.1B market cap>",
      "relevance": "<one sentence why this is a good comparable>"
    }},
    {{
      "name": "<company>",
      "description": "<description>",
      "outcome": "<outcome>",
      "relevance": "<relevance>"
    }},
    {{
      "name": "<company>",
      "description": "<description>",
      "outcome": "<outcome>",
      "relevance": "<relevance>"
    }}
  ],
  "valuation_corridor": {{
    "low": "<e.g. $50M — if product stays narrow>",
    "mid": "<e.g. $300M — if category leadership achieved>",
    "high": "<e.g. $1.5B — if platform expansion succeeds>",
    "rationale": "<2 sentences explaining the range>"
  }},
  "strategic_acquirers": ["<company 1>", "<company 2>", "<company 3>"],
  "most_likely_exit": "Acquisition|IPO|Acquihire|Unclear",
  "exit_rationale": "<one sentence — why this exit path makes most sense>"
}}"""


if __name__ == "__main__":
    test = [
        {
            "name": "Blacksmith",
            "tagline": "Faster GitHub Actions with persistent runner cache",
            "category": "Dev Tools",
            "stage": "Seed",
            "business_model": "SaaS",
            "market_size": "Medium",
            "conviction_score": 61,
            "recommendation": "Monitor",
            "memo": "Blacksmith solves CI/CD performance with measurable ROI but faces platform risk from GitHub building natively."
        }
    ]
    results = add_comparables(test)
    for r in results:
        print(f"\n{'='*55}")
        print(f"  {r['name']} — Comparables Analysis")
        print(f"{'─'*55}")
        for c in r.get("comparable_companies", []):
            print(f"  • {c['name']}: {c['outcome']}")
            print(f"    {c['relevance']}")
        vc = r.get("valuation_corridor", {})
        print(f"\n  VALUATION CORRIDOR:")
        print(f"  Low:  {vc.get('low')}")
        print(f"  Mid:  {vc.get('mid')}")
        print(f"  High: {vc.get('high')}")
        print(f"\n  EXIT: {r.get('most_likely_exit')} — {r.get('exit_rationale')}")
        print(f"  ACQUIRERS: {', '.join(r.get('strategic_acquirers', []))}")
