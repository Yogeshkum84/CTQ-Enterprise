"""Load ServiceNow CSV/XLSX exports into a clean, typed DataFrame."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

log = logging.getLogger(__name__)

_DATE_COLS = {"opened_at", "resolved_at", "closed_at", "sla_due"}


def normalise_columns(cols: Iterable[str]) -> list[str]:
    """ServiceNow exports often ship as 'Short description' / 'Assignment group'.

    We normalise to snake_case so downstream code never has to guess.
    """
    out = []
    for c in cols:
        s = re.sub(r"[^0-9a-zA-Z]+", "_", str(c).strip().lower()).strip("_")
        out.append(s)
    return out


def _read_any(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv", ".txt"}:
        sep = "\t" if suffix == ".tsv" else ","
        return pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False, na_values=[""])
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, dtype=str)
    raise ValueError(f"Unsupported file type: {suffix}")


def load_tickets(path: str | Path, ticket_type: str | None = None) -> pd.DataFrame:
    """Read an export and return a normalised DataFrame.

    ``ticket_type`` is forced onto the ``ticket_type`` column when provided so
    that combining Incident/Request/Task/Change exports keeps provenance.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    df = _read_any(path)
    df.columns = normalise_columns(df.columns)

    # Backfill provenance
    if ticket_type and "ticket_type" not in df.columns:
        df["ticket_type"] = ticket_type
    elif ticket_type:
        df["ticket_type"] = df["ticket_type"].fillna(ticket_type)

    # Parse dates where present
    for col in _DATE_COLS & set(df.columns):
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=False)

    # Strip whitespace on object columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df.loc[df[col].isin({"", "nan", "None"}), col] = pd.NA

    log.info("Loaded %s rows from %s", len(df), path.name)
    return df


def load_folder(folder: str | Path) -> pd.DataFrame:
    """Load every supported file in a folder and concatenate."""
    folder = Path(folder)
    frames = []
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() in {".csv", ".tsv", ".xlsx", ".xls"}:
            # Infer ticket_type from the filename if user named it sensibly
            stem = p.stem.lower()
            inferred = None
            for key in ("incident", "request", "task", "change"):
                if key in stem:
                    inferred = key.capitalize()
                    break
            frames.append(load_tickets(p, ticket_type=inferred))
    if not frames:
        raise FileNotFoundError(f"No ticket exports found in {folder}")
    return pd.concat(frames, ignore_index=True)
