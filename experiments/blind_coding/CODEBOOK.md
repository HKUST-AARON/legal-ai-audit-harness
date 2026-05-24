# Blind Coding Codebook

Coders score each packet without reading the original scenario `scores`, `expected_allowed_status`, `expected_disposition`, or prior harness result.

Use only the packet JSON fields: `claimed_status`, `jurisdiction_profile`, `deployment_context`, `authority_sets`, `upstream_metrics`, `evidence_packet`, `review_gate`, and `counter_material_complete`.

## Scores

Score each dimension `0`, `1`, or `2`.

- `S`: source and corpus verifiability.
  - `0`: sources or corpus cannot be reconstructed.
  - `1`: sources are named or linked, but corpus scope, source tags, official verification, or update status is incomplete.
  - `2`: source identifiers, locators, verification posture, corpus/source collection, and version/update context are reviewable.
- `Q`: query and version traceability.
  - `0`: issue, query, output ID, source collection, or run state is unavailable.
  - `1`: some issue or output context is available but incomplete.
  - `2`: issue/output context, source collection, workflow or capture mode, and output identity are reconstructable.
- `H`: authority hierarchy.
  - `0`: legal status is not distinguished.
  - `1`: broad categories such as court, source type, binding/persuasive, statutory/case material, or authority level are present.
  - `2`: jurisdiction, hierarchy, validity, later treatment, and relation to governing norms are reviewable.
- `K`: ranking and counter-material verifiability.
  - `0`: ranking is opaque and no contrary or limiting materials are surfaced.
  - `1`: ordering, ranking factors, or some contrary/limiting materials are present but incomplete.
  - `2`: retrieved high-authority materials, counter/limiting materials, omitted-material checks, and ranking or issue-set logic are reviewable.
- `T`: contestability support.
  - `0`: affected reviewers cannot inspect or challenge the output.
  - `1`: internal or professional reviewer can inspect and challenge.
  - `2`: party-facing or decision-procedure-facing challenge, supplement, and recorded response path exists.
- `L`: adoption logging and audit responsibility.
  - `0`: no adoption path or responsible actor is recorded.
  - `1`: run/output/reviewer action is logged but no authorized adoption with reasons is recorded.
  - `2`: output ID, displayed materials, accepted/rejected items, reasons, timestamp, responsible actor, and contestation record are logged.

## Failure Flags

Add only flags directly supported by packet evidence:

- `authority_omission`: `retrieved_high_authority` omits a known `high_authority`.
- `counter_material_suppression`: known counter/limiting materials exist but are not retrieved, or `counter_material_complete` is true and the retrieved counter set is incomplete.
- `invalid_authority`: retrieved authorities or treatments include known invalid/superseded items.
- `source_attribution_gap`: claimed normative or decision status uses missing/non-procedural source tags such as `needs_verification`.
- `jurisdiction_assumption_gap`: claimed normative or decision status lacks jurisdiction assumptions.
- `review_gate_failure`: required professional or institutional review is incomplete.
- `unauthorized_action`: irreversible action is present without human authorization.
- `summary_distortion`: output-source links do not support the output units or locators are missing.
- `contestation_failure`: claimed decision status lacks contestation record.

Return one JSON file:

```json
{
  "coder_id": "coder_a",
  "annotations": [
    {
      "packet_id": "packet-id",
      "scores": {"S": 1, "Q": 2, "H": 2, "K": 1, "T": 1, "L": 1},
      "failure_flags": ["source_attribution_gap"],
      "notes": "Short rationale."
    }
  ]
}
```
