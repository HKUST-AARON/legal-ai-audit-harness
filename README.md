# Legal AI Audit Harness

A lightweight scoring harness for legal AI outputs above any search, retrieval, generation, agent, database, or manual review stack.

The harness operationalizes a verifiability-based audit model for deciding whether a legal AI output should remain an internal reference, qualify as professional support, qualify as a normative material screening output, or be treated as a decision-support reason only after accountable human adoption.

## Model

Each scenario scores six dimensions from `0` to `2`:

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

It applies gate rules, total-score rules, authority coverage, counter-authority recall, output-evidence metrics, source-attribution checks, human-review gates, and downgrade or withdrawal triggers.

The repository follows a local-first CLI and artifact-log pattern: each run is reproducible from local scenario files, produces Markdown/JSON artifacts, and is checked by CI. Its legal-workflow guardrails are adapted from the public [`anthropics/claude-for-legal`](https://github.com/anthropics/claude-for-legal) design: legal AI outputs remain draft or screening artefacts until a review gate is satisfied; source links carry source tags; jurisdiction assumptions are explicit; and actions such as filing, sending, external reliance, or execution require accountable human authorization. The harness does not import or require an agent runtime, and it does not inspect upstream implementation details.

## Quick Start

```bash
python -m audit_harness.cli score examples/scenarios/court_authority_report.json
python -m audit_harness.cli run examples/scenarios --out reports/sample_report.md --json-out reports/sample_report.json
python -m audit_harness.cli experiment examples/scenarios --out reports/experiment_report.md --json-out reports/experiment_report.json
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
      { "source_id": "binding-precedent-a", "locator": "para 3", "supports_claim": true, "source_tag": "tool_verified" }
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
| `decision_support_reason` | `S, Q, H, K >= 1` and `T = L = 2` |
| `no_external_legal_effect` | missing gates or withdrawal-level failures |

Failure flags can downgrade or withdraw an output from external procedural use.

## Jurisdiction Profiles

Profiles in `examples/jurisdiction_profiles/` parameterize `H` and `K` for different legal settings. Common-law scenarios use binding and persuasive precedent labels, while civil-law scenarios use code provisions, special statutes, high-court decisions, doctrinal views and later amendments. The scoring dimensions stay stable; the legal materials used to prove each dimension vary by profile.

## Output Evidence Auditing

Scenarios can include an `evidence_packet` object with output-to-source mappings. This sits above any upstream implementation. The harness reports evidence fidelity, evidence coverage, and source-tag coverage. Unsupported output units are withdrawal-level failures when they claim external procedural status; missing source tags downgrade external status because reviewers cannot tell whether a citation was tool-verified, user-provided, public metadata, or still needs verification.

## Review Gates

Scenarios can include a `review_gate` object. It records whether attorney review is required, whether review is complete, which reliance gate applies, what jurisdiction assumptions were used, and whether an irreversible action has human authorization. An unreviewed output cannot become a decision-support reason for external reliance, and an irreversible action without human authorization is withdrawn from external legal effect.

## Real Case Experiment

The repository includes a reproducible source-integrity experiment over six jurisdictions:

```bash
python scripts/collect_real_cases.py
python -m audit_harness.cli experiment experiments/real_cases/scenarios --out experiments/real_cases/results/real_case_experiment.md --json-out experiments/real_cases/results/real_case_experiment.json
```

By default the script uses the committed public metadata snapshots for deterministic reruns. Pass `--refresh` to download fresh snapshots. The experiment samples 20 records per jurisdiction with a fixed seed, writes source manifests, and runs the harness over the generated output evidence packets. It tests whether evidence packets can be reconstructed and audited; it does not evaluate legal merits, ranking quality or any upstream system architecture. For that reason these metadata-only packets are capped at `professional_support_output`, not `normative_material_screening_output`.

The repository also includes one issue-defined gold-set experiment:

```bash
python -m audit_harness.cli experiment experiments/issue_gold_sets/scenarios --out experiments/issue_gold_sets/results/issue_gold_set_experiment.md --json-out experiments/issue_gold_sets/results/issue_gold_set_experiment.json
```

The current gold set covers U.S. agency statutory interpretation after `Loper Bright`, with manually curated high-authority, limiting and invalidated-authority treatment for `Loper Bright`, `Chevron`, `Skidmore`, APA `5 U.S.C. 706` and `Kisor`.

## Repository Layout

```text
audit_harness/          scoring model and CLI
examples/scenarios/     runnable audit scenarios
examples/jurisdiction_profiles/  legal-system parameter profiles
tests/                  unit tests
docs/paper_mapping.md   mapping from the paper framework to code
.github/workflows/      CI test harness
```
