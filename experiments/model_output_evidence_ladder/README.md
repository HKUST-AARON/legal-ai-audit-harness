# Model-Output Evidence Ladder

This experiment reuses the ten committed Codex GPT-5.5 xhigh legal outputs and evaluates each output under seven controlled evidence conditions:

1. raw unverified output;
2. source-bound output with a counter-material omission;
3. source-bound output without contestability;
4. source-bound output without audit logging;
5. contestable normative-material screening;
6. authorized decision-support adoption;
7. unauthorized irreversible external action.

The ladder tests whether procedural status changes with source binding, counter-material coverage, contestability, logging and adoption conditions while holding the upstream model output fixed.

Replication:

```bash
python scripts/build_model_output_evidence_ladder.py
python -m audit_harness.cli experiment experiments/model_output_evidence_ladder/scenarios \
  --out experiments/model_output_evidence_ladder/results/model_output_evidence_ladder_experiment.md \
  --json-out experiments/model_output_evidence_ladder/results/model_output_evidence_ladder_experiment.json
```
