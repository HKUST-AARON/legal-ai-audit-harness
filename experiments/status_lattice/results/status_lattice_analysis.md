# Status Lattice Analysis

States: 466560
Score vectors: 729
Roles: 5
Gates: 7
High-status states: 168
Decision-status states: 11

## Status Distribution

| Status | Count |
| --- | ---: |
| decision_support_reason | 11 |
| no_external_legal_effect | 321408 |
| normative_material_screening_output | 157 |
| professional_support_output | 1128 |
| reference_information | 143856 |

## Lattice Checks

| Check | Passed | Total | Failed |
| --- | ---: | ---: | ---: |
| High-status necessity | 1019 | 1019 | 0 |
| Gate ablation drops | 1019 | 1019 | 0 |
| Substitute-rule non-reduction | 2 | 2 | 0 |

## Cover-Edge Diagnostics

| Edges | Promotions | Demotions | Stable |
| ---: | ---: | ---: | ---: |
| 3499200 | 195525 | 20736 | 3282939 |

## Substitute Rules

| Rule | Precision | Recall | FP | FN |
| --- | ---: | ---: | ---: | ---: |
| total_score_at_least_9 | 0.0034 | 1.0000 | 49752 | 0 |
| complete_vector_and_score | 0.0063 | 1.0000 | 26712 | 0 |
| role_ready_and_score | 0.0084 | 1.0000 | 19800 | 0 |
| source_bound_score | 0.0250 | 1.0000 | 6552 | 0 |
| claim_anchored_source_score | 0.0500 | 1.0000 | 3192 | 0 |
| source_authority_score | 0.1000 | 1.0000 | 1512 | 0 |
| source_authority_counter_score | 0.2000 | 1.0000 | 672 | 0 |
| full_screening_predicate | 1.0000 | 1.0000 | 0 | 0 |
