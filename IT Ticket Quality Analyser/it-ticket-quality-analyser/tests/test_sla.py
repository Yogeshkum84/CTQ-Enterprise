import pandas as pd

from ticket_analyser.analysis.sla import evaluate_sla


def test_evaluate_sla_breach():
    df = pd.DataFrame({
        "priority": ["1 - Critical", "4 - Low"],
        "opened_at": pd.to_datetime(["2026-01-01 10:00:00", "2026-01-01 10:00:00"]),
        "resolved_at": pd.to_datetime(["2026-01-01 18:00:00", "2026-01-01 10:30:00"]),
    })
    out = evaluate_sla(df)
    # 8h on Critical (240 min target) -> breach
    assert bool(out["sla_breached"].iloc[0]) is True
    # 30 min on Low (10080 min target) -> no breach
    assert bool(out["sla_breached"].iloc[1]) is False
