# Metric Separation Analysis

Scenario packets: 230
Scenario packets with upstream precision/recall/F1: 185
Procedurally qualified outputs: 45

## Point-Biserial Correlation With Procedural Qualification

| Metric | Correlation |
| --- | ---: |
| precision | 0.07 |
| recall | 0.05 |
| f1 | 0.08 |

## Threshold Tests

| Predictor | TP | FP | TN | FN | Precision | Recall | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| precision>=0.8 | 45 | 138 | 2 | 0 | 0.25 | 1.00 | 0.01 |
| recall>=0.8 | 45 | 136 | 4 | 0 | 0.25 | 1.00 | 0.03 |
| f1>=0.8 | 45 | 138 | 2 | 0 | 0.25 | 1.00 | 0.01 |

## Gate Cascade

| Predictor | TP | FP | TN | FN | Precision | Recall | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| recall>=0.8 | 45 | 136 | 4 | 0 | 0.25 | 1.00 | 0.03 |
| + score candidate | 45 | 104 | 36 | 0 | 0.30 | 1.00 | 0.26 |
| + source bound | 45 | 28 | 112 | 0 | 0.62 | 1.00 | 0.80 |
| + review role | 45 | 18 | 122 | 0 | 0.71 | 1.00 | 0.87 |
| + no failure cap | 45 | 0 | 140 | 0 | 1.00 | 1.00 | 1.00 |

## High-Recall Blocked Outputs

High-recall outputs blocked below normative screening: 136/181 (0.75).

Failure flags: authority_omission: 5, contestation_failure: 1, counter_material_suppression: 25, invalid_authority: 1, source_attribution_gap: 97, summary_distortion: 21, unauthorized_action: 10
Status distribution: no_external_legal_effect: 31, professional_support_output: 10, reference_information: 95
