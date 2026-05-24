# Legal AI Audit Harness Experiment

Scenarios: 10
Scenario-regression expectations passed: 10/10
Mean audit score: 8.30
Mean upstream recall: 0.84
High-upstream-performance but procedurally blocked scenarios: 3
Blocked reason distribution: authority_omission: 1, contestation_failure: 1, counter_material_suppression: 1, invalid_authority: 1, source_attribution_gap: 2, summary_distortion: 1

## Allowed Status Distribution

| Status | Count |
| --- | ---: |
| decision_support_reason | 2 |
| no_external_legal_effect | 2 |
| normative_material_screening_output | 3 |
| professional_support_output | 1 |
| reference_information | 2 |

## Scenario Results

| Scenario | Profile | Claimed | Allowed | Score | Upstream recall | CAR | Authority coverage | Evidence fidelity | Source tags | Procedural tags | Disposition |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| administrative-guidance-conflict | administrative | normative_material_screening_output | reference_information | 8 | 0.88 | 0.00 | 1.00 | n/a | n/a | n/a | suspension |
| civil-law-statutory-interpretation | civil_law | normative_material_screening_output | normative_material_screening_output | 10 | 0.82 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| court-authority-report | common_law | normative_material_screening_output | normative_material_screening_output | 10 | 0.83 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| decision-support-ready | arbitral | decision_support_reason | decision_support_reason | 12 | 0.95 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| grounded-output-summary | common_law | normative_material_screening_output | normative_material_screening_output | 11 | 0.90 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| high-coverage-uncontestable-output | common_law | normative_material_screening_output | no_external_legal_effect | 5 | 0.93 | 1.00 | 1.00 | 0.50 | 1.00 | 1.00 | withdrawal |
| odr-authorized-review | odr | decision_support_reason | decision_support_reason | 12 | 0.91 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| professional-research-support | common_law | professional_support_output | professional_support_output | 5 | 0.58 | 0.00 | n/a | n/a | n/a | n/a | none |
| suspended-authority-omission | common_law | normative_material_screening_output | reference_information | 10 | 0.84 | 1.00 | 0.00 | n/a | n/a | n/a | suspension |
| unverifiable-legal-output | common_law | normative_material_screening_output | no_external_legal_effect | 0 | 0.72 | 0.00 | n/a | 0.00 | 1.00 | 0.00 | withdrawal |