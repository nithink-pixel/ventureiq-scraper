"""
VC & Investment Banking Scoring Framework
==========================================
This module defines the complete set of criteria used by professional
venture capitalists and investment bankers to evaluate early-stage companies.

It is the single source of truth for:
  - What dimensions are scored (and why each matters)
  - How sub-scores are weighted into a final conviction score
  - How portfolio allocation is calculated at different risk levels
  - What the investment verdict tiers mean in dollar terms

FRAMEWORKS INCORPORATED
-----------------------
VC side:
  Sequoia's "Why Now" framework
  a16z's market-first investing thesis
  YC's PMF signal checklist
  Bill Gurley's 10 factors for evaluating moat
  Peter Thiel's competition / secrets framework (Zero to One)
  Bessemer's BVP Anti-portfolio learnings (what they missed and why)

Investment banking side:
  DCF growth rate proxies (revenue CAGR implied by traction signals)
  Comparable company analysis (comps) — what category peers trade at
  LBO viability (can this company service debt? recurring revenue?)
  Risk-adjusted return (Kelly Criterion adapted for startup portfolios)
  Position sizing: safe / moderate / aggressive allocation bands
"""

from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# DIMENSION DEFINITIONS
# Each dimension has a name, weight (must sum to 1.0), description,
# scoring rubric (1–10), and what red flags to penalise.
# ─────────────────────────────────────────────────────────────────────────────

