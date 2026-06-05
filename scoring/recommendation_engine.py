"""
Recommendation Engine
======================
Replaces the raw conviction score as the primary output.

Instead of "score: 65" produces:

  RECOMMENDATION: Monitor
  CONFIDENCE: 72%
  
  WHY:
  - Large market with strong tailwinds
  - Technical founder with domain expertise
  - Crowded category but defensible wedge
  
  WHAT WOULD CHANGE THIS:
  - Revenue milestone above $50k MRR
  - Enterprise customer announced
  - Competitor acquisition (validates market)

This is how VC partners actually think and communicate
about deals internally.
"""

import os
import json
import time
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-5"


def generate_recommendations(companies: list[dict]) -> list[dict]:
    """
    Takes fully enriched companies (scored + memo + comparables + founder).
    Generates final investment recommendation for each.
    """
    results = []
    total = len(companies)
    print(f"[Recommendation] Generating final recommendations for {total} companies...")

    for i, company in enumerate(companies):
        print(f"[Recommendation] {i+1}/{total} — {company.get('name')}")
        try:
            rec = _generate_recommendation(company)
            merged = {**company, **rec}
            results.append(merged)
        except Exception as e:
            print(f"[Recommendation] Failed for {company.get('name')}: {e}")
            results.append(company)
        if i < total - 1:
            time.sleep(0.4)

    invest = len([r for r in results if r.get("final_recommendation") == "Invest"])
    monitor = len([r for r in results if r.get("final_recommendation") == "Monitor"])
    passes = len([r for r in results if r.get("final_recommendation") == "Pass"])
    print(f"[Recommendation] Complete — Invest: {invest} | Monitor: {monitor} | Pass: {passes}")
    return results


def _generate_recommendation(company: dict) -> dict:
    prompt = _build_prompt(company)

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


def _build_prompt(company: dict) -> str:
    name        = company.get("name", "")
    tagline     = company.get("tagline", "")
    category    = company.get("category", "")
    stage       = company.get("stage", "")
    score       = company.get("conviction_score", 0)
    memo        = company.get("memo", "")
    rec         = company.get("recommendation", "")
    confidence  = company.get("confidence_pct", 0)
    thesis      = company.get("investment_thesis", [])
    risks       = company.get("key_risks", [])
    bull        = company.get("bull_case", "")
    bear        = company.get("bear_case", "")
    comparables = company.get("comparable_companies", [])
    valuation   = company.get("valuation_corridor", {})
    f_score     = company.get("founder_score", 0)
    f_type      = company.get("founder_type", "")
    f_summary   = company.get("founder_summary", "")
    f_signals   = company.get("positive_signals", [])
    f_risks     = company.get("risk_signals", [])
    exit_path   = company.get("most_likely_exit", "")
    acquirers   = company.get("strategic_acquirers", [])
    market_size = company.get("market_size", "")
    moat        = company.get("moat_strength", "")

    comp_text = ""
    if comparables:
        comp_text = "\n".join([f"- {c.get('name')}: {c.get('outcome')}" for c in comparables[:3]])

    val_text = f"Low: {valuation.get('low')} | Mid: {valuation.get('mid')} | High: {valuation.get('high')}" if valuation else ""

    return f"""You are a General Partner at a top-tier VC fund making a final investment decision.

You have reviewed all available analysis on this company. Now synthesize everything
into a clear, opinionated final recommendation — the kind you'd give at IC.

COMPANY: {name}
Tagline: {tagline}
Category: {category} | Stage: {stage} | Market: {market_size} | Moat: {moat}

SCORING: {score}/100 conviction | Initial rec: {rec} ({confidence}% confidence)

MEMO SUMMARY: {memo}

INVESTMENT THESIS:
{chr(10).join([f"• {t}" for t in thesis])}

KEY RISKS:
{chr(10).join([f"• {r}" for r in risks])}

BULL CASE: {bull}
BEAR CASE: {bear}

FOUNDER: Score {f_score}/10 | {f_type} | {f_summary}
Founder signals: {", ".join(f_signals[:2])}
Founder risks: {", ".join(f_risks[:2])}

COMPARABLES:
{comp_text}

VALUATION CORRIDOR: {val_text}
EXIT: {exit_path} | Acquirers: {", ".join(acquirers[:3])}

Now give your final IC recommendation. Be direct and opinionated.
A "Monitor" means you want to see specific milestones before investing.
An "Invest" means you'd write a check today.
A "Pass" means you wouldn't invest at any reasonable valuation.

Return ONLY valid JSON (no markdown):
{{
  "final_recommendation": "Invest|Monitor|Pass",
  "final_confidence": <integer 50-95>,
  "decision_summary": "<2 sentences — the core reason for this decision, written as you'd say it at IC>",
  "key_reasons": [
    "<reason 1 — most important factor driving this decision>",
    "<reason 2>",
    "<reason 3>"
  ],
  "what_would_change_to_invest": [
    "<milestone 1 that would make you invest e.g. $100k MRR achieved>",
    "<milestone 2 e.g. Enterprise customer signed>",
    "<milestone 3>"
  ],
  "what_would_make_you_pass": [
    "<signal 1 that would make you pass e.g. GitHub launches native caching>",
    "<signal 2>"
  ],
  "suggested_check_size": "<e.g. Pass | $250k angel | $500k seed | Lead $2M seed>",
  "follow_up_actions": [
    "<action 1 e.g. Request customer reference calls>",
    "<action 2 e.g. Map GitHub product roadmap>",
    "<action 3>"
  ],
  "one_line_verdict": "<one punchy sentence — the kind a partner says walking out of IC>"
}}"""


