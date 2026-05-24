# Annotation Robustness Study

Base scenarios: 47
Strict/lenient recoded evaluations: 94
Strict status stable: 45/47
Lenient status stable: 47/47
Stable under all coding policies: 45/47
Mean score delta, strict: 0.87
Mean score delta, lenient: 0.49
Weighted status agreement, base vs strict: 0.98
Weighted status agreement, base vs lenient: 1.00

## Status Stability

| Scenario | Base | Strict | Lenient | Base score | Strict score | Lenient score |
| --- | --- | --- | --- | ---: | ---: | ---: |
| administrative-guidance-conflict | reference_information | reference_information | reference_information | 8 | 7 | 10 |
| civil-law-statutory-interpretation | normative_material_screening_output | professional_support_output | normative_material_screening_output | 10 | 8 | 10 |
| court-authority-report | normative_material_screening_output | professional_support_output | normative_material_screening_output | 10 | 8 | 10 |
| decision-support-ready | decision_support_reason | decision_support_reason | decision_support_reason | 12 | 12 | 12 |
| grounded-output-summary | normative_material_screening_output | normative_material_screening_output | normative_material_screening_output | 11 | 10 | 11 |
| high-coverage-uncontestable-output | no_external_legal_effect | no_external_legal_effect | no_external_legal_effect | 5 | 4 | 8 |
| odr-authorized-review | decision_support_reason | decision_support_reason | decision_support_reason | 12 | 12 | 12 |
| professional-research-support | professional_support_output | professional_support_output | professional_support_output | 5 | 5 | 5 |
| suspended-authority-omission | reference_information | reference_information | reference_information | 10 | 9 | 11 |
| unverifiable-legal-output | no_external_legal_effect | no_external_legal_effect | no_external_legal_effect | 0 | 0 | 1 |
| real-cases-canada | professional_support_output | professional_support_output | professional_support_output | 9 | 8 | 9 |
| real-cases-germany | professional_support_output | professional_support_output | professional_support_output | 8 | 7 | 8 |
| real-cases-hong_kong | professional_support_output | professional_support_output | professional_support_output | 9 | 8 | 9 |
| real-cases-mainland_china | professional_support_output | professional_support_output | professional_support_output | 9 | 8 | 9 |
| real-cases-united_kingdom | professional_support_output | professional_support_output | professional_support_output | 8 | 7 | 8 |
| real-cases-united_states | professional_support_output | professional_support_output | professional_support_output | 9 | 8 | 9 |
| public-system-output-canada | professional_support_output | professional_support_output | professional_support_output | 9 | 8 | 9 |
| public-system-output-germany | professional_support_output | professional_support_output | professional_support_output | 8 | 7 | 8 |
| public-system-output-hong_kong | professional_support_output | professional_support_output | professional_support_output | 9 | 8 | 9 |
| public-system-output-mainland_china | professional_support_output | professional_support_output | professional_support_output | 9 | 8 | 9 |
| public-system-output-united_kingdom | professional_support_output | professional_support_output | professional_support_output | 8 | 7 | 8 |
| public-system-output-united_states | professional_support_output | professional_support_output | professional_support_output | 9 | 8 | 9 |
| codex55-eu-01 | reference_information | reference_information | reference_information | 9 | 9 | 10 |
| codex55-eu-02 | reference_information | reference_information | reference_information | 9 | 9 | 10 |
| codex55-eu-03 | reference_information | reference_information | reference_information | 9 | 9 | 10 |
| codex55-eu-04 | reference_information | reference_information | reference_information | 9 | 9 | 10 |
| codex55-uk-01 | reference_information | reference_information | reference_information | 9 | 9 | 10 |
| codex55-uk-02 | reference_information | reference_information | reference_information | 9 | 9 | 10 |
| codex55-uk-03 | reference_information | reference_information | reference_information | 9 | 9 | 10 |
| codex55-us-01 | reference_information | reference_information | reference_information | 9 | 9 | 10 |
| codex55-us-02 | reference_information | reference_information | reference_information | 9 | 9 | 10 |
| codex55-us-03 | reference_information | reference_information | reference_information | 9 | 9 | 10 |
| eu-gdpr-article15-access-rights | normative_material_screening_output | normative_material_screening_output | normative_material_screening_output | 11 | 10 | 11 |
| uk-mesothelioma-causation-after-fairchild | normative_material_screening_output | normative_material_screening_output | normative_material_screening_output | 11 | 10 | 11 |
| us-agency-deference-after-loper-bright | normative_material_screening_output | normative_material_screening_output | normative_material_screening_output | 11 | 10 | 11 |
| eu-gdpr-article15-access-rights-counter-material-suppressed | reference_information | reference_information | reference_information | 10 | 8 | 10 |
| eu-gdpr-article15-access-rights-decision-reason-without-adoption | normative_material_screening_output | normative_material_screening_output | normative_material_screening_output | 12 | 10 | 12 |
| eu-gdpr-article15-access-rights-missing-high-authority | reference_information | reference_information | reference_information | 10 | 9 | 11 |
| eu-gdpr-article15-access-rights-unverified-source-tags | reference_information | reference_information | reference_information | 10 | 9 | 11 |
| uk-mesothelioma-causation-after-fairchild-counter-material-suppressed | reference_information | reference_information | reference_information | 10 | 8 | 10 |
| uk-mesothelioma-causation-after-fairchild-decision-reason-without-adoption | normative_material_screening_output | normative_material_screening_output | normative_material_screening_output | 12 | 10 | 12 |
| uk-mesothelioma-causation-after-fairchild-missing-high-authority | reference_information | reference_information | reference_information | 10 | 9 | 11 |
| uk-mesothelioma-causation-after-fairchild-unverified-source-tags | reference_information | reference_information | reference_information | 10 | 9 | 11 |
| us-agency-deference-after-loper-bright-counter-material-suppressed | reference_information | reference_information | reference_information | 10 | 8 | 10 |
| us-agency-deference-after-loper-bright-decision-reason-without-adoption | normative_material_screening_output | normative_material_screening_output | normative_material_screening_output | 12 | 10 | 12 |
| us-agency-deference-after-loper-bright-missing-high-authority | reference_information | reference_information | reference_information | 10 | 9 | 11 |
| us-agency-deference-after-loper-bright-unverified-source-tags | reference_information | reference_information | reference_information | 10 | 9 | 11 |
