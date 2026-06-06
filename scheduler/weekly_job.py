import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from scrapers import producthunt, ycombinator, indiehackers, wellfound
from scoring.scorer import score_companies
from scoring.memo_generator import generate_memos
from scoring.market_intelligence import generate_market_report
from scoring.comparables import add_comparables
from scoring.recommendation_engine import generate_recommendations
from scrapers.founder_intel import add_founder_intelligence
from scoring.report import save_report

ENABLED_SOURCES = {
    "producthunt": True,
    "yc": True,
    "indiehackers": True,
    "wellfound": True,
}

MIN_PH_UPVOTES = 0
MIN_WF_ROLES = 0

def run_pipeline():
    print("\n=== VentureIQ Weekly Scan starting ===\n")
    week_of = date.today()
    raw = []

    if ENABLED_SOURCES["producthunt"]:
        try:
            r = producthunt.scrape()
            print(f"[Pipeline] producthunt returned {len(r)} items")
            raw.extend(r)
        except Exception as e:
            print(f"[Pipeline] producthunt error: {e}")

    if ENABLED_SOURCES["yc"]:
        try:
            r = ycombinator.scrape()
            print(f"[Pipeline] yc returned {len(r)} items")
            raw.extend(r)
        except Exception as e:
            print(f"[Pipeline] yc error: {e}")

    if ENABLED_SOURCES["indiehackers"]:
        try:
            r = indiehackers.scrape()
            print(f"[Pipeline] indiehackers returned {len(r)} items")
            raw.extend(r)
        except Exception as e:
            print(f"[Pipeline] indiehackers error: {e}")

    if ENABLED_SOURCES["wellfound"]:
        try:
            r = wellfound.scrape()
            print(f"[Pipeline] wellfound returned {len(r)} items")
            raw.extend(r)
        except Exception as e:
            print(f"[Pipeline] wellfound error: {e}")

    print(f"\n[Pipeline] Total raw companies: {len(raw)}")

    seen = set()
    filtered = []
    for c in raw:
        name = (c.get("name") or "").strip().lower()
        if not name or len(name) < 2 or name in seen:
            continue
        seen.add(name)
        filtered.append(c)

    print(f"[Pipeline] After dedup: {len(filtered)} companies")

    if not filtered:
        print("[Pipeline] Nothing to score — exiting.")
        return

    scored = score_companies(filtered)
    # Top 20 only for expensive layers
    scored = sorted(scored, key=lambda x: int(x.get('conviction_score') or 0), reverse=True)
    top20 = scored[:20]
    rest = scored[20:]
    print('[Pipeline] Generating deal memos for top 20...')
    top20 = generate_memos(top20)
    scored = top20 + rest
    top20 = [c for c in scored if c.get('memo')][:20]
    rest = [c for c in scored if not c.get('memo')]
    print('[Pipeline] Adding founder intelligence for top 20...')
    top20 = add_founder_intelligence(top20)
    scored = top20 + rest
    print('[Pipeline] Adding comparables for top 10...')
    scored_sorted2 = sorted(scored, key=lambda x: int(x.get('conviction_score') or 0), reverse=True)
    top10 = scored_sorted2[:10]
    rest10 = scored_sorted2[10:]
    top10 = add_comparables(top10)
    scored = top10 + rest10
    print('[Pipeline] Generating market intelligence report...')
    market_report = generate_market_report(scored, week_of=week_of)
    top20 = [c for c in scored if c.get('memo')][:20]
    rest = [c for c in scored if not c.get('memo')]
    print('[Pipeline] Generating final recommendations for top 20...')
    top20 = generate_recommendations(top20)
    scored = top20 + rest
    csv_path = save_report(scored, week_of=week_of)
    print(f"[Pipeline] Done. Report saved to {csv_path}")

if __name__ == "__main__":
    run_pipeline()
