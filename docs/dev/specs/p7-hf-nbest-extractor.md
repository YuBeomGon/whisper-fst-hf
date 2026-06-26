# P7 Hugging Face Whisper N-best Extractor Spec

Date: 2026-06-26

Branch: `wbs/P7-hf-nbest-extractor`

## Goal

P7는 HF Transformers Whisper generation 결과를 P3 `NBestArtifact` contract로 저장하는 adapter를 구현한다.

실제 model download와 audio inference는 환경 의존성이 크므로 P7 MVP는 mocked generation output에서
artifact를 생성하는 경로를 필수 구현으로 둔다. 실제 short audio smoke는 환경 가능 여부를 report에 residual
risk로 남긴다.

## Decode Config

기본 decode config:

- `num_beams=20`
- `num_return_sequences=20`
- `return_dict_in_generate=true`
- `output_scores=true`
- `length_penalty=1.0`

## Score Contract

Artifact hypothesis는 다음 score metadata를 기록한다.

- `score_source`
- `score_is_logprob`
- `length_penalty`
- `raw_logprob`
- `decoder_score`
- `asr_cost`

MVP score conversion:

```text
asr_cost = max(0, -raw_logprob)
```

Score 해석은 residual uncertainty가 있으므로 report에 명시한다.

## N-best Diversity Report

P7 report는 다음을 포함한다.

- requested hypotheses count
- returned hypotheses count
- unique normalized hypothesis count
- duplicate count
- domain oracle risk flag
- N-best oracle risk flag
- score uncertainty note

## Non-goals

- long-form segmentation
- GPU performance optimization
- teacher-force rescore
- production model download management

## Acceptance Criteria

- mocked generation에서 N-best artifact 생성 가능
- raw score, decoder score, decode config가 artifact에 기록됨
- `score_source`, `score_is_logprob`, `length_penalty`, `asr_cost`가 artifact에 기록됨
- unique hypothesis count가 report에 남음
- domain oracle hit와 N-best oracle 개선 여부가 P10 진입 risk flag로 남음
- score 해석의 residual uncertainty가 문서화됨
- `uv run --group dev pytest -q`가 통과함
- `uv run --group dev ruff check .`가 통과함