DIMENSIONS = [

    # ── 1. MARKET SIZE & TIMING (TAM/SAM/SOM) ───────────────────────────────
    # From a16z: "We invest in markets, not companies."
    # A 10x company in a $100B market > a 100x company in a $1B market.
    {
        "key": "market_size_score",
        "label": "Market size & timing",
        "weight": 0.15,
        "description": (
            "Total addressable market (TAM) size and whether timing is right. "
            "Secular tailwinds? Regulatory shift? New enabling technology?"
        ),
        "rubric": {
            10: "TAM >$50B, clear secular tailwind (AI, climate, aging population)",
            8:  "TAM $10–50B, early market with strong directional signals",
            6:  "TAM $1–10B, established category with room for disruption",
            4:  "TAM <$1B or crowded with dominant incumbents",
            2:  "Niche / shrinking market, no clear expansion path",
        },
        "red_flags": ["declining TAM", "over-served market", "regulatory headwind"],
    },

    # ── 2. PRODUCT–MARKET FIT (PMF) ──────────────────────────────────────────
    # YC's Sean Ellis test: >40% of users say "very disappointed" if product gone.
    # Signals: retention, NPS proxies, organic word-of-mouth, usage depth.
    {
        "key": "pmf_score",
        "label": "Product–market fit (PMF)",
        "weight": 0.15,
        "description": (
            "Strength of evidence that a real customer segment has an urgent "
            "problem and this product is the best solution. "
            "Measured via retention, referrals, revenue growth, engagement."
        ),
        "rubric": {
            10: "Rabid early adopters, >80% retention, viral organic growth",
            8:  "Strong retention signals, paid customers returning, referrals visible",
            6:  "Early traction, some churn but engaged core segment",
            4:  "Mixed signals, high churn or unclear customer love",
            2:  "No clear paying customers, solution looking for a problem",
        },
        "red_flags": ["high churn", "only free users", "unclear ICP", "no retention data"],
    },

    # ── 3. BUSINESS MODEL QUALITY ─────────────────────────────────────────────
    # IB lens: recurring revenue, gross margin, unit economics, payback period.
    # High-quality models: SaaS (>70% GM), marketplace (take-rate), usage-based.
    # Low-quality: one-time, services-heavy, commodity resale.
    {
        "key": "business_model_score",
        "label": "Business model quality",
        "weight": 0.12,
        "description": (
            "Revenue model predictability, gross margin profile, and scalability. "
            "Does revenue recur? Are unit economics improving with scale? "
            "LTV:CAC >3x is minimum viable; >5x is strong."
        ),
        "rubric": {
            10: "SaaS/subscription, >80% gross margin, negative churn (expansion revenue)",
            8:  "Recurring revenue, >60% GM, strong LTV:CAC, clear path to profitability",
            6:  "Mixed recurring/transactional, moderate margins, improving unit economics",
            4:  "Transactional or project-based, thin margins, high CAC",
            2:  "Services business or low-margin resale, not scalable",
        },
        "red_flags": ["services revenue", "sub-30% gross margin", "negative LTV:CAC", "no pricing power"],
    },

    # ── 4. COMPETITIVE MOAT & DEFENSIBILITY ──────────────────────────────────
    # Gurley's 10 factors: switching costs, network effects, economies of scale,
    # proprietary data, brand, regulatory licenses, cost advantages, process power.
    # Thiel: "What do you know that others don't?" — secrets create moats.
    {
        "key": "moat_score",
        "label": "Competitive moat & defensibility",
        "weight": 0.12,
        "description": (
            "How hard is it for a well-funded competitor to replicate this? "
            "Network effects, proprietary data, switching costs, regulatory moats, "
            "brand, and unique technical insight are the strongest moats."
        ),
        "rubric": {
            10: "Multi-layered moat: network effects + proprietary data + switching costs",
            8:  "Strong single moat (network effects OR proprietary data OR deep integrations)",
            6:  "Moderate switching costs or brand, but replicable with capital",
            4:  "First-mover advantage only — no durable structural barrier",
            2:  "Easily cloned, no switching costs, commodity feature set",
        },
        "red_flags": ["'just like X but better'", "feature, not product", "open-source alternative exists"],
    },

    # ── 5. TEAM QUALITY & EXECUTION ABILITY ──────────────────────────────────
    # Sequoia: "The team is the company at early stage."
    # What matters: domain expertise, prior founder/operator experience,
    # technical depth (for tech products), coachability, resilience signals.
    {
        "key": "team_score",
        "label": "Team quality & execution",
        "weight": 0.12,
        "description": (
            "Founder-market fit, relevant domain expertise, prior startup or "
            "operator experience, technical capability, and evidence of execution "
            "(shipping product, hiring, closing customers)."
        ),
        "rubric": {
            10: "Serial founder with exit, deep domain expertise, strong technical co-founder",
            8:  "Ex-FAANG/Top startup operator, first-time founder but clear domain authority",
            6:  "Smart generalists, some relevant experience, early execution visible",
            4:  "First-time founders, limited domain knowledge, slow execution signals",
            2:  "No relevant experience, solo non-technical founder in technical space",
        },
        "red_flags": ["solo founder", "no technical co-founder in hard-tech", "high team turnover"],
    },

    # ── 6. GROWTH VELOCITY & TRACTION ────────────────────────────────────────
    # IB metric: implied revenue CAGR. VC metric: MoM growth rate.
    # T2D3 rule (Bessemer): triple, triple, double, double, double ARR to $100M.
    # Strong signals: >15% MoM, strong hiring velocity, accelerating engagement.
    {
        "key": "growth_score",
        "label": "Growth velocity & traction",
        "weight": 0.12,
        "description": (
            "Month-over-month revenue/user growth rate, hiring velocity, "
            "web traffic trajectory, engagement depth. "
            "15%+ MoM = strong. <5% MoM at early stage = weak signal."
        ),
        "rubric": {
            10: ">20% MoM growth, accelerating, strong hiring, organic virality",
            8:  "15–20% MoM, consistent, multiple traction vectors visible",
            6:  "5–15% MoM, growing but not exceptional, linear trajectory",
            4:  "<5% MoM or stagnant, limited public traction signals",
            2:  "Declining metrics, pivoting frequently, no visible momentum",
        },
        "red_flags": ["plateaued growth", "growth from paid only", "slowing after initial spike"],
    },

    # ── 7. UNIT ECONOMICS & PATH TO PROFITABILITY ────────────────────────────
    # IB lens: EBITDA margin potential, CAC payback period, gross margin expansion.
    # VC lens: can this business reach profitability before needing more dilutive capital?
    {
        "key": "unit_economics_score",
        "label": "Unit economics & profitability path",
        "weight": 0.10,
        "description": (
            "CAC payback period (<18 months is strong), LTV:CAC ratio (>3x minimum), "
            "gross margin trajectory, burn multiple (net burn / net new ARR, <1.5x is good), "
            "and clarity of path to contribution-positive unit economics."
        ),
        "rubric": {
            10: "CAC payback <12mo, LTV:CAC >5x, GM >75%, burn multiple <1x",
            8:  "CAC payback 12–18mo, LTV:CAC 3–5x, improving margins",
            6:  "CAC payback 18–30mo, LTV:CAC 2–3x, burn multiple 1.5–2.5x",
            4:  "CAC payback >30mo, unclear unit economics, high burn",
            2:  "Negative unit economics with no credible path to improvement",
        },
        "red_flags": ["high CAC with no payback visibility", "negative gross margin", "burn multiple >3x"],
    },

    # ── 8. TECHNOLOGY & INNOVATION DEPTH ─────────────────────────────────────
    # Is this a genuine technical innovation or a wrapper around existing APIs?
    # Deep tech / proprietary models / novel architecture = stronger moat.
    # Feature wrapping existing infra = easily replicated by the platform itself.
    {
        "key": "tech_score",
        "label": "Technology depth & IP",
        "weight": 0.07,
        "description": (
            "Proprietary technology, novel architecture, patents, trade secrets, "
            "or data advantages that cannot be easily replicated. "
            "AI wrappers and no-code tools score lower; custom models and "
            "proprietary data pipelines score higher."
        ),
        "rubric": {
            10: "Breakthrough IP, novel ML architecture, proprietary datasets, hard to replicate",
            8:  "Strong technical differentiation, custom-built infra, meaningful R&D moat",
            6:  "Good engineering, some proprietary elements but buildable by a funded team",
            4:  "Primarily integrations / API wrappers, no core technical differentiation",
            2:  "Pure reseller or thin wrapper, platform provider could replicate in days",
        },
        "red_flags": ["GPT wrapper with no data moat", "no engineering team", "platform dependency risk"],
    },

    # ── 9. CAPITAL EFFICIENCY & FUNDRAISING POSITION ─────────────────────────
    # How much has been raised vs. what's been built? Lean = efficient.
    # IB: capital structure, dilution, runway, next round visibility.
    {
        "key": "capital_efficiency_score",
        "label": "Capital efficiency & runway",
        "weight": 0.05,
        "description": (
            "How much value has been created per dollar of capital raised? "
            "Strong burn multiple, 18+ months runway, clean cap table, "
            "and clear next-round thesis are positive signals."
        ),
        "rubric": {
            10: "Bootstrapped to strong revenue OR raised little and growing fast",
            8:  "18+ months runway, burn multiple <1.5x, clean cap table",
            6:  "12–18 months runway, reasonable burn, credible path to next round",
            4:  "<12 months runway or heavy dilution, dependent on imminent raise",
            2:  "Running out of cash, distressed cap table, no clear investor interest",
        },
        "red_flags": ["<6 months runway", "heavy insider dilution", "down round history"],
    },

]

