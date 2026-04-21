import pandas as pd

from ticket_analyser.analysis.quality import score_quality


def test_score_quality_range():
    df = pd.DataFrame([
        {
            "short_description": "Printer is broken on floor three",
            "description": "User reports the printer on the third floor is jammed and will not print anything at all this morning.",
            "category": "Hardware",
            "assignment_group": "EUC",
            "priority": "3 - Moderate",
            "resolution_code": "Resolved by IT",
            "resolution_notes": "Replaced toner cartridge and ran cleaning cycle. User confirmed working.",
        },
        {
            "short_description": "broken",
            "description": None,
            "category": None,
            "assignment_group": None,
            "priority": None,
            "resolution_code": None,
            "resolution_notes": None,
        },
    ])
    out = score_quality(df)
    assert out["quality_score"].iloc[0] > 80
    assert out["quality_score"].iloc[1] < 20
    assert set(out["quality_band"].dropna().astype(str)) <= {"Poor", "Fair", "Good", "Excellent"}
