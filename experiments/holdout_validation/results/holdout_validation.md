# Legal AI Audit Harness Experiment

Scenarios: 24
Scenario-regression expectations passed: 24/24
Mean audit score: 9.71
Mean upstream recall: 0.77
High-upstream-performance but procedurally blocked scenarios: 9
Blocked reason distribution: counter_material_suppression: 1, source_attribution_gap: 8

## Allowed Status Distribution

| Status | Count |
| --- | ---: |
| normative_material_screening_output | 8 |
| reference_information | 16 |

## Scenario Results

| Scenario | Profile | Claimed | Allowed | Score | Upstream recall | CAR | Authority coverage | Evidence fidelity | Source tags | Procedural tags | Disposition |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| holdout-public-retrieval-canada-vavilov-standard-of-review-q05 | common_law | normative_material_screening_output | reference_information | 9 | 0.67 | 0.00 | 0.67 | 1.00 | 1.00 | 1.00 | suspension |
| holdout-public-retrieval-canada-vavilov-standard-of-review-q06 | common_law | normative_material_screening_output | reference_information | 10 | 1.00 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | suspension |
| holdout-public-retrieval-eu-gdpr-article15-access-rights-q05 | civil_law | normative_material_screening_output | reference_information | 9 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | suspension |
| holdout-public-retrieval-eu-gdpr-article15-access-rights-q06 | civil_law | normative_material_screening_output | reference_information | 9 | 0.33 | 0.00 | 0.33 | 1.00 | 1.00 | 1.00 | suspension |
| holdout-public-retrieval-germany-right-to-be-forgotten-review-q05 | civil_law | normative_material_screening_output | reference_information | 9 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 0.00 | suspension |
| holdout-public-retrieval-germany-right-to-be-forgotten-review-q06 | civil_law | normative_material_screening_output | reference_information | 9 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 0.00 | suspension |
| holdout-public-retrieval-uk-mesothelioma-causation-after-fairchild-q05 | common_law | normative_material_screening_output | reference_information | 9 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | suspension |
| holdout-public-retrieval-us-agency-deference-after-loper-bright-q05 | common_law | normative_material_screening_output | reference_information | 9 | 0.50 | 0.00 | 0.50 | 1.00 | 1.00 | 0.00 | suspension |
| holdout-raw-canada-vavilov-01 | common_law | normative_material_screening_output | reference_information | 9 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| holdout-raw-eu-gdpr-01 | civil_law | normative_material_screening_output | reference_information | 9 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| holdout-raw-eu-gdpr-02 | civil_law | normative_material_screening_output | reference_information | 9 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| holdout-raw-germany-rtbf-01 | civil_law | normative_material_screening_output | reference_information | 9 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| holdout-raw-uk-mesothelioma-01 | common_law | normative_material_screening_output | reference_information | 9 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| holdout-raw-uk-mesothelioma-02 | common_law | normative_material_screening_output | reference_information | 9 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| holdout-raw-us-deference-01 | common_law | normative_material_screening_output | reference_information | 9 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| holdout-raw-us-deference-02 | common_law | normative_material_screening_output | reference_information | 9 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| holdout-source-bound-canada-vavilov-01 | common_law | normative_material_screening_output | normative_material_screening_output | 11 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| holdout-source-bound-eu-gdpr-01 | civil_law | normative_material_screening_output | normative_material_screening_output | 11 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| holdout-source-bound-eu-gdpr-02 | civil_law | normative_material_screening_output | normative_material_screening_output | 11 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| holdout-source-bound-germany-rtbf-01 | civil_law | normative_material_screening_output | normative_material_screening_output | 11 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| holdout-source-bound-uk-mesothelioma-01 | common_law | normative_material_screening_output | normative_material_screening_output | 11 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| holdout-source-bound-uk-mesothelioma-02 | common_law | normative_material_screening_output | normative_material_screening_output | 11 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| holdout-source-bound-us-deference-01 | common_law | normative_material_screening_output | normative_material_screening_output | 11 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| holdout-source-bound-us-deference-02 | common_law | normative_material_screening_output | normative_material_screening_output | 11 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |