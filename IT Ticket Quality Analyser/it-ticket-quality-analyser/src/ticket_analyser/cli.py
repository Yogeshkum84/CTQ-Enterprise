"""Command-line interface: ``ticket-analyser analyse <path>``."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .config import load_settings
from .pipeline import run


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ticket-analyser", description="Local IT ticket quality & trends analyser")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyse", help="Run the full analysis pipeline")
    a.add_argument("source", help="CSV/XLSX file or folder of ServiceNow exports")
    a.add_argument("--config", help="Path to YAML config", default=None)
    a.add_argument("--clusters", type=int, default=12, help="Number of issue clusters")
    a.add_argument("--verbose", "-v", action="store_true")

    sub.add_parser("version", help="Print version and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd == "version":
        print(__version__)
        return 0

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = load_settings(args.config)
    result = run(args.source, settings=settings, n_clusters=args.clusters)
    print(f"Processed {len(result.tickets):,} tickets (batch_id={result.batch_id}).")
    print(f"Dashboard: {Path(result.dashboard_path).resolve()}")
    print(f"Report:    {Path(result.report_path).resolve()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
