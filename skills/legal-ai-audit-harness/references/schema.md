# Scenario JSON Schema Guide

Minimum scenario shape:

```json
{
  "id": "scenario-id",
  "claimed_status": "normative_material_screening_output",
  "system_role": "auditable_procedural_tool",
  "jurisdiction_profile": "common_law",
  "deployment_context": "Short description.",
  "scores": {
    "S": { "score": 2, "evidence": "Source evidence." },
    "Q": { "score": 2, "evidence": "Query/version evidence." },
    "H": { "score": 2, "evidence": "Authority hierarchy evidence." },
    "K": { "score": 1, "evidence": "Ranking/counter-material evidence." },
    "T": { "score": 2, "evidence": "Contestability evidence." },
    "L": { "score": 1, "evidence": "Adoption logging evidence." }
  },
  "authority_sets": {
    "high_authority": ["source-a"],
    "retrieved_high_authority": ["source-a"],
    "counter_or_limiting": ["source-b"],
    "retrieved_counter_or_limiting": [],
    "invalid_or_superseded": [],
    "invalid_treatments": [],
    "retrieved_invalid_treatments": [],
    "retrieved": ["source-a"]
  },
  "upstream_metrics": {
    "precision": 0.8,
    "recall": 0.8,
    "f1": 0.8
  },
  "evidence_packet": {
    "output_links": [
      { "unit_id": "unit-1", "source_id": "source-a", "locator": "para 3", "supports_claim": true, "source_tag": "tool_verified" }
    ],
    "output_units": [
      { "id": "unit-1", "claim": "The cited authority supports the material proposition.", "source_ids": ["source-a"], "locators": ["para 3"] }
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

Use deterministic IDs. Keep source text excerpts short and prefer links, paragraph IDs, neutral citations, and hashes over long copyrighted text. `evidence_packet` is provider-agnostic and can be produced by any upstream search, database, generation, agent, or manual review process.

`system_role` is optional but recommended. Use `back_office_tool`, `disclosed_assistance_tool`, `auditable_procedural_tool`, `authorized_decision_support_tool`, or `unaccountable_external_disposition`. The role caps the maximum procedural status, so a disclosed assistance tool cannot become a court-facing screening output without the audit artefacts and review posture of an auditable procedural tool. If omitted, the harness infers the role from `review_gate` and `claimed_status`.

`source_tag` should state how a reviewer should treat the source link, for example `tool_verified`, `official_source`, `public_metadata`, `user_provided`, `user_provided_verified`, `settled`, `needs_verification`, or `pinpoint_needs_verification`. Missing tags downgrade external procedural claims. For `normative_material_screening_output`, tags such as `needs_verification`, `pinpoint_needs_verification`, `public_metadata`, or unverified `user_provided` are not enough; they show the source is visible but not procedurally verified.

For `normative_material_screening_output` or `decision_support_reason`, non-empty authority sets, `evidence_packet`, material claim text in `output_units[*].claim`, `review_gate` and counter-material fields are mandatory. If no counter-material exists after a complete omitted-material check, set `counter_material_complete` to `true` and keep `counter_or_limiting` and `retrieved_counter_or_limiting` present.

`review_gate` records attorney-review and reliance posture. Use `reliance_gate` values such as `internal_only`, `attorney_review`, `not_for_merits_reliance`, `external_reliance`, `filing`, `sending`, `execution`, or `authorized_adoption`. Irreversible action without `human_authorization: true` is withdrawn from external legal effect.
