# Adversarial Source-Support Repair Experiment

This experiment uses the same ten Codex GPT-5.5 xhigh legal-authority outputs as the raw-output and repair experiments, then generates six negative controls per output:

- locator mismatch;
- unsupported claim;
- contradiction-pattern claim;
- out-of-manifest source;
- missing output-source link;
- counter-material omission.

Run:

```bash
python scripts/build_model_output_adversarial.py
python -m audit_harness.cli experiment experiments/model_output_adversarial/scenarios --out experiments/model_output_adversarial/results/model_output_adversarial_experiment.md --json-out experiments/model_output_adversarial/results/model_output_adversarial_experiment.json
```

The suite tests whether the source-support repair layer is merely a hand-built positive control. A valid repair must pass manifest membership, locator, hashed source-support, contradiction-pattern, output-link, source-tag and issue-set checks. The current result rejects all sixty adversarial variants: forty are capped at `reference_information`, and twenty unsupported or contradictory source-support variants are withdrawn as `no_external_legal_effect`.
