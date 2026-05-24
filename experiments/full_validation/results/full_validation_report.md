# Full Legal AI Audit Harness Validation

Validation suites: 5
Scenario files: 35
Validation units: 203 (10 stress scenarios, 120 public metadata records, 60 public-system records, 10 raw model outputs, 3 issue-defined gold sets)
Expected outcomes passed: 35/35
High-upstream-performance but procedurally blocked scenarios: 13

| Suite | Validation units | Scenarios | Expected passed | Mean score | Mean recall | Blocked high-upstream | Status distribution |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Protocol stress scenarios | 10 stress scenarios | 10 | 10 | 8.30 | 0.84 | 3 | decision_support_reason: 2, no_external_legal_effect: 2, normative_material_screening_output: 3, professional_support_output: 1, reference_information: 2 |
| Public metadata records | 120 public metadata records | 6 | 6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Public legal-system outputs | 60 visible public-system records | 6 | 6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Raw Codex GPT-5.5 xhigh outputs | 10 raw model outputs | 10 | 10 | 9.00 | 1.00 | 10 | reference_information: 10 |
| Issue-defined gold sets | 3 curated issue packets | 3 | 3 | 11.00 | 1.00 | 0 | normative_material_screening_output: 3 |

## Findings

- **Protocol stress scenarios:** Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior.
- **Public metadata records:** Tests source reconstruction across six jurisdictions.
- **Public legal-system outputs:** Tests ordered real upstream legal-output reconstruction.
- **Raw Codex GPT-5.5 xhigh outputs:** Tests whether strong authority coverage without source binding remains procedurally capped.
- **Issue-defined gold sets:** Tests normative material screening with source-bound high-authority and counter-material sets.
