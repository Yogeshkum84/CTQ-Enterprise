# Security policy

The Ticket Analyser runs entirely on your machine — **no ticket data is sent off the device**. That said, please follow these guidelines.

## Reporting a vulnerability

If you believe you have found a security issue, please open a **private** security advisory on GitHub or email the maintainer rather than filing a public issue. We will respond within 14 days.

## Scope

- Arbitrary-code-execution paths in ingestion or templating
- Path-traversal when loading a folder of exports
- Dependency vulnerabilities flagged by `pip-audit`

## Out of scope

- Anything requiring access to the user's machine or filesystem
- Self-XSS in locally-opened HTML dashboards (the output is trust-own-machine by design)
