# Public Retrieval Benchmark

This experiment freezes public search outputs and scores them against endpoint-compatible high-authority and counter-material sets.

```bash
python scripts/collect_public_retrieval_benchmark.py
python -m audit_harness.cli experiment experiments/public_retrieval_benchmark/scenarios --out experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.md --json-out experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.json
```

The current benchmark uses thirty committed outputs across five issue families: CourtListener searches for U.S. agency deference after `Loper Bright`, National Archives searches for English mesothelioma causation after `Fairchild`, Supreme Court of Canada Lexum searches for standard of review after `Vavilov`, OpenLegalData searches for German/EU right-to-be-forgotten review, and CURIA list/search outputs for EU GDPR Article 15 access-right cases. It tests whether visible top-k records preserve the authority and counter-material chain required for `normative_material_screening_output`. Case-law endpoints are scored against case-law gold sets; mixed statute/case screening is tested in the issue-defined public source-screening packets.
