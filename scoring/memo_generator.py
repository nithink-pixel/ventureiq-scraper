"""
Deal Memo Generator
====================
Generates investment committee-style deal memos for each startup.
Output mirrors what a junior VC analyst writes manually.

For every company produces:
- What they do
- Why now (market timing)
- Investment thesis
- Competitive advantages
- Key risks
- Bull case / bear case
- Comparable companies + valuations
- Recommendation: Invest / Monitor / Pass
- Confidence %
"""

import os
import json
import time
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-5"


def generate_memos(companies: list[dict]) -> list[dict]:
    """
    Takes scored companies, adds full deal memo to each.
    Processes one at a time for quality — memos need depth.
    """
    results = []
    total = len(companies)

    for i, company in enumerate(companies):
        print(f"[Memo] {i+1}/{total} — {company.get('name')}")
        try:
            memo = _generate_single_memo(company)
            merged = {**company, **memo}
            results.append(merged)
        except Exception as e:
            print(f"[Memo] Failed for {company.get('name')}: {e}")
            results.append(company)
        # Avoid rate limits
        if i < total - 1:
            time.sleep(0.5)

    print(f"[Memo] Complete — {len([r for r in results if 'memo' in r])}/{total} memos generated")
    return results


def _generate_single_memo(company: dict) -> dict:
    prompt = _build_memo_prompt(company)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    return json.loads(text)


def _build_memo_prompt(company: dict) -> str:
    name = company.get("name", "Unknown")
    tagline = company.get("tagline", "")
    source = company.get("source", "")
    category = company.get("category", "")
    stage = company.get("stage", "")
    score = company.get("conviction_score", 0)
    strength = company.get("top_strength", "")
    risk = company.get("top_risk", "")
    model = company.get("business_model", "")
    market = company.get("market_size", "")
    moat = company.get("moat_strength", "")
    growth = company.get("growth_signal", "")
    comparable = company.get("comparable_to", "")

    return f"""You are a Partner-level VC analyst at a top-tier fund writing an investment memo for an IC (Investment Committee) meeting.

COMPANY INFORMATION:
Name: {name}
Tagline: {tagline}
Source: {source}
Category: {category}
Stage: {stage}
Business Model: {model}
Market Size: {market}
Moat: {moat}
Growth Signal: {growth}
Comparable To: {comparable}
Conviction Score: {score}/100
Top Strength: {strength}
Top Risk: {risk}

Write a concise but thorough investment memo. Be specific, direct, and opinionated — like a real VC partner would be. No fluff.

Return ONLY valid JSON (no markdown, no explanation):
{{
  "recommendation": "Invest|Monitor|Pass",
  "confidence_pct": <integer 50-95>,
  "what_they_do": "<2 sentences — clear, specific description>",
  "why_now": "<2 sentences — market timing, tailwinds, why this moment>",
  "investment_thesis": ["<bullet 1>", "<bullet 2>", "<bullet 3>"],
  "competitive_advantages": ["<advantage 1>", "<advantage 2>", "<advantage 3>"],
  "key_risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
  "bull_case": "<2 sentences — best case outcome in 5 years>",
  "bear_case": "<2 sentences — worst case, what kills this company>",
  "comparables": [
    {{"name": "<company>", "outcome": "<acquired for $XM / raised $XM Series X / IPO at $XB>"}},
    {{"name": "<company>", "outcome": "<outcome>"}},
    {{"name": "<company>", "outcome": "<outcome>"}}
  ],
  "memo": "<Full 3-4 sentence investment memo summary a partner would read before IC meeting>"
}}"""


if __name__ == "__main__":
    # Test with sample companies
    test = [
        {
            "name": "Blacksmith",
            "tagline": "Faster GitHub Actions with persistent runner cache",
            "source": "yc",
            "category": "Dev Tools",
            "stage": "Seed",
            "conviction_score": 61,
            "business_model": "SaaS",
            "market_size": "Medium",
            "moat_strength": "Moderate",
            "growth_signal": "Strong YC batch hiring",
            "top_strength": "Deep CI/CD integration reduces switching costs",
            "top_risk": "GitHub could build this natively"
        }
    ]
    results = generate_memos(test)
    for r in results:
        print(f"\n{'='*50}")
        print(f"  {r['name']} — {r.get('recommendation')} ({r.get('confidence_pct')}% confidence)")
        print(f"\n  THESIS:")
        for b in r.get('investment_thesis', []):
            print(f"    • {b}")
        print(f"\n  BULL: {r.get('bull_case')}")
        print(f"  BEAR: {r.get('bear_case')}")
        print(f"\n  MEMO: {r.get('memo')}")
