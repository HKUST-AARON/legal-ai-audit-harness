from __future__ import annotations

import json
import random
import sys
from copy import deepcopy
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audit_harness.model import DIMENSIONS, STATUS_RANK, evaluate_scenario

RESULTS = ROOT / "experiments" / "annotation_uncertainty" / "results"
SCENARIO_DIRS = [
    ROOT / "examples" / "scenarios",
    ROOT / "experiments" / "real_cases" / "scenarios",
    ROOT / "experiments" / "public_system_outputs" / "scenarios",
    ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios",
    ROOT / "experiments" / "ai_outputs" / "scenarios",
    ROOT / "experiments" / "model_output_repairs" / "scenarios",
    ROOT / "experiments" / "model_output_evidence_ladder" / "scenarios",
    ROOT / "experiments" / "model_output_adversarial" / "scenarios",
    ROOT / "experiments" / "issue_public_outputs" / "scenarios",
    ROOT / "experiments" / "issue_gold_sets" / "scenarios",
    ROOT / "experiments" / "issue_ablations" / "scenarios",
]
ITERATIONS = 250
SEED = 10506
SHIFT_PROBABILITY = 0.10


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    scenarios = _load_scenarios()
    rows = [_scenario_uncertainty(scenario, rng) for scenario in scenarios]
    evaluation_count = len(rows) * ITERATIONS
    stable_samples = sum(row["stable_samples"] for row in rows)
    qualified_rows = [row for row in rows if STATUS_RANK[row["base_status"]] >= STATUS_RANK["normative_material_screening_output"]]
    payload = {
        "scenario_count": len(rows),
        "iterations_per_scenario": ITERATIONS,
        "evaluation_count": evaluation_count,
        "seed": SEED,
        "shift_probability": SHIFT_PROBABILITY,
        "status_stability_rate": stable_samples / evaluation_count,
        "scenario_exact_stability_count": sum(row["status_stability_rate"] == 1 for row in rows),
        "scenario_high_stability_count": sum(row["high_status_stability_rate"] == 1 for row in rows),
        "qualified_scenario_count": len(qualified_rows),
        "qualified_status_stability_rate": mean(row["status_stability_rate"] for row in qualified_rows),
        "qualified_high_status_stability_rate": mean(row["high_status_stability_rate"] for row in qualified_rows),
        "mean_status_rank_shift": mean(row["mean_status_rank_shift"] for row in rows),
        "boundary_scenarios": [row for row in rows if row["status_stability_rate"] < 0.95],
        "rows": rows,
    }
    (RESULTS / "annotation_uncertainty.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (RESULTS / "annotation_uncertainty.md").write_text(_format_report(payload) + "\n", encoding="utf-8")
    print(_format_report(payload))
    return 0


def _load_scenarios() -> list[dict]:
    scenarios = []
    for directory in SCENARIO_DIRS:
        for path in sorted(directory.glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            scenario["_source_path"] = str(path.relative_to(ROOT))
            scenarios.append(scenario)
    return scenarios


def _scenario_uncertainty(scenario: dict, rng: random.Random) -> dict:
    base = evaluate_scenario(scenario)
    base_rank = STATUS_RANK[base.allowed_status]
    stable = high_stable = upward = downward = 0
    rank_shifts = []
    distribution: dict[str, int] = {}
    for _ in range(ITERATIONS):
        perturbed = _perturbed_scores(scenario, rng)
        result = evaluate_scenario(perturbed)
        rank = STATUS_RANK[result.allowed_status]
        distribution[result.allowed_status] = distribution.get(result.allowed_status, 0) + 1
        stable += int(result.allowed_status == base.allowed_status)
        high_stable += int(_is_high_status(result.allowed_status) == _is_high_status(base.allowed_status))
        upward += int(rank > base_rank)
        downward += int(rank < base_rank)
        rank_shifts.append(abs(rank - base_rank))
    return {
        "scenario_id": scenario["id"],
        "source_path": scenario["_source_path"],
        "base_status": base.allowed_status,
        "base_score": base.total_score,
        "stable_samples": stable,
        "high_status_stable_samples": high_stable,
        "upward_shifts": upward,
        "downward_shifts": downward,
        "status_stability_rate": stable / ITERATIONS,
        "high_status_stability_rate": high_stable / ITERATIONS,
        "mean_status_rank_shift": mean(rank_shifts),
        "distribution": distribution,
    }


def _perturbed_scores(scenario: dict, rng: random.Random) -> dict:
    perturbed = deepcopy(scenario)
    perturbed.pop("_source_path", None)
    perturbed.pop("expected_allowed_status", None)
    perturbed.pop("expected_disposition", None)
    for dimension in DIMENSIONS:
        score = _score(perturbed, dimension)
        roll = rng.random()
        if roll < SHIFT_PROBABILITY:
            score = max(0, score - 1)
        elif roll > 1 - SHIFT_PROBABILITY:
            score = min(2, score + 1)
        perturbed["scores"][dimension] = _score_value(perturbed["scores"][dimension], score)
    return perturbed


def _score(scenario: dict, dimension: str) -> int:
    value = scenario["scores"][dimension]
    return int(value.get("score", value) if isinstance(value, dict) else value)


def _score_value(current, score: int):
    if isinstance(current, dict):
        updated = dict(current)
        updated["score"] = score
        return updated
    return score


def _is_high_status(status: str) -> bool:
    return STATUS_RANK[status] >= STATUS_RANK["normative_material_screening_output"]


def _format_report(payload: dict) -> str:
    lines = [
        "# Annotation Uncertainty Analysis",
        "",
        f"Scenario packets: {payload['scenario_count']}",
        f"Monte Carlo score perturbations: {payload['evaluation_count']}",
        f"Iterations per scenario: {payload['iterations_per_scenario']}",
        f"Seed: {payload['seed']}",
        f"Per-dimension shift probability: {payload['shift_probability']:.2f}",
        f"Sample-level status stability: {payload['status_stability_rate']:.3f}",
        f"Exact-stable scenarios: {payload['scenario_exact_stability_count']}/{payload['scenario_count']}",
        f"High-status boundary stable scenarios: {payload['scenario_high_stability_count']}/{payload['scenario_count']}",
        f"Qualified scenarios: {payload['qualified_scenario_count']}",
        f"Qualified exact-status stability: {payload['qualified_status_stability_rate']:.3f}",
        f"Qualified high-status stability: {payload['qualified_high_status_stability_rate']:.3f}",
        f"Mean absolute status-rank shift: {payload['mean_status_rank_shift']:.3f}",
        f"Boundary scenarios below 0.95 exact stability: {len(payload['boundary_scenarios'])}",
        "",
        "## Boundary Scenarios",
        "",
        "| Scenario | Base status | Stability | High-status stability | Up | Down | Distribution |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in sorted(payload["boundary_scenarios"], key=lambda item: item["status_stability_rate"])[:40]:
        distribution = ", ".join(f"{status}: {count}" for status, count in sorted(row["distribution"].items()))
        lines.append(
            "| "
            + " | ".join(
                [
                    row["scenario_id"],
                    row["base_status"],
                    f"{row['status_stability_rate']:.3f}",
                    f"{row['high_status_stability_rate']:.3f}",
                    str(row["upward_shifts"]),
                    str(row["downward_shifts"]),
                    distribution,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
