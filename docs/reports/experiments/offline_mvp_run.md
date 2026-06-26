# Offline MVP Run

Mode: synthetic fixture offline MVP.

P8 targetability risk flag: ok

No production-quality claim is made from this run.

## Targetability

# N-best Targetability Probe

## Summary

- Segments: 1
- Average unique hypotheses: 2.00
- Top1 CER: 0.1429
- N-best oracle CER: 0.0000
- Top1 WER: 0.5000
- N-best oracle WER: 0.0000
- Domain term oracle accuracy: 1.0000
- Reference surface in N-best ratio: 1.0000
- Seed wrong surface in top1 ratio: 1.0000
- Seed wrong surface in N-best ratio: 1.0000
- P10 risk flag: ok

## Policy

P8 does not run the correction engine. final eval leakage candidates from P3.5 must not be used for final claims.

## Evaluation

# Evaluation Baseline Report

## Comparison Sets

- A: top1 baseline
- B: top1 + correction
- C: N-best oracle
- D: N-best + correction

## Metrics

- Segments: 2
- Top1 CER: 0.0714
- Top1 WER: 0.2500
- Corrected CER: 0.0000
- Corrected WER: 0.0000
- Domain term accuracy: 1.0000
- N-best oracle CER: 0.0000
- N-best oracle WER: 0.0000
- Domain term oracle accuracy: 1.0000
- Correction precision: 1.0000
- Correction recall: 1.0000
- Overcorrection rate: 0.0000
- free-talk correction rate: 0.0000
- free-talk overcorrection rate: 0.0000
- Average unique hypothesis count: 1.50
- Latency p50 ms: not_applicable
- Latency p95 ms: not_applicable

## Checksums

- `tests/fixtures/targetability_artifact.json`: `c69e5f4114f30d620c8e4708aa19b4ff5033c9599fdc1124a5002ae85493c115`
- `tests/fixtures/targetability_manifest.json`: `719bf3c9d961b81829faf165c318f56f9ef7952f1b4001a17271d7483642bfea`
- `tests/fixtures/correction_rules.csv`: `ec6538150c026ce38cbf645a8c9ca83d53b3a439c4cf694f8ff8636bdc370119`
- `tests/fixtures/evaluation_manifest.json`: `96f587c4c979756f3e6d7ece5f2400836728090f204c1bbb43c5aa8d6d20b9c7`
- `tests/fixtures/evaluation_predictions.json`: `f7df0169382702be8fcc7bb2142cbb666490b06dcd369f7c7091b1880adae0a2`
- `outputs/offline_mvp/correction_trace.json`: `231b5e22c385f1ca395d447a97050878a52bb4a2531233b78df606b6834df8f4`
- `outputs/offline_mvp/evaluation_report.md`: `6d5ffcd257cab9c2799faa01f168ae56e2b95ed269348807de3a66837d79999b`
