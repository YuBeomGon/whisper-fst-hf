# P19 Real HF N-best Extraction Implementation Plan

## Goal

Use the AIG HF chunk dataset as the real audio/text source and attempt HF Whisper N-best
extraction.

## Tasks

1. Add failing tests for HF dataset row conversion, duration filtering, artifact metadata, and redacted reporting.
2. Implement `src/whisper_wfst/hf_audio_extractor.py`.
3. Add CLI `scripts/extract_real_hf_nbest.py`.
4. Add `configs/hf-real.yaml`.
5. Update WBS 2.0 to reference the HF dataset source and manual confirmed 49 rules.
6. Run dataset dry-run against `/data/MyProject/stt/data-gen/aig-audio-3/data/processed/hf_dataset`.
7. Attempt one validation chunk with beam 20 / return 20.
8. If extraction is infeasible, write blocker report and stop P19.
9. Run `pytest`, `ruff`, and `git diff --check`.
10. Commit, merge to `main`, and push.
