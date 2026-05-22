# Issue-Defined Gold Set Experiment

This experiment adds three real legal issues with manually curated authority sets. It is not a model benchmark and it does not call any upstream retrieval or generation system. It tests whether the audit model can distinguish a source-integrity packet from a real normative material screening packet with high-authority materials, limiting materials, invalidated treatment labels, source tags and a review gate.

Run:

```bash
python -m audit_harness.cli experiment experiments/issue_gold_sets/scenarios --out experiments/issue_gold_sets/results/issue_gold_set_experiment.md --json-out experiments/issue_gold_sets/results/issue_gold_set_experiment.json
```

Scenarios:

- `us-agency-deference-after-loper-bright`: U.S. federal administrative-law issue packet for agency statutory interpretations after `Loper Bright`.
- `uk-mesothelioma-causation-after-fairchild`: English-law tort issue packet for mesothelioma causation and liability after `Fairchild`, `Barker`, the Compensation Act 2006 and `Sienkiewicz`.
- `eu-gdpr-article15-access-rights`: EU-law issue packet for GDPR Article 15 access rights concerning recipient identity and copies of personal data.

## Curation Protocol

Each issue packet uses public, stable source links and keeps legal propositions short. Sources are selected under four rules:

1. include governing statutes, regulations or apex-court/Court of Justice materials that a competent reviewer would expect to see for the issue;
2. include limiting, contrary, superseding or exception materials where omission would make the result set one-sided;
3. label invalidated treatments separately from historical authorities, so a source can be visible without being presented as current controlling law;
4. record output-source links with `unit_id`, `source_id`, locator and source tag, so each material claim can be checked against a specific authority.

The gold sets are audit artifacts, not jurisdictional treatises. They validate the protocol's behavior across different authority structures.

The manually curated U.S. set includes:

- high-authority materials: `Loper Bright`, APA `5 U.S.C. 706`, and `Skidmore`;
- limiting or counter-materials: `Skidmore` and `Kisor`;
- invalidated treatment: `Chevron` as a currently controlling mandatory deference rule.

The scenarios qualify as `normative_material_screening_output` because each defines an issue, distinguishes current high-authority materials from limiting or invalidated treatment, exposes counter-materials, and provides source-tagged output-to-source links. They do not qualify as decision-support reasons because none has been adopted by a court, agency, arbitrator or other authorized decision-maker.
