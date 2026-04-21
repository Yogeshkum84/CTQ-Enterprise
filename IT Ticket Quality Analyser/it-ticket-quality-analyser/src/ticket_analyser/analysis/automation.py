"""Identify automation candidates from Request/Incident patterns.

Heuristic: a cluster is an automation candidate when it is high-volume,
low-variance in category, short-resolution, and has high quality notes.
"""
from __future__ import annotations

import pandas as pd


def automation_candidates(
    df: pd.DataFrame,
    *,
    min_volume: int = 30,
    max_median_minutes: float = 240.0,
) -> pd.DataFrame:
    """Return a ranked frame of automation opportunities."""
    required = {"issue_cluster", "ticket_type"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing columns for automation scoring: {required - set(df.columns)}")

    base = df[df["issue_cluster"] >= 0]
    g = base.groupby(["ticket_type", "issue_cluster"]).agg(
        volume=("issue_cluster", "size"),
        median_minutes=("resolution_minutes", "median"),
        distinct_categories=("category", pd.Series.nunique),
        distinct_groups=("assignment_group", pd.Series.nunique),
        avg_quality=("quality_score", "mean"),
    ).reset_index()

    g = g[(g["volume"] >= min_volume) & (g["median_minutes"].fillna(1e9) <= max_median_minutes)]
    # Score: high volume, low variance, low resolution time → good automation
    g["automation_score"] = (
        g["volume"].rank(pct=True) * 50
        + (1 / (1 + g["distinct_categories"])) * 25
        + (1 / (1 + g["median_minutes"].fillna(240) / 240)) * 25
    ).round(2)
    return g.sort_values("automation_score", ascending=False).reset_index(drop=True)
