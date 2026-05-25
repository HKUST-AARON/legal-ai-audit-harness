# Real Case Source-Integrity Experiment

This experiment tests the harness above any upstream search, retrieval, generation, agent, database, or manual review stack. It asks whether a legal-output evidence packet can be reconstructed from public case metadata across jurisdictions.

Run:

```bash
python scripts/collect_real_cases.py
python -m audit_harness.cli experiment experiments/real_cases/scenarios --out experiments/real_cases/results/real_case_experiment.md --json-out experiments/real_cases/results/real_case_experiment.json
```

By default `collect_real_cases.py` uses the committed source snapshots in `downloads/`. Pass `--refresh` to fetch current source pages and feeds.

Sampling:

- Fixed base seed: `20260523`
- Jurisdictions: Hong Kong, Mainland China, United States, United Kingdom, Germany, Canada
- Sample size: 20 records per jurisdiction
- Candidate pools: public metadata pages, feeds, or APIs downloaded into `downloads/`

Sources:

- Hong Kong: HKLII Court of Final Appeal API
- Mainland China: Supreme People's Court English Typical Cases pages
- United States: Supreme Court of the United States slip-opinion pages
- United Kingdom: The National Archives Find Case Law Atom feed
- Germany: OpenLegalData German case API
- Canada: Supreme Court of Canada JSON feed

Scope:

- The experiment uses public metadata, citations, docket numbers, court labels, dates, URLs and source collection labels.
- It does not copy full case texts into the scenario evidence packets.
- Each output link is tagged as `public_metadata`, and each generated scenario uses a `not_for_merits_reliance` review gate. These scenarios are expected to reach `professional_support_output` because they supply source reconstruction without issue-specific ranking or counter-material gold sets.
