from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import DIMENSIONS, STATUS_RANK, SYSTEM_ROLE_CAPS, evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "metric_separation" / "results"
THRESHOLD = 0.8


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = _metric_rows()
    payload = {
        "scenario_count": len(_all_scenario_paths()),
        "metric_scenario_count": len(rows),
        "qualified_count": sum(row["qualified"] for row in rows),
        "upstream_threshold": THRESHOLD,
        "point_biserial": {
            metric: _point_biserial(rows, metric)
            for metric in ("precision", "recall", "f1")
        },
        "threshold_tests": [
            _confusion_row(rows, f"{metric}>={THRESHOLD}", lambda row, metric=metric: row[metric] >= THRESHOLD)
            for metric in ("precision", "recall", "f1")
        ],
        "gate_cascade": _gate_cascade(rows),
        "high_recall_blocked": _high_recall_blocked(rows),
    }
    report = _format_report(payload)
    (RESULTS / "metric_separation_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "metric_separation_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


def _all_scenario_paths() -> list[Path]:
    paths: list[Path] = []
    for suite in SUITES:
        paths.extend(sorted(suite["path"].glob("*.json")))
    return paths


def _metric_rows() -> list[dict]:
    rows = []
    for path in _all_scenario_paths():
        scenario = json.loads(path.read_text(encoding="utf-8"))
        metrics = scenario.get("upstream_metrics") or {}
        if not all(isinstance(metrics.get(key), (int, float)) for key in ("precision", "recall", "f1")):
            continue
        result = evaluate_scenario(scenario)
        qualified = STATUS_RANK[result.allowed_status] >= STATUS_RANK["normative_material_screening_output"]
        rows.append(
            {
                "scenario_id": scenario["id"],
                "path": str(path.relative_to(ROOT)),
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "qualified": qualified,
                "allowed_status": result.allowed_status,
                "total_score": result.total_score,
                "score_candidate": all(result.scores[dimension] >= 1 for dimension in DIMENSIONS) and result.total_score >= 9,
                "source_bound": result.evidence_fidelity == 1.0
                and result.evidence_coverage == 1.0
                and result.procedural_source_tag_coverage == 1.0,
                "review_role_ready": _review_role_ready(scenario, result.system_role),
                "no_active_failure_cap": not result.failure_flags and result.disposition == "none",
                "failure_flags": result.failure_flags,
                "disposition": result.disposition,
            }
        )
    return rows


def _review_role_ready(scenario: dict, system_role: str) -> bool:
    gate = scenario.get("review_gate") or {}
    return (
        STATUS_RANK[SYSTEM_ROLE_CAPS[system_role]] >= STATUS_RANK["normative_material_screening_output"]
        and bool(gate.get("jurisdiction_assumptions"))
    )


def _point_biserial(rows: list[dict], metric: str) -> float:
    xs = [row[metric] for row in rows]
    ys = [1 if row["qualified"] else 0 for row in rows]
    mean_x = mean(xs)
    mean_y = mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator_x = sum((x - mean_x) ** 2 for x in xs)
    denominator_y = sum((y - mean_y) ** 2 for y in ys)
    if denominator_x == 0 or denominator_y == 0:
        return 0.0
    return numerator / ((denominator_x * denominator_y) ** 0.5)


def _confusion_row(rows: list[dict], label: str, predicate) -> dict:
    tp = fp = tn = fn = 0
    for row in rows:
        predicted = bool(predicate(row))
        actual = row["qualified"]
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and not actual:
            tn += 1
        else:
            fn += 1
    return {
        "label": label,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision": _safe_div(tp, tp + fp),
        "recall": _safe_div(tp, tp + fn),
        "specificity": _safe_div(tn, tn + fp),
    }


def _gate_cascade(rows: list[dict]) -> list[dict]:
    predicates = [
        ("recall>=0.8", lambda row: row["recall"] >= THRESHOLD),
        ("+ score candidate", lambda row: row["recall"] >= THRESHOLD and row["score_candidate"]),
        ("+ source bound", lambda row: row["recall"] >= THRESHOLD and row["score_candidate"] and row["source_bound"]),
        (
            "+ review role",
            lambda row: row["recall"] >= THRESHOLD
            and row["score_candidate"]
            and row["source_bound"]
            and row["review_role_ready"],
        ),
        (
            "+ no failure cap",
            lambda row: row["recall"] >= THRESHOLD
            and row["score_candidate"]
            and row["source_bound"]
            and row["review_role_ready"]
            and row["no_active_failure_cap"],
        ),
    ]
    return [_confusion_row(rows, label, predicate) for label, predicate in predicates]


def _high_recall_blocked(rows: list[dict]) -> dict:
    blocked = [
        row
        for row in rows
        if row["recall"] >= THRESHOLD and STATUS_RANK[row["allowed_status"]] < STATUS_RANK["normative_material_screening_output"]
    ]
    return {
        "count": len(blocked),
        "denominator": sum(row["recall"] >= THRESHOLD for row in rows),
        "rate": _safe_div(len(blocked), sum(row["recall"] >= THRESHOLD for row in rows)),
        "failure_flags": _flag_counts(blocked),
        "status_distribution": _status_counts(blocked),
    }


def _flag_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for flag in row["failure_flags"]:
            counts[flag] = counts.get(flag, 0) + 1
    return counts


def _status_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["allowed_status"]] = counts.get(row["allowed_status"], 0) + 1
    return counts


def _safe_div(numerator: int | float, denominator: int | float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _format_report(payload: dict) -> str:
    lines = [
        "# Metric Separation Analysis",
        "",
        f"Scenario packets: {payload['scenario_count']}",
        f"Scenario packets with upstream precision/recall/F1: {payload['metric_scenario_count']}",
        f"Procedurally qualified outputs: {payload['qualified_count']}",
        "",
        "## Point-Biserial Correlation With Procedural Qualification",
        "",
        "| Metric | Correlation |",
        "| --- | ---: |",
    ]
    for metric, value in payload["point_biserial"].items():
        lines.append(f"| {metric} | {value:.2f} |")
    lines.extend(["", "## Threshold Tests", "", "| Predictor | TP | FP | TN | FN | Precision | Recall | Specificity |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for row in payload["threshold_tests"]:
        lines.append(_confusion_line(row))
    lines.extend(["", "## Gate Cascade", "", "| Predictor | TP | FP | TN | FN | Precision | Recall | Specificity |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for row in payload["gate_cascade"]:
        lines.append(_confusion_line(row))
    blocked = payload["high_recall_blocked"]
    lines.extend(
        [
            "",
            "## High-Recall Blocked Outputs",
            "",
            f"High-recall outputs blocked below normative screening: {blocked['count']}/{blocked['denominator']} ({blocked['rate']:.2f}).",
            "",
            "Failure flags: " + _distribution(blocked["failure_flags"]),
            "Status distribution: " + _distribution(blocked["status_distribution"]),
        ]
    )
    return "\n".join(lines)


def _confusion_line(row: dict) -> str:
    return (
        f"| {row['label']} | {row['true_positive']} | {row['false_positive']} | {row['true_negative']} | "
        f"{row['false_negative']} | {row['precision']:.2f} | {row['recall']:.2f} | {row['specificity']:.2f} |"
    )


def _distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "none"
    return ", ".join(f"{key}: {value}" for key, value in sorted(distribution.items()))


if __name__ == "__main__":
    raise SystemExit(main())
