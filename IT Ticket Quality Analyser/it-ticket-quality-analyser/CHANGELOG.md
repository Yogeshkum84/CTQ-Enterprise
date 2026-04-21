# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-04-14

### Added
- Initial public release.
- CSV / XLSX ingestion from ServiceNow exports (Incident, Request, Task, Change).
- Weighted quality scoring and quality bands.
- SLA adherence evaluation against configurable priority targets.
- Issue clustering via TF-IDF + MiniBatchKMeans.
- Automation-candidate ranking.
- Empirical change-risk scoring (change → follow-on incidents).
- Standalone HTML dashboard (Plotly) and Markdown executive report.
- Local SQLite store for week-over-week trending.
- CLI (`ticket-analyser analyse ...`) and Python API.
