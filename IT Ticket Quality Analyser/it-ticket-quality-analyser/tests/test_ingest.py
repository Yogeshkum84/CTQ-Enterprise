from io import StringIO

import pandas as pd

from ticket_analyser.ingest.loader import normalise_columns


def test_normalise_columns():
    cols = ["Short description", "Assignment Group", "Opened at", "resolved_at"]
    assert normalise_columns(cols) == [
        "short_description", "assignment_group", "opened_at", "resolved_at",
    ]


def test_load_tickets_csv(tmp_path):
    from ticket_analyser.ingest.loader import load_tickets

    csv = StringIO()
    df = pd.DataFrame({
        "Number": ["INC1", "INC2"],
        "Short description": ["a b c d e", "issue"],
        "Opened at": ["2026-01-01 10:00:00", "2026-01-02 11:00:00"],
    })
    p = tmp_path / "t.csv"
    df.to_csv(p, index=False)

    out = load_tickets(p, ticket_type="Incident")
    assert list(out.columns[:3]) == ["number", "short_description", "opened_at"]
    assert out["ticket_type"].iloc[0] == "Incident"
    assert pd.api.types.is_datetime64_any_dtype(out["opened_at"])
