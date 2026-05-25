from __future__ import annotations

import json
import re
import sys
from itertools import combinations
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))

from audit_harness.model import STATUS_RANK, evaluate_scenario


RESULTS = ROOT / "experiments" / "query_perturbation" / "results"
PUBLIC_RETRIEVAL = ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios"
HOLDOUT = ROOT / "experiments" / "holdout_validation" / "scenarios"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [_row(path) for path in _scenario_paths()]
    groups = [_group_row(group_id, group_rows) for group_id, group_rows in _groups(rows).items()]
    payload = {
        "issue_group_count": len(groups),
        "query_variant_count": len(rows),
        "scenario_count": len(rows),
        "public_retrieval_variants": sum(row["suite"] == "public_retrieval_benchmark" for row in rows),
        "holdout_variants": sum(row["suite"] == "holdout_validation" for row in rows),
        "status_stable_group_count": sum(group["status_stable"] for group in groups),
        "authority_coverage_unstable_group_count": sum(group["authority_coverage_gap"] > 0 for group in groups),
        "counter_recall_unstable_group_count": sum(group["counter_recall_gap"] > 0 for group in groups),
        "record_set_unstable_group_count": sum(group["mean_pairwise_record_overlap"] < 1 for group in groups),
        "top_result_unstable_group_count": sum(group["distinct_top_result_count"] > 1 for group in groups),
        "max_authority_coverage_gap": max(group["authority_coverage_gap"] for group in groups),
        "max_counter_recall_gap": max(group["counter_recall_gap"] for group in groups),
        "mean_pairwise_record_overlap": mean(group["mean_pairwise_record_overlap"] for group in groups),
        "min_pairwise_record_overlap": min(group["min_pairwise_record_overlap"] for group in groups),
        "high_upstream_but_blocked": sum(row["high_upstream_but_blocked"] for row in rows),
        "groups": groups,
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "query_perturbation_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "query_perturbation_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


def _scenario_paths() -> list[Path]:
    return sorted(PUBLIC_RETRIEVAL.glob("*.json")) + sorted(HOLDOUT.glob("holdout-public-retrieval-*.json"))


def _row(path: Path) -> dict:
    scenario = json.loads(path.read_text(encoding="utf-8"))
    result = evaluate_scenario(scenario)
    retrieved = _retrieved_ids(scenario)
    recall = (scenario.get("upstream_metrics") or {}).get("recall")
    return {
        "scenario_id": scenario["id"],
        "group_id": _group_id(scenario["id"]),
        "suite": "holdout_validation" if "holdout_validation" in str(path) else "public_retrieval_benchmark",
        "path": str(path.relative_to(ROOT)),
        "query": _query(scenario),
        "allowed_status": result.allowed_status,
        "disposition": result.disposition,
        "failure_flags": result.failure_flags,
        "total_score": result.total_score,
        "authority_coverage": _zero_if_none(result.authority_coverage),
        "counter_authority_recall": _zero_if_none(result.counter_authority_recall),
        "upstream_recall": _zero_if_none(recall),
        "high_upstream_but_blocked": bool(
            isinstance(recall, (int, float))
            and recall >= 0.8
            and STATUS_RANK[result.allowed_status] < STATUS_RANK["normative_material_screening_output"]
        ),
        "record_count": len(retrieved),
        "retrieved_ids": sorted(retrieved),
        "top_result": _top_result(scenario),
    }


def _group_id(scenario_id: str) -> str:
    stripped = scenario_id.removeprefix("holdout-public-retrieval-").removeprefix("public-retrieval-")
    return re.sub(r"-q\d+$", "", stripped)


def _query(scenario: dict) -> str:
    match = re.search(r"query: (.+)$", scenario.get("deployment_context", ""))
    return match.group(1) if match else ""


def _retrieved_ids(scenario: dict) -> set[str]:
    ids: set[str] = set()
    for unit in scenario.get("evidence_packet", {}).get("output_units", []):
        ids.update(unit.get("source_ids") or [])
    return ids


def _top_result(scenario: dict) -> str | None:
    units = scenario.get("evidence_packet", {}).get("output_units", [])
    if not units:
        return None
    ranked = sorted(units, key=lambda unit: unit.get("output_rank", len(units) + 1))
    source_ids = ranked[0].get("source_ids") or []
    return source_ids[0] if source_ids else None


def _groups(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["group_id"], []).append(row)
    return dict(sorted(grouped.items()))


def _group_row(group_id: str, rows: list[dict]) -> dict:
    authority_values = [row["authority_coverage"] for row in rows]
    counter_values = [row["counter_authority_recall"] for row in rows]
    recall_values = [row["upstream_recall"] for row in rows]
    overlaps = [_jaccard(left["retrieved_ids"], right["retrieved_ids"]) for left, right in combinations(rows, 2)]
    statuses = {row["allowed_status"] for row in rows}
    top_results = {row["top_result"] for row in rows if row["top_result"]}
    return {
        "group_id": group_id,
        "variant_count": len(rows),
        "status_distribution": _counts(row["allowed_status"] for row in rows),
        "status_stable": len(statuses) == 1,
        "qualified_variant_count": sum(
            STATUS_RANK[row["allowed_status"]] >= STATUS_RANK["normative_material_screening_output"] for row in rows
        ),
        "authority_coverage_range": _range(authority_values),
        "authority_coverage_gap": max(authority_values) - min(authority_values),
        "counter_recall_range": _range(counter_values),
        "counter_recall_gap": max(counter_values) - min(counter_values),
        "upstream_recall_range": _range(recall_values),
        "upstream_recall_gap": max(recall_values) - min(recall_values),
        "distinct_top_result_count": len(top_results),
        "mean_pairwise_record_overlap": 1.0 if not overlaps else mean(overlaps),
        "min_pairwise_record_overlap": 1.0 if not overlaps else min(overlaps),
        "high_upstream_but_blocked": sum(row["high_upstream_but_blocked"] for row in rows),
        "queries": [row["query"] for row in rows],
    }


def _jaccard(left: list[str], right: list[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    union = left_set | right_set
    if not union:
        return 1.0
    return len(left_set & right_set) / len(union)


def _range(values: list[float]) -> list[float]:
    return [min(values), max(values)]


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _zero_if_none(value) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0


def _format_report(payload: dict) -> str:
    lines = [
        "# Query Perturbation Stability Analysis",
        "",
        f"Issue groups: {payload['issue_group_count']}",
        f"Query variants: {payload['query_variant_count']} ({payload['public_retrieval_variants']} public-retrieval, {payload['holdout_variants']} holdout)",
        f"Status-stable issue groups: {payload['status_stable_group_count']}/{payload['issue_group_count']}",
        f"Authority-coverage unstable groups: {payload['authority_coverage_unstable_group_count']}/{payload['issue_group_count']}",
        f"Counter-material recall unstable groups: {payload['counter_recall_unstable_group_count']}/{payload['issue_group_count']}",
        f"Record-set unstable groups: {payload['record_set_unstable_group_count']}/{payload['issue_group_count']}",
        f"Top-result unstable groups: {payload['top_result_unstable_group_count']}/{payload['issue_group_count']}",
        f"Maximum authority-coverage gap: {payload['max_authority_coverage_gap']:.2f}",
        f"Maximum counter-material recall gap: {payload['max_counter_recall_gap']:.2f}",
        f"Mean pairwise record overlap: {payload['mean_pairwise_record_overlap']:.2f}",
        f"Minimum pairwise record overlap: {payload['min_pairwise_record_overlap']:.2f}",
        f"High-upstream but procedurally blocked variants: {payload['high_upstream_but_blocked']}/{payload['query_variant_count']}",
        "",
        "| Issue group | Variants | Stable status | Qualified | Authority gap | Counter gap | Recall gap | Top results | Mean overlap | High-upstream blocked | Status distribution |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for group in payload["groups"]:
        distribution = ", ".join(f"{key}: {value}" for key, value in group["status_distribution"].items())
        lines.append(
            f"| {group['group_id']} | {group['variant_count']} | {group['status_stable']} | "
            f"{group['qualified_variant_count']} | {group['authority_coverage_gap']:.2f} | "
            f"{group['counter_recall_gap']:.2f} | {group['upstream_recall_gap']:.2f} | "
            f"{group['distinct_top_result_count']} | {group['mean_pairwise_record_overlap']:.2f} | "
            f"{group['high_upstream_but_blocked']} | {distribution} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
