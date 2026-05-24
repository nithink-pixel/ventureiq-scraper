"""
Report builder  (updated for full VC/IB framework output)
-----------------------------------------------------------
Saves ranked CSV + Supabase rows + console summary.
All allocation and dimension breakdown fields are included.
"""

import os
import csv
import json
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR   = Path(os.getenv("OUTPUT_DIR", "./data"))
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Core fields saved to CSV (dimension breakdown saved as JSON column)
CORE_FIELDS = [
    "name", "source", "url", "tagline", "category", "stage",
    "business_model", "market_size", "moat_strength",
    # VC scores
    "conviction_score", "risk_level", "investment_verdict",
    "win_probability_pct", "expected_multiple",
    # Allocation model
    "safe_allocation_pct", "moderate_allocation_pct", "aggressive_allocation_pct",
    "allocation_verdict",
    # Qualitative
    "growth_signal", "comparable_to", "top_strength", "top_risk", "analysis_note",
    # Dimension breakdown (JSON)
    "dimension_breakdown",
    # Dollar examples (JSON)
    "dollar_examples",
]


def save_report(companies: list[dict], week_of: date | None = None) -> Path:
    if week_of is None:
        week_of = date.today()

    ranked = sorted(companies, key=lambda c: int(c.get("conviction_score") or 0), reverse=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / f"startups_{week_of.isoformat()}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "week_of"] + CORE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for rank, c in enumerate(ranked, 1):
            row = {"rank": rank, "week_of": week_of.isoformat()}
            for k in CORE_FIELDS:
                val = c.get(k, "")
                # Serialise dicts to JSON strings for CSV
                if isinstance(val, dict):
                    val = json.dumps(val)
                row[k] = val
            writer.writerow(row)

    print(f"[Report] CSV saved → {csv_path}  ({len(ranked)} companies)")

    if SUPABASE_URL and SUPABASE_KEY:
        _push_supabase(ranked, week_of)

    _print_summary(ranked, week_of)
    return csv_path


def _push_supabase(companies, week_of):
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        rows = []
        for c in companies:
            row = {"week_of": week_of.isoformat()}
            for k in CORE_FIELDS:
                val = c.get(k)
                if isinstance(val, dict):
                    val = json.dumps(val)
                row[k] = val
            try:
                row["conviction_score"] = int(row.get("conviction_score") or 0)
            except (ValueError, TypeError):
                row["conviction_score"] = None
            rows.append(row)
        sb.table("startups").insert(rows).execute()
        print(f"[Report] Pushed {len(rows)} rows to Supabase")
    except Exception as e:
        print(f"[Report] Supabase push failed: {e}")


def _print_summary(ranked, week_of):
    invest  = [c for c in ranked if c.get("investment_verdict") in ("Invest","Strong Invest")]
    avg_sc  = round(sum(c.get("conviction_score",0) for c in ranked) / max(len(ranked),1))
    gems    = [c for c in ranked if c.get("conviction_score",0) >= 75 and c.get("risk_level") in ("Low","Very Low")]

    w = 65
    print(f"\n{'═'*w}")
    print(f"  VentureIQ Weekly Report — {week_of.isoformat()}")
    print(f"  {len(ranked)} companies  |  {len(invest)} invest signals  |  avg conviction {avg_sc}")
    print(f"{'─'*w}")
    print(f"  {'#':<3} {'Score':<6} {'Risk':<12} {'Verdict':<15} {'Name':<24} Source")
    print(f"  {'─'*60}")
    for c in ranked[:12]:
        sc   = c.get("conviction_score","—")
        risk = c.get("risk_level","—")[:11]
        v    = c.get("investment_verdict","—")[:14]
        name = str(c.get("name",""))[:22]
        src  = c.get("source","")
        print(f"  {ranked.index(c)+1:<3} {str(sc):<6} {risk:<12} {v:<15} {name:<24} {src}")

    if gems:
        print(f"{'─'*w}")
        print("  HIDDEN GEMS — high conviction + low risk")
        for g in gems[:3]:
            alloc = g.get("moderate_allocation_pct", 0)
            print(f"  ★ {g.get('name')}  score={g.get('conviction_score')}  "
                  f"allocate ~{alloc}% moderate  |  {g.get('top_strength','')[:60]}")

    print(f"{'═'*w}\n")
