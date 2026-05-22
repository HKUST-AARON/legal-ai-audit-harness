# Codex GPT-5.5 xhigh Output Audit Pilot

This experiment audits ten raw Codex `gpt-5.5` / `xhigh` legal authority recommendations as the object under review. It is different from the public metadata and public-system-output experiments: the unit here is an upstream model answer, not a court database record or a curated issue packet.

Run:

```bash
python -m audit_harness.cli experiment experiments/ai_outputs/scenarios --out experiments/ai_outputs/results/ai_output_experiment.md --json-out experiments/ai_outputs/results/ai_output_experiment.json
```

Raw outputs are stored in `raw/codex_gpt55_xhigh_first10.md`. Each scenario records the prompt, model label, visible cited authorities, authority coverage, counter-material coverage, source-tag posture, review gate and adoption record. The harness then decides the output's procedural status.

The experiment asks:

- whether high-quality model answers with good authority coverage nevertheless fail procedural qualification when their citations are not source-bound;
- whether `normative_material_screening_output` should require more than fluent legal reasoning and recognizable case names;
- whether the harness separates upstream legal-content coverage from procedural verifiability.

This is an output audit, not a model benchmark. It does not inspect model weights, hidden prompts, vendor internals or RAG architecture. In this pilot, all ten Codex outputs are intentionally treated as raw model text: their source tags are `needs_verification`, so a claimed screening output is downgraded unless source-bound evidence is added.
