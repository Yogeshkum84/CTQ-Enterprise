"""Change risk model.

Joins Change records with follow-on Incidents by assignment_group within a
configurable window to estimate the empirical probability that a change
triggers an incident. A simple logistic regression can optionally be fitted
when enough historical data is available.
"""
from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd


def _mark_incident_followups(
    changes: pd.DataFrame,
    incidents: pd.DataFrame,
    window_hours: int = 72,
) -> pd.Series:
    """Return a boolean Series aligned to ``changes`` — True if a related
    incident was opened within ``window_hours`` on the same assignment_group."""
    window = timedelta(hours=window_hours)
    out = pd.Series(False, index=changes.index)
    if "assignment_group" not in changes.columns or "assignment_group" not in incidents.columns:
        return out

    inc_by_group = {
        g: sub["opened_at"].dropna().sort_values().to_numpy()
        for g, sub in incidents.groupby("assignment_group")
    }
    for idx, row in changes.iterrows():
        grp = row.get("assignment_group")
        opened = row.get("resolved_at") or row.get("opened_at")
        if pd.isna(opened) or grp not in inc_by_group:
            continue
        arr = inc_by_group[grp]
        mask = (arr >= np.datetime64(opened)) & (arr <= np.datetime64(opened + window))
        out.loc[idx] = bool(mask.any())
    return out


def change_risk_scores(
    df: pd.DataFrame,
    *,
    window_hours: int = 72,
) -> pd.DataFrame:
    """Return per-change risk data augmented with an empirical risk score 0..1."""
    changes = df[df["ticket_type"].str.lower() == "change"].copy()
    incidents = df[df["ticket_type"].str.lower() == "incident"].copy()
    if changes.empty:
        return changes

    changes["triggered_incident"] = _mark_incident_followups(changes, incidents, window_hours)

    # Empirical rate by (category, assignment_group)
    rate = (
        changes.groupby(["category", "assignment_group"])["triggered_incident"]
        .mean()
        .rename("risk_rate")
        .reset_index()
    )
    changes = changes.merge(rate, on=["category", "assignment_group"], how="left")
    changes["risk_score"] = changes["risk_rate"].fillna(0.0).clip(0, 1).round(3)
    return changes
