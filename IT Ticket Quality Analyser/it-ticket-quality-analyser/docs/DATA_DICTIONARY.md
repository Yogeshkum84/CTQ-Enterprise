# Data dictionary

The analyser normalises all column names to `snake_case`. If your export uses different headers, the ingest step will map them automatically — as long as they lowercase to the same string (e.g. "Short description" → `short_description`).

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| `number` | str | recommended | Ticket ID — used as primary key in the SQLite store. |
| `ticket_type` | str | yes\* | `Incident`, `Request`, `Task`, `Change`. Inferred from filename if missing. |
| `short_description` | str | yes | Drives the quality score. |
| `description` | str | recommended | Longer text, drives quality and clustering. |
| `category` | str | recommended | L1 category. Quality + automation signal. |
| `subcategory` | str | no | Reserved for future use. |
| `priority` | str | recommended | Format `"1 - Critical"`, `"2 - High"`, etc. Maps to SLA target. |
| `state` | str | no | Display only. |
| `assignment_group` | str | recommended | Used for SLA, automation, change risk. |
| `assigned_to` | str | no | Display only. |
| `opened_at` | datetime | yes | Required for trending, SLA. |
| `resolved_at` | datetime | recommended | Required for SLA resolution calc. |
| `closed_at` | datetime | no | Display only. |
| `sla_due` | datetime | no | Not used (we recompute from priority). |
| `resolution_code` | str | recommended | Drives part of quality score. |
| `resolution_notes` | str | recommended | Drives part of quality score. |
| `caller_id` | str | no | Kept for future personalisation. |

\* Either provide a `ticket_type` column or use filename conventions (`incidents_q1.csv`, `requests_2026_w15.xlsx`, etc.) — the loader infers the type from the stem.

## Computed columns (added by the pipeline)

| Column | Description |
|--------|-------------|
| `q_*` | Per-rule quality sub-scores (0..1). |
| `quality_score` | Weighted total (0..100). |
| `quality_band` | `Poor` / `Fair` / `Good` / `Excellent`. |
| `resolution_minutes` | Minutes between `opened_at` and `resolved_at`. |
| `sla_target_resolution_minutes` | Target from priority map. |
| `sla_breached` | True if actual > target. |
| `issue_cluster` | TF-IDF + KMeans label (−1 if dataset too small). |
| `risk_score` | Change-only: empirical probability of a follow-on incident. |
