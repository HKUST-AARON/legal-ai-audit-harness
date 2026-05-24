# Legal AI Audit Harness

A lightweight scoring harness for legal AI outputs above any search, retrieval, generation, agent, database, or manual review stack.

The harness operationalizes a verifiability-based audit model for deciding whether a legal AI output should remain an internal reference, qualify as professional support, qualify as a normative material screening output, or be treated as a decision-support reason only after accountable human adoption.

## Model

Each scenario contains a human-coded audit vector with six dimensions scored from `0` to `2`:

| Code | Dimension |
| --- | --- |
| `S` | Source and corpus verifiability |
| `Q` | Query and version traceability |
| `H` | Authority-hierarchy representation |
| `K` | Ranking and counter-material verifiability |
| `T` | Contestability support |
| `L` | Adoption logging and audit responsibility |

The harness computes:

```text
PS(o) = g(E(o), R(o), A(o))
A(o) = (S, Q, H, K, T, L)
```

It applies gate rules and computes derived checks including authority coverage, counter-authority recall, output-evidence metrics, source-attribution coverage, human-review gates, and downgrade or withdrawal triggers. It is an output-status audit layer, not a legal merits evaluator.

The repository follows a local-first CLI and artifact-log pattern: each run is reproducible from local scenario files, produces Markdown/JSON artifacts, and is checked by CI. Its legal-workflow guardrails are adapted from the public [`anthropics/claude-for-legal`](https://github.com/anthropics/claude-for-legal) design: legal AI outputs remain draft or screening artefacts until a review gate is satisfied; source links carry source tags; jurisdiction assumptions are explicit; and actions such as filing, sending, external reliance, or execution require accountable human authorization. The harness does not import or require an agent runtime, and it does not inspect upstream implementation details.

## Quick Start

```bash
python -m audit_harness.cli score examples/scenarios/court_authority_report.json
python -m audit_harness.cli run examples/scenarios --out reports/sample_report.md --json-out reports/sample_report.json
python -m audit_harness.cli experiment examples/scenarios --out reports/experiment_report.md --json-out reports/experiment_report.json
python -m audit_harness.cli sensitivity examples/scenarios --out reports/sensitivity_report.md --json-out reports/sensitivity_report.json
python scripts/collect_public_system_outputs.py
python scripts/collect_issue_public_outputs.py
python scripts/collect_public_retrieval_benchmark.py
python scripts/build_blind_coding_packets.py
python scripts/run_blind_coding_study.py
python scripts/run_annotation_robustness.py
python scripts/run_full_validation.py
python -m unittest discover -s tests
```

Installed as a package:

```bash
python -m pip install -e .
legal-ai-audit run examples/scenarios --out reports/sample_report.md
```

## Scenario Format

```json
{
  "id": "court-authority-report",
  "claimed_status": "normative_material_screening_output",
  "system_role": "auditable_procedural_tool",
  "jurisdiction_profile": "common_law",
  "scores": {
    "S": { "score": 2, "evidence": "Corpus manifest and source links are recorded." },
    "Q": { "score": 2, "evidence": "Issue, filters, source-collection version, workflow version and output identifier are recorded." },
    "H": { "score": 2, "evidence": "Binding, persuasive and invalid authorities are labelled." },
    "K": { "score": 1, "evidence": "Ranking factors are broad; counter-material recall is incomplete." },
    "T": { "score": 2, "evidence": "Reviewers can inspect and challenge the result set." },
    "L": { "score": 1, "evidence": "Adoption is logged, but reasons are not structured." }
  },
  "counter_authority": {
    "known": ["limiting-authority-a", "contrary-authority-b"],
    "retrieved": ["limiting-authority-a"]
  },
  "authority_sets": {
    "high_authority": ["binding-precedent-a"],
    "retrieved_high_authority": ["binding-precedent-a"],
    "counter_or_limiting": ["limiting-authority-a"],
    "retrieved_counter_or_limiting": ["limiting-authority-a"],
    "invalid_or_superseded": [],
    "retrieved": ["binding-precedent-a", "limiting-authority-a"]
  },
  "upstream_metrics": { "precision": 0.88, "recall": 0.83, "f1": 0.85 },
  "evidence_packet": {
    "output_links": [
      { "unit_id": "unit-1", "source_id": "binding-precedent-a", "locator": "para 3", "supports_claim": true, "source_tag": "tool_verified" }
    ],
    "output_units": [
      { "id": "unit-1", "source_ids": ["binding-precedent-a"], "locators": ["para 3"] }
    ]
  },
  "review_gate": {
    "attorney_review_required": true,
    "review_status": "completed",
    "reliance_gate": "attorney_review",
    "jurisdiction_assumptions": ["common_law"],
    "irreversible_action": false,
    "human_authorization": false
  },
  "failure_flags": [],
  "expected_allowed_status": "normative_material_screening_output",
  "expected_disposition": "none"
}
```

## Status Rules

| Allowed status | Minimum rule |
| --- | --- |
| `reference_information` | `S >= 1` and `Q >= 1` |
| `professional_support_output` | `S, Q, L >= 1` |
| `normative_material_screening_output` | all six dimensions `>= 1` and total score `>= 9` |
| `decision_support_reason` | all normative-screening gates, total score `>= 10`, `T = L = 2`, completed review, `authorized_adoption`, human authorization, recorded jurisdiction assumptions, adoption reasons, and contestation record |
| `no_external_legal_effect` | missing gates or withdrawal-level failures |

`system_role` caps the highest status available to an output: `back_office_tool` caps at reference, `disclosed_assistance_tool` at professional support, `auditable_procedural_tool` at normative screening, `authorized_decision_support_tool` at decision support, and `unaccountable_external_disposition` at no external legal effect. When `system_role` is omitted, the harness infers it from the review gate and claimed status.

Failure flags can downgrade or withdraw an output from external procedural use.

## Full Validation Suite

Run the complete validation matrix with:

```bash
python scripts/run_full_validation.py
```

The full suite reruns all committed validation layers and writes:

```text
experiments/full_validation/results/full_validation_report.md
experiments/full_validation/results/full_validation_report.json
```

Current coverage:

| Layer | Embedded records/items | Purpose |
| --- | ---: | --- |
| Protocol stress scenarios | 10 | Tests downgrade, withdrawal, decision-support and high-recall-but-blocked behavior. |
| Public legal-record metadata | 120 | Tests source reconstruction across six public legal-record sources. |
| Public legal-system outputs | 60 | Tests ordered real upstream public legal-output reconstruction. |
| Issue-specific public output/source packets | 19 | Tests public issue-search outputs and a source-bound public-source packet against high-authority and counter-material requirements. |
| Public retrieval benchmark | 99 | Tests true public search outputs against issue-defined high-authority and counter-material gold sets. |
| Raw Codex GPT-5.5 xhigh outputs | 10 | Tests whether strong authority coverage without source binding remains procedurally capped. |
| Issue-defined positive controls | 3 | Tests normative material screening with source-bound high-authority and counter-material sets. |
| Issue-defined ablations | 12 | Tests whether high-authority omissions, counter-material suppression, unverified source tags and missing adoption gates trigger the expected caps. |
| Annotation robustness recoding | 124 | Re-scores all 62 scenario packets under strict and lenient coding policies to test status stability. |
| Score-blinded dual coding | 124 | Two coding passes score all 62 packets without original scores or expected outcomes. |
| Full-threshold sensitivity | 310 | Re-evaluates all 62 scenario packets under normative thresholds 8-12. |

The current full validation report covers 62 scenario files containing 333 embedded records/items, 124 strict/lenient recoded evaluations, 124 score-blinded coder evaluations, and 310 full-threshold sensitivity evaluations. Expected outcomes are scenario-regression checks: they verify rule conformance and artifact integrity, while the public retrieval benchmark, full-threshold sensitivity, robustness and blind-coding layers test whether status allocation survives real public search outputs, threshold changes and plausible coding disagreement. The dual-coding layer is not a substitute for future external human annotation, but it separates packet evidence from original scenario scores and expected outcomes.

## Jurisdiction Profiles

Profiles in `examples/jurisdiction_profiles/` parameterize `H` and `K` for different legal settings. Common-law scenarios use binding and persuasive precedent labels, while civil-law scenarios use code provisions, special statutes, high-court decisions, doctrinal views and later amendments. The scoring dimensions stay stable; the legal materials used to prove each dimension vary by profile.

## Output Evidence Auditing

Scenarios can include an `evidence_packet` object with output-to-source mappings. This sits above any upstream implementation. The harness reports evidence fidelity, evidence coverage, source-tag coverage, and procedural-source-tag coverage. Unsupported output units are withdrawal-level failures when they claim external procedural status; missing or nonprocedural source tags downgrade external status because reviewers cannot tell whether a citation was tool-verified, officially sourced, user-verified, public metadata, or still needs verification.

## Review Gates

Scenarios can include a `review_gate` object. It records whether attorney review is required, whether review is complete, which reliance gate applies, what jurisdiction assumptions were used, whether adoption reasons and contestation records exist, and whether an irreversible action has human authorization. An unreviewed output cannot become a decision-support reason for external reliance, and an irreversible action without human authorization is withdrawn from external legal effect.

## Real Case Experiment

The repository includes a reproducible source-integrity experiment over six public legal-record sources:

```bash
python scripts/collect_real_cases.py
python -m audit_harness.cli experiment experiments/real_cases/scenarios --out experiments/real_cases/results/real_case_experiment.md --json-out experiments/real_cases/results/real_case_experiment.json
```

By default the script uses the committed public metadata snapshots for deterministic reruns. Pass `--refresh` to download fresh snapshots. The experiment samples 20 records per jurisdiction with a fixed seed, writes source manifests, and runs the harness over the generated output evidence packets. It tests whether evidence packets can be reconstructed and audited; it does not evaluate legal merits, ranking quality or any upstream system architecture. For that reason these metadata-only packets are capped at `professional_support_output`, not `normative_material_screening_output`.

The repository also includes three issue-defined positive-control packets:

```bash
python -m audit_harness.cli experiment experiments/issue_gold_sets/scenarios --out experiments/issue_gold_sets/results/issue_gold_set_experiment.md --json-out experiments/issue_gold_sets/results/issue_gold_set_experiment.json
```

The current positive controls cover:

- U.S. agency statutory interpretation after `Loper Bright`, with manually curated high-authority, limiting and invalidated-treatment labels for `Loper Bright`, `Chevron`, `Skidmore`, APA `5 U.S.C. 706` and `Kisor`;
- English-law mesothelioma causation after `Fairchild`, `Barker`, the Compensation Act 2006 and `Sienkiewicz`;
- EU GDPR Article 15 access-right materials on recipients and copies of personal data, including CJEU decisions C-154/21 and C-487/21 plus regulation-based limitations.

The sensitivity command varies the normative-screening threshold from 8 to 11 for a selected scenario directory. The full validation suite additionally re-evaluates all 62 scenario packets under thresholds 8-12, so threshold robustness is tested across the complete artifact rather than only the stress scenarios.

The issue-ablation suite is generated from the same issue packets:

```bash
python scripts/build_issue_ablations.py
python -m audit_harness.cli experiment experiments/issue_ablations/scenarios --out experiments/issue_ablations/results/issue_ablation_experiment.md --json-out experiments/issue_ablations/results/issue_ablation_experiment.json
```

It removes or weakens one procedural condition at a time. The ablations check that partial high-authority omission, complete-set counter-material suppression, unverified source tags, and missing authorized-adoption gates cap the claimed status.

## Annotation Robustness Study

The repository includes a coding-uncertainty experiment:

```bash
python scripts/run_annotation_robustness.py
```

The script re-scores all 62 committed scenario packets under two alternative coding policies. The strict policy lowers scores when evidence is only internally reviewable, counter-material recall is incomplete, source tags are not procedural, or adoption and contestation records are absent. The lenient policy raises scores only when evidence-packet metrics, authority coverage, counter-authority recall, or review gates support the higher score. It then reports status stability, score deltas, and weighted status agreement against the base coding. This is not a substitute for a future human inter-annotator study, but it directly tests whether the protocol's status outcomes are fragile to plausible audit-vector disagreement.

## Score-Blinded Dual Coding Study

The repository includes a score-blinded coding layer:

```bash
python scripts/build_blind_coding_packets.py
python scripts/run_blind_coding_study.py
```

The packet builder strips original `scores`, `expected_allowed_status`, `expected_disposition`, and manual failure flags from 62 committed score-blinded coding packets. The resulting packet files preserve only the legal-output evidence: claimed status, jurisdiction profile, authority sets, upstream metrics, evidence packet, review gate, and deployment context. Two separate annotation files in `experiments/blind_coding/annotations/` then score the packets under the shared codebook in `experiments/blind_coding/CODEBOOK.md`. The study reports exact status agreement, weighted status agreement, dimension-level agreement, and disputed packets.

## Raw Model Output Pilot

The repository includes a ten-output Codex `gpt-5.5` / `xhigh` pilot:

```bash
python -m audit_harness.cli experiment experiments/ai_outputs/scenarios --out experiments/ai_outputs/results/ai_output_experiment.md --json-out experiments/ai_outputs/results/ai_output_experiment.json
```

Raw outputs are stored in `experiments/ai_outputs/raw/codex_gpt55_xhigh_first10.md`. The pilot asks whether fluent model answers with strong authority and counter-material coverage can claim `normative_material_screening_output` status without source-bound evidence. The current result is deliberately strict: all ten outputs are downgraded to `reference_information` because their citations are marked `needs_verification`.

## Issue-Specific Public Output/Source Study

The repository includes a stricter public layer over issue-specific public search outputs and a source-bound public-source packet:

```bash
python scripts/collect_issue_public_outputs.py
python -m audit_harness.cli experiment experiments/issue_public_outputs/scenarios --out experiments/issue_public_outputs/results/issue_public_output_experiment.md --json-out experiments/issue_public_outputs/results/issue_public_output_experiment.json
```

The default command uses committed snapshots. Pass `--refresh` to fetch current public pages/API output. The study freezes a CourtListener issue search for U.S. agency deference after `Loper Bright`, a National Archives issue search for English mesothelioma causation, and a Legislation.gov.uk/CURIA public-source packet for GDPR Article 15. It then tests whether the visible records preserve enough high-authority and counter-material evidence to claim `normative_material_screening_output` status. The current result is mixed by design: one source-bound public-source packet qualifies, while two issue-search outputs are capped at `reference_information` because their returned records omit high-authority or counter-material materials.

## Public Retrieval Benchmark

The repository includes a true public-search benchmark over issue-defined authority sets:

```bash
python scripts/collect_public_retrieval_benchmark.py
python -m audit_harness.cli experiment experiments/public_retrieval_benchmark/scenarios --out experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.md --json-out experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.json
```

The benchmark freezes twelve public search outputs: six CourtListener queries for U.S. agency deference after `Loper Bright`, and six National Archives queries for English mesothelioma causation after `Fairchild`. It then measures high-authority recall, counter-material recall, source reconstruction and procedural status. The current result is stringent: all twelve real search outputs remain `reference_information`, with mean high-authority recall of 0.11, because top-k public search results do not preserve the complete issue-specific authority and counter-material chain.

## Public System Output Pilot

The repository includes a public legal system output pilot:

```bash
python scripts/collect_public_system_outputs.py
python -m audit_harness.cli experiment experiments/public_system_outputs/scenarios --out experiments/public_system_outputs/results/public_system_output_experiment.md --json-out experiments/public_system_outputs/results/public_system_output_experiment.json
```

This pilot freezes the ordered top 10 records exposed by each of six public legal retrieval or listing systems and converts those visible outputs into provider-agnostic evidence packets. It tests whether real public system outputs can be reconstructed, source-tagged and status-qualified by the harness. It does not evaluate legal merits, doctrinal correctness, issue-specific ranking quality, RAG behavior or any upstream model architecture. The current public-output scenarios are capped at `professional_support_output` because they lack issue-defined counter-material packets and party-facing contestation pathways.

## Repository Layout

```text
audit_harness/          scoring model and CLI
examples/scenarios/     runnable audit scenarios
examples/jurisdiction_profiles/  legal-system parameter profiles
experiments/stress_tests/results/  committed stress-test and sensitivity outputs
experiments/full_validation/        aggregate full-suite validation report
experiments/issue_gold_sets/       curated issue packets and gold-set outputs
experiments/issue_ablations/       generated positive-control ablations
experiments/issue_public_outputs/  issue-specific public output snapshots and scenarios
experiments/public_retrieval_benchmark/ public search snapshots and issue benchmark outputs
experiments/blind_coding/          score-blinded packets and dual-coding outputs
experiments/ai_outputs/            raw Codex model-output pilot and scored scenarios
experiments/real_cases/            public metadata snapshots, manifests and outputs
experiments/public_system_outputs/ ordered public output snapshots and pilot outputs
tests/                  unit tests
docs/paper_mapping.md   mapping from the paper framework to code
.github/workflows/      CI test harness
```
