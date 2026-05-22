# Legal AI Audit Harness

A lightweight scoring harness for legal AI case-recommendation and legal-retrieval outputs.

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

It applies gate rules, total-score rules, counter-authority recall, and downgrade or withdrawal triggers.

## Quick Start

```bash
python -m audit_harness.cli score examples/scenarios/court_authority_report.json
python -m audit_harness.cli run examples/scenarios --out reports/sample_report.md --json-out reports/sample_report.json
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
  "scores": {
    "S": { "score": 2, "evidence": "Corpus manifest and source links are recorded." },
    "Q": { "score": 2, "evidence": "Query, filters, model and index version are recorded." },
    "H": { "score": 2, "evidence": "Binding, persuasive and invalid authorities are labelled." },
    "K": { "score": 1, "evidence": "Ranking factors are broad; counter-material recall is incomplete." },
    "T": { "score": 2, "evidence": "Reviewers can inspect and challenge the result set." },
    "L": { "score": 1, "evidence": "Adoption is logged, but reasons are not structured." }
  },
  "counter_authority": {
    "known": ["limiting-authority-a", "contrary-authority-b"],
    "retrieved": ["limiting-authority-a"]
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

## Repository Layout

```text
audit_harness/          scoring model and CLI
examples/scenarios/     runnable audit scenarios
tests/                  unit tests
docs/paper_mapping.md   mapping from the paper framework to code
.github/workflows/      CI test harness
```
