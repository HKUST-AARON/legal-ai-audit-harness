# Full Legal AI Audit Harness Validation

Validation suites: 6
Scenario files: 47
Embedded records/items: 215 (10 stress scenarios, 120 public metadata records, 60 public-system records, 10 raw model outputs, 3 issue-defined positive controls, 12 issue ablations)
Expected outcomes passed: 47/47
High-upstream-performance but procedurally blocked scenarios: 20

| Suite | Embedded records/items | Scenario files | Rule pass | Mean score | Mean recall | Blocked high-upstream | Status distribution |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Protocol stress scenarios | 10 stress scenarios | 10 | 10 | 8.30 | 0.84 | 3 | decision_support_reason: 2, no_external_legal_effect: 2, normative_material_screening_output: 3, professional_support_output: 1, reference_information: 2 |
| Public legal-record metadata | 120 public metadata records | 6 | 6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Public legal-system outputs | 60 visible public-system records | 6 | 6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Raw Codex GPT-5.5 xhigh outputs | 10 raw model outputs | 10 | 10 | 9.00 | 1.00 | 10 | reference_information: 10 |
| Issue-defined positive controls | 3 curated issue packets | 3 | 3 | 11.00 | 1.00 | 0 | normative_material_screening_output: 3 |
| Issue-defined ablations | 12 issue-packet ablations | 12 | 12 | 10.50 | 0.93 | 7 | normative_material_screening_output: 3, reference_information: 9 |

## Findings

- **Protocol stress scenarios:** Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior.
- **Public legal-record metadata:** Tests source reconstruction across six public legal-record sources.
- **Public legal-system outputs:** Tests ordered real upstream legal-output reconstruction.
- **Raw Codex GPT-5.5 xhigh outputs:** Tests whether strong authority coverage without source binding remains procedurally capped.
- **Issue-defined positive controls:** Tests normative material screening with source-bound high-authority and counter-material sets.
- **Issue-defined ablations:** Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps.
