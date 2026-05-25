# Multi-Axis Holdout Generalization

Axes: 6
Holdout folds: 34
Scenario packets: 264
Qualified packets: 63
Holdout baseline predictions: 19235
Training baseline predictions: 91333
Full protocol holdout false positives: 0
Full protocol holdout false negatives: 0
Best trained simplified rule holdout false positives: 510
Best trained simplified rule holdout false negatives: 0
Lowest-FP trained simplified rule holdout false positives: 530
Lowest-FP trained simplified rule holdout false negatives: 0
Balanced trained simplified rule holdout false positives: 510
Balanced trained simplified rule holdout false negatives: 0
Folds where the best trained simplified rule erred: 17/34
Folds where the lowest-FP trained simplified rule erred: 19/34
Folds where the balanced trained simplified rule erred: 17/34

## Axis Summary

| Axis | Folds | Holdout packets | Holdout predictions | Best-rule FP | Best-rule FN | Lowest-FP FP | Lowest-FP FN | Full FP/FN | Best-rule error folds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| issue_family | 5 | 242 | 3014 | 38 | 0 | 38 | 0 | 0/0 | 5 |
| suite | 14 | 264 | 3252 | 68 | 0 | 68 | 0 | 0/0 | 4 |
| system_role | 4 | 264 | 3252 | 149 | 0 | 159 | 0 | 0/0 | 1 |
| jurisdiction_profile | 2 | 261 | 3213 | 38 | 0 | 38 | 0 | 0/0 | 2 |
| claimed_status | 3 | 264 | 3252 | 149 | 0 | 159 | 0 | 0/0 | 1 |
| origin_class | 6 | 264 | 3252 | 68 | 0 | 68 | 0 | 0/0 | 4 |

## Holdout Folds

| Axis | Held-out group | Packets | Qualified | Best trained rule | Best FP | Best FN | Lowest-FP rule | Lowest-FP FP | Lowest-FP FN | Balanced rule | Balanced FP | Balanced FN | Full FP/FN |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: |
| issue_family | canada_vavilov | 13 | 3 | source_score_review | 8 | 0 | source_score_review | 8 | 0 | source_score_review | 8 | 0 | 0/0 |
| issue_family | eu_gdpr_article15 | 82 | 20 | source_score_review | 12 | 0 | source_score_review | 12 | 0 | source_score_review | 12 | 0 | 0/0 |
| issue_family | germany_rtbf | 13 | 3 | source_score_review | 2 | 0 | source_score_review | 2 | 0 | source_score_review | 2 | 0 | 0/0 |
| issue_family | uk_mesothelioma | 67 | 16 | source_score_review | 11 | 0 | source_score_review | 11 | 0 | source_score_review | 11 | 0 | 0/0 |
| issue_family | us_agency_deference | 67 | 16 | source_score_review | 5 | 0 | source_score_review | 5 | 0 | source_score_review | 5 | 0 | 0/0 |
| suite | ai_outputs | 10 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| suite | cross_engine_model_outputs | 9 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| suite | cross_engine_model_repairs | 9 | 9 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| suite | holdout_validation | 24 | 8 | source_score_review | 5 | 0 | source_score_review | 5 | 0 | source_score_review | 5 | 0 | 0/0 |
| suite | issue_ablations | 20 | 5 | source_score_review | 10 | 0 | source_score_review | 10 | 0 | source_score_review | 10 | 0 | 0/0 |
| suite | issue_gold_sets | 5 | 5 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| suite | issue_public_outputs | 3 | 1 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| suite | model_output_adversarial | 60 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| suite | model_output_evidence_ladder | 70 | 20 | source_and_recall | 40 | 0 | source_and_recall | 40 | 0 | source_and_recall | 40 | 0 | 0/0 |
| suite | model_output_repairs | 10 | 10 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| suite | public_retrieval_benchmark | 22 | 0 | source_score_review | 13 | 0 | source_score_review | 13 | 0 | source_score_review | 13 | 0 | 0/0 |
| suite | public_system_outputs | 6 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| suite | real_cases | 6 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| suite | stress_tests | 10 | 5 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| system_role | auditable_procedural_tool | 200 | 51 | review_ready_only | 149 | 0 | review_ready_only | 149 | 0 | review_ready_only | 149 | 0 | 0/0 |
| system_role | authorized_decision_support_tool | 12 | 12 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| system_role | disclosed_assistance_tool | 42 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| system_role | unaccountable_external_disposition | 10 | 0 | source_score_review | 0 | 0 | source_and_recall | 10 | 0 | source_score_review | 0 | 0 | 0/0 |
| jurisdiction_profile | civil_law | 100 | 24 | source_score_review | 14 | 0 | source_score_review | 14 | 0 | source_score_review | 14 | 0 | 0/0 |
| jurisdiction_profile | common_law | 161 | 37 | source_score_review | 24 | 0 | source_score_review | 24 | 0 | source_score_review | 24 | 0 | 0/0 |
| claimed_status | decision_support_reason | 27 | 17 | source_score_review | 0 | 0 | source_and_recall | 10 | 0 | source_score_review | 0 | 0 | 0/0 |
| claimed_status | normative_material_screening_output | 224 | 46 | review_ready_only | 149 | 0 | review_ready_only | 149 | 0 | review_ready_only | 149 | 0 | 0/0 |
| claimed_status | professional_support_output | 13 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| origin_class | curated_protocol_packet | 15 | 10 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| origin_class | frozen_holdout_output | 24 | 8 | source_score_review | 5 | 0 | source_score_review | 5 | 0 | source_score_review | 5 | 0 | 0/0 |
| origin_class | negative_control_output | 80 | 5 | source_score_review | 10 | 0 | source_score_review | 10 | 0 | source_score_review | 10 | 0 | 0/0 |
| origin_class | public_legal_output | 37 | 1 | source_score_review | 13 | 0 | source_score_review | 13 | 0 | source_score_review | 13 | 0 | 0/0 |
| origin_class | raw_model_output | 19 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | source_score_review | 0 | 0 | 0/0 |
| origin_class | source_supported_model_output | 89 | 39 | source_and_recall | 40 | 0 | source_and_recall | 40 | 0 | source_and_recall | 40 | 0 | 0/0 |
