# Changelog

## 2026-06-26

- Added project design and WBS seed documents.
- Added AIG domain/data context reference under `docs/assets/`.
- Added design review and feasibility research records.
- Added evaluation and calibration policy for sweep, hard gate, and best config selection.
- Completed P0 Governance / Docs Scaffold.
- Completed P1 Python Scaffold / Environment.
- Added initial Python package scaffold, pytest smoke test, ruff/pytest config, and artifact ignore policy.
- Moved project design SSOT to `docs/dev/specs/project-design.md`.
- Updated WBS/design to make the current PoC HF-only.
- Added HF targetability probe to the WBS.
- Added `scripts/archive_project_snapshot.py` for timestamped docs/config/code snapshots.
- Updated WBS with Rule Source Audit, stronger P2/P5 gates, expanded evaluation manifest fields, and pure P8 targetability scope.
- Updated project snapshot archive to include small `data/` files while excluding generated data subtrees.
- Reformatted WBS phases to include branch, phase design spec, implementation plan, loop level, and ops promotion candidates.
- Completed P2 FST Backend Feasibility with a structured Pynini availability probe, CLI report writer, tests, and current-environment blocker report.
- Completed P3 Core Contracts / DTO / Config with validated DTOs, JSON/JSONL artifact IO, CSV rule IO, schema docs, backend fail-fast config, and committed fixtures.
- Completed P3.5 Rule Source Audit / Seed Rule Review with provenance audit logic, safe-only seed CSV generation, leakage/risk report, CLI, and tests.
