# Source-Supported Model-Output Repair Experiment

This experiment holds the ten raw Codex GPT-5.5 xhigh legal-authority outputs constant and changes only the audit posture: the visible authorities are connected to source collections, output-source links, and a completed professional review gate.

Run:

```bash
python scripts/build_model_output_repairs.py
python -m audit_harness.cli experiment experiments/model_output_repairs/scenarios --out experiments/model_output_repairs/results/model_output_repair_experiment.md --json-out experiments/model_output_repairs/results/model_output_repair_experiment.json
```

The builder validates every repaired output-source link against the issue manifest, locator, hashed manifest source-support excerpt, contradiction patterns, procedural source tag, high-authority coverage and counter-material coverage before writing `source_binding_validation` and derived scores. The experiment tests whether procedural status turns on source support rather than model identity. Raw model outputs remain `reference_information`; validator-backed source-supported variants of the same outputs qualify as `normative_material_screening_output` but not as `decision_support_reason`.
