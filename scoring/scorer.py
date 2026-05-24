"""
AI Scorer  (rebuilt with full VC/IB framework)
-----------------------------------------------
Calls Claude with the professional multi-dimension rubric defined in
vc_framework.py, then post-processes the raw dimension scores into:

  - weighted conviction score (0–100)
  - risk tier (Very Low → Very High)
  - investment verdict (Pass / Watch / Invest / Strong Invest)
  - Kelly-based portfolio allocation (safe / moderate / aggressive)
  - dollar examples at $50k / $250k / $1M portfolio sizes

Every output field is documented so the UI and CSV report can surface
exactly what a VC or investment banker would want to see.
"""

import os
import json
import time
import anthropic
from dotenv import load_dotenv

from scoring.vc_framework import (
    DIMENSIONS,
    build_scoring_prompt,
    calculate_allocation,
    classify_risk,
    get_verdict,
)

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

BATCH_SIZE = 4          # smaller batches = more focused analysis
MODEL      = "claude-sonnet-4-5"
MAX_TOKENS = 6000


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def score_companies(companies: list[dict]) -> list[dict]:
    """
    Main entry point.
    Takes raw scraped company dicts, returns fully scored dicts.
    """
    scored = []
    batches = _chunk(companies, BATCH_SIZE)

    for i, batch in enumerate(batches):
        print(f"[Scorer] Batch {i+1}/{len(batches)} — {[c['name'] for c in batch]}")
        try:
            results = _score_batch(batch)
            scored.extend(results)
        except Exception as e:
            print(f"[Scorer] Batch {i+1} failed: {e}")
            for c in batch:
                c["score_error"] = str(e)
                scored.append(c)

        if i < len(batches) - 1:
            time.sleep(1.5)   # stay well under rate limits

    success = len([s for s in scored if "conviction_score" in s])
    print(f"[Scorer] Complete — {success}/{len(companies)} scored successfully")
    return scored


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL
# ─────────────────────────────────────────────────────────────────────────────

def _score_batch(batch: list[dict]) -> list[dict]:
    prompt = build_scoring_prompt(batch)

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    raw_scores = json.loads(text)

    name_to_raw = {s["name"].lower().strip(): s for s in raw_scores}

    result = []
    for company in batch:
        key = company["name"].lower().strip()
        raw = name_to_raw.get(key, {})
        if not raw:
            # fuzzy fallback — first result if only one returned
            if len(raw_scores) == 1:
                raw = raw_scores[0]
            else:
                company["score_error"] = "name mismatch in AI response"
                result.append(company)
                continue

        enriched = _enrich(company, raw)
        result.append(enriched)

    return result


def _enrich(company: dict, raw: dict) -> dict:
    """
    Merge raw AI scores onto company dict, then compute:
      - weighted conviction score
      - risk tier
      - verdict
      - allocation model output
    """
    merged = {**company, **raw}

    # ── 1. Weighted conviction score ─────────────────────────────────────────
    total = 0.0
    breakdown = {}
    for dim in DIMENSIONS:
        raw_val = raw.get(dim["key"], 5)
        try:
            val = max(1, min(10, int(raw_val)))
        except (TypeError, ValueError):
            val = 5
        breakdown[dim["key"]] = val
        total += val * dim["weight"]

    # Normalise from 1–10 scale → 0–100
    conviction_score = round((total - 1) / 9 * 100)
    merged["conviction_score"]   = conviction_score
    merged["dimension_breakdown"] = breakdown

    # ── 2. Risk tier ──────────────────────────────────────────────────────────
    merged["risk_level"] = classify_risk(conviction_score)

    # ── 3. Investment verdict ─────────────────────────────────────────────────
    merged["investment_verdict"] = get_verdict(conviction_score)

    # ── 4. Portfolio allocation (Kelly-based) ─────────────────────────────────
    alloc = calculate_allocation(
        conviction_score = conviction_score,
        market_size      = raw.get("market_size", "Medium"),
        moat_strength    = raw.get("moat_strength", "Moderate"),
        stage            = raw.get("stage", "Seed"),
    )
    merged.update(alloc)

    # ── 5. Dimension labels for UI display ────────────────────────────────────
    merged["dimension_labels"] = {d["key"]: d["label"] for d in DIMENSIONS}

    return merged


def _chunk(lst, size):
    return [lst[i:i+size] for i in range(0, len(lst), size)]


# ─────────────────────────────────────────────────────────────────────────────
# CLI TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test = [
        {"name": "Lemon.io",   "tagline": "Vetted freelance developer marketplace", "source": "producthunt", "upvotes": 420},
        {"name": "Pika Labs",  "tagline": "AI video generation from text prompts",   "source": "yc",          "batch": "W24"},
        {"name": "Raycast",    "tagline": "Mac productivity launcher replacing Spotlight", "source": "indiehackers"},
        {"name": "Beehiiv",    "tagline": "Newsletter platform for creators and media companies", "source": "producthunt", "upvotes": 310},
    ]
    results = score_companies(test)
    for r in results:
        print(f"\n{'='*55}")
        print(f"  {r['name']}  —  score {r.get('conviction_score','?')}  —  {r.get('investment_verdict','?')}")
        print(f"  Risk: {r.get('risk_level')}   Expected multiple: {r.get('expected_multiple')}x")
        print(f"  Allocation: safe {r.get('safe_allocation_pct')}% / moderate {r.get('moderate_allocation_pct')}% / aggressive {r.get('aggressive_allocation_pct')}%")
        print(f"  {r.get('allocation_verdict','')}")
        print(f"  Dollars ($250k portfolio): {r.get('dollar_examples',{}).get('$250k_portfolio','')}")
        print(f"\n  Dimension breakdown:")
        for k, v in (r.get("dimension_breakdown") or {}).items():
            label = (r.get("dimension_labels") or {}).get(k, k)
            bar = "█" * v + "░" * (10-v)
            print(f"    {label:<42} {bar}  {v}/10")
