# Contributing

Thanks for wanting to help! A few ground rules to keep things smooth.

## Getting set up

```bash
git clone https://github.com/Yogeshkum84/it-ticket-quality-analyser.git
cd it-ticket-quality-analyser
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Workflow

1. Fork the repo and create a feature branch from `main`.
2. Follow the existing code style (`ruff check src tests` should pass).
3. Add tests for any new behaviour (`pytest -q`).
4. Open a pull request describing the change and the motivation.

## What to contribute

Good first issues are tagged `good first issue`. Ideas we'd love help on:

- Additional ticket-quality heuristics
- Alternative clustering (HDBSCAN, BERT embeddings)
- A Power BI `.pbit` template bound to the SQLite store
- Docker packaging

## Reporting bugs

Open an issue with:

- A minimal, anonymised CSV snippet that reproduces the problem
- The full stack trace
- Your Python version and OS

Please never include real ticket data or personally identifying information.

## Code of conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
