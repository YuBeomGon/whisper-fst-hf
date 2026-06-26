# P11 Calibration / Rule Tuning Spec

Date: 2026-06-26

Branch: `wbs/P11-calibration-rule-tuning`

## Goal

P11은 lambda, margin, rule cost, risky rule policy를 evaluation 결과로 조정하는 calibration report를 만든다.

현재 real audio evaluation이 없으므로 P11은 synthetic sweep result를 사용해 hard gate와 best config selection
로직을 고정한다.

## Sweep Dimensions

- lambda
- margin
- num_beams
- num_return_sequences
- correction cost
- keep cost
- rule policy: `safe_only`, `safe_optional_medium`, `diagnostic_all`
- domain gate policy

## Hard Gates

Candidate config는 다음 hard gate를 통과해야 한다.

- free-talk overcorrection rate <= allowed maximum
- overcorrection rate <= allowed maximum
- domain term accuracy >= baseline

통과 후보 중 best는 다음 순서로 선택한다.

1. higher domain term accuracy
2. lower corrected CER
3. lower overcorrection rate
4. stable config id

## Freeze

P11 report는 final eval 전 freeze 후보의 config/rule checksum을 기록한다.

## Acceptance Criteria

- chosen lambda/margin이 report 근거와 함께 기록된다.
- chosen `num_beams`/`num_return_sequences`와 rule/gate policy가 report 근거와 함께 기록된다.
- hard gate를 통과한 config 중 best를 선택한다.
- final eval 전 config/rule/artifact checksum이 freeze된다.
- domain metric 개선과 free-talk risk가 함께 보고된다.
- tuning 후 regression tests가 통과한다.
