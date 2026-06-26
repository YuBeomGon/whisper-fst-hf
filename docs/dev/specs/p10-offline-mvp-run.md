# P10 End-to-End Offline MVP Run Spec

Date: 2026-06-26

Branch: `wbs/P10-offline-mvp-run`

## Goal

P10은 selected sample에서 N-best artifact, targetability, correction trace, evaluation report를 한 번에
재현하는 offline MVP pipeline을 구현한다.

현재 repository에는 real audio/model artifact가 없으므로 P10은 committed synthetic fixtures 기반으로 실행한다.
생성 artifact는 `outputs/` 아래 ignored path에 쓰고, committed report/manifest에는 path와 checksum만 기록한다.

## Pipeline Steps

1. Load N-best artifact.
2. Run P8 targetability probe.
3. Run P6 safety correction with seed rules.
4. Write correction trace artifact under `outputs/`.
5. Run P9 evaluation fixture.
6. Write report and manifest with checksums.

## Outputs

- `scripts/run_offline_pipeline.py`
- `docs/reports/experiments/offline_mvp_run.md`
- `docs/reports/experiments/offline_mvp_manifest.json`
- ignored generated artifacts under `outputs/offline_mvp/`

## Non-goals

- large-scale batch processing
- serving API
- model fine-tuning
- production-quality claim

## Acceptance Criteria

- all input/output artifact paths and checksums are recorded.
- P8 targetability conclusion and risk flag are reflected.
- correction trace is reproducible from committed config and fixtures.
- repository contains reports/manifests only, not large generated artifacts.
- no full-quality production claim is made.
- `uv run --group dev pytest -q` passes.
- `uv run --group dev ruff check .` passes.
