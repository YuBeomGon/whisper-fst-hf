# Real HF N-best Extraction

## Summary

- Dataset path: `/data/MyProject/stt/data-gen/aig-audio-3/data/processed/hf_dataset`
- Model: `openai/whisper-large-v3`
- Requested split: `validation`
- Total rows in split: 424
- Selected rows: 1
- Written artifacts: 0
- Output JSONL: `outputs/hf_nbest_real/nbest.jsonl`
- Manifest JSONL: `outputs/hf_nbest_real/manifest.jsonl`

## Dataset Check

| Split | Rows | First row audio | Sampling rate |
| --- | ---: | ---: | ---: |
| train | 2,556 | 401,600 samples | 16,000 |
| validation | 424 | 27,520 samples | 16,000 |

## Skipped Counts

| Reason | Count |
| --- | ---: |
| limit_excluded | 419 |
| over_max_duration | 4 |

## Unique Hypothesis Count Distribution

| Unique hypotheses | Segments |
| ---: | ---: |
| none | 0 |

## Blockers

- Current `uv` environment is missing `datasets`, `transformers`, `torch`, and `numpy`; system Python has them.
- `torch.cuda.is_available()` is false on this machine.
- `openai/whisper-large-v3` with `num_beams=20` and `num_return_sequences=20` on CPU did not finish one 1.72s validation chunk after more than 120 seconds.
- P19 real N-best extraction is blocked until GPU/runtime resources are available or decode/model settings are explicitly reduced.

## Notes

- The committed report intentionally omits reference text and hypothesis text.
- A dry-run local manifest was written under `outputs/hf_nbest_real/manifest.jsonl`.
- No real N-best artifact was produced.
