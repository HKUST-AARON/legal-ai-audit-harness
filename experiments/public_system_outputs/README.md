# Public Legal System Output Pilot

This experiment audits ordered outputs from public legal retrieval or listing systems. It is distinct from the public metadata validation in `experiments/real_cases`: the unit here is the visible top-k output stream exposed by a public system, not a random sample from a source pool.

```bash
python scripts/collect_public_system_outputs.py
python -m audit_harness.cli experiment experiments/public_system_outputs/scenarios --out experiments/public_system_outputs/results/public_system_output_experiment.md --json-out experiments/public_system_outputs/results/public_system_output_experiment.json
```

The default run uses committed snapshots for deterministic reruns. Pass `--refresh` to download fresh snapshots before rebuilding manifests and scenarios.

The current pilot uses top 10 records from each of six public output streams. The scenarios are expected to reach `professional_support_output`, not `normative_material_screening_output`, because public output lists expose source-visible legal materials but do not define issue-specific counter-material gold sets or party-facing contestability.
