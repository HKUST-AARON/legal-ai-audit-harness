# Issue-Defined Gold Set Experiment

This experiment adds one real legal issue with a manually curated authority set. It is not a model benchmark and it does not call any upstream retrieval or generation system. It tests whether the audit model can distinguish a source-integrity packet from a real normative material screening packet with high-authority materials, limiting materials, invalidated authority treatment, source tags and a review gate.

Run:

```bash
python -m audit_harness.cli experiment experiments/issue_gold_sets/scenarios --out experiments/issue_gold_sets/results/issue_gold_set_experiment.md --json-out experiments/issue_gold_sets/results/issue_gold_set_experiment.json
```

Scenario:

- `us-agency-deference-after-loper-bright`: U.S. federal administrative-law issue packet for agency statutory interpretations after `Loper Bright`.

The manually curated set includes:

- high-authority materials: `Loper Bright`, `Chevron`, APA `5 U.S.C. 706`, and `Skidmore`;
- limiting or counter-materials: `Skidmore` and `Kisor`;
- invalidated treatment: `Chevron` as a currently controlling mandatory deference rule.

The scenario qualifies as `normative_material_screening_output` because it defines an issue, distinguishes current controlling authority from overruled deference treatment, exposes limiting materials, and provides source-tagged output-to-source links. It does not qualify as a decision-support reason because it has not been adopted by a court, agency, arbitrator or other authorized decision-maker.
