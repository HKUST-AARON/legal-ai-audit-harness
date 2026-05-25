from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from run_policy_constants_replay import _evaluate, _scenario_paths


POLICY_PATH = ROOT / "policy" / "legal_output_policy.json"
RESULTS = ROOT / "experiments" / "policy_family_robustness" / "results"
THRESHOLD = 0.8


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    base_policy = _load_json(POLICY_PATH)
    scenarios = [_load_json(path) | {"_path": str(path.relative_to(ROOT))} for path in _scenario_paths()]
    default_rows = [_evaluate(scenario, base_policy) for scenario in scenarios]
    variants = [_variant(name, base_policy, mutate) for name, mutate in VARIANTS]
    rows = [_variant_row(name, policy, scenarios, default_rows) for name, policy in variants]
    payload = {
        "variant_count": len(rows),
        "scenario_count": len(scenarios),
        "status_evaluation_count": len(rows) * len(scenarios),
        "baseline_prediction_count": sum(row["baseline_prediction_count"] for row in rows),
        "total_evaluation_count": len(rows) * len(scenarios)
        + sum(row["baseline_prediction_count"] for row in rows),
        "total_status_promotions": sum(row["status_promotions"] for row in rows),
        "total_high_status_promotions": sum(row["high_status_promotions"] for row in rows),
        "total_high_status_demotions": sum(row["high_status_demotions"] for row in rows),
        "variants_with_simplified_errors": sum(row["all_simplified_rules_have_errors"] for row in rows),
        "best_simplified_false_positive_total": sum(
            row["best_simplified"]["false_positive"] for row in rows
        ),
        "best_simplified_false_negative_total": sum(
            row["best_simplified"]["false_negative"] for row in rows
        ),
        "full_protocol_false_positive_total": sum(row["full_gate"]["false_positive"] for row in rows),
        "full_protocol_false_negative_total": sum(row["full_gate"]["false_negative"] for row in rows),
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "policy_family_robustness.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "policy_family_robustness.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


VARIANTS = (
    ("default", lambda policy: None),
    (
        "lenient_threshold_8_10",
        lambda policy: policy["thresholds"].update(
            {"normative_material_screening_output": 8, "decision_support_reason": 10}
        ),
    ),
    (
        "strict_threshold_10_11",
        lambda policy: policy["thresholds"].update(
            {"normative_material_screening_output": 10, "decision_support_reason": 11}
        ),
    ),
    (
        "strict_threshold_11_12",
        lambda policy: policy["thresholds"].update(
            {"normative_material_screening_output": 11, "decision_support_reason": 12}
        ),
    ),
    ("rank_window_2", lambda policy: policy.update({"rank_salience_window": 2})),
    ("rank_window_4", lambda policy: policy.update({"rank_salience_window": 4})),
    (
        "strict_procedural_tags",
        lambda policy: policy.update(
            {"procedural_source_tags": ["tool_verified", "official_source", "user_provided_verified"]}
        ),
    ),
    (
        "official_source_tags_only",
        lambda policy: policy.update({"procedural_source_tags": ["tool_verified", "official_source"]}),
    ),
    (
        "authorized_cap_to_screening",
        lambda policy: policy["system_role_caps"].update(
            {"authorized_decision_support_tool": "normative_material_screening_output"}
        ),
    ),
    (
        "auditable_cap_to_decision",
        lambda policy: policy["system_role_caps"].update(
            {"auditable_procedural_tool": "decision_support_reason"}
        ),
    ),
    (
        "strict_downgrade_to_suspension",
        lambda policy: policy["flag_dispositions"].update(
            {
                "source_attribution_gap": "suspension",
                "jurisdiction_assumption_gap": "suspension",
                "review_gate_failure": "suspension",
                "automation_dependence": "suspension",
                "contestation_failure": "suspension",
            }
        ),
    ),
    (
        "strict_failure_withdrawal",
        lambda policy: policy["flag_dispositions"].update(
            {
                "authority_omission": "withdrawal",
                "counter_material_suppression": "withdrawal",
                "invalid_authority": "withdrawal",
                "ranking_drift": "withdrawal",
            }
        ),
    ),
)


def _variant(name: str, base_policy: dict, mutate) -> tuple[str, dict]:
    policy = copy.deepcopy(base_policy)
    mutate(policy)
    return name, policy


def _variant_row(name: str, policy: dict, scenarios: list[dict], default_rows: list[dict]) -> dict:
    evaluated = [_evaluate(scenario, policy) for scenario in scenarios]
    scenario_rows = [_scenario_row(scenario, row, policy) for scenario, row in zip(scenarios, evaluated, strict=True)]
    baselines = _baseline_rows(scenario_rows, policy)
    simplified = [row for row in baselines if row["id"] != "full_audit_gate"]
    best_simplified = max(simplified, key=lambda row: (row["f1"], row["precision"], row["specificity"]))
    lowest_false_positive = min(simplified, key=lambda row: (row["false_positive"], -row["recall"]))
    rank = policy["status_rank"]
    return {
        "variant": name,
        "thresholds": policy["thresholds"],
        "rank_salience_window": policy["rank_salience_window"],
        "procedural_source_tags": policy["procedural_source_tags"],
        "qualified_count": sum(row["qualified"] for row in scenario_rows),
        "status_distribution": _distribution(evaluated, "allowed_status"),
        "status_changes_from_default": sum(
            row["allowed_status"] != default["allowed_status"]
            for row, default in zip(evaluated, default_rows, strict=True)
        ),
        "status_promotions": sum(
            rank[row["allowed_status"]] > rank[default["allowed_status"]]
            for row, default in zip(evaluated, default_rows, strict=True)
        ),
        "high_status_promotions": sum(
            rank[default["allowed_status"]] < rank["normative_material_screening_output"]
            and rank[row["allowed_status"]] >= rank["normative_material_screening_output"]
            for row, default in zip(evaluated, default_rows, strict=True)
        ),
        "high_status_demotions": sum(
            rank[default["allowed_status"]] >= rank["normative_material_screening_output"]
            and rank[row["allowed_status"]] < rank["normative_material_screening_output"]
            for row, default in zip(evaluated, default_rows, strict=True)
        ),
        "baseline_prediction_count": sum(row["denominator"] for row in baselines),
        "all_simplified_rules_have_errors": all(
            row["false_positive"] + row["false_negative"] > 0 for row in simplified
        ),
        "best_simplified": best_simplified,
        "lowest_false_positive_simplified": lowest_false_positive,
        "full_gate": next(row for row in baselines if row["id"] == "full_audit_gate"),
        "baselines": baselines,
    }


def _scenario_row(scenario: dict, result: dict, policy: dict) -> dict:
    upstream = scenario.get("upstream_metrics") or {}
    metrics = result["metric_bundle"]
    rank = policy["status_rank"]
    scores = result["score_vector"]
    role_cap = policy["system_role_caps"][result["system_role"]]
    normative_threshold = policy["thresholds"]["normative_material_screening_output"]
    return {
        "id": scenario["id"],
        "path": scenario["_path"],
        "qualified": rank[result["allowed_status"]] >= rank["normative_material_screening_output"],
        "total_score": result["total_score"],
        "all_dimensions_present": all(scores[dimension] >= 1 for dimension in policy["dimensions"]),
        "full_audit_gate": rank[result["allowed_status"]] >= rank["normative_material_screening_output"],
        "metric_complete": all(isinstance(upstream.get(key), (int, float)) for key in ("precision", "recall", "f1")),
        "precision": upstream.get("precision"),
        "recall": upstream.get("recall"),
        "f1": upstream.get("f1"),
        "authority_complete": metrics["authority_coverage"] == 1.0,
        "source_bound": metrics["evidence_fidelity"] == 1.0
        and metrics["evidence_coverage"] == 1.0
        and metrics["procedural_source_tag_coverage"] == 1.0,
        "counter_complete": bool(scenario.get("counter_material_complete"))
        or metrics["counter_authority_recall"] == 1.0,
        "review_ready": rank[role_cap] >= rank["normative_material_screening_output"]
        and bool((scenario.get("review_gate") or {}).get("jurisdiction_assumptions")),
        "normative_threshold": normative_threshold,
    }


def _baseline_rows(scenarios: list[dict], policy: dict) -> list[dict]:
    normative_threshold = policy["thresholds"]["normative_material_screening_output"]
    rules = [
        ("recall_threshold", "Recall >= 0.8", "metric", lambda row: row["recall"] >= THRESHOLD),
        ("f1_threshold", "F1 >= 0.8", "metric", lambda row: row["f1"] >= THRESHOLD),
        ("precision_threshold", "Precision >= 0.8", "metric", lambda row: row["precision"] >= THRESHOLD),
        ("total_score_only", "Total score >= policy threshold", "all", lambda row: row["total_score"] >= normative_threshold),
        (
            "score_candidate",
            "All dimensions present and score >= policy threshold",
            "all",
            lambda row: row["all_dimensions_present"] and row["total_score"] >= normative_threshold,
        ),
        ("source_bound_only", "Source-bound output evidence", "all", lambda row: row["source_bound"]),
        ("review_ready_only", "Review gate and role ready", "all", lambda row: row["review_ready"]),
        (
            "authority_material_only",
            "High-authority and counter-material coverage",
            "all",
            lambda row: row["authority_complete"] and row["counter_complete"],
        ),
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
            and row["total_score"] >= normative_threshold
            and row["counter_complete"],
        ),
        (
            "source_score_review",
            "Source-bound score candidate with review gate",
            "all",
            lambda row: row["source_bound"]
            and row["all_dimensions_present"]
            and row["total_score"] >= normative_threshold
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
    return [_confusion_row(rule_id, label, scenarios, scope, predicate) for rule_id, label, scope, predicate in rules]


def _confusion_row(rule_id: str, label: str, scenarios: list[dict], scope: str, predicate) -> dict:
    scoped = [row for row in scenarios if scope == "all" or row["metric_complete"]]
    true_positive = false_positive = true_negative = false_negative = 0
    for row in scoped:
        predicted = bool(predicate(row))
        actual = row["qualified"]
        if predicted and actual:
            true_positive += 1
        elif predicted and not actual:
            false_positive += 1
        elif not predicted and not actual:
            true_negative += 1
        else:
            false_negative += 1
    precision = _safe_div(true_positive, true_positive + false_positive)
    recall = _safe_div(true_positive, true_positive + false_negative)
    specificity = _safe_div(true_negative, true_negative + false_positive)
    return {
        "id": rule_id,
        "label": label,
        "denominator": len(scoped),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "true_negative": true_negative,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": _safe_div(2 * precision * recall, precision + recall),
    }


def _safe_div(numerator: int | float, denominator: int | float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _distribution(rows: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row[key]
        counts[value] = counts.get(value, 0) + 1
    return counts


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _format_report(payload: dict) -> str:
    lines = [
        "# Policy-Family Robustness",
        "",
        f"Policy variants: {payload['variant_count']}",
        f"Scenario packets per variant: {payload['scenario_count']}",
        f"Status evaluations: {payload['status_evaluation_count']}",
        f"Baseline-rule predictions: {payload['baseline_prediction_count']}",
        f"Total evaluations: {payload['total_evaluation_count']}",
        f"Status promotions from default: {payload['total_status_promotions']}",
        f"High-status promotions from below screening: {payload['total_high_status_promotions']}",
        f"High-status demotions from default: {payload['total_high_status_demotions']}",
        f"Variants where every simplified rule erred: {payload['variants_with_simplified_errors']}/{payload['variant_count']}",
        f"Best simplified-rule false positives across variants: {payload['best_simplified_false_positive_total']}",
        f"Best simplified-rule false negatives across variants: {payload['best_simplified_false_negative_total']}",
        f"Full protocol false positives across variants: {payload['full_protocol_false_positive_total']}",
        f"Full protocol false negatives across variants: {payload['full_protocol_false_negative_total']}",
        "",
        "| Variant | Qualified | Changes | Promotions | High promotions | High demotions | Best simplified FP/FN | Full FP/FN |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['variant']} | {row['qualified_count']} | {row['status_changes_from_default']} | "
            f"{row['status_promotions']} | {row['high_status_promotions']} | {row['high_status_demotions']} | "
            f"{row['best_simplified']['false_positive']}/{row['best_simplified']['false_negative']} | "
            f"{row['full_gate']['false_positive']}/{row['full_gate']['false_negative']} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
