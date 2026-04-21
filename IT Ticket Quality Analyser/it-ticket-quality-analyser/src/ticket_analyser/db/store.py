"""Local SQLite persistence for trend-over-time analysis.

Stores every analysed batch so a weekly drop keeps growing the warehouse.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pandas as pd


class TicketStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self):
        con = sqlite3.connect(self.path)
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _init_schema(self) -> None:
        with self._conn() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ingested_at TEXT NOT NULL,
                    source TEXT,
                    row_count INTEGER
                );
                CREATE TABLE IF NOT EXISTS tickets (
                    number TEXT,
                    batch_id INTEGER,
                    ticket_type TEXT,
                    short_description TEXT,
                    description TEXT,
                    category TEXT,
                    subcategory TEXT,
                    priority TEXT,
                    state TEXT,
                    assignment_group TEXT,
                    assigned_to TEXT,
                    opened_at TEXT,
                    resolved_at TEXT,
                    closed_at TEXT,
                    resolution_code TEXT,
                    resolution_notes TEXT,
                    quality_score REAL,
                    quality_band TEXT,
                    resolution_minutes REAL,
                    sla_breached INTEGER,
                    issue_cluster INTEGER,
                    PRIMARY KEY (number, batch_id)
                );
                CREATE INDEX IF NOT EXISTS idx_tickets_opened ON tickets(opened_at);
                CREATE INDEX IF NOT EXISTS idx_tickets_type ON tickets(ticket_type);
                """
            )

    def save_batch(self, df: pd.DataFrame, source: str = "") -> int:
        with self._conn() as con:
            cur = con.execute(
                "INSERT INTO batches (ingested_at, source, row_count) VALUES (?, ?, ?)",
                (datetime.utcnow().isoformat(timespec="seconds"), source, len(df)),
            )
            batch_id = int(cur.lastrowid)
            persisted_cols = [
                "number", "ticket_type", "short_description", "description", "category",
                "subcategory", "priority", "state", "assignment_group", "assigned_to",
                "opened_at", "resolved_at", "closed_at", "resolution_code", "resolution_notes",
                "quality_score", "quality_band", "resolution_minutes", "sla_breached",
                "issue_cluster",
            ]
            out = df.reindex(columns=persisted_cols).copy()
            out["batch_id"] = batch_id
            for col in ("opened_at", "resolved_at", "closed_at"):
                if col in out.columns:
                    out[col] = pd.to_datetime(out[col], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
            if "sla_breached" in out.columns:
                out["sla_breached"] = out["sla_breached"].astype("Int64")
            if "quality_band" in out.columns:
                out["quality_band"] = out["quality_band"].astype(str)
            out.to_sql("tickets", con, if_exists="append", index=False)
            return batch_id

    def latest_trend(self, freq: str = "W") -> pd.DataFrame:
        with self._conn() as con:
            df = pd.read_sql("SELECT ticket_type, priority, opened_at FROM tickets", con)
        df["opened_at"] = pd.to_datetime(df["opened_at"], errors="coerce")
        df = df.dropna(subset=["opened_at"])
        if df.empty:
            return df
        df["period"] = df["opened_at"].dt.to_period(freq).dt.to_timestamp()
        return df.groupby(["period", "ticket_type", "priority"]).size().rename("count").reset_index()
