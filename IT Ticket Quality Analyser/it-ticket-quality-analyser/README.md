<!-- markdownlint-disable MD033 MD041 -->
<h1 align="center">IT Ticket Quality Analyser</h1>

<p align="center">
  <em>Local-first, open-source analytics for ServiceNow Incident, Request, Task &amp; Change tickets.</em>
</p>

<p align="center">
  <a href="#"><img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue.svg"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
  <a href="#"><img alt="Status" src="https://img.shields.io/badge/status-beta-orange.svg"></a>
  <a href="#-support-the-project"><img alt="Donate" src="https://img.shields.io/badge/%E2%9D%A4%20support-buy%20me%20a%20coffee-ff69b4"></a>
</p>

---

## What it does

Feed it a ServiceNow CSV/XLSX export and it will:

1. **Score ticket quality** (short description, description, categorisation, closure notes, etc.) with a transparent weighted rubric.
2. **Evaluate SLA adherence** per priority.
3. **Cluster issues & requests** (TF-IDF + MiniBatchKMeans) to surface the real repeat offenders.
4. **Rank automation candidates** from those clusters.
5. **Model change risk** — which change categories empirically trigger follow-on incidents.
6. **Persist everything locally** in a SQLite database so week-over-week trends accumulate.
7. **Emit a standalone HTML dashboard** (Plotly, no server) and a short Markdown executive report.

Everything runs on your machine. Nothing leaves the box.

---

## Install

```bash
# Option A — as a user
pip install -e .

# Option B — just the runtime deps
pip install -r requirements.txt
```

Requires Python 3.10+.

## Quick start

```bash
# Analyse a single export (CSV or XLSX)
ticket-analyser analyse ./data/incidents_2026q1.csv

# Or point it at a folder of exports (Incident / Request / Task / Change)
ticket-analyser analyse ./data/samples/
```

Outputs land in `./output/`:

- `output/dashboard.html` — interactive dashboard (open in any browser)
- `output/report.md` — executive summary
- `data/tickets.db` — SQLite store (retained across runs for trending)

### Using the Python API

```python
from ticket_analyser.pipeline import run

result = run("data/samples/")
print(result.automation.head())
result.dashboard_path  # Path to the HTML dashboard
```

### Configuration (optional)

Drop a `config.yml` next to your data and pass `--config config.yml`:

```yaml
data_dir: ./data
db_path:  ./data/tickets.db
output_dir: ./output
quality:
  weights:
    short_description: 15
    description: 20
    category: 10
    assignment_group: 10
    priority: 10
    resolution_notes: 20
    closure_code: 15
sla:
  resolution_minutes:
    "1 - Critical": 240
    "2 - High": 480
    "3 - Moderate": 2880
    "4 - Low": 10080
```

---

## How it works

See [`docs/APPROACH.md`](docs/APPROACH.md) for the end-to-end design, scoring rubric, clustering model, and change-risk methodology. Short version:

```
ServiceNow CSV/XLSX  ──►  Normalise  ──►  Quality score  ──►  SLA eval
                                                        └──►  Issue clusters (TF-IDF + KMeans)
                                                        └──►  Automation score
                                                        └──►  Change risk (empirical)
                                                                      │
                            SQLite (tickets.db)  ◄──── persist ◄──────┤
                            HTML dashboard + MD report  ◄──── render ◄─┘
```

---

## Project layout

```
it-ticket-quality-analyser/
├─ src/ticket_analyser/
│  ├─ ingest/       # CSV / XLSX loaders, column normalisation
│  ├─ analysis/     # quality, sla, trends, automation, change_risk
│  ├─ dashboard/    # standalone HTML dashboard
│  ├─ reports/      # Markdown executive summary
│  ├─ db/           # SQLite persistence
│  ├─ config.py     # settings + YAML loader
│  ├─ pipeline.py   # one-call end-to-end runner
│  └─ cli.py        # `ticket-analyser` command
├─ tests/            # pytest unit tests
├─ docs/             # APPROACH, DATA_DICTIONARY, screenshots
├─ examples/         # sample notebooks and usage recipes
└─ data/samples/     # small synthetic exports for the smoke test
```

---

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```

---

## Roadmap

- Power BI dataset export (`.pbit` template) driven off the same SQLite store
- Optional Streamlit UI for interactive drill-down
- Pluggable NLP backend (swap TF-IDF for Sentence-Transformers when offline embeddings are available)
- Incident-change causal inference with counterfactual modelling

---

## Contributing

Issues, feature requests and PRs are all welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md) first.

## License

[MIT](LICENSE) — free for personal and commercial use.

---

## ❤️ Support the project

If this tool saves you time, please consider buying me a coffee. It genuinely keeps the weekends-and-evenings development going.

<table align="center">
  <tr>
    <td align="center">
      <a href="docs/assets/donate-qr.png">
        <img src="docs/assets/donate-qr.png" alt="Scan to donate" width="180" />
      </a>
      <br/>
      <sub>Scan to donate · any amount appreciated</sub>
    </td>
    <td align="center">
      <p><strong>Prefer a button?</strong></p>
      <a href="https://monzo.me/yogeshkumar36?h=_Ye7K0">
        <img alt="Donate" src="https://img.shields.io/badge/%E2%98%95%20Buy%20me%20a%20coffee-Donate-ff5e5b?style=for-the-badge" />
      </a>
      <br/><br/>
      <sub>100% optional. Thank you 🙏</sub>
    </td>
  </tr>
</table>

<!--
Donation link is attached to the QR image and the badge above rather than
printed in-line, as requested.
-->
