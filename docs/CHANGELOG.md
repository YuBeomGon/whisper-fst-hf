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
- Completed P4 Normalization / Protection Layer with NFC normalization, structured protected spans, external span protection, restore roundtrip, and tests.
- Completed P5 Synthetic N-best WFST Composition MVP with a Pynini-independent phrase-rule fallback engine, deterministic overlap handling, optional/obligatory semantics, fallback trace, and tests.
- Completed P6 Correction Safety / Trace / Domain Gating with domain gate, margin decision, JSON traces, protected span ordering, free-talk safety smoke, and tests.
- Completed P7 Hugging Face Whisper N-best Extractor with mocked HF generation conversion, score metadata, N-best diversity report, CLI, config, and tests.
- Completed P8 HF N-best Targetability Probe with CER/WER oracle metrics, domain oracle, seed wrong-surface ratios, leakage policy report, CLI, and tests.
- Completed P9 Evaluation Harness with manifest validation, CER/WER, domain/oracle/safety metrics, A/B/C/D report, CLI, and tests.
- Completed P10 End-to-End Offline MVP Run with synthetic pipeline, correction trace output, evaluation report, checksum manifest, no-production-claim report, CLI, and tests.
- Completed P11 Calibration / Rule Tuning with hard-gate selection, synthetic best config report, freeze checksums, config metadata, CLI, and tests.
