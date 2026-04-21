"""End-to-end analysis pipeline exposed as a single callable."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from .analysis import (
    automation_candidates,
    change_risk_scores,
    cluster_issues,
    evaluate_sla,
    score_quality,
)
from .config import Settings, load_settings
from .dashboard import render_dashboard
from .db import TicketStore
from .ingest import load_folder, load_tickets
from .reports import write_markdown_report


@dataclass
class PipelineResult:
    tickets: pd.DataFrame
    automation: pd.DataFrame
    change_risk: pd.DataFrame
    dashboard_path: Path
    report_path: Path
    batch_id: int


def run(
    source: str | Path,
    *,
    settings: Optional[Settings] = None,
    n_clusters: int = 12,
) -> PipelineResult:
    """Run the full pipeline against a file or folder of exports."""
    settings = settings or load_settings()
    settings.ensure_dirs()

    src = Path(source)
    df = load_folder(src) if src.is_dir() else load_tickets(src)

    df = score_quality(df, settings.quality)
    df = evaluate_sla(df, settings.sla)
    cluster = cluster_issues(df, n_clusters=n_clusters)
    df = df.merge(
        cluster.df[["issue_cluster"]] if "issue_cluster" in cluster.df.columns else pd.DataFrame(),
        how="left", left_index=True, right_index=True,
    ) if "issue_cluster" in cluster.df.columns else df
    # Simpler: replace df with cluster.df (keeps all original columns)
    df = cluster.df

    automation = automation_candidates(df) if "issue_cluster" in df.columns and df["issue_cluster"].ge(0).any() else pd.DataFrame()
    change_risk = change_risk_scores(df) if "ticket_type" in df.columns else pd.DataFrame()

    dash_path = render_dashboard(df, cluster, automation, settings.output_dir / "dashboard.html")
    rep_path = write_markdown_report(df, automation, settings.output_dir / "report.md")

    store = TicketStore(settings.db_path)
    batch_id = store.save_batch(df, source=str(src))

    return PipelineResult(
        tickets=df,
        automation=automation,
        change_risk=change_risk,
        dashboard_path=dash_path,
        report_path=rep_path,
        batch_id=batch_id,
    )
