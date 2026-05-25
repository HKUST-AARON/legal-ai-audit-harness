from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audit_harness.model import DIMENSIONS, STATUS_RANK, evaluate_scenario


BASE_DIR = ROOT / "experiments" / "blind_coding"
PACKETS = BASE_DIR / "packets"
ANNOTATIONS = BASE_DIR / "annotations"
RESULTS = BASE_DIR / "results"
SOURCE_DIRS = [
    ROOT / "examples" / "scenarios",
    ROOT / "experiments" / "real_cases" / "scenarios",
    ROOT / "experiments" / "public_system_outputs" / "scenarios",
    ROOT / "experiments" / "ai_outputs" / "scenarios",
    ROOT / "experiments" / "model_output_repairs" / "scenarios",
    ROOT / "experiments" / "model_output_evidence_ladder" / "scenarios",
    ROOT / "experiments" / "model_output_adversarial" / "scenarios",
    ROOT / "experiments" / "issue_public_outputs" / "scenarios",
    ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios",
    ROOT / "experiments" / "issue_gold_sets" / "scenarios",
    ROOT / "experiments" / "issue_ablations" / "scenarios",
]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    packets = _load_packets()
    coder_files = sorted(ANNOTATIONS.glob("coder_*.json"))
    if len(coder_files) < 2:
        raise SystemExit("Need at least two annotation files in experiments/blind_coding/annotations")
    coders = [_load_coder(path) for path in coder_files]
    rows = []
    for packet in packets:
        packet_rows = []
        base = _source_scenario(packet["packet_id"])
        base_status = evaluate_scenario(base).allowed_status
        for coder in coders:
            annotation = coder["annotations"].get(packet["packet_id"])
            if annotation is None:
                raise SystemExit(f"Missing annotation for {packet['packet_id']} in {coder['coder_id']}")
            scenario = _scenario_from_annotation(packet, annotation, coder["coder_id"])
            result = evaluate_scenario(scenario)
            packet_rows.append(
                {
                    "coder_id": coder["coder_id"],
                    "scores": result.scores,
                    "total_score": result.total_score,
                    "allowed_status": result.allowed_status,
                    "disposition": result.disposition,
                    "missing_gates": result.missing_gates,
                    "failure_flags": result.failure_flags,
                }
            )
        rows.append(
            {
                "packet_id": packet["packet_id"],
                "base_allowed_status": base_status,
                "base_scores": _score_values(base),
                "annotations": packet_rows,
            }
        )
    payload = _payload(rows, coders)
    (RESULTS / "blind_coding_study.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (RESULTS / "blind_coding_study.md").write_text(_format_report(payload) + "\n", encoding="utf-8")
    print(_format_report(payload))
    return 0


def _load_packets() -> list[dict]:
    packets = []
    for path in sorted(PACKETS.glob("*.json")):
        if path.name == "manifest.json":
            continue
        packets.append(json.loads(path.read_text(encoding="utf-8")))
    if not packets:
        raise SystemExit("No blind coding packets found. Run scripts/build_blind_coding_packets.py first.")
    return packets


def _load_coder(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    annotations = {item["packet_id"]: item for item in payload["annotations"]}
    return {"coder_id": payload["coder_id"], "annotations": annotations}


def _source_scenario(packet_id: str) -> dict:
    for directory in SOURCE_DIRS:
        for path in sorted(directory.glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            if scenario["id"] == packet_id:
                return scenario
    raise SystemExit(f"Cannot find source scenario for {packet_id}")


def _scenario_from_annotation(packet: dict, annotation: dict, coder_id: str) -> dict:
    scenario = {
        "id": f"{packet['packet_id']}--{coder_id}",
        "claimed_status": packet["claimed_status"],
        "system_role": packet.get("system_role"),
        "jurisdiction_profile": packet.get("jurisdiction_profile", "unspecified"),
        "scores": {dimension: {"score": annotation["scores"][dimension]} for dimension in DIMENSIONS},
        "authority_sets": packet.get("authority_sets", {}),
        "upstream_metrics": packet.get("upstream_metrics", {}),
        "evidence_packet": packet.get("evidence_packet", {}),
        "review_gate": packet.get("review_gate", {}),
        "failure_flags": annotation.get("failure_flags", []),
    }
    if packet.get("counter_material_complete") is not None:
        scenario["counter_material_complete"] = packet["counter_material_complete"]
    return {key: value for key, value in scenario.items() if value is not None}


def _payload(rows: list[dict], coders: list[dict]) -> dict:
    coder_ids = [coder["coder_id"] for coder in coders]
    status_lists = {
        coder_id: [
            next(annotation for annotation in row["annotations"] if annotation["coder_id"] == coder_id)["allowed_status"]
            for row in rows
        ]
        for coder_id in coder_ids
    }
    pairwise_status = []
    pairwise_dimensions = []
    for i, left in enumerate(coder_ids):
        for right in coder_ids[i + 1 :]:
            left_statuses = status_lists[left]
            right_statuses = status_lists[right]
            pairwise_status.append(
                {
                    "left": left,
                    "right": right,
                    "exact_status_agreement": _exact_agreement(left_statuses, right_statuses),
                    "weighted_status_agreement": _weighted_agreement(left_statuses, right_statuses),
                    "cohen_kappa": _cohen_kappa(left_statuses, right_statuses),
                    "quadratic_weighted_kappa": _quadratic_weighted_kappa(left_statuses, right_statuses),
                }
            )
            pairwise_dimensions.append(
                {
                    "left": left,
                    "right": right,
                    "dimension_agreement": _dimension_agreement(rows, left, right),
                    "gate_agreement": _gate_agreement(rows, left, right),
                }
            )
    high_disagreement = [
        row["packet_id"]
        for row in rows
        if len({annotation["allowed_status"] for annotation in row["annotations"]}) > 1
    ]
    base_statuses = [row["base_allowed_status"] for row in rows]
    base_status_agreement = {}
    for coder_id in coder_ids:
        coder_statuses = status_lists[coder_id]
        mismatches = [
            row["packet_id"]
            for row, base_status, coder_status in zip(rows, base_statuses, coder_statuses)
            if base_status != coder_status
        ]
        base_status_agreement[coder_id] = {
            "exact_status_agreement": _exact_agreement(base_statuses, coder_statuses),
            "weighted_status_agreement": _weighted_agreement(base_statuses, coder_statuses),
            "cohen_kappa": _cohen_kappa(base_statuses, coder_statuses),
            "quadratic_weighted_kappa": _quadratic_weighted_kappa(base_statuses, coder_statuses),
            "dimension_agreement": _base_dimension_agreement(rows, coder_id),
            "match_count": len(rows) - len(mismatches),
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
        }
    base_dimension_summaries = [
        {"coder_id": coder_id, "dimension": dimension, **stats}
        for coder_id, item in base_status_agreement.items()
        for dimension, stats in item["dimension_agreement"].items()
    ]
    base_dimension_worst_kappa = min(
        base_dimension_summaries,
        key=lambda item: (item["cohen_kappa"], item["coder_id"], item["dimension"]),
    )
    dimension_min_kappa = {
        dimension: min(
            item["dimension_agreement"][dimension]["cohen_kappa"]
            for item in pairwise_dimensions
        )
        for dimension in DIMENSIONS
    }
    gate_agreements = [item["gate_agreement"] for item in pairwise_dimensions]
    return {
        "packet_count": len(rows),
        "coder_count": len(coders),
        "coder_ids": coder_ids,
        "pairwise_status": pairwise_status,
        "pairwise_dimensions": pairwise_dimensions,
        "dimension_min_kappa": dimension_min_kappa,
        "minimum_dimension_kappa": min(dimension_min_kappa.values()),
        "minimum_dimension_exact_agreement": min(
            item["dimension_agreement"][dimension]["exact_agreement"]
            for item in pairwise_dimensions
            for dimension in DIMENSIONS
        ),
        "minimum_failure_flag_exact_agreement": min(item["failure_flag_exact_agreement"] for item in gate_agreements),
        "minimum_failure_flag_jaccard": min(item["failure_flag_mean_jaccard"] for item in gate_agreements),
        "minimum_missing_gate_exact_agreement": min(item["missing_gate_exact_agreement"] for item in gate_agreements),
        "minimum_missing_gate_jaccard": min(item["missing_gate_mean_jaccard"] for item in gate_agreements),
        "base_status_agreement": base_status_agreement,
        "base_dimension_min_kappa": base_dimension_worst_kappa["cohen_kappa"],
        "base_dimension_min_kappa_dimension": base_dimension_worst_kappa["dimension"],
        "base_dimension_min_kappa_coder": base_dimension_worst_kappa["coder_id"],
        "base_dimension_min_kappa_exact_agreement": base_dimension_worst_kappa["exact_agreement"],
        "base_dimension_min_exact_agreement": min(item["exact_agreement"] for item in base_dimension_summaries),
        "base_dimension_min_pabak": min(item["pabak"] for item in base_dimension_summaries),
        "base_dimension_max_mean_absolute_delta": max(item["mean_absolute_delta"] for item in base_dimension_summaries),
        "status_disagreements": high_disagreement,
        "status_disagreement_count": len(high_disagreement),
        "mean_total_score": {
            coder_id: mean(
                next(annotation for annotation in row["annotations"] if annotation["coder_id"] == coder_id)["total_score"]
                for row in rows
            )
            for coder_id in coder_ids
        },
        "rows": rows,
    }


def _exact_agreement(left: list[str], right: list[str]) -> float:
    return sum(a == b for a, b in zip(left, right)) / len(left)


def _dimension_agreement(rows: list[dict], left: str, right: str) -> dict[str, float]:
    agreement = {}
    for dimension in DIMENSIONS:
        left_values = []
        right_values = []
        for row in rows:
            left_scores = next(annotation for annotation in row["annotations"] if annotation["coder_id"] == left)["scores"]
            right_scores = next(annotation for annotation in row["annotations"] if annotation["coder_id"] == right)["scores"]
            left_values.append(left_scores[dimension])
            right_values.append(right_scores[dimension])
        agreement[dimension] = {
            "exact_agreement": _exact_agreement(left_values, right_values),
            "weighted_agreement": _score_weighted_agreement(left_values, right_values),
            "cohen_kappa": _nominal_kappa(left_values, right_values, [0, 1, 2]),
            "quadratic_weighted_kappa": _ordinal_kappa(left_values, right_values, {0: 0, 1: 1, 2: 2}),
        }
    return agreement


def _base_dimension_agreement(rows: list[dict], coder_id: str) -> dict[str, dict[str, float]]:
    agreement = {}
    for dimension in DIMENSIONS:
        base_values = [row["base_scores"][dimension] for row in rows]
        coder_values = [
            next(annotation for annotation in row["annotations"] if annotation["coder_id"] == coder_id)["scores"][dimension]
            for row in rows
        ]
        agreement[dimension] = {
            "exact_agreement": _exact_agreement(base_values, coder_values),
            "weighted_agreement": _score_weighted_agreement(base_values, coder_values),
            "cohen_kappa": _nominal_kappa(base_values, coder_values, [0, 1, 2]),
            "quadratic_weighted_kappa": _ordinal_kappa(base_values, coder_values, {0: 0, 1: 1, 2: 2}),
            "pabak": _pabak(base_values, coder_values),
            "mean_absolute_delta": mean(abs(base - coder) for base, coder in zip(base_values, coder_values)),
            "coder_lower_count": sum(coder < base for base, coder in zip(base_values, coder_values)),
            "coder_higher_count": sum(coder > base for base, coder in zip(base_values, coder_values)),
            "coder_equal_count": sum(coder == base for base, coder in zip(base_values, coder_values)),
        }
    return agreement


def _gate_agreement(rows: list[dict], left: str, right: str) -> dict[str, float]:
    failure_exact = []
    failure_jaccard = []
    missing_exact = []
    missing_jaccard = []
    for row in rows:
        left_row = next(annotation for annotation in row["annotations"] if annotation["coder_id"] == left)
        right_row = next(annotation for annotation in row["annotations"] if annotation["coder_id"] == right)
        left_flags = set(left_row["failure_flags"])
        right_flags = set(right_row["failure_flags"])
        left_gates = set(left_row["missing_gates"])
        right_gates = set(right_row["missing_gates"])
        failure_exact.append(left_flags == right_flags)
        failure_jaccard.append(_jaccard(left_flags, right_flags))
        missing_exact.append(left_gates == right_gates)
        missing_jaccard.append(_jaccard(left_gates, right_gates))
    return {
        "failure_flag_exact_agreement": mean(failure_exact),
        "failure_flag_mean_jaccard": mean(failure_jaccard),
        "missing_gate_exact_agreement": mean(missing_exact),
        "missing_gate_mean_jaccard": mean(missing_jaccard),
    }


def _score_values(scenario: dict) -> dict[str, int]:
    return {dimension: scenario["scores"][dimension]["score"] for dimension in DIMENSIONS}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right)


def _weighted_agreement(left: list[str], right: list[str]) -> float:
    ranks = sorted(set(STATUS_RANK.values()))
    max_distance = max(ranks) - min(ranks)
    if not left:
        return 1.0
    distances = [
        abs(STATUS_RANK[a] - STATUS_RANK[b]) / max_distance
        for a, b in zip(left, right)
    ]
    return 1 - mean(distances)


def _cohen_kappa(left: list[str], right: list[str]) -> float:
    return _nominal_kappa(left, right, sorted(STATUS_RANK, key=STATUS_RANK.get))


def _quadratic_weighted_kappa(left: list[str], right: list[str]) -> float:
    return _ordinal_kappa(left, right, STATUS_RANK)


def _score_weighted_agreement(left: list[int], right: list[int]) -> float:
    if not left:
        return 1.0
    return 1 - mean(abs(a - b) / 2 for a, b in zip(left, right))


def _pabak(left: list, right: list, category_count: int = 3) -> float:
    return (category_count * _exact_agreement(left, right) - 1) / (category_count - 1)


def _nominal_kappa(left: list, right: list, labels: list) -> float:
    total = len(left)
    if total == 0:
        return 1.0
    observed = _exact_agreement(left, right)
    expected = 0.0
    for label in labels:
        expected += (left.count(label) / total) * (right.count(label) / total)
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1 - expected)


def _ordinal_kappa(left: list, right: list, rank_map: dict) -> float:
    labels = sorted(rank_map, key=rank_map.get)
    total = len(left)
    if total == 0:
        return 1.0
    max_rank = max(rank_map.values())
    observed_disagreement = 0.0
    expected_disagreement = 0.0
    for a in labels:
        for b in labels:
            weight = ((rank_map[a] - rank_map[b]) / max_rank) ** 2
            observed_disagreement += weight * sum(x == a and y == b for x, y in zip(left, right)) / total
            expected_disagreement += weight * (left.count(a) / total) * (right.count(b) / total)
    if expected_disagreement == 0.0:
        return 1.0 if observed_disagreement == 0.0 else 0.0
    return 1 - observed_disagreement / expected_disagreement


def _format_report(payload: dict) -> str:
    lines = [
        "# Blind Coding Study",
        "",
        f"Packets: {payload['packet_count']}",
        f"Coding passes: {payload['coder_count']} ({', '.join(payload['coder_ids'])})",
        f"Status disagreements: {payload['status_disagreement_count']}",
        f"Minimum dimension kappa: {payload['minimum_dimension_kappa']:.2f}",
        f"Minimum derived failure-flag exact agreement: {payload['minimum_failure_flag_exact_agreement']:.2f}",
        f"Minimum derived missing-gate exact agreement: {payload['minimum_missing_gate_exact_agreement']:.2f}",
        f"Base dimension minimum kappa: {payload['base_dimension_min_kappa']:.2f} ({payload['base_dimension_min_kappa_dimension']}, exact {payload['base_dimension_min_kappa_exact_agreement']:.2f})",
        f"Base dimension minimum exact agreement: {payload['base_dimension_min_exact_agreement']:.2f}",
        f"Base dimension minimum PABAK: {payload['base_dimension_min_pabak']:.2f}",
        f"Base dimension maximum mean absolute delta: {payload['base_dimension_max_mean_absolute_delta']:.2f}",
        "",
        "## Pairwise Status Agreement",
        "",
        "| Left | Right | Exact status agreement | Weighted status agreement | Cohen's kappa | Quadratic weighted kappa |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in payload["pairwise_status"]:
        lines.append(
            f"| {item['left']} | {item['right']} | {item['exact_status_agreement']:.2f} | {item['weighted_status_agreement']:.2f} | {item['cohen_kappa']:.2f} | {item['quadratic_weighted_kappa']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Pairwise Dimension Agreement",
            "",
            "| Left | Right | Dimension | Exact | Weighted | Cohen's kappa | Quadratic weighted kappa |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in payload["pairwise_dimensions"]:
        for dimension in DIMENSIONS:
            stats = item["dimension_agreement"][dimension]
            lines.append(
                f"| {item['left']} | {item['right']} | {dimension} | {stats['exact_agreement']:.2f} | {stats['weighted_agreement']:.2f} | {stats['cohen_kappa']:.2f} | {stats['quadratic_weighted_kappa']:.2f} |"
            )
    lines.extend(
        [
            "",
            "## Pairwise Gate Agreement",
            "",
            "| Left | Right | Failure-flag exact | Failure-flag Jaccard | Missing-gate exact | Missing-gate Jaccard |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in payload["pairwise_dimensions"]:
        stats = item["gate_agreement"]
        lines.append(
            f"| {item['left']} | {item['right']} | {stats['failure_flag_exact_agreement']:.2f} | {stats['failure_flag_mean_jaccard']:.2f} | {stats['missing_gate_exact_agreement']:.2f} | {stats['missing_gate_mean_jaccard']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Base Status Agreement",
            "",
            "| Coder | Exact base agreement | Weighted base agreement | Cohen's kappa | Quadratic weighted kappa | Matches | Mismatches |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for coder_id in payload["coder_ids"]:
        item = payload["base_status_agreement"][coder_id]
        lines.append(
            f"| {coder_id} | {item['exact_status_agreement']:.2f} | {item['weighted_status_agreement']:.2f} | {item['cohen_kappa']:.2f} | {item['quadratic_weighted_kappa']:.2f} | {item['match_count']} | {item['mismatch_count']} |"
        )
    lines.extend(
        [
            "",
            "## Base Dimension Calibration",
            "",
            "| Coder | Dimension | Exact | Cohen's kappa | PABAK | Mean absolute delta | Lower | Higher | Equal |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for coder_id in payload["coder_ids"]:
        for dimension in DIMENSIONS:
            stats = payload["base_status_agreement"][coder_id]["dimension_agreement"][dimension]
            lines.append(
                f"| {coder_id} | {dimension} | {stats['exact_agreement']:.2f} | {stats['cohen_kappa']:.2f} | {stats['pabak']:.2f} | {stats['mean_absolute_delta']:.2f} | {stats['coder_lower_count']} | {stats['coder_higher_count']} | {stats['coder_equal_count']} |"
            )
    lines.extend(["", "## Mean Total Score", "", "| Coder | Mean total score |", "| --- | ---: |"])
    for coder_id, score in payload["mean_total_score"].items():
        lines.append(f"| {coder_id} | {score:.2f} |")
    lines.extend(["", "## Status Disagreements", ""])
    if payload["status_disagreements"]:
        for packet_id in payload["status_disagreements"]:
            lines.append(f"- {packet_id}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Packet Results",
            "",
            "| Packet | Base | " + " | ".join(payload["coder_ids"]) + " |",
            "| --- | --- | " + " | ".join("---" for _ in payload["coder_ids"]) + " |",
        ]
    )
    for row in payload["rows"]:
        statuses = [
            next(annotation for annotation in row["annotations"] if annotation["coder_id"] == coder_id)["allowed_status"]
            for coder_id in payload["coder_ids"]
        ]
        lines.append("| " + " | ".join([row["packet_id"], row["base_allowed_status"], *statuses]) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
