# Rule Source Audit Report

## Summary

- Input records: 5
- Safe-only seed rules: 1
- Review optional candidates: 1
- Disabled candidates: 3
- Final eval leakage candidates: 1
- High-risk disabled candidates: 2

## Rules

| Rule | Decision | Mode | Support | Split | Source wav | Segment | Risk | Provenance | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `R_SAFE_001` | safe_seed | optional | 2 | train | source_wav_train_l.wav | train-seg-001 | low | aligned_segment:aig_train:2 | sufficient_support_domain_span |
| `R_LOW_SUPPORT_001` | review_optional | optional | 1 | train |  |  | low | dictionary_registry:aig_terms:v1 | low_support |
| `R_FINAL_EVAL_001` | disabled | disabled | 3 | final_eval | source_wav_final_l.wav | final-seg-001 | low | aligned_segment:aig_final_eval:1 | final_eval_source |
| `R_PII_001` | disabled | disabled | 5 | train | source_wav_train_l.wav | train-seg-002 | low | phrase_bias:pii_probe:v1 | number_or_pii_surface |
| `R_LONG_SPAN_001` | disabled | disabled | 4 | train | source_wav_train_l.wav | train-seg-003 | low | aligned_segment:aig_train:long_span | long_script_span |
