from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import DIMENSIONS, STATUS_RANK, SYSTEM_ROLE_CAPS, evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "baseline_comparisons" / "results"
THRESHOLD = 0.8


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    scenarios = _scenario_rows()
    baselines = _baseline_rows(scenarios)
    simplified = [row for row in baselines if row["id"] != "full_audit_gate"]
    best_simplified = max(simplified, key=lambda row: (row["f1"], row["precision"], row["specificity"]))
    lowest_false_positive = min(simplified, key=lambda row: (row["false_positive"], -row["recall"]))
    payload = {
        "scenario_count": len(scenarios),
        "qualified_count": sum(row["qualified"] for row in scenarios),
        "baseline_count": len(baselines),
        "baseline_prediction_count": sum(row["denominator"] for row in baselines),
        "simplified_baseline_count": len(simplified),
        "best_simplified": best_simplified,
        "lowest_false_positive_simplified": lowest_false_positive,
        "all_simplified_rules_have_errors": all(row["false_positive"] + row["false_negative"] > 0 for row in simplified),
        "full_gate": next(row for row in baselines if row["id"] == "full_audit_gate"),
        "baselines": baselines,
    }
    report = _format_report(payload)
    (RESULTS / "baseline_comparison_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "baseline_comparison_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


def _scenario_rows() -> list[dict]:
    rows = []
    for suite in SUITES:
        for path in sorted(suite["path"].glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            metrics = scenario.get("upstream_metrics") or {}
            gate = scenario.get("review_gate") or {}
            scores = result.scores
            rows.append(
                {
                    "id": scenario["id"],
                    "path": str(path.relative_to(ROOT)),
                    "qualified": STATUS_RANK[result.allowed_status]
                    >= STATUS_RANK["normative_material_screening_output"],
                    "total_score": result.total_score,
                    "all_dimensions_present": all(scores[dimension] >= 1 for dimension in DIMENSIONS),
                    "full_audit_gate": STATUS_RANK[result.allowed_status]
                    >= STATUS_RANK["normative_material_screening_output"],
                    "metric_complete": all(isinstance(metrics.get(key), (int, float)) for key in ("precision", "recall", "f1")),
                    "precision": metrics.get("precision"),
                    "recall": metrics.get("recall"),
                    "f1": metrics.get("f1"),
                    "source_bound": result.evidence_fidelity == 1.0
                    and result.evidence_coverage == 1.0
                    and result.procedural_source_tag_coverage == 1.0,
                    "counter_complete": bool(scenario.get("counter_material_complete"))
                    or result.counter_authority_recall == 1.0,
                    "review_ready": _review_ready(scenario, result.system_role),
                    "no_failure_cap": not result.failure_flags and result.disposition == "none",
                    "allowed_status": result.allowed_status,
                }
            )
    return rows


def _review_ready(scenario: dict, system_role: str) -> bool:
    gate = scenario.get("review_gate") or {}
    return (
        STATUS_RANK[SYSTEM_ROLE_CAPS[system_role]] >= STATUS_RANK["normative_material_screening_output"]
        and bool(gate.get("jurisdiction_assumptions"))
    )


def _baseline_rows(scenarios: list[dict]) -> list[dict]:
    rules = [
        ("recall_threshold", "Recall >= 0.8", "metric", lambda row: row["recall"] >= THRESHOLD),
        ("f1_threshold", "F1 >= 0.8", "metric", lambda row: row["f1"] >= THRESHOLD),
        ("precision_threshold", "Precision >= 0.8", "metric", lambda row: row["precision"] >= THRESHOLD),
        ("total_score_only", "Total score >= 9", "all", lambda row: row["total_score"] >= 9),
        (
            "score_candidate",
            "All dimensions present and total >= 9",
            "all",
            lambda row: row["all_dimensions_present"] and row["total_score"] >= 9,
        ),
        ("source_bound_only", "Source-bound output evidence", "all", lambda row: row["source_bound"]),
        ("review_ready_only", "Review gate and role ready", "all", lambda row: row["review_ready"]),
        (
            "source_and_recall",
            "Source-bound evidence plus recall >= 0.8",
            "metric",
            lambda row: row["source_bound"] and row["recall"] >= THRESHOLD,
        ),
        (
            "source_score_counter",
            "Source-bound score candidate with counter-material",
            "all",
            lambda row: row["source_bound"]
            and row["all_dimensions_present"]
            and row["total_score"] >= 9
            and row["counter_complete"],
        ),
        (
            "source_score_review",
            "Source-bound score candidate with review gate",
            "all",
            lambda row: row["source_bound"]
            and row["all_dimensions_present"]
            and row["total_score"] >= 9
            and row["review_ready"],
        ),
        (
            "source_counter_review",
            "Source-bound evidence, counter-material and review gate",
            "all",
            lambda row: row["source_bound"] and row["counter_complete"] and row["review_ready"],
        ),
        ("full_audit_gate", "Full audit gate function", "all", lambda row: row["full_audit_gate"]),
    ]
    rows = []
    for rule_id, label, scope, predicate in rules:
        scoped = [row for row in scenarios if scope == "all" or row["metric_complete"]]
        rows.append(_confusion_row(rule_id, label, scoped, predicate))
    return rows


def _confusion_row(rule_id: str, label: str, scenarios: list[dict], predicate) -> dict:
    tp = fp = tn = fn = 0
    false_positive_ids = []
    false_negative_ids = []
    for row in scenarios:
        predicted = bool(predicate(row))
        actual = row["qualified"]
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
            false_positive_ids.append(row["id"])
        elif not predicted and not actual:
            tn += 1
        else:
            fn += 1
            false_negative_ids.append(row["id"])
    return {
        "id": rule_id,
        "label": label,
        "denominator": len(scenarios),
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision": _safe_div(tp, tp + fp),
        "recall": _safe_div(tp, tp + fn),
        "specificity": _safe_div(tn, tn + fp),
        "f1": _f1(tp, fp, fn),
        "balanced_accuracy": (_safe_div(tp, tp + fn) + _safe_div(tn, tn + fp)) / 2,
        "false_positive_examples": false_positive_ids[:10],
        "false_negative_examples": false_negative_ids[:10],
    }


def _safe_div(numerator: int | float, denominator: int | float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _f1(tp: int, fp: int, fn: int) -> float:
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    return _safe_div(2 * precision * recall, precision + recall)


def _format_report(payload: dict) -> str:
    lines = [
        "# Baseline Rule Comparison",
        "",
        f"Scenario packets: {payload['scenario_count']}",
        f"Qualified packets under the full audit model: {payload['qualified_count']}",
        f"Baseline rules: {payload['baseline_count']}",
        f"Baseline predictions: {payload['baseline_prediction_count']}",
        f"Simplified rules with at least one reproduction error: {payload['all_simplified_rules_have_errors']}",
        "Target label: protocol-defined reference allocation.",
        "",
        "Best simplified rule by F1: "
        f"{payload['best_simplified']['label']} "
        f"(precision {payload['best_simplified']['precision']:.2f}, "
        f"recall {payload['best_simplified']['recall']:.2f}, "
        f"false positives {payload['best_simplified']['false_positive']}, "
        f"false negatives {payload['best_simplified']['false_negative']})",
        "Lowest-false-positive simplified rule: "
        f"{payload['lowest_false_positive_simplified']['label']} "
        f"(false positives {payload['lowest_false_positive_simplified']['false_positive']}, "
        f"false negatives {payload['lowest_false_positive_simplified']['false_negative']})",
        "",
        "| Rule | Denom. | Precision | Recall | Specificity | F1 | Reproduction FP | Reproduction FN |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["baselines"]:
        label = "Full audit gate reference allocation" if row["id"] == "full_audit_gate" else row["label"]
        lines.append(
            f"| {label} | {row['denominator']} | {row['precision']:.2f} | "
            f"{row['recall']:.2f} | {row['specificity']:.2f} | {row['f1']:.2f} | "
            f"{row['false_positive']} | {row['false_negative']} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
