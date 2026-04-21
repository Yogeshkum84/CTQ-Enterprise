"""Central configuration for the Ticket Analyser.

All paths and tunables live here so the rest of the codebase stays small.
Override via environment variables or a user-provided YAML.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2].parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "tickets.db"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"


@dataclass
class QualityRules:
    """Heuristic weights used to score ticket quality (0-100)."""

    short_description_min_words: int = 5
    description_min_words: int = 15
    require_category: bool = True
    require_assignment_group: bool = True
    require_resolution_notes: bool = True
    # Scoring weights — must sum to 100
    weights: Dict[str, int] = field(default_factory=lambda: {
        "short_description": 15,
        "description": 20,
        "category": 10,
        "assignment_group": 10,
        "priority": 10,
        "resolution_notes": 20,
        "closure_code": 15,
    })


@dataclass
class SLAConfig:
    """Default SLA minutes per priority. Override from org data."""

    response_minutes: Dict[str, int] = field(default_factory=lambda: {
        "1 - Critical": 15,
        "2 - High": 60,
        "3 - Moderate": 240,
        "4 - Low": 1440,
    })
    resolution_minutes: Dict[str, int] = field(default_factory=lambda: {
        "1 - Critical": 240,
        "2 - High": 480,
        "3 - Moderate": 2880,
        "4 - Low": 10080,
    })


@dataclass
class Settings:
    data_dir: Path = DEFAULT_DATA_DIR
    db_path: Path = DEFAULT_DB_PATH
    output_dir: Path = DEFAULT_OUTPUT_DIR
    quality: QualityRules = field(default_factory=QualityRules)
    sla: SLAConfig = field(default_factory=SLAConfig)
    # Columns expected from ServiceNow export (lower_snake_case after normalisation)
    expected_columns: List[str] = field(default_factory=lambda: [
        "number", "short_description", "description", "category", "subcategory",
        "priority", "state", "assignment_group", "assigned_to", "opened_at",
        "resolved_at", "closed_at", "sla_due", "resolution_code",
        "resolution_notes", "caller_id", "ticket_type",
    ])

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)


def load_settings(path: str | os.PathLike | None = None) -> Settings:
    """Load settings from YAML if available, otherwise use defaults."""
    settings = Settings()
    if path and Path(path).exists():
        data = yaml.safe_load(Path(path).read_text()) or {}
        if "data_dir" in data:
            settings.data_dir = Path(data["data_dir"]).expanduser()
        if "db_path" in data:
            settings.db_path = Path(data["db_path"]).expanduser()
        if "output_dir" in data:
            settings.output_dir = Path(data["output_dir"]).expanduser()
        if "quality" in data:
            q = data["quality"]
            settings.quality.weights.update(q.get("weights", {}))
        if "sla" in data:
            s = data["sla"]
            settings.sla.response_minutes.update(s.get("response_minutes", {}))
            settings.sla.resolution_minutes.update(s.get("resolution_minutes", {}))
    settings.ensure_dirs()
    return settings
