# Full Legal AI Audit Harness Validation

Validation suites: 9
Scenario files: 50
Base embedded records/items: 234 (10 stress scenarios, 120 public metadata records, 60 public-system records, 10 raw model outputs, 19 issue-specific public output/source records, 3 issue-defined positive controls, 12 issue ablations)
Strict/lenient recoded evaluations: 100
Score-blinded coding-pass evaluations: 94
Total evaluation rows including recodings: 428
Expected outcomes passed: 50/50
High-upstream-performance but procedurally blocked scenarios: 20
Annotation robustness: 48/50 stable across base, strict and lenient coding policies
Score-blinded coding: 47 packets, 2 coding passes, 0.96 exact status agreement, 0.97 weighted status agreement

| Suite | Embedded records/items | Files/evals | Rule/stability | Mean score | Mean recall | Blocked high-upstream | Status distribution |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Protocol stress scenarios | 10 stress scenarios | 10 | 10/10 | 8.30 | 0.84 | 3 | decision_support_reason: 2, no_external_legal_effect: 2, normative_material_screening_output: 3, professional_support_output: 1, reference_information: 2 |
| Public legal-record metadata | 120 public metadata records | 6 | 6/6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Public legal-system outputs | 60 visible public-system records | 6 | 6/6 | 8.67 | n/a | 0 | professional_support_output: 6 |
| Issue-specific public output/source packets | 19 issue-specific public output/source records | 3 | 3/3 | 9.67 | 0.44 | 0 | normative_material_screening_output: 1, reference_information: 2 |
| Raw Codex GPT-5.5 xhigh outputs | 10 raw model outputs | 10 | 10/10 | 9.00 | 1.00 | 10 | reference_information: 10 |
| Issue-defined positive controls | 3 curated issue packets | 3 | 3/3 | 11.00 | 1.00 | 0 | normative_material_screening_output: 3 |
| Issue-defined ablations | 12 issue-packet ablations | 12 | 12/12 | 10.50 | 0.93 | 7 | normative_material_screening_output: 3, reference_information: 9 |
| Annotation robustness recoding | 100 strict/lenient recoded evaluations | 50 | 48/50 stable across all policies | n/a | n/a | n/a | base_vs_lenient_weighted_agreement: 1.0, base_vs_strict_weighted_agreement: 0.98 |
| Score-blinded dual coding | 47 packets x 2 coding passes | 47 | 0.96 exact status agreement | n/a | n/a | n/a | status_disagreements: 2, weighted_status_agreement: 0.97 |

## Findings

- **Protocol stress scenarios:** Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior.
- **Public legal-record metadata:** Tests source reconstruction across six public legal-record sources.
- **Public legal-system outputs:** Tests ordered real upstream legal-output reconstruction.
- **Issue-specific public output/source packets:** Tests public issue-search outputs and a source-bound public-source packet against high-authority and counter-material requirements.
- **Raw Codex GPT-5.5 xhigh outputs:** Tests whether strong authority coverage without source binding remains procedurally capped.
- **Issue-defined positive controls:** Tests normative material screening with source-bound high-authority and counter-material sets.
- **Issue-defined ablations:** Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps.
- **Annotation robustness recoding:** Tests whether status allocation survives strict and lenient recoding of the same evidence packets.
- **Score-blinded dual coding:** Tests whether two score-blinded coding passes assign similar procedural status from the same evidence packets.
