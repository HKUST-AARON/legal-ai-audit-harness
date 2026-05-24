# Legal AI Audit Harness Experiment

Scenarios: 20
Expected outcomes passed: 20/20
Mean audit score: 10.50
Mean upstream recall: 0.92
High-upstream-performance but procedurally blocked scenarios: 13
Blocked reason distribution: authority_omission: 4, counter_material_suppression: 4, source_attribution_gap: 5

## Allowed Status Distribution

| Status | Count |
| --- | ---: |
| normative_material_screening_output | 5 |
| reference_information | 15 |

## Scenario Results

| Scenario | Profile | Claimed | Allowed | Score | Upstream recall | CAR | Authority coverage | Evidence fidelity | Source tags | Procedural tags | Disposition |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| canada-vavilov-standard-of-review-counter-material-suppressed | common_law | normative_material_screening_output | reference_information | 10 | 0.80 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | suspension |
| canada-vavilov-standard-of-review-decision-reason-without-adoption | common_law | decision_support_reason | normative_material_screening_output | 12 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| canada-vavilov-standard-of-review-missing-high-authority | common_law | normative_material_screening_output | reference_information | 10 | 0.80 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | suspension |
| canada-vavilov-standard-of-review-unverified-source-tags | common_law | normative_material_screening_output | reference_information | 10 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| eu-gdpr-article15-access-rights-counter-material-suppressed | civil_law | normative_material_screening_output | reference_information | 10 | 0.80 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | suspension |
| eu-gdpr-article15-access-rights-decision-reason-without-adoption | civil_law | decision_support_reason | normative_material_screening_output | 12 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| eu-gdpr-article15-access-rights-missing-high-authority | civil_law | normative_material_screening_output | reference_information | 10 | 0.80 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | suspension |
| eu-gdpr-article15-access-rights-unverified-source-tags | civil_law | normative_material_screening_output | reference_information | 10 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| germany-right-to-be-forgotten-review-counter-material-suppressed | civil_law | normative_material_screening_output | reference_information | 10 | 0.80 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | suspension |
| germany-right-to-be-forgotten-review-decision-reason-without-adoption | civil_law | decision_support_reason | normative_material_screening_output | 12 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| germany-right-to-be-forgotten-review-missing-high-authority | civil_law | normative_material_screening_output | reference_information | 10 | 0.80 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | suspension |
| germany-right-to-be-forgotten-review-unverified-source-tags | civil_law | normative_material_screening_output | reference_information | 10 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| uk-mesothelioma-causation-after-fairchild-counter-material-suppressed | common_law | normative_material_screening_output | reference_information | 10 | 0.75 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | suspension |
| uk-mesothelioma-causation-after-fairchild-decision-reason-without-adoption | common_law | decision_support_reason | normative_material_screening_output | 12 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| uk-mesothelioma-causation-after-fairchild-missing-high-authority | common_law | normative_material_screening_output | reference_information | 10 | 0.75 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | suspension |
| uk-mesothelioma-causation-after-fairchild-unverified-source-tags | common_law | normative_material_screening_output | reference_information | 10 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |
| us-agency-deference-after-loper-bright-counter-material-suppressed | common_law | normative_material_screening_output | reference_information | 10 | 1.00 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | suspension |
| us-agency-deference-after-loper-bright-decision-reason-without-adoption | common_law | decision_support_reason | normative_material_screening_output | 12 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| us-agency-deference-after-loper-bright-missing-high-authority | common_law | normative_material_screening_output | reference_information | 10 | 1.00 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | suspension |
| us-agency-deference-after-loper-bright-unverified-source-tags | common_law | normative_material_screening_output | reference_information | 10 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | downgrade |