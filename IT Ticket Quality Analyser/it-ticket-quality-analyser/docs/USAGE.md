# Usage Guide

## 1. Export from ServiceNow

From any ticket list (Incident, Request, Task, Change):

1. Apply the filter you want to analyse (e.g. "All incidents opened in the last 90 days").
2. Right-click the list header → **Export → CSV** (or **Excel**).
3. Save the file to your local `./data/` folder.

Repeat for each ticket type you want in the analysis.

## 2. Run the analyser

### One file at a time

```bash
ticket-analyser analyse ./data/incidents_q1_2026.csv
```

### A folder of exports

```bash
ticket-analyser analyse ./data/2026_w15/
```

The loader recognises `incident`, `request`, `task`, `change` in the filename and tags the `ticket_type` automatically.

### Options

```
--config FILE       YAML config with custom weights / SLA targets
--clusters N        Number of issue clusters (default 12)
-v, --verbose       Debug logging
```

## 3. Review the output

Open `output/dashboard.html` in any browser.

The dashboard is a single self-contained file — safe to email, drop into SharePoint, or open from a USB stick.

`output/report.md` gives you an executive summary suitable for pasting into a weekly update email.

## 4. Week-over-week trending

Drop each week's exports into a new folder and re-run the analyser. The SQLite store at `data/tickets.db` accumulates every batch:

```python
import pandas as pd
from ticket_analyser.db import TicketStore

store = TicketStore("data/tickets.db")
trend = store.latest_trend(freq="W")   # pandas DataFrame
```

## 5. Privacy

Nothing leaves your machine. The only remote request is to the Plotly.js CDN when you **open** the dashboard HTML. If your organisation blocks CDNs, set `include_plotlyjs="inline"` in `html_dashboard.py` — the file will be ~4MB but fully offline.
