# Public Retrieval Benchmark

This experiment freezes true public search outputs and scores them against issue-defined high-authority and counter-material sets.

```bash
python scripts/collect_public_retrieval_benchmark.py
python -m audit_harness.cli experiment experiments/public_retrieval_benchmark/scenarios --out experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.md --json-out experiments/public_retrieval_benchmark/results/public_retrieval_benchmark.json
```

The current benchmark uses twelve committed outputs: six CourtListener searches for U.S. agency deference after `Loper Bright`, and six National Archives searches for English mesothelioma causation after `Fairchild`. It tests whether the visible top-k records preserve the authority and counter-material chain required for `normative_material_screening_output`.
