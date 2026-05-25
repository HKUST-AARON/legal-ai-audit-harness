# Policy-Family Robustness

Policy variants: 12
Scenario packets per variant: 264
Status evaluations: 3168
Baseline-rule predictions: 39024
Total evaluations: 42192
Status promotions from default: 0
High-status promotions from below screening: 0
High-status demotions from default: 42
Variants where every simplified rule erred: 12/12
Best simplified-rule false positives across variants: 449
Best simplified-rule false negatives across variants: 0
Full protocol false positives across variants: 0
Full protocol false negatives across variants: 0

| Variant | Qualified | Changes | Promotions | High promotions | High demotions | Best simplified FP/FN | Full FP/FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| default | 63 | 0 | 0 | 0 | 0 | 38/0 | 0/0 |
| lenient_threshold_8_10 | 63 | 0 | 0 | 0 | 0 | 38/0 | 0/0 |
| strict_threshold_10_11 | 63 | 0 | 0 | 0 | 0 | 22/0 | 0/0 |
| strict_threshold_11_12 | 61 | 2 | 0 | 0 | 2 | 10/0 | 0/0 |
| rank_window_2 | 26 | 37 | 0 | 0 | 37 | 75/0 | 0/0 |
| rank_window_4 | 63 | 0 | 0 | 0 | 0 | 38/0 | 0/0 |
| strict_procedural_tags | 62 | 1 | 0 | 0 | 1 | 38/0 | 0/0 |
| official_source_tags_only | 61 | 2 | 0 | 0 | 2 | 38/0 | 0/0 |
| authorized_cap_to_screening | 63 | 12 | 0 | 0 | 0 | 38/0 | 0/0 |
| auditable_cap_to_decision | 63 | 0 | 0 | 0 | 0 | 38/0 | 0/0 |
| strict_downgrade_to_suspension | 63 | 0 | 0 | 0 | 0 | 38/0 | 0/0 |
| strict_failure_withdrawal | 63 | 72 | 0 | 0 | 0 | 38/0 | 0/0 |
