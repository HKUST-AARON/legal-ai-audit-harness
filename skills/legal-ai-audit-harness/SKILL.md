---
name: legal-ai-audit-harness
description: Use when evaluating legal AI outputs above any search, retrieval, generation, agent, database, or manual review stack for procedural status, verifiability, contestability, audit readiness, jurisdictional authority mapping, or when running the legal-ai-audit-harness CLI on scenario JSON files.
---

# Legal AI Audit Harness

This skill has two functions:

1. **Output capture and scenario construction.** Convert a legal AI, RAG, search, database, agent, or human-review output into a provider-agnostic scenario JSON. This includes the issue, upstream output text or visible result list, source links, authority sets, counter-materials, review gate, and evidence packet.
2. **Procedural-status scoring.** Run the repository harness to score the scenario and decide whether the output remains `reference_information`, qualifies as `professional_support_output`, qualifies as `normative_material_screening_output`, becomes a `decision_support_reason`, or must be downgraded/withdrawn.

Use the skill as the operating layer and the repository CLI as the scoring engine. The skill should not pretend to evaluate hidden model internals. It evaluates the legal output and its audit artefacts.

Use this skill to evaluate legal AI outputs with the verifiability-based audit model:

```text
A(o) = (S, Q, H, K, T, L)
```

Score each dimension from `0` to `2`:

- `S`: source and corpus verifiability
- `Q`: query and version traceability
- `H`: authority-hierarchy representation
- `K`: ranking and counter-material verifiability
- `T`: contestability support
- `L`: adoption logging and audit responsibility

## Workflow

1. Identify the upstream output to audit:
   - captured LLM answer;
   - RAG answer with citations;
   - case-recommendation list;
   - public legal-search/listing output;
   - manually reviewed legal-material packet.
2. Record the issue, jurisdiction, source collection, visible output units, cited authorities, source locators, counter-materials and review/adoption posture.
3. Identify the claimed procedural status:
   - `reference_information`
   - `professional_support_output`
   - `normative_material_screening_output`
   - `decision_support_reason`
   - `no_external_legal_effect`
4. Identify the system role:
   - `back_office_tool`
   - `disclosed_assistance_tool`
   - `auditable_procedural_tool`
   - `authorized_decision_support_tool`
   - `unaccountable_external_disposition`
5. Select or define the jurisdiction profile before scoring `H` and `K`.
6. Prepare a scenario JSON file with scores, evidence, authority sets, upstream metrics, optional `system_role`, optional `upstream_output`, optional `evidence_packet`, and optional `review_gate`.
7. Run the harness from the repository root:

```bash
python -m audit_harness.cli score examples/scenarios/court_authority_report.json
python -m audit_harness.cli run examples/scenarios --out reports/sample_report.md --json-out reports/sample_report.json
python -m audit_harness.cli experiment examples/scenarios --out reports/experiment_report.md --json-out reports/experiment_report.json
python -m audit_harness.cli experiment experiments/ai_outputs/scenarios --out experiments/ai_outputs/results/ai_output_experiment.md --json-out experiments/ai_outputs/results/ai_output_experiment.json
python scripts/collect_issue_public_outputs.py
python scripts/collect_public_retrieval_benchmark.py
python scripts/verify_source_text_anchors.py
python scripts/build_blind_coding_packets.py
python scripts/run_blind_coding_study.py
python scripts/run_annotation_robustness.py
```

8. Treat strong upstream performance as insufficient if the output fails source reconstruction, source tagging, counter-material presentation, contestability, review gating, role gating, or adoption logging.
9. For paper or review work, report the harness as a status-allocation instrument, not as a legal merits evaluator.

## Full Validation Protocol

When the user asks for the most complete validation, run the full matrix rather than only a single pilot:

```bash
python scripts/run_full_validation.py
python -m unittest discover -s tests
```

The full matrix includes stress scenarios, public metadata records, public legal-system outputs, issue-specific public output/source packets, a public retrieval benchmark, raw model outputs, source-supported model-output repairs, adversarial source-support repairs, public source-text anchor checks, issue-defined positive controls, issue ablations, annotation robustness recoding, score-blinded dual coding and threshold sensitivity reports. Report the aggregate file at `experiments/full_validation/results/full_validation_report.md`, the source-text anchor file at `experiments/source_text_verification/results/source_text_anchor_verification.md`, the issue-public-output file at `experiments/issue_public_outputs/results/issue_public_output_experiment.md`, the public retrieval file at `experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.md`, the model-repair files at `experiments/model_output_repairs/results/model_output_repair_experiment.md` and `experiments/model_output_adversarial/results/model_output_adversarial_experiment.md`, the recoding file at `experiments/annotation_robustness/results/annotation_robustness.md`, and the blind-coding file at `experiments/blind_coding/results/blind_coding_study.md`. Describe it as scenario-regression, artifact validation, public retrieval audit, public output/source audit, source-support positive and negative control validation, external source-anchor validation, and coding-uncertainty analysis, not as independent legal merits validation.

## Single-Model Output Audit Protocol

When the user asks to evaluate one model or provider, run a ten-output pilot before claiming broader empirical validation:

1. Choose 2--3 issue-defined legal questions with known high-authority and counter-material sets.
2. Capture or generate one upstream output at a time. Save raw prompts, output text, provider label if available, timestamp, source links and any visible citations.
3. Convert each output into one scenario under `experiments/ai_outputs/scenarios/`.
4. Score each scenario immediately with `python -m audit_harness.cli score <scenario>`.
5. Fix only schema/scoring defects that prevent faithful auditing. Do not massage the output to obtain a better status.
6. After ten outputs, run:

```bash
python -m audit_harness.cli experiment experiments/ai_outputs/scenarios --out experiments/ai_outputs/results/ai_output_experiment.md --json-out experiments/ai_outputs/results/ai_output_experiment.json
python -m unittest discover -s tests
```

Report both halves separately: (a) what upstream outputs were captured, and (b) what procedural status the harness assigned.

## Status Rules

- `reference_information`: `S >= 1` and `Q >= 1`
- `professional_support_output`: `S, Q, L >= 1`
- `normative_material_screening_output`: all six dimensions `>= 1` and total score `>= 9`
- `decision_support_reason`: `S, Q, H, K >= 1`, `T = L = 2`, completed authorized adoption, human authorization, jurisdiction assumptions, adoption reasons and contestation record
- `no_external_legal_effect`: missing gates or withdrawal-level failures

System roles cap status:

- `back_office_tool`: maximum `reference_information`
- `disclosed_assistance_tool`: maximum `professional_support_output`
- `auditable_procedural_tool`: maximum `normative_material_screening_output`
- `authorized_decision_support_tool`: maximum `decision_support_reason`
- `unaccountable_external_disposition`: maximum `no_external_legal_effect`

Failure flags can cap or downgrade status:

- `authority_omission`
- `counter_material_suppression`
- `invalid_authority`
- `ranking_drift`
- `source_attribution_gap`
- `jurisdiction_assumption_gap`
- `review_gate_failure`
- `unauthorized_action`
- `summary_distortion`
- `automation_dependence`
- `contestation_failure`

## References

- Read `references/schema.md` when creating or validating scenario JSON.
- Read `references/jurisdictions.md` when scoring Hong Kong, Mainland China, United States, United Kingdom, Germany, or Canada.
- Read `references/claude_for_legal_mapping.md` when explaining how the harness adapts legal-workflow guardrails from `anthropics/claude-for-legal`.