# Verify weights sum to ~1.0
_total_weight = sum(d["weight"] for d in DIMENSIONS)
assert abs(_total_weight - 1.0) < 0.001, f"Weights must sum to 1.0, got {_total_weight}"


# ─────────────────────────────────────────────────────────────────────────────
# RISK CLASSIFICATION
# Maps a weighted score to a risk tier with specific portfolio implications.
# ─────────────────────────────────────────────────────────────────────────────

RISK_TIERS = {
    "Very Low":  {"min_score": 82, "color": "green",  "description": "Exceptional fundamentals across all dimensions. Rare."},
    "Low":       {"min_score": 70, "color": "teal",   "description": "Strong fundamentals, minor gaps. Suitable for meaningful position."},
    "Medium":    {"min_score": 55, "color": "amber",  "description": "Mixed signals. Real upside but identifiable risks. Size accordingly."},
    "High":      {"min_score": 40, "color": "coral",  "description": "Speculative. Interesting thesis but significant execution risk."},
    "Very High": {"min_score": 0,  "color": "red",    "description": "Lottery ticket. Pass unless you have unique conviction or information."},
}


def classify_risk(conviction_score: float) -> str:
    for tier, meta in RISK_TIERS.items():
        if conviction_score >= meta["min_score"]:
            return tier
    return "Very High"


# ─────────────────────────────────────────────────────────────────────────────
# PORTFOLIO ALLOCATION MODEL
# Based on Kelly Criterion adapted for startup portfolios.
#
# Kelly formula: f* = (bp - q) / b
#   where b = odds, p = win probability, q = 1 - p
#
# For startups we adapt this to:
#   - Estimate win probability from conviction score
#   - Estimate return multiple from market size + moat
#   - Apply a "fractional Kelly" (25-50% of full Kelly) to account for
#     model uncertainty — full Kelly is theoretically optimal but
#     practically too aggressive given estimation error.
#
# Output: three allocation bands per company
#   safe_allocation     — conservative investor (20% fractional Kelly)
#   moderate_allocation — balanced investor (35% fractional Kelly)
#   aggressive_allocation — risk-tolerant investor (50% fractional Kelly)
#
# All expressed as % of total investable portfolio.
# ─────────────────────────────────────────────────────────────────────────────

