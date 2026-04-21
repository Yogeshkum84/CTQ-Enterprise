"""Emit a concise Markdown executive summary alongside the HTML dashboard."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_markdown_report(tickets: pd.DataFrame, automation: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    lines: list[str] = []
    lines.append("# IT Ticket Quality Report\n")
    lines.append(f"_Generated: {pd.Timestamp.now():%Y-%m-%d %H:%M}_\n")

    lines.append("## Executive summary\n")
    lines.append(f"- Total tickets analysed: **{len(tickets):,}**")
    if "quality_score" in tickets:
        lines.append(f"- Average quality score: **{tickets['quality_score'].mean():.1f} / 100**")
    if "sla_breached" in tickets:
        lines.append(f"- SLA breach rate: **{tickets['sla_breached'].mean() * 100:.1f}%**")
    if "resolution_minutes" in tickets:
        lines.append(f"- Median resolution time: **{tickets['resolution_minutes'].median():.0f} min**")
    lines.append("")

    if "quality_band" in tickets:
        lines.append("## Quality bands\n")
        band_tbl = tickets["quality_band"].value_counts(dropna=False).to_frame("tickets")
        lines.append(band_tbl.to_markdown())
        lines.append("")

    if automation is not None and not automation.empty:
        lines.append("## Top automation candidates\n")
        show = automation.head(10)[[
            "ticket_type", "issue_cluster", "volume", "median_minutes", "automation_score",
        ]]
        lines.append(show.to_markdown(index=False))
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
