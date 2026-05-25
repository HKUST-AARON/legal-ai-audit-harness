# Status Lattice Analysis

States: 233280
Score vectors: 729
Roles: 5
Gates: 6
High-status states: 168
Decision-status states: 11

## Status Distribution

| Status | Count |
| --- | ---: |
| decision_support_reason | 11 |
| no_external_legal_effect | 160704 |
| normative_material_screening_output | 157 |
| professional_support_output | 1128 |
| reference_information | 71280 |

## Lattice Checks

| Check | Passed | Total | Failed |
| --- | ---: | ---: | ---: |
| High-status necessity | 851 | 851 | 0 |
| Gate ablation drops | 851 | 851 | 0 |
| Substitute-rule non-reduction | 2 | 2 | 0 |

## Cover-Edge Diagnostics

| Edges | Promotions | Demotions | Stable |
| ---: | ---: | ---: | ---: |
| 1632960 | 100917 | 10368 | 1521675 |

## Substitute Rules

| Rule | Precision | Recall | FP | FN |
| --- | ---: | ---: | ---: | ---: |
| total_score_at_least_9 | 0.0067 | 1.0000 | 24792 | 0 |
| complete_vector_and_score | 0.0125 | 1.0000 | 13272 | 0 |
| role_ready_and_score | 0.0168 | 1.0000 | 9816 | 0 |
| source_bound_score | 0.0500 | 1.0000 | 3192 | 0 |
| source_authority_score | 0.1000 | 1.0000 | 1512 | 0 |
| source_authority_counter_score | 0.2000 | 1.0000 | 672 | 0 |
| full_screening_predicate | 1.0000 | 1.0000 | 0 | 0 |
