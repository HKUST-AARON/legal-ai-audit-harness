# Mapping from `claude-for-legal`

This harness adapts legal-workflow patterns from `anthropics/claude-for-legal` without depending on Claude, an agent runtime, or any specific upstream architecture.

| `claude-for-legal` pattern | Harness implementation |
| --- | --- |
| Legal outputs are drafts for attorney review, not legal conclusions. | `claimed_status` is capped by the score gates and `review_gate`; unsupported outputs cannot become decision-support reasons. |
| Every legal citation should carry source attribution. | `evidence_packet.output_links[*].source_tag` and `source_tag_coverage`. |
| Jurisdiction assumptions are surfaced. | `jurisdiction_profile` plus `review_gate.jurisdiction_assumptions`. |
| Filing, sending, execution, and external reliance require explicit gates. | `review_gate.reliance_gate`, `review_status`, and `human_authorization`. |
| Consequential AI classifications should be per system or use case, not at company level. | Each scenario is an output-specific audit unit; no global obligation table is hardcoded. |
| Policy drift should be reviewed before a sweep is accepted. | Reports are written as artifacts; adoption is separate from generation and remains a human responsibility. |

Keep the harness above the upstream system. It evaluates whether a legal-output evidence packet is reconstructable, contestable, source-tagged and review-gated; it does not evaluate provider internals.
