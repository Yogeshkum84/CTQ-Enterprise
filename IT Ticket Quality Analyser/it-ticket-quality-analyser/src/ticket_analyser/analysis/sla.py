"""SLA adherence: compute response / resolution breach against configured targets."""
from __future__ import annotations

import pandas as pd

from ..config import SLAConfig


def _minutes_between(a: pd.Series, b: pd.Series) -> pd.Series:
    return (b - a).dt.total_seconds() / 60.0


def evaluate_sla(df: pd.DataFrame, sla: SLAConfig | None = None) -> pd.DataFrame:
    """Add ``resolution_minutes``, ``sla_target_resolution_minutes`` and
    ``sla_breached`` columns. If the required date columns are missing the
    function degrades gracefully and leaves the outputs as NA."""
    sla = sla or SLAConfig()
    out = df.copy()

    if {"opened_at", "resolved_at"}.issubset(out.columns):
        out["resolution_minutes"] = _minutes_between(out["opened_at"], out["resolved_at"])
    else:
        out["resolution_minutes"] = pd.NA

    if "priority" in out.columns:
        out["sla_target_resolution_minutes"] = out["priority"].map(sla.resolution_minutes)
    else:
        out["sla_target_resolution_minutes"] = pd.NA

    out["sla_breached"] = (
        out["resolution_minutes"].astype("Float64") > out["sla_target_resolution_minutes"].astype("Float64")
    )
    return out
