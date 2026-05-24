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
                }
            )
        rows.append({"packet_id": packet["packet_id"], "annotations": packet_rows})
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
                }
            )
            pairwise_dimensions.append(
                {
                    "left": left,
                    "right": right,
                    "dimension_agreement": _dimension_agreement(rows, left, right),
                }
            )
    high_disagreement = [
        row["packet_id"]
        for row in rows
        if len({annotation["allowed_status"] for annotation in row["annotations"]}) > 1
    ]
    return {
        "packet_count": len(rows),
        "coder_count": len(coders),
        "coder_ids": coder_ids,
        "pairwise_status": pairwise_status,
        "pairwise_dimensions": pairwise_dimensions,
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
        matches = 0
        total = 0
        for row in rows:
            left_scores = next(annotation for annotation in row["annotations"] if annotation["coder_id"] == left)["scores"]
            right_scores = next(annotation for annotation in row["annotations"] if annotation["coder_id"] == right)["scores"]
            matches += left_scores[dimension] == right_scores[dimension]
            total += 1
        agreement[dimension] = matches / total
    return agreement


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


def _format_report(payload: dict) -> str:
    lines = [
        "# Blind Coding Study",
        "",
        f"Packets: {payload['packet_count']}",
        f"Coding passes: {payload['coder_count']} ({', '.join(payload['coder_ids'])})",
        f"Status disagreements: {payload['status_disagreement_count']}",
        "",
        "## Pairwise Status Agreement",
        "",
        "| Left | Right | Exact status agreement | Weighted status agreement |",
        "| --- | --- | ---: | ---: |",
    ]
    for item in payload["pairwise_status"]:
        lines.append(
            f"| {item['left']} | {item['right']} | {item['exact_status_agreement']:.2f} | {item['weighted_status_agreement']:.2f} |"
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
            "| Packet | " + " | ".join(payload["coder_ids"]) + " |",
            "| --- | " + " | ".join("---" for _ in payload["coder_ids"]) + " |",
        ]
    )
    for row in payload["rows"]:
        statuses = [
            next(annotation for annotation in row["annotations"] if annotation["coder_id"] == coder_id)["allowed_status"]
            for coder_id in payload["coder_ids"]
        ]
        lines.append("| " + " | ".join([row["packet_id"], *statuses]) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