if __name__ == "__main__":
    test = [
        {
            "name": "Blacksmith",
            "tagline": "Faster GitHub Actions with persistent runner cache",
            "category": "Dev Tools",
            "stage": "Seed",
            "conviction_score": 61,
            "recommendation": "Monitor",
            "confidence_pct": 68,
            "market_size": "Medium",
            "moat_strength": "Moderate",
            "memo": "Blacksmith solves CI/CD performance with measurable ROI but faces platform risk from GitHub building natively.",
            "investment_thesis": [
                "Immediate measurable ROI drives fast sales cycles",
                "Deep GitHub Actions integration creates switching costs",
                "Wedge into broader CI/CD platform"
            ],
            "key_risks": [
                "GitHub could build native caching",
                "Small initial market size",
                "Distribution challenge in dev tools"
            ],
            "bull_case": "Becomes de facto CI/CD performance layer, acquired by GitLab or Atlassian for $500M+",
            "bear_case": "GitHub ships native caching, company loses 80% of customers overnight",
            "founder_score": 7.2,
            "founder_type": "Technical",
            "founder_summary": "Strong technical founders with DevOps expertise, YC validated.",
            "positive_signals": ["YC W24 backing", "Deep domain expertise"],
            "risk_signals": ["First-time founders", "No public profile"],
            "comparable_companies": [
                {"name": "CircleCI", "outcome": "Raised $100M at $1.7B valuation"},
                {"name": "BuildKite", "outcome": "Raised $28M Series A"},
            ],
            "valuation_corridor": {"low": "$40M", "mid": "$200M", "high": "$800M"},
            "most_likely_exit": "Acquisition",
            "strategic_acquirers": ["GitLab", "Atlassian", "JFrog"]
        }
    ]
    results = generate_recommendations(test)
    for r in results:
        print(f"\n{'='*55}")
        print(f"  {r['name']}")
        print(f"  FINAL: {r.get('final_recommendation')} ({r.get('final_confidence')}% confidence)")
        print(f"  CHECK: {r.get('suggested_check_size')}")
        print(f"\n  VERDICT: {r.get('one_line_verdict')}")
        print(f"\n  DECISION: {r.get('decision_summary')}")
        print(f"\n  KEY REASONS:")
        for reason in r.get("key_reasons", []):
            print(f"    • {reason}")
        print(f"\n  WHAT WOULD CHANGE TO INVEST:")
        for m in r.get("what_would_change_to_invest", []):
            print(f"    → {m}")
        print(f"\n  FOLLOW UP:")
        for a in r.get("follow_up_actions", []):
            print(f"    ☐ {a}")
