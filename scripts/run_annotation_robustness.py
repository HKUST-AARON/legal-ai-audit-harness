from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audit_harness.model import DIMENSIONS, STATUS_RANK, evaluate_scenario

RESULTS = ROOT / "experiments" / "annotation_robustness" / "results"
SCENARIO_DIRS = [
    ROOT / "examples" / "scenarios",
    ROOT / "experiments" / "real_cases" / "scenarios",
    ROOT / "experiments" / "public_system_outputs" / "scenarios",
    ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios",
    ROOT / "experiments" / "ai_outputs" / "scenarios",
    ROOT / "experiments" / "model_output_repairs" / "scenarios",
    ROOT / "experiments" / "model_output_adversarial" / "scenarios",
    ROOT / "experiments" / "issue_public_outputs" / "scenarios",
    ROOT / "experiments" / "issue_gold_sets" / "scenarios",
    ROOT / "experiments" / "issue_ablations" / "scenarios",
]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    scenarios = _load_scenarios()
    rows = [_robustness_row(scenario) for scenario in scenarios]
    payload = {
        "scenario_count": len(rows),
        "recoded_evaluations": len(rows) * 2,
        "policy_count": 3,
        "strict_status_stable": sum(row["strict"]["allowed_status"] == row["base"]["allowed_status"] for row in rows),
        "lenient_status_stable": sum(row["lenient"]["allowed_status"] == row["base"]["allowed_status"] for row in rows),
        "all_policy_status_stable": sum(
            row["strict"]["allowed_status"] == row["base"]["allowed_status"] == row["lenient"]["allowed_status"]
            for row in rows
        ),
        "mean_score_delta_strict": mean(row["base"]["total_score"] - row["strict"]["total_score"] for row in rows),
        "mean_score_delta_lenient": mean(row["lenient"]["total_score"] - row["base"]["total_score"] for row in rows),
        "weighted_status_agreement_base_strict": _weighted_agreement(
            [row["base"]["allowed_status"] for row in rows],
            [row["strict"]["allowed_status"] for row in rows],
        ),
        "weighted_status_agreement_base_lenient": _weighted_agreement(
            [row["base"]["allowed_status"] for row in rows],
            [row["lenient"]["allowed_status"] for row in rows],
        ),
        "rows": rows,
    }
    (RESULTS / "annotation_robustness.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (RESULTS / "annotation_robustness.md").write_text(_format_report(payload) + "\n", encoding="utf-8")
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


def _robustness_row(scenario: dict) -> dict:
    base = evaluate_scenario(scenario)
    strict = evaluate_scenario(_recoded(scenario, "strict"))
    lenient = evaluate_scenario(_recoded(scenario, "lenient"))
    return {
        "scenario_id": scenario["id"],
        "source_path": scenario["_source_path"],
        "jurisdiction_profile": scenario.get("jurisdiction_profile", "unspecified"),
        "base": _result_row(base),
        "strict": _result_row(strict),
        "lenient": _result_row(lenient),
    }


def _recoded(scenario: dict, mode: str) -> dict:
    recoded = deepcopy(scenario)
    recoded.pop("_source_path", None)
    recoded.pop("expected_allowed_status", None)
    recoded.pop("expected_disposition", None)
    metrics = evaluate_scenario(scenario)
    for dimension in DIMENSIONS:
        current = _score(recoded, dimension)
        if mode == "strict":
            score = _strict_score(scenario, metrics, dimension, current)
        elif mode == "lenient":
            score = _lenient_score(scenario, metrics, dimension, current)
        else:
            raise ValueError(f"Unknown recoding mode: {mode}")
        recoded["scores"][dimension] = _score_value(recoded["scores"][dimension], score)
    return recoded


def _strict_score(scenario: dict, metrics, dimension: str, score: int) -> int:
    if score == 0:
        return score
    claimed_rank = STATUS_RANK[scenario["claimed_status"]]
    if dimension == "S":
        if metrics.source_tag_coverage is not None and metrics.source_tag_coverage < 1:
            return max(0, score - 1)
        if metrics.evidence_fidelity is not None and metrics.evidence_fidelity < 1:
            return max(0, score - 1)
    if dimension == "H" and claimed_rank >= STATUS_RANK["normative_material_screening_output"]:
        if metrics.authority_coverage is None:
            return max(1, score - 1)
    if dimension == "K" and claimed_rank >= STATUS_RANK["normative_material_screening_output"]:
        if metrics.counter_authority_recall is None:
            return max(0, score - 1)
        if metrics.counter_authority_recall < 1:
            return max(0, score - 1)
    if dimension == "T" and score == 2:
        gate = scenario.get("review_gate", {})
        if gate.get("contestation_recorded") is not True and gate.get("reliance_gate") != "authorized_adoption":
            return 1
    if dimension == "L" and score == 2:
        gate = scenario.get("review_gate", {})
        if gate.get("adoption_reasons_recorded") is not True:
            return 1
    return score


def _lenient_score(scenario: dict, metrics, dimension: str, score: int) -> int:
    if score == 2:
        return score
    if dimension == "S":
        if metrics.evidence_fidelity == 1 and metrics.evidence_coverage == 1 and metrics.source_tag_coverage == 1:
            return min(2, score + 1)
    if dimension == "H":
        if metrics.authority_coverage == 1:
            return min(2, score + 1)
    if dimension == "K":
        if metrics.counter_authority_recall == 1:
            return min(2, score + 1)
    if dimension == "T":
        gate = scenario.get("review_gate", {})
        if gate.get("review_status") == "completed" and gate.get("jurisdiction_assumptions"):
            return min(2, score + 1)
    if dimension == "L":
        gate = scenario.get("review_gate", {})
        if gate.get("adoption_reasons_recorded") is True and gate.get("contestation_recorded") is True:
            return min(2, score + 1)
    return score


def _score(scenario: dict, dimension: str) -> int:
    value = scenario["scores"][dimension]
    return int(value.get("score", value) if isinstance(value, dict) else value)


def _score_value(current, score: int):
    if isinstance(current, dict):
        updated = dict(current)
        updated["score"] = score
        return updated
    return score


def _result_row(result) -> dict:
    return {
        "allowed_status": result.allowed_status,
        "total_score": result.total_score,
        "disposition": result.disposition,
        "claim_supported": result.claim_supported,
    }


def _weighted_agreement(left: list[str], right: list[str]) -> float:
    n = len(left)
    ranks = sorted(set(STATUS_RANK.values()))
    max_distance = max(ranks) - min(ranks)
    observed = sum(_weight(STATUS_RANK[a], STATUS_RANK[b], max_distance) for a, b in zip(left, right)) / n
    left_counts = {rank: 0 for rank in ranks}
    right_counts = {rank: 0 for rank in ranks}
    for status in left:
        left_counts[STATUS_RANK[status]] += 1
    for status in right:
        right_counts[STATUS_RANK[status]] += 1
    expected = 0.0
    for left_rank in ranks:
        for right_rank in ranks:
            expected += (
                left_counts[left_rank]
                * right_counts[right_rank]
                * _weight(left_rank, right_rank, max_distance)
            )
    expected /= n * n
    if expected == 0:
        return 1.0
    return 1 - observed / expected


def _weight(left_rank: int, right_rank: int, max_distance: int) -> float:
    return ((left_rank - right_rank) / max_distance) ** 2


def _format_report(payload: dict) -> str:
    lines = [
        "# Annotation Robustness Study",
        "",
        f"Base scenarios: {payload['scenario_count']}",
        f"Strict/lenient recoded evaluations: {payload['recoded_evaluations']}",
        f"Strict status stable: {payload['strict_status_stable']}/{payload['scenario_count']}",
        f"Lenient status stable: {payload['lenient_status_stable']}/{payload['scenario_count']}",
        f"Stable under all coding policies: {payload['all_policy_status_stable']}/{payload['scenario_count']}",
        f"Mean score delta, strict: {payload['mean_score_delta_strict']:.2f}",
        f"Mean score delta, lenient: {payload['mean_score_delta_lenient']:.2f}",
        f"Weighted status agreement, base vs strict: {payload['weighted_status_agreement_base_strict']:.2f}",
        f"Weighted status agreement, base vs lenient: {payload['weighted_status_agreement_base_lenient']:.2f}",
        "",
        "## Status Stability",
        "",
        "| Scenario | Base | Strict | Lenient | Base score | Strict score | Lenient score |",
        "| --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["scenario_id"],
                    row["base"]["allowed_status"],
                    row["strict"]["allowed_status"],
                    row["lenient"]["allowed_status"],
                    str(row["base"]["total_score"]),
                    str(row["strict"]["total_score"]),
                    str(row["lenient"]["total_score"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
