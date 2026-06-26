# Correction Calibration

Chosen config: safe_only_margin_025

## Selected Parameters

- lambda: 1.0
- margin: 0.25
- num_beams: 20
- num_return_sequences: 20
- correction_cost: 1.0
- keep_cost: 0.0
- rule_policy: safe_only
- domain_gate_policy: script_span_only

## Metrics

- corrected CER: 0.0000
- domain term accuracy: 1.0000
- overcorrection rate: 0.0000
- free-talk overcorrection rate: 0.0000

## Freeze Checksums

- `configs/correction.yaml` sha256 `19aed5c442a944b0e1bb514d08eb1fbab2dec4ece62fdaba1f79a37d22b29c7b`
- `data/correction_rules_seed.csv` sha256 `89f2597b011f6d5211b047fc58f0864de3c919ccf2bde04aaee8fe138a794566`
- `docs/reports/experiments/offline_mvp_manifest.json` sha256 `df81561d01b84d09a5c9ff580cf08be46a7f8efbcb735367f57f796d33c458bd`

Synthetic calibration only. Final eval must use frozen config/rules/artifacts.
