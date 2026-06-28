# Real HF N-best Extraction

## Summary

- Dataset path: `/data/MyProject/stt/data-gen/aig-audio-3/data/processed/hf_dataset`
- Model: `openai/whisper-large-v3`
- Requested split: `validation`
- Total rows in split: 424
- Selected rows: 420
- Written artifacts: 0
- Output JSONL: `outputs/hf_nbest_real/nbest.jsonl`
- Manifest JSONL: `outputs/hf_nbest_real/manifest.jsonl`

## Skipped Counts

| Reason | Count |
| --- | ---: |
| over_max_duration | 4 |

## Unique Hypothesis Count Distribution

| Unique hypotheses | Segments |
| ---: | ---: |
| none | 0 |

## Blockers

- OutOfMemoryError: CUDA out of memory. Tried to allocate 1.43 GiB. GPU 0 has a total capacity of 15.54 GiB of which 1.09 GiB is free. Including non-PyTorch memory, this process has 11.87 GiB memory in use. Of the allocated memory 11.54 GiB is allocated by PyTorch, and 31.37 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

## Notes

- This committed report intentionally omits reference text and hypothesis text.
- Full N-best and reference manifest artifacts are local ignored outputs.
