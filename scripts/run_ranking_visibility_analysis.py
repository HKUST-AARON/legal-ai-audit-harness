from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import RANK_SALIENCE_WINDOW, STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES


RESULTS = ROOT / "experiments" / "ranking_visibility" / "results"
FRONT_WINDOW_SIZE = RANK_SALIENCE_WINDOW
WINDOW_SIZES = (1, 2, 3, 4)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [_row(path, suite["id"]) for suite in SUITES for path in sorted(suite["path"].glob("*.json"))]
    rows = [row for row in rows if row]
    counterfactuals = [row for row in rows if row["rank_intervention_applied"]]
    failures = [row for row in counterfactuals if not row["counterfactual_passed"]]
    window_sensitivity = _window_sensitivity(rows)
    first_ranks = [row["first_counter_rank"] for row in rows if row["first_counter_rank"] is not None]
    front_window = next(item for item in window_sensitivity if item["window_size"] == FRONT_WINDOW_SIZE)
    payload = {
        "eligible_packet_count": len(rows),
        "visibility_check_count": len(rows),
        "window_check_count": sum(item["eligible_packet_count"] for item in window_sensitivity),
        "window_sensitivity": window_sensitivity,
        "first_counter_rank_distribution": _rank_distribution(first_ranks),
        "median_first_counter_rank": _median(first_ranks),
        "mean_reciprocal_first_counter_rank": sum(1 / rank for rank in first_ranks) / len(first_ranks),
        "rank_order_counterfactual_count": len(counterfactuals),
        "rank_order_passed_count": len(counterfactuals) - len(failures),
        "baseline_rank_drift_count": sum(row["baseline_rank_drift"] for row in rows),
        "failed_count": len(failures),
        "front_window_size": FRONT_WINDOW_SIZE,
        "front_window_packet_count": front_window["eligible_packet_count"],
        "front_window_counter_visible": front_window["counter_visible_count"],
        "front_window_counter_not_visible": front_window["counter_not_visible_count"],
        "counterfactual_front_window_counter_visible": sum(
            row["counterfactual_counter_visible_in_front_window"] for row in counterfactuals
        ),
        "rank_intervention_applied_count": len(counterfactuals),
        "coverage_preserved_count": sum(row["coverage_preserved"] for row in counterfactuals),
        "downgraded_count": sum(row["downgraded_below_high_status"] for row in counterfactuals),
        "failures": failures,
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "ranking_visibility_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "ranking_visibility_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if not failures else 1


def _row(path: Path, suite_id: str) -> dict | None:
    scenario = json.loads(path.read_text(encoding="utf-8"))
    baseline = evaluate_scenario(scenario)
    claimed_rank = STATUS_RANK[scenario.get("claimed_status", "reference_information")]
    if max(STATUS_RANK[baseline.allowed_status], claimed_rank) < STATUS_RANK["normative_material_screening_output"]:
        return None
    units = _ranked_units(scenario.get("evidence_packet", {}).get("output_units", []))
    counter_material = set(scenario.get("authority_sets", {}).get("counter_or_limiting") or [])
    if not units or not counter_material:
        return None

    baseline_visible = _counter_visible_in_front_window(units, counter_material)
    drifted_units = _move_counter_material_below_front_window(units, counter_material) if baseline_visible else units
    rank_intervention_applied = baseline_visible and units != drifted_units
    if rank_intervention_applied:
        drifted = copy.deepcopy(scenario)
        drifted["evidence_packet"]["output_units"] = drifted_units
        drifted_result = evaluate_scenario(drifted)
        coverage_preserved = (
            baseline.authority_coverage == drifted_result.authority_coverage
            and baseline.counter_authority_recall == drifted_result.counter_authority_recall
            and baseline.evidence_fidelity == drifted_result.evidence_fidelity
            and baseline.procedural_source_tag_coverage == drifted_result.procedural_source_tag_coverage
        )
        downgraded = STATUS_RANK[drifted_result.allowed_status] < STATUS_RANK["normative_material_screening_output"]
        counterfactual_status = drifted_result.allowed_status
        counterfactual_disposition = drifted_result.disposition
        counterfactual_counter_authority_recall = drifted_result.counter_authority_recall
        counterfactual_authority_coverage = drifted_result.authority_coverage
        counterfactual_passed = coverage_preserved and downgraded and "ranking_drift" in drifted_result.failure_flags
    else:
        coverage_preserved = False
        downgraded = False
        counterfactual_status = None
        counterfactual_disposition = None
        counterfactual_counter_authority_recall = None
        counterfactual_authority_coverage = None
        counterfactual_passed = None
    return {
        "scenario_id": scenario["id"],
        "suite": suite_id,
        "path": str(path.relative_to(ROOT)),
        "baseline_status": baseline.allowed_status,
        "baseline_rank_drift": "ranking_drift" in baseline.failure_flags,
        "counterfactual_status": counterfactual_status,
        "counterfactual_disposition": counterfactual_disposition,
        "baseline_counter_visible_in_front_window": baseline_visible,
        "counterfactual_counter_visible_in_front_window": _counter_visible_in_front_window(drifted_units, counter_material),
        "rank_intervention_applied": rank_intervention_applied,
        "output_unit_count": len(units),
        "first_counter_rank": _first_counter_rank(units, counter_material),
        "baseline_counter_authority_recall": baseline.counter_authority_recall,
        "counterfactual_counter_authority_recall": counterfactual_counter_authority_recall,
        "baseline_authority_coverage": baseline.authority_coverage,
        "counterfactual_authority_coverage": counterfactual_authority_coverage,
        "coverage_preserved": coverage_preserved,
        "downgraded_below_high_status": downgraded,
        "counterfactual_passed": counterfactual_passed,
    }


def _counter_visible_in_front_window(units: list[dict], counter_material: set[str]) -> bool:
    if len(units) < FRONT_WINDOW_SIZE:
        return False
    visible_sources: set[str] = set()
    for unit in units[:FRONT_WINDOW_SIZE]:
        visible_sources.update(unit.get("source_ids") or [])
    return bool(visible_sources & counter_material)


def _move_counter_material_below_front_window(units: list[dict], counter_material: set[str]) -> list[dict]:
    counter_units = [unit for unit in units if set(unit.get("source_ids") or []) & counter_material]
    other_units = [unit for unit in units if not (set(unit.get("source_ids") or []) & counter_material)]
    if len(other_units) < FRONT_WINDOW_SIZE:
        return units
    return _refresh_output_ranks(other_units + counter_units)


def _ranked_units(units: list[dict]) -> list[dict]:
    if any("output_rank" in unit for unit in units):
        return sorted(units, key=lambda unit: unit.get("output_rank", len(units) + 1))
    return units


def _refresh_output_ranks(units: list[dict]) -> list[dict]:
    if not any("output_rank" in unit for unit in units):
        return units
    for rank, unit in enumerate(units, start=1):
        unit["output_rank"] = rank
    return units


def _first_counter_rank(units: list[dict], counter_material: set[str]) -> int | None:
    for index, unit in enumerate(units, start=1):
        if set(unit.get("source_ids") or []) & counter_material:
            return index
    return None


def _window_sensitivity(rows: list[dict]) -> list[dict]:
    sensitivity = []
    for window_size in WINDOW_SIZES:
        eligible = [row for row in rows if row["output_unit_count"] >= window_size]
        visible = [row for row in eligible if row["first_counter_rank"] is not None and row["first_counter_rank"] <= window_size]
        sensitivity.append(
            {
                "window_size": window_size,
                "eligible_packet_count": len(eligible),
                "counter_visible_count": len(visible),
                "counter_not_visible_count": len(eligible) - len(visible),
                "visible_ratio": 0 if not eligible else len(visible) / len(eligible),
            }
        )
    return sensitivity


def _rank_distribution(ranks: list[int]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for rank in ranks:
        key = str(rank)
        distribution[key] = distribution.get(key, 0) + 1
    return dict(sorted(distribution.items(), key=lambda item: int(item[0])))


def _median(values: list[int]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[midpoint])
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def _format_report(payload: dict) -> str:
    lines = [
        "# Ranking Visibility Analysis",
        "",
        f"Eligible high-status claims: {payload['eligible_packet_count']}",
        f"Ranking-visibility diagnostics: {payload['visibility_check_count']} high-status claims and {payload['window_check_count']} rank-window checks",
        f"First counter-material rank distribution: {_format_distribution(payload['first_counter_rank_distribution'])}",
        f"Median first counter-material rank: {payload['median_first_counter_rank']:.1f}; mean reciprocal rank: {payload['mean_reciprocal_first_counter_rank']:.2f}",
        f"Baseline rank-drift caps: {payload['baseline_rank_drift_count']}/{payload['visibility_check_count']}",
        f"Rank-order counterfactuals: {payload['rank_order_passed_count']}/{payload['rank_order_counterfactual_count']} downgraded with coverage preserved",
        f"Counter-material visible in top {payload['front_window_size']}: {payload['front_window_counter_visible']}/{payload['front_window_packet_count']}",
        f"Counter-material outside top {payload['front_window_size']}: {payload['front_window_counter_not_visible']}/{payload['front_window_packet_count']}",
        f"Counterfactual top-window counter-material visible: {payload['counterfactual_front_window_counter_visible']}/{payload['rank_order_counterfactual_count']}",
        f"Rank-order interventions applied: {payload['rank_intervention_applied_count']}/{payload['eligible_packet_count']}",
        "",
        "| Window | Eligible packets | Counter visible | Counter not visible | Visible ratio |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in payload["window_sensitivity"]:
        lines.append(
            f"| {item['window_size']} | {item['eligible_packet_count']} | {item['counter_visible_count']} | "
            f"{item['counter_not_visible_count']} | {item['visible_ratio']:.2f} |"
        )
    lines.extend(
        [
        "",
        "| Scenario | Suite | Base | Drifted | CAR preserved | Authority preserved | Top-window counter | Drifted top-window counter |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["rows"]:
        car_preserved = (
            "n/a"
            if row["counterfactual_counter_authority_recall"] is None
            else row["baseline_counter_authority_recall"] == row["counterfactual_counter_authority_recall"]
        )
        authority_preserved = (
            "n/a"
            if row["counterfactual_authority_coverage"] is None
            else row["baseline_authority_coverage"] == row["counterfactual_authority_coverage"]
        )
        lines.append(
            f"| {row['scenario_id']} | {row['suite']} | {row['baseline_status']} | {row['counterfactual_status'] or 'n/a'} | "
            f"{car_preserved} | "
            f"{authority_preserved} | "
            f"{row['baseline_counter_visible_in_front_window']} | "
            f"{row['counterfactual_counter_visible_in_front_window']} |"
        )
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(f"- {failure['scenario_id']}: {failure['counterfactual_status']}")
    return "\n".join(lines)


def _format_distribution(distribution: dict[str, int]) -> str:
    return ", ".join(f"{rank}: {count}" for rank, count in distribution.items())


if __name__ == "__main__":
    raise SystemExit(main())
