# Environment

최종 갱신: 2026-06-26

## 1. Runtime

- Python: `>=3.11`
- Package manager: `uv`
- Source layout: `src/whisper_wfst`
- Test layout: `tests`

## 2. Setup

```bash
uv sync --group dev
```

Network-restricted 환경에서는 dependency download가 실패할 수 있다. 이 경우 이미 설치된 local Python과
pytest로 smoke test를 먼저 실행하고, dependency 설치는 별도 승인 후 진행한다.

## 3. Verification Commands

기본 후보:

```bash
uv run --group dev ruff check .
uv run --group dev pytest
git diff --check
```

scaffold 직후 최소 검증:

```bash
python -m pytest tests/test_scaffold.py -q
uv run --group dev python -c "import whisper_wfst; print(whisper_wfst.__version__)"
```

## 4. Artifact Paths

- `configs/`: 작은 config 파일
- `data/`: 작은 sample data, rule CSV, manifest
- `outputs/`: local generated artifacts, git ignored
- `outputs/archives/`: local project source snapshot archives, git ignored

대용량 audio, model checkpoint, full N-best artifact, full prediction output은 repository에 넣지 않는다.
`data/raw/`와 `data/processed/`는 generated/large data subtree로 취급한다.

## 5. Project Snapshot

문서, 설정, 코드만 압축한다.

```bash
uv run --group dev python scripts/archive_project_snapshot.py
```

출력 파일은 `outputs/archives/` 아래에 `프로젝트명_docs-config-code_YYYYMMDD_HHMMSS.tar.gz` 형식으로
생성된다.

snapshot에는 `data/`의 작은 rule/manifest 파일을 포함하지만, `data/raw/`, `data/processed/`,
`outputs/`, cache, audio/model artifact는 제외한다.

## 6. Optional Dependencies

후속 phase에서 검증한다.

- P2: Pynini/OpenFST
- P7: Hugging Face Whisper stack
- P8: HF N-best targetability probe

CTranslate2/faster-whisper integration은 현재 PoC 범위가 아니며 후속 WBS에서 별도로 판단한다.