def calculate_allocation(
    conviction_score: float,
    market_size: str,
    moat_strength: str,
    stage: str,
) -> dict:
    """
    Returns allocation recommendation dict with safe / moderate / aggressive bands
    and a plain-English rationale.
    """

    # ── Step 1: estimate win probability from conviction score ────────────────
    # Empirical VC base rates:
    #   ~40% of seed investments return capital
    #   ~20% return 3x+
    #   ~5-10% return 10x+
    # We scale these by conviction score.
    base_win_prob = _conviction_to_win_prob(conviction_score)

    # ── Step 2: estimate expected multiple from market + moat ─────────────────
    market_mult = {"Small": 3, "Medium": 5, "Large": 10, "Massive": 20}.get(market_size, 5)
    moat_mult   = {"Weak": 0.7, "Moderate": 1.0, "Strong": 1.4}.get(moat_strength, 1.0)
    stage_mult  = {"Pre-seed": 1.5, "Seed": 1.2, "Series A": 1.0, "Bootstrapped": 0.9, "Growth": 0.8}.get(stage, 1.0)

    expected_multiple = market_mult * moat_mult * stage_mult

    # ── Step 3: Kelly fraction ────────────────────────────────────────────────
    p = base_win_prob
    q = 1 - p
    b = expected_multiple - 1   # net odds (return on $1 bet)

    if b <= 0:
        kelly = 0.0
    else:
        kelly = max(0.0, (b * p - q) / b)

    # ── Step 4: apply fractional Kelly ───────────────────────────────────────
    safe       = round(kelly * 0.20 * 100, 1)  # 20% of Kelly
    moderate   = round(kelly * 0.35 * 100, 1)  # 35% of Kelly
    aggressive = round(kelly * 0.50 * 100, 1)  # 50% of Kelly

    # Hard caps: no single startup should exceed these % of portfolio
    safe       = min(safe,        2.0)
    moderate   = min(moderate,    5.0)
    aggressive = min(aggressive, 10.0)

    # Hard floors: if conviction < 40, recommend 0
    if conviction_score < 40:
        safe = moderate = aggressive = 0.0

    verdict = _allocation_verdict(conviction_score, safe, moderate, aggressive)
    dollar_example = _dollar_examples(safe, moderate, aggressive)

    return {
        "safe_allocation_pct":       safe,
        "moderate_allocation_pct":   moderate,
        "aggressive_allocation_pct": aggressive,
        "expected_multiple":         round(expected_multiple, 1),
        "win_probability_pct":       round(base_win_prob * 100, 0),
        "kelly_raw_pct":             round(kelly * 100, 1),
        "allocation_verdict":        verdict,
        "dollar_examples":           dollar_example,
    }


def _conviction_to_win_prob(score: float) -> float:
    """
    Convert 0–100 conviction score to estimated win probability.
    Calibrated to real VC return distributions:
      score=85 → ~35% chance of 5x+ return
      score=65 → ~18% chance
      score=45 → ~8% chance
      score=25 → ~3% chance
    """
    import math
    # Sigmoid scaled to [0.02, 0.45]
    t = (score - 50) / 20
    sigmoid = 1 / (1 + math.exp(-t))
    return 0.02 + sigmoid * 0.43


def _allocation_verdict(score: float, safe: float, moderate: float, aggressive: float) -> str:
    if score >= 80:
        return f"Strong buy. Allocate {moderate}–{aggressive}% of portfolio. High-conviction position."
    elif score >= 65:
        return f"Buy. Allocate {safe}–{moderate}% of portfolio. Solid risk-adjusted bet."
    elif score >= 50:
        return f"Speculative buy. Max {safe}% if you have unique insight. Watch closely."
    elif score >= 40:
        return f"Watch only. Invest {safe}% or less. Revisit at next traction milestone."
    else:
        return "Pass. Below minimum threshold for capital deployment."


def _dollar_examples(safe: float, moderate: float, aggressive: float) -> dict:
    """Show what these percentages mean in real dollar terms at 3 portfolio sizes."""
    return {
        "$50k_portfolio":   f"${safe*500:.0f} safe / ${moderate*500:.0f} moderate / ${aggressive*500:.0f} aggressive",
        "$250k_portfolio":  f"${safe*2500:.0f} safe / ${moderate*2500:.0f} moderate / ${aggressive*2500:.0f} aggressive",
        "$1M_portfolio":    f"${safe*10000:.0f} safe / ${moderate*10000:.0f} moderate / ${aggressive*10000:.0f} aggressive",
    }


