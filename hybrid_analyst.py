"""
hybrid_analyst.py — AHI Diagnostic Reasoning Engine
The statistical engine. ALL math happens here with Pandas/NumPy.

Hybrid Math Rule: This module owns every numerical computation that involves
more than one respondent. Z-scores, percentiles, role averages, perception
gaps — all Pandas. Zero LLM math calls.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from heuristics import (
    MIN_BENCHMARK_SAMPLE,
    PERCEPTION_GAP_THRESHOLD,
    ZSCORE_OUTLIER_THRESHOLD,
)
from schema import (
    AnalysisResponse,
    AssessmentPayload,
    HybridAnalystSummary,
    RespondentRole,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BENCHMARK_CSV = Path(__file__).parent / "data" / "benchmark_50_users.csv"

# Canonical column names in the benchmark CSV (must match generate_benchmark.py)
CATEGORY_COLS = {
    "Leadership & Vision":    "Leadership_and_Vision",
    "Ways of Working":        "Ways_of_Working",
    "Culture & Workforce":    "Culture_and_Workforce",
    "Governance Readiness":   "Governance_Readiness",
    "Technology Readiness":   "Technology_Readiness",
    "Data Readiness":         "Data_Readiness",
}

COMPOSITE_COL = "composite_score"
ROLE_COL      = "role"


# ---------------------------------------------------------------------------
# Data Loader
# ---------------------------------------------------------------------------

_benchmark_df: Optional[pd.DataFrame] = None


def load_benchmark() -> pd.DataFrame:
    """
    Load and cache the benchmark dataset.
    Returns an empty DataFrame if the file does not exist.
    """
    global _benchmark_df
    if _benchmark_df is not None:
        return _benchmark_df

    if not BENCHMARK_CSV.exists():
        _benchmark_df = pd.DataFrame()
        return _benchmark_df

    df = pd.read_csv(BENCHMARK_CSV)
    # Coerce numeric columns
    numeric_cols = list(CATEGORY_COLS.values()) + [COMPOSITE_COL]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    _benchmark_df = df
    return _benchmark_df


def reload_benchmark() -> None:
    """Force reload — call after benchmark CSV is updated."""
    global _benchmark_df
    _benchmark_df = None
    load_benchmark()


# ---------------------------------------------------------------------------
# Role Average Computation
# ---------------------------------------------------------------------------

def role_category_averages(role: str) -> Dict[str, Optional[float]]:
    """
    Return per-category average scores for a given role.
    Returns None for any category with fewer than MIN_BENCHMARK_SAMPLE responses.
    """
    df = load_benchmark()
    if df.empty:
        return {}

    role_df = df[df[ROLE_COL] == role]
    if len(role_df) < MIN_BENCHMARK_SAMPLE:
        return {}

    result: Dict[str, Optional[float]] = {}
    for cat_label, col in CATEGORY_COLS.items():
        if col in role_df.columns:
            series = role_df[col].dropna()
            result[cat_label] = round(float(series.mean()), 2) if len(series) >= MIN_BENCHMARK_SAMPLE else None
        else:
            result[cat_label] = None

    return result


def role_composite_average(role: str) -> Optional[float]:
    """Return the mean composite score for a role cohort."""
    df = load_benchmark()
    if df.empty:
        return None

    role_df = df[df[ROLE_COL] == role]
    series  = role_df[COMPOSITE_COL].dropna()
    if len(series) < MIN_BENCHMARK_SAMPLE:
        return None

    return round(float(series.mean()), 2)


# ---------------------------------------------------------------------------
# Z-Score Computation
# ---------------------------------------------------------------------------

def composite_zscore(respondent_composite: float, role: Optional[str] = None) -> Optional[float]:
    """
    Compute the respondent's Z-score relative to:
      - Their role cohort (if role provided and N >= MIN_BENCHMARK_SAMPLE)
      - The full benchmark population otherwise

    Returns None if insufficient data.
    """
    df = load_benchmark()
    if df.empty:
        return None

    if role:
        cohort = df[df[ROLE_COL] == role][COMPOSITE_COL].dropna()
    else:
        cohort = df[COMPOSITE_COL].dropna()

    if len(cohort) < MIN_BENCHMARK_SAMPLE:
        return None

    mean = cohort.mean()
    std  = cohort.std()

    if std == 0:
        return 0.0

    return round(float((respondent_composite - mean) / std), 2)


def category_zscore(
    respondent_score: float,
    category: str,
    role: Optional[str] = None,
) -> Optional[float]:
    """Z-score for a single category score vs cohort."""
    df = load_benchmark()
    if df.empty or category not in CATEGORY_COLS:
        return None

    col = CATEGORY_COLS[category]
    if col not in df.columns:
        return None

    if role:
        cohort = df[df[ROLE_COL] == role][col].dropna()
    else:
        cohort = df[col].dropna()

    if len(cohort) < MIN_BENCHMARK_SAMPLE:
        return None

    mean = cohort.mean()
    std  = cohort.std()

    if std == 0:
        return 0.0

    return round(float((respondent_score - mean) / std), 2)


# ---------------------------------------------------------------------------
# Perception Gap (Strategic Blind Spot Detection)
# ---------------------------------------------------------------------------

def detect_perception_gaps(
    respondent_role: str,
    respondent_scores: Dict[str, float],
) -> List[str]:
    """
    For each category, compare the respondent's role cohort average
    against all other role cohorts. If the gap exceeds
    PERCEPTION_GAP_THRESHOLD, flag it as a "Strategic Blind Spot."

    Returns a list of human-readable gap descriptions.
    """
    df = load_benchmark()
    if df.empty:
        return []

    gaps: List[str] = []
    all_roles = df[ROLE_COL].dropna().unique().tolist()

    for cat_label, col in CATEGORY_COLS.items():
        if col not in df.columns or cat_label not in respondent_scores:
            continue

        respondent_cat_score = respondent_scores[cat_label]

        for other_role in all_roles:
            if other_role == respondent_role:
                continue

            other_cohort = df[df[ROLE_COL] == other_role][col].dropna()
            if len(other_cohort) < MIN_BENCHMARK_SAMPLE:
                continue

            other_avg = round(float(other_cohort.mean()), 2)
            gap = abs(respondent_cat_score - other_avg)

            if gap >= PERCEPTION_GAP_THRESHOLD:
                direction = "above" if respondent_cat_score > other_avg else "below"
                gaps.append(
                    f"Strategic Blind Spot — {cat_label}: "
                    f"{respondent_role} avg {respondent_cat_score:.1f} vs "
                    f"{other_role} avg {other_avg:.1f} "
                    f"(gap: {gap:.1f}, respondent is {direction} peer cohort)"
                )

    return gaps


# ---------------------------------------------------------------------------
# Outlier Detection
# ---------------------------------------------------------------------------

def outlier_flags(
    respondent_composite: float,
    respondent_role: Optional[str],
) -> List[str]:
    """
    Return flags if the respondent is a significant outlier vs their cohort.
    """
    z = composite_zscore(respondent_composite, respondent_role)
    if z is None:
        return []

    flags: List[str] = []

    if z <= -ZSCORE_OUTLIER_THRESHOLD:
        flags.append(
            f"Pessimism Outlier: this respondent scores {abs(z):.1f} standard deviations "
            f"below their {respondent_role or 'peer'} cohort. "
            "Validate whether this reflects genuine operational insight or reporting bias."
        )
    elif z >= ZSCORE_OUTLIER_THRESHOLD:
        flags.append(
            f"Optimism Outlier: this respondent scores {z:.1f} standard deviations "
            f"above their {respondent_role or 'peer'} cohort. "
            "High optimism without corroborating evidence is an 'Overconfidence Candidate' — "
            "probe for specific artifacts before accepting the self-assessment at face value."
        )

    return flags


# ---------------------------------------------------------------------------
# Z-Score Interpretation (text — no LLM)
# ---------------------------------------------------------------------------

def interpret_zscore(z: Optional[float], role: Optional[str]) -> Optional[str]:
    if z is None:
        return None

    cohort_str = f"{role} cohort" if role else "benchmark population"

    if z >= 1.5:
        return (
            f"This respondent sits {z:.1f} SD above the {cohort_str}. "
            "Treat high self-ratings with skepticism unless supported by operational artifacts. "
            "This is a candidate for overconfidence recalibration."
        )
    if z >= 0.5:
        return (
            f"Modestly above average for the {cohort_str} (+{z:.1f} SD). "
            "Consistent with a well-structured AI program — verify with artifact evidence."
        )
    if z >= -0.5:
        return (
            f"Scores are close to the {cohort_str} median ({z:+.1f} SD). "
            "No significant outlier behavior detected."
        )
    if z >= -1.5:
        return (
            f"Modestly below average for the {cohort_str} ({z:.1f} SD). "
            "Indicates area(s) where this organization may be lagging peers — "
            "prioritize for remediation planning."
        )
    return (
        f"This respondent sits {abs(z):.1f} SD below the {cohort_str}. "
        "Significant pessimism relative to peers — either genuine underperformance "
        "or a highly critical respondent. Cross-reference with other respondent data."
    )


# ---------------------------------------------------------------------------
# Benchmark Note Generator
# ---------------------------------------------------------------------------

def build_benchmark_note(
    role: Optional[str],
    role_avg: Optional[float],
    respondent_composite: float,
    z: Optional[float],
) -> str:
    df = load_benchmark()

    if df.empty or not BENCHMARK_CSV.exists():
        return (
            "Benchmark dataset not loaded. Run generate_benchmark.py to create "
            "the synthetic peer dataset, then restart the server."
        )

    n_total = len(df)

    if role and z is not None and role_avg is not None:
        n_role = len(df[df[ROLE_COL] == role])
        return (
            f"Compared against {n_role} {role} respondents in a {n_total}-person "
            f"synthetic benchmark. Respondent composite ({respondent_composite:.2f}) vs "
            f"role avg ({role_avg:.2f}). Z-score: {z:+.2f}."
        )

    return (
        f"Benchmark contains {n_total} synthetic respondents across 6 roles. "
        "Role-specific comparison unavailable — respondent_role not provided in payload."
    )


# ---------------------------------------------------------------------------
# Top-Level: Generate HybridAnalystSummary
# ---------------------------------------------------------------------------

def generate_hybrid_summary(
    payload: AssessmentPayload,
    analysis: AnalysisResponse,
) -> HybridAnalystSummary:
    """
    Compute all statistical benchmarking for one respondent.
    Called after analyze_assessment() in routes.py.
    """
    role = payload.respondent_role.value if payload.respondent_role else None

    # Build respondent score dict from dimension summaries
    respondent_scores: Dict[str, float] = {
        d.category: d.avg_score
        for d in analysis.dimensions
        if d.avg_score is not None
    }

    # Composite stats
    composite     = analysis.overall.composite_score
    role_avg      = role_composite_average(role) if role else None
    z             = composite_zscore(composite, role)
    z_interp      = interpret_zscore(z, role)

    # Outlier flags
    o_flags = outlier_flags(composite, role)

    # Perception gaps
    p_gaps: List[str] = []
    if role and respondent_scores:
        p_gaps = detect_perception_gaps(role, respondent_scores)

    # Benchmark note
    note = build_benchmark_note(role, role_avg, composite, z)

    return HybridAnalystSummary(
        role_compared_to=role,
        role_avg_composite=role_avg,
        respondent_zscore=z,
        zscore_interpretation=z_interp,
        perception_gaps=p_gaps,
        outlier_flags=o_flags,
        benchmark_note=note,
    )
