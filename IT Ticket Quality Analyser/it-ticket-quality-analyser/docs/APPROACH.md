# Approach &amp; Architecture

This document describes *what* the analyser computes, *how*, and *why* the choices were made.

## Goals

1. Make it trivial to score the quality of incoming tickets so coaching cycles can be targeted, not blanket.
2. Track SLA adherence without relying on the source platform's own calculated fields (which drift between instances).
3. Surface repeat issues that *should* be automated — but aren't — so automation roadmaps are driven by data, not anecdote.
4. Spot the change categories that historically trigger incidents so the CAB has a risk signal, not just a gut feel.
5. Keep everything local, explainable, and free.

## Non-goals

- Real-time streaming from ServiceNow. A daily/weekly CSV drop is the assumed cadence.
- Hosting a multi-user web app. The dashboard is a single HTML file.
- Replacing ServiceNow Performance Analytics. The analyser is a complement — cheaper, more transparent, and tuned for coaching and automation use-cases.

## High-level pipeline

```
┌──────────────┐   ┌──────────┐   ┌─────────────────┐   ┌──────────┐
│ Export .csv  │──►│ Ingest   │──►│ Analyse         │──►│ Render    │
│ / .xlsx      │   │ (pandas) │   │ ─ quality        │   │ - HTML    │
└──────────────┘   └──────────┘   │ ─ SLA           │   │ - MD      │
                                   │ ─ clusters      │   └──────────┘
                                   │ ─ automation    │          │
                                   │ ─ change risk   │          ▼
                                   └─────────────────┘   ┌──────────┐
                                         │               │ SQLite   │
                                         └──────────────►│ trends   │
                                                         └──────────┘
```

Each stage is a single Python module under `src/ticket_analyser/` so contributors can replace or extend one stage without touching the others.

## Quality scoring

Quality is a transparent, weighted heuristic rather than a black-box model. That was a deliberate call: ITSM coaches must be able to explain *why* a ticket scored the way it did.

Per-rule signals are normalised to 0..1 and multiplied by a weight (defaults sum to 100):

| Rule | Default weight | How |
|------|----------------|-----|
| Short description length | 15 | words / `short_description_min_words` |
| Description length | 20 | words / `description_min_words` |
| Category present | 10 | 1 if non-null else 0 |
| Assignment group present | 10 | 1 if non-null else 0 |
| Priority present | 10 | 1 if non-null else 0 |
| Resolution notes | 20 | words / 10 |
| Closure/resolution code | 15 | 1 if non-null else 0 |

The final score is 0..100 and bucketed into Poor / Fair / Good / Excellent (40 / 70 / 85 cuts).

Weights are overrideable via `config.yml` — for example, organisations that enforce priority matrix reviews may down-weight `priority` and up-weight `closure_code`.

## SLA evaluation

- `resolution_minutes = resolved_at − opened_at`.
- `sla_target_resolution_minutes` = mapped from priority via the configured `SLAConfig`.
- `sla_breached` = actual > target.

The analyser intentionally *does not* use the platform's own `made_sla` field — it lets you reproduce the number from raw timestamps, which exposes errors in the source instance.

## Issue / request clustering

- Vectoriser: `TfidfVectorizer(ngram_range=(1,2), min_df=2, max_features=5000, stop_words="english")`.
- Clusterer: `MiniBatchKMeans(n_clusters=12, batch_size=256)` — chosen because it runs on 100k+ rows on a laptop in a few seconds.
- Each cluster gets the top 7 TF-IDF terms as a human-readable label.
- Very small datasets (< 20 rows) skip clustering and mark everything as `cluster = -1`.

Why not sentence embeddings? They are better but require downloading a model and a GPU-free inference path. A future optional backend is on the roadmap; the heuristic result is already good enough to find the top 10-15 repeat issues in a typical enterprise month.

## Automation candidate ranking

For each (ticket_type, cluster) we compute:

- `volume` — number of tickets in the cluster.
- `median_minutes` — half of tickets resolve below this time.
- `distinct_categories` — how fragmented the cluster is across L1 category.
- `avg_quality` — the mean quality score of the cluster.

The automation score is:

```
automation_score = 50 * percentile(volume)
                 + 25 * 1 / (1 + distinct_categories)
                 + 25 * 1 / (1 + median_minutes / 240)
```

Rationale: **high volume + low variance + short handling time** = classic automation sweet spot. We filter out anything below `min_volume=30` or above `max_median_minutes=240` to avoid suggesting automation for long, complex tickets.

## Change-risk model

A pragmatic, explainable baseline:

1. Join Change tickets with follow-on Incidents on `assignment_group` within 72 hours (configurable).
2. Per (category, assignment_group), compute the empirical fraction of changes that were followed by an incident.
3. Each change inherits that fraction as its `risk_score`.

This gives the CAB a **historical base-rate** for "changes like this one" without having to label data manually. An optional logistic regression on categorical features (priority, assignment_group, risk, CAB risk) is planned for v0.2 once enough users have labelled data.

## Local persistence

- `data/tickets.db` (SQLite) with `batches` and `tickets` tables.
- Every run appends a new `batch_id` — you can replay history or diff batches week-over-week.
- No user, no password, no server. `sqlite3` ships with Python.

## Why standalone HTML (and not a web app)?

- Zero infrastructure — attach it to an email, open from a USB stick, drop into SharePoint.
- No backend means no vulnerability surface.
- Plotly inline + CDN for Plotly.js keeps the file small (~200 KB) yet interactive.

A Power BI flavour (`.pbit`) bound to the same SQLite store is on the roadmap for teams that already standardise on Power BI.

## Extension points

Everything is a plain module — the analyser is meant to be hacked on:

- New quality rule → add to `analysis/quality.py` and register its weight in `config.QualityRules.weights`.
- New clustering backend → implement `cluster_issues`-compatible function and swap it in `pipeline.run`.
- New ticket type (e.g. Problem) → no code change; set `ticket_type` on ingest and everything downstream treats it as a first-class citizen.

## Operating the tool

```bash
# Week 1: backfill a year's data (all four types in one folder)
ticket-analyser analyse ./exports/2025_full_year/

# Weekly cadence: drop this week's exports into ./exports/2026_w15/ and re-run
ticket-analyser analyse ./exports/2026_w15/
```

The SQLite store accumulates so `report.md` and `dashboard.html` reflect the full history every time.
