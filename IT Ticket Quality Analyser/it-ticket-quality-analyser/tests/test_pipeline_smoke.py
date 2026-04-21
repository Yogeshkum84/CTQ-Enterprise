"""End-to-end smoke test against the synthetic sample data."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_pipeline_runs_end_to_end(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    samples = repo / "data" / "samples"
    if not any(samples.glob("*.csv")):
        # Generate them on demand
        subprocess.check_call([sys.executable, str(repo / "examples" / "generate_sample_data.py")])

    from ticket_analyser.config import Settings
    from ticket_analyser.pipeline import run

    settings = Settings(
        data_dir=tmp_path,
        db_path=tmp_path / "tickets.db",
        output_dir=tmp_path / "output",
    )
    settings.ensure_dirs()

    result = run(samples, settings=settings, n_clusters=6)
    assert len(result.tickets) > 0
    assert result.dashboard_path.exists()
    assert result.report_path.exists()
    assert (tmp_path / "tickets.db").exists()
    assert "quality_score" in result.tickets.columns
