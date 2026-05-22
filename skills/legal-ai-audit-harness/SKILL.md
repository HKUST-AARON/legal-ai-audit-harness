---
name: legal-ai-audit-harness
description: Use when evaluating legal AI outputs above any search, retrieval, generation, agent, database, or manual review stack for procedural status, verifiability, contestability, audit readiness, jurisdictional authority mapping, or when running the legal-ai-audit-harness CLI on scenario JSON files.
---

# Legal AI Audit Harness

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

1. Identify the claimed procedural status:
   - `reference_information`
   - `professional_support_output`
   - `normative_material_screening_output`
   - `decision_support_reason`
   - `no_external_legal_effect`
2. Select or define the jurisdiction profile before scoring `H` and `K`.
3. Prepare a scenario JSON file with scores, evidence, authority sets, upstream metrics, optional `evidence_packet`, and optional `review_gate`.
4. Run the harness from the repository root:

```bash
python -m audit_harness.cli score examples/scenarios/court_authority_report.json
python -m audit_harness.cli run examples/scenarios --out reports/sample_report.md --json-out reports/sample_report.json
python -m audit_harness.cli experiment examples/scenarios --out reports/experiment_report.md --json-out reports/experiment_report.json
```

5. Treat strong upstream performance as insufficient if the output fails source reconstruction, source tagging, counter-material presentation, contestability, review gating, or adoption logging.
6. For paper or review work, report the harness as a status-allocation instrument, not as a legal merits evaluator.

## Status Rules

- `reference_information`: `S >= 1` and `Q >= 1`
- `professional_support_output`: `S, Q, L >= 1`
- `normative_material_screening_output`: all six dimensions `>= 1` and total score `>= 9`
- `decision_support_reason`: `S, Q, H, K >= 1` and `T = L = 2`
- `no_external_legal_effect`: missing gates or withdrawal-level failures

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