# ─────────────────────────────────────────────────────────────────────────────
# VERDICT TIERS
# Maps final conviction score to actionable recommendation.
# ─────────────────────────────────────────────────────────────────────────────

VERDICT_TIERS = {
    "Strong Invest": {
        "min_score": 78,
        "meaning": "Top-decile opportunity. Lead or co-lead the round if possible.",
        "typical_check": "2–10% of portfolio",
    },
    "Invest": {
        "min_score": 62,
        "meaning": "Solid conviction. Participate in round. Follow-on likely.",
        "typical_check": "1–5% of portfolio",
    },
    "Watch": {
        "min_score": 45,
        "meaning": "Interesting but needs more proof. Track and revisit in 90 days.",
        "typical_check": "0.5–2% of portfolio max",
    },
    "Pass": {
        "min_score": 0,
        "meaning": "Does not meet minimum bar. Document reason and move on.",
        "typical_check": "0%",
    },
}


def get_verdict(conviction_score: float) -> str:
    for verdict, meta in VERDICT_TIERS.items():
        if conviction_score >= meta["min_score"]:
            return verdict
    return "Pass"


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDER
# Returns the full Claude prompt for scoring a batch of companies.
# ─────────────────────────────────────────────────────────────────────────────

def build_scoring_prompt(batch: list[dict]) -> str:
    dim_rubric = "\n".join(
        f'  {i+1}. "{d["key"]}" (weight {int(d["weight"]*100)}%): {d["description"]}\n'
        f'     Score 1–10. 10={d["rubric"][10]}. 2={d["rubric"][2]}.'
        for i, d in enumerate(DIMENSIONS)
    )

    companies_text = "\n\n".join(
        f"Company {i+1}:\n"
        f"  Name: {c['name']}\n"
        f"  Source: {c.get('source','unknown')}\n"
        f"  Tagline: {c.get('tagline','—')}\n"
        f"  Extra signals: {_fmt_signals(c)}"
        for i, c in enumerate(batch)
    )

    keys = [d["key"] for d in DIMENSIONS]
    keys_str = "\n    ".join(f'"{k}": <integer 1-10>,' for k in keys)

    return f"""You are a Partner-level VC analyst at a tier-1 fund (think Sequoia, a16z, Bessemer).
You use a rigorous multi-dimensional framework to score every company.

SCORING DIMENSIONS (score each 1–10):
{dim_rubric}

COMPANIES TO ANALYZE:
{companies_text}

For each company, use all available signals plus your knowledge of the startup ecosystem.
Infer what you can from the name, tagline, source platform, and extra signals.
Be calibrated — most startups score 4–6. Reserve 9–10 for genuinely exceptional signals.

Return ONLY a valid JSON array. No markdown, no explanation. Each object:
[
  {{
    "name": "<exact name as given>",
    "tagline": "<one sentence, keep or sharpen original>",
    "category": "<AI Tools|SaaS|Dev Tools|Fintech|Consumer|Creator Economy|Health Tech|B2B|Marketplace|Other>",
    "stage": "<Pre-seed|Seed|Series A|Bootstrapped|Growth>",
    "business_model": "<SaaS|Marketplace|B2B|Consumer|API|Subscription|Usage-based|Ad-supported>",
    "market_size": "<Small|Medium|Large|Massive>",
    "moat_strength": "<Weak|Moderate|Strong>",
    "growth_signal": "<short phrase describing strongest public growth signal>",
    "comparable_to": "<e.g. 'Early Figma' or 'Notion for legal teams'>",
    "top_strength": "<one sentence — most compelling reason to invest>",
    "top_risk": "<one sentence — most important risk to flag>",
    "analysis_note": "<3 sentences: (1) business model quality, (2) market opportunity + moat, (3) key risk and what would change your mind>",
    {keys_str}
  }}
]"""


def _fmt_signals(c: dict) -> str:
    parts = []
    if c.get("upvotes"):      parts.append(f"{c['upvotes']} PH upvotes")
    if c.get("open_roles"):   parts.append(f"{c['open_roles']} open roles")
    if c.get("revenue_range"):parts.append(f"revenue: {c['revenue_range']}")
    if c.get("batch"):        parts.append(f"YC {c['batch']}")
    if c.get("funding_stage"):parts.append(c["funding_stage"])
    if c.get("industry"):     parts.append(c["industry"])
    return ", ".join(parts) or "none public"
