"""Generate small, synthetic ServiceNow-style exports for demos and tests.

Writes CSVs into ../data/samples/. Everything is fake — the tool refuses to
ship real ticket data for obvious privacy reasons.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUPS = ["Service Desk", "Network Ops", "Windows Platform", "Database", "Identity", "End User Compute"]
CATEGORIES_INC = ["Access", "Hardware", "Software", "Network", "Email", "Printer"]
CATEGORIES_REQ = ["Account creation", "Software install", "Access request", "Hardware request"]
CATEGORIES_CHG = ["Patch", "Config", "Release", "Firewall rule"]
PRIORITIES = ["1 - Critical", "2 - High", "3 - Moderate", "4 - Low"]

def _dt(start: datetime, max_days: int = 90) -> datetime:
    return start + timedelta(minutes=random.randint(0, max_days * 24 * 60))


def make_incidents(n: int = 350) -> pd.DataFrame:
    start = datetime(2026, 1, 1)
    rows = []
    for i in range(n):
        opened = _dt(start)
        pri = random.choices(PRIORITIES, weights=[1, 4, 10, 5])[0]
        target_min = {"1 - Critical": 240, "2 - High": 480, "3 - Moderate": 2880, "4 - Low": 10080}[pri]
        resolved = opened + timedelta(minutes=int(random.gauss(target_min * 0.7, target_min * 0.4)))
        cat = random.choice(CATEGORIES_INC)
        rows.append({
            "Number": f"INC{100000 + i}",
            "Short description": f"{cat} issue for user {random.randint(1,500)}",
            "Description": f"User reports {cat.lower()} problem. Error observed at login. Restart attempted without success.",
            "Category": cat,
            "Priority": pri,
            "State": "Closed",
            "Assignment group": random.choice(GROUPS),
            "Opened at": opened.strftime("%Y-%m-%d %H:%M:%S"),
            "Resolved at": resolved.strftime("%Y-%m-%d %H:%M:%S"),
            "Closed at": (resolved + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "Resolution code": random.choice(["Resolved by IT", "Resolved by caller", "User education"]),
            "Resolution notes": "Password reset performed and user confirmed access restored." if random.random() > 0.3 else None,
        })
    return pd.DataFrame(rows)


def make_requests(n: int = 200) -> pd.DataFrame:
    start = datetime(2026, 1, 1)
    rows = []
    for i in range(n):
        opened = _dt(start)
        cat = random.choice(CATEGORIES_REQ)
        rows.append({
            "Number": f"RITM{200000 + i}",
            "Short description": f"{cat} for user {random.randint(1,500)}",
            "Description": f"Standard {cat.lower()} following the usual workflow.",
            "Category": cat,
            "Priority": "3 - Moderate",
            "State": "Closed Complete",
            "Assignment group": random.choice(GROUPS),
            "Opened at": opened.strftime("%Y-%m-%d %H:%M:%S"),
            "Resolved at": (opened + timedelta(hours=random.randint(1, 48))).strftime("%Y-%m-%d %H:%M:%S"),
            "Resolution code": "Fulfilled",
            "Resolution notes": "Request completed as per standard procedure.",
        })
    return pd.DataFrame(rows)


def make_changes(n: int = 80) -> pd.DataFrame:
    start = datetime(2026, 1, 1)
    rows = []
    for i in range(n):
        opened = _dt(start)
        cat = random.choice(CATEGORIES_CHG)
        rows.append({
            "Number": f"CHG{300000 + i}",
            "Short description": f"{cat} change in {random.choice(GROUPS)}",
            "Description": f"Planned {cat.lower()} change following CAB approval.",
            "Category": cat,
            "Priority": random.choice(PRIORITIES),
            "State": "Closed",
            "Assignment group": random.choice(GROUPS),
            "Opened at": opened.strftime("%Y-%m-%d %H:%M:%S"),
            "Resolved at": (opened + timedelta(hours=random.randint(2, 72))).strftime("%Y-%m-%d %H:%M:%S"),
            "Resolution code": "Successful",
            "Resolution notes": "Change implemented per plan. Smoke tests passed.",
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    make_incidents().to_csv(OUT_DIR / "incidents_sample.csv", index=False)
    make_requests().to_csv(OUT_DIR / "requests_sample.csv", index=False)
    make_changes().to_csv(OUT_DIR / "changes_sample.csv", index=False)
    print(f"Wrote sample CSVs to {OUT_DIR}")
