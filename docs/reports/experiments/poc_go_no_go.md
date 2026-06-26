# PoC Go / No-Go Report

Date: 2026-06-26

## Decision

`Continue-with-scope-change`

The project should continue as an engineering PoC, but not as a quality-validated domain improvement claim yet.

## Evidence Summary

| Area | Evidence | Status |
| --- | --- | --- |
| FST backend | P2 report | Pynini unavailable in current Python environment |
| Core contracts | P3 schema/tests | Done |
| Rule provenance | P3.5 audit | Safe seed separated from risky/leakage candidates |
| Protection | P4 tests | NFC and protected spans implemented |
| Composition | P5 tests | Phrase-rule fallback works without Pynini |
| Safety | P6 report/tests | Domain gate, margin, trace, free-talk smoke implemented |
| HF extraction | P7 report/tests | Mocked HF generation artifact path works |
| Targetability | P8 report | Synthetic positive targetability |
| Evaluation | P9 report | Synthetic A/B/C/D metric format fixed |
| Offline MVP | P10 report | Synthetic pipeline reproducible with checksums |
| Calibration | P11 report | Synthetic hard-gate config selected |
| Rescore | P12 decision | Teacher-force rescore deferred |

## Judgment Questions

| Question | Answer |
| --- | --- |
| N-best 안에 domain correction 기회가 충분히 있었는가? | Synthetic fixture에서는 yes. Real audio에서는 unknown. |
| N-best + WFST가 top1 correction보다 나았는가? | Current fixture proves report path only. Real comparison is not established. |
| overcorrection rate가 허용 가능한가? | Synthetic fixture에서는 0. Real free-talk eval required. |
| 자유대화 영향이 제한적인가? | Domain gate smoke에서는 limited. Real free-talk set required. |
| HF runtime PoC로 충분한가? | Contract PoC로는 sufficient. Real runtime smoke remains. |
| Pynini/OpenFST 운영 리스크가 감당 가능한가? | 현재 환경에서는 no. Fallback works, but true WFST backend requires dependency decision. |
| teacher-force rescore가 필요한가? | 지금은 no. Real N-best targetability 이후 재검토. |

## Unresolved Risks

- Real HF model/audio inference has not been run.
- Pynini/OpenFST is unavailable in the current environment.
- Targetability, evaluation, calibration, and offline MVP evidence are synthetic.
- Rule seed coverage is minimal.
- Production speaker/channel/domain gating is not implemented.

## Follow-up WBS

1. Real HF smoke with a reviewed small audio set.
2. Real N-best targetability report with leakage-safe references.
3. Pynini install path decision or explicit production fallback decision.
4. Expanded rule source audit from actual training/dev sources.
5. Free-talk regression set and hard gate thresholds.
6. Real offline MVP run with artifact checksums.

## Final Note

No production-quality claim is made from this PoC. The current repository is ready for the next evidence-gathering
iteration.
