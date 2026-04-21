"""Render a standalone, zero-backend HTML dashboard using Plotly.

Everything is inlined into a single .html file so it can be emailed,
checked in, or opened from a USB stick without a web server.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_html

from ..analysis.trends import ClusterResult


_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>IT Ticket Quality Analyser</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #f4f6fb; color: #1a2240; }}
  header {{ padding: 28px 40px; background: linear-gradient(120deg,#0c1428,#2a3a75); color:#fff; }}
  header h1 {{ margin: 0; font-size: 22px; letter-spacing: .3px; }}
  header p  {{ margin: 6px 0 0; opacity: .85; font-size: 13px; }}
  main {{ padding: 24px 40px 60px; display: grid; gap: 24px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(170px,1fr)); gap: 16px; }}
  .kpi {{ background:#fff; border-radius:14px; padding:16px 20px; box-shadow:0 1px 3px rgba(16,24,40,.08); }}
  .kpi h3 {{ margin:0; font-size:12px; letter-spacing:.8px; text-transform:uppercase; color:#566188; }}
  .kpi .v {{ font-size:26px; font-weight:600; margin-top:6px; }}
  .card {{ background:#fff; border-radius:14px; padding:16px; box-shadow:0 1px 3px rgba(16,24,40,.08); }}
  .card h2 {{ margin:0 0 8px; font-size:15px; color:#2a3a75; }}
  table {{ width:100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ padding: 6px 10px; text-align:left; border-bottom:1px solid #eef0f6; }}
  th {{ background:#f4f6fb; }}
  footer {{ padding: 14px 40px 30px; font-size:12px; color:#566188; }}
</style>
</head>
<body>
<header>
  <h1>IT Ticket Quality Analyser</h1>
  <p>Generated {timestamp} • {rows:,} tickets analysed</p>
</header>
<main>
  <section class="kpis">{kpi_html}</section>
  <section class="card"><h2>Ticket volume over time</h2>{volume_chart}</section>
  <section class="card"><h2>Quality score distribution</h2>{quality_chart}</section>
  <section class="card"><h2>SLA adherence by priority</h2>{sla_chart}</section>
  <section class="card"><h2>Top issue clusters</h2>{clusters_table}</section>
  <section class="card"><h2>Automation candidates</h2>{automation_table}</section>
</main>
<footer>Open-source • Local-first • MIT licensed</footer>
</body>
</html>
"""


def _kpi(label: str, value: str) -> str:
    return f'<div class="kpi"><h3>{label}</h3><div class="v">{value}</div></div>'


def _fig_to_html(fig: go.Figure) -> str:
    return to_html(fig, full_html=False, include_plotlyjs="cdn", config={"displayModeBar": False})


def _table(df: pd.DataFrame, max_rows: int = 15) -> str:
    if df is None or df.empty:
        return "<p><em>No data.</em></p>"
    return df.head(max_rows).to_html(index=False, border=0, classes="tbl", na_rep="-")


def render_dashboard(
    tickets: pd.DataFrame,
    cluster_result: ClusterResult,
    automation_df: pd.DataFrame | None,
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # --- KPI block -----------------------------------------------------------
    total = len(tickets)
    avg_quality = round(tickets["quality_score"].mean(), 1) if "quality_score" in tickets else 0
    breach = tickets["sla_breached"].dropna().mean() * 100 if "sla_breached" in tickets else 0
    median_res = tickets["resolution_minutes"].median() if "resolution_minutes" in tickets else 0
    kpis = "".join([
        _kpi("Total tickets", f"{total:,}"),
        _kpi("Avg quality", f"{avg_quality:.1f}/100"),
        _kpi("SLA breach rate", f"{breach:.1f}%"),
        _kpi("Median resolution", f"{median_res:.0f} min" if pd.notna(median_res) else "—"),
    ])

    # --- Charts --------------------------------------------------------------
    if "opened_at" in tickets.columns and tickets["opened_at"].notna().any():
        vol = (
            tickets.dropna(subset=["opened_at"])
            .assign(period=lambda d: d["opened_at"].dt.to_period("W").dt.to_timestamp())
            .groupby(["period", "ticket_type"], dropna=False).size().reset_index(name="count")
        )
        fig_vol = px.line(vol, x="period", y="count", color="ticket_type", markers=True)
    else:
        fig_vol = go.Figure().add_annotation(text="opened_at not available", showarrow=False)
    fig_vol.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)

    if "quality_score" in tickets:
        fig_q = px.histogram(tickets, x="quality_score", nbins=20, color="ticket_type")
    else:
        fig_q = go.Figure()
    fig_q.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)

    if {"priority", "sla_breached"}.issubset(tickets.columns):
        sla_df = (
            tickets.dropna(subset=["priority"])
            .groupby("priority")["sla_breached"].mean().fillna(0).mul(100).round(1).reset_index()
        )
        fig_sla = px.bar(sla_df, x="priority", y="sla_breached",
                         labels={"sla_breached": "Breach %"})
    else:
        fig_sla = go.Figure()
    fig_sla.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)

    # --- Cluster table ------------------------------------------------------
    if cluster_result.top_terms:
        ct = pd.DataFrame([
            {"cluster": k, "size": int(cluster_result.sizes.get(k, 0)), "top_terms": ", ".join(v)}
            for k, v in cluster_result.top_terms.items()
        ]).sort_values("size", ascending=False)
    else:
        ct = pd.DataFrame()

    html = _TEMPLATE.format(
        timestamp=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        rows=total,
        kpi_html=kpis,
        volume_chart=_fig_to_html(fig_vol),
        quality_chart=_fig_to_html(fig_q),
        sla_chart=_fig_to_html(fig_sla),
        clusters_table=_table(ct),
        automation_table=_table(automation_df) if automation_df is not None else "<p><em>No data.</em></p>",
    )
    output_path.write_text(html, encoding="utf-8")
    return output_path
