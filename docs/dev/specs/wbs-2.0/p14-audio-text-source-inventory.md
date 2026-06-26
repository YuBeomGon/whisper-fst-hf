# P14 Audio/Text Source Inventory Spec

Date: 2026-06-26

Branch: `wbs/v2/P14-audio-text-source-inventory`

## Goal

실제 AIG 상담원 채널 `_l` label과 audio를 file stem 기준으로 매칭하고, WBS 2.0의 leakage-safe
file-level split manifest를 만든다.

P14는 원문 label/audio 내용을 repository에 저장하지 않는다. 산출물은 path, count, exclusion reason,
checksum 같은 metadata와 aggregate report만 포함한다.

## Inputs

기본 입력:

```text
/data/MyProject/stt/aig/stt-engine/shared/annotations/*/*_l.txt
/data/MyProject/stt/aig/stt-engine/shared/debug/input/**/*_l.wav
/data/MyProject/stt/aig/stt-engine/shared/input/**/*_l.wav
```

## Matching Policy

matching key:

```text
source_stem = Path(file).stem
channel = trailing "_l"
```

audio candidate가 여러 개인 경우 우선순위:

1. label batch와 같은 path segment를 가진 audio
2. `shared/debug/input/<batch>/<stem>.wav`
3. `shared/debug/input/<stem>.wav`
4. `shared/input/<stem>.wav`
5. stable lexical first fallback

모든 candidate path는 metadata로 보존하되, downstream default audio는 `selected_audio_path`를 사용한다.

## Exclusion Policy

P14는 label parser v2가 아니므로 rough check만 한다.

초기 exclusion reason:

- `missing_audio`
- `too_short_label`
- `bad_label_read`
- `duplicate_label_stem`

too-short rough default:

```text
index_count <= 2
or rough_text_chars < 120
```

`too_short_label`은 source inventory에서는 제외 후보로 기록하고, P15에서 parser 기준으로 확정한다.

## Split Policy

file-level deterministic split을 만든다.

```text
rule_mining: hash bucket 0-59
dev_review: hash bucket 60-79
eval_holdout: hash bucket 80-99
```

split hash input:

```text
source_stem
```

같은 source file은 어떤 run에서도 같은 split을 유지한다.

## Outputs

Committed:

```text
src/whisper_wfst/source_inventory.py
scripts/inventory_audio_text_sources.py
tests/test_source_inventory.py
docs/reports/audits/audio_text_source_inventory.md
docs/reviews/code/2026-06-26-p14-audio-text-source-inventory-review.md
```

Ignored/local:

```text
outputs/wbs-2.0/source_inventory/source_inventory.json
outputs/wbs-2.0/source_inventory/split_manifest.json
```

## Acceptance Criteria

- `_l` label/audio paths can be inventoried without committing raw transcript/audio.
- selected audio path is deterministic when duplicate candidates exist.
- split assignment is deterministic and file-level.
- missing/short/duplicate sources are reported explicitly.
- report contains counts and checksum references only.
- `uv run --group dev pytest -q` passes.
- `uv run --group dev ruff check .` passes.
