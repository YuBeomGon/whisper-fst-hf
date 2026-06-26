# Pair Rule Source Audit v2

## Summary

- Input candidates: 104924
- Seed optional rules: 0
- Seed obligatory rules: 0
- Needs review candidates: 394
- Rejected candidates: 104530

## Reason Counts

| Reason | Count |
| --- | ---: |
| affix_only_change | 2221 |
| eval_holdout_only | 128 |
| format_only_change | 5035 |
| large_length_delta | 2961 |
| low_alignment_confidence | 24898 |
| low_allowed_file_support | 394 |
| multi_token_or_spacing_change | 47573 |
| protected_or_pii_surface | 15469 |
| punctuation_surface | 6245 |

## Split Counts

| Split | Candidate references |
| --- | ---: |
| dev_review | 17196 |
| eval_holdout | 24633 |
| rule_mining | 68395 |

## Notes

- This report intentionally omits actual wrong/right surfaces.
- Full review CSV and seed rule CSV are local ignored artifacts.
- Seed rules require downstream correction evaluation before production use.
- No candidate passed the conservative automatic seed promotion policy.
