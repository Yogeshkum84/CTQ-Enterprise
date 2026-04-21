"""Ticket quality scoring.

The score is a transparent, weighted heuristic. Each rule returns 0..1 and is
multiplied by its configured weight. Total is 0..100.
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

from ..config import QualityRules


def _word_count(s: object) -> int:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return 0
    return len(str(s).split())


def _rule_scores(row: pd.Series, rules: QualityRules) -> Dict[str, float]:
    short_words = _word_count(row.get("short_description"))
    desc_words = _word_count(row.get("description"))
    res_words = _word_count(row.get("resolution_notes"))

    return {
        "short_description": min(1.0, short_words / rules.short_description_min_words),
        "description": min(1.0, desc_words / rules.description_min_words),
        "category": 1.0 if pd.notna(row.get("category")) else 0.0,
        "assignment_group": 1.0 if pd.notna(row.get("assignment_group")) else 0.0,
        "priority": 1.0 if pd.notna(row.get("priority")) else 0.0,
        "resolution_notes": min(1.0, res_words / 10) if pd.notna(row.get("resolution_notes")) else 0.0,
        "closure_code": 1.0 if pd.notna(row.get("resolution_code")) else 0.0,
    }


def score_quality(df: pd.DataFrame, rules: QualityRules | None = None) -> pd.DataFrame:
    """Return a copy of ``df`` enriched with per-rule and total quality scores."""
    rules = rules or QualityRules()
    weights = rules.weights
    total_weight = sum(weights.values()) or 1

    records: list[dict] = []
    for _, row in df.iterrows():
        rs = _rule_scores(row, rules)
        weighted = {k: rs[k] * weights.get(k, 0) for k in rs}
        total = sum(weighted.values()) * 100 / total_weight
        records.append({f"q_{k}": round(v, 2) for k, v in rs.items()} | {"quality_score": round(total, 2)})

    scores = pd.DataFrame(records, index=df.index)
    out = pd.concat([df, scores], axis=1)
    out["quality_band"] = pd.cut(
        out["quality_score"],
        bins=[-0.01, 40, 70, 85, 100],
        labels=["Poor", "Fair", "Good", "Excellent"],
    )
    return out
