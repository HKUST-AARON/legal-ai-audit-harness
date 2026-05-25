from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import evaluate_scenario
from run_baseline_comparison_analysis import _baseline_rows, _scenario_rows
from run_issue_family_generalization import _with_family


RESULTS = ROOT / "experiments" / "multiaxis_generalization" / "results"
MIN_HOLDOUT_SIZE = 3


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [_with_metadata(row) for row in _scenario_rows()]
    folds = []
    for axis in AXES:
        folds.extend(_axis_folds(axis, rows))
    payload = {
        "axis_count": len(AXES),
        "fold_count": len(folds),
        "scenario_count": len(rows),
        "qualified_count": sum(row["qualified"] for row in rows),
        "holdout_prediction_count": sum(fold["holdout_prediction_count"] for fold in folds),
        "training_prediction_count": sum(fold["training_prediction_count"] for fold in folds),
        "full_protocol_holdout_false_positive": sum(fold["full_protocol"]["false_positive"] for fold in folds),
        "full_protocol_holdout_false_negative": sum(fold["full_protocol"]["false_negative"] for fold in folds),
        "best_trained_rule_holdout_false_positive": sum(
            fold["best_trained_rule_holdout"]["false_positive"] for fold in folds
        ),
        "best_trained_rule_holdout_false_negative": sum(
            fold["best_trained_rule_holdout"]["false_negative"] for fold in folds
        ),
        "lowest_fp_rule_holdout_false_positive": sum(fold["lowest_fp_rule_holdout"]["false_positive"] for fold in folds),
        "lowest_fp_rule_holdout_false_negative": sum(fold["lowest_fp_rule_holdout"]["false_negative"] for fold in folds),
        "balanced_rule_holdout_false_positive": sum(fold["balanced_rule_holdout"]["false_positive"] for fold in folds),
        "balanced_rule_holdout_false_negative": sum(fold["balanced_rule_holdout"]["false_negative"] for fold in folds),
        "folds_with_best_trained_rule_error": sum(_has_error(fold["best_trained_rule_holdout"]) for fold in folds),
        "folds_with_lowest_fp_rule_error": sum(_has_error(fold["lowest_fp_rule_holdout"]) for fold in folds),
        "folds_with_balanced_rule_error": sum(_has_error(fold["balanced_rule_holdout"]) for fold in folds),
        "axis_summaries": [_axis_summary(axis["id"], folds) for axis in AXES],
        "folds": folds,
    }
    report = _format_report(payload)
    (RESULTS / "multiaxis_generalization.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "multiaxis_generalization.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if payload["full_protocol_holdout_false_positive"] == 0 and payload["full_protocol_holdout_false_negative"] == 0 else 1


AXES = [
    {"id": "issue_family", "label": "Issue family"},
    {"id": "suite", "label": "Validation suite"},
    {"id": "system_role", "label": "System role"},
    {"id": "jurisdiction_profile", "label": "Jurisdiction profile"},
    {"id": "claimed_status", "label": "Claimed status"},
    {"id": "origin_class", "label": "Output origin class"},
]


def _with_metadata(row: dict) -> dict:
    scenario = json.loads((ROOT / row["path"]).read_text(encoding="utf-8"))
    result = evaluate_scenario(scenario)
    suite = _suite_id(row["path"])
    return {
        **_with_family(row),
        "suite": suite,
        "system_role": result.system_role,
        "jurisdiction_profile": scenario.get("jurisdiction_profile") or "unspecified_profile",
        "claimed_status": scenario["claimed_status"],
        "origin_class": _origin_class(suite),
    }


def _suite_id(path: str) -> str:
    parts = path.split("/")
    if parts[0] == "examples":
        return "stress_tests"
    return parts[1]


def _origin_class(suite: str) -> str:
    if suite in {"real_cases", "public_system_outputs", "issue_public_outputs", "public_retrieval_benchmark"}:
        return "public_legal_output"
    if suite in {"ai_outputs", "cross_engine_model_outputs"}:
        return "raw_model_output"
    if suite in {"model_output_repairs", "cross_engine_model_repairs", "model_output_evidence_ladder"}:
        return "source_supported_model_output"
    if suite in {"model_output_adversarial", "issue_ablations"}:
        return "negative_control_output"
    if suite == "holdout_validation":
        return "frozen_holdout_output"
    return "curated_protocol_packet"


def _axis_folds(axis: dict, rows: list[dict]) -> list[dict]:
    groups = sorted({row[axis["id"]] for row in rows if row.get(axis["id"]) is not None})
    folds = []
    for group in groups:
        holdout = [row for row in rows if row.get(axis["id"]) == group]
        if len(holdout) < MIN_HOLDOUT_SIZE:
            continue
        training = [row for row in rows if row.get(axis["id"]) != group]
        if not training:
            continue
        folds.append(_fold(axis, group, training, holdout))
    return folds


def _fold(axis: dict, group: str, training: list[dict], holdout: list[dict]) -> dict:
    training_rules = _baseline_rows(training)
    holdout_rules = {row["id"]: row for row in _baseline_rows(holdout)}
    simplified_training = [row for row in training_rules if row["id"] != "full_audit_gate"]
    best_training = max(simplified_training, key=lambda row: (row["f1"], row["precision"], row["specificity"]))
    lowest_fp_training = min(simplified_training, key=lambda row: (row["false_positive"], -row["recall"]))
    balanced_training = max(
        simplified_training,
        key=lambda row: (row["balanced_accuracy"], row["f1"], row["precision"], row["specificity"]),
    )
    return {
        "axis": axis["id"],
        "axis_label": axis["label"],
        "holdout_group": group,
        "holdout_scenario_count": len(holdout),
        "holdout_qualified_count": sum(row["qualified"] for row in holdout),
        "training_scenario_count": len(training),
        "training_qualified_count": sum(row["qualified"] for row in training),
        "training_prediction_count": sum(row["denominator"] for row in training_rules),
        "holdout_prediction_count": sum(row["denominator"] for row in holdout_rules.values()),
        "best_trained_rule": best_training["id"],
        "best_trained_rule_training": _compact_rule(best_training),
        "best_trained_rule_holdout": _compact_rule(holdout_rules[best_training["id"]]),
        "lowest_fp_rule": lowest_fp_training["id"],
        "lowest_fp_rule_training": _compact_rule(lowest_fp_training),
        "lowest_fp_rule_holdout": _compact_rule(holdout_rules[lowest_fp_training["id"]]),
        "balanced_rule": balanced_training["id"],
        "balanced_rule_training": _compact_rule(balanced_training),
        "balanced_rule_holdout": _compact_rule(holdout_rules[balanced_training["id"]]),
        "full_protocol": _compact_rule(holdout_rules["full_audit_gate"]),
        "simplified_rules_with_holdout_error": sum(
            _has_error(row) for rule_id, row in holdout_rules.items() if rule_id != "full_audit_gate"
        ),
        "simplified_rule_count": len(holdout_rules) - 1,
    }


def _compact_rule(row: dict) -> dict:
    return {
        "id": row["id"],
        "label": row["label"],
        "denominator": row["denominator"],
        "precision": row["precision"],
        "recall": row["recall"],
        "specificity": row["specificity"],
        "balanced_accuracy": row["balanced_accuracy"],
        "f1": row["f1"],
        "false_positive": row["false_positive"],
        "false_negative": row["false_negative"],
    }


def _axis_summary(axis_id: str, folds: list[dict]) -> dict:
    axis_folds = [fold for fold in folds if fold["axis"] == axis_id]
    return {
        "axis": axis_id,
        "fold_count": len(axis_folds),
        "holdout_scenario_count": sum(fold["holdout_scenario_count"] for fold in axis_folds),
        "holdout_prediction_count": sum(fold["holdout_prediction_count"] for fold in axis_folds),
        "best_trained_rule_false_positive": sum(
            fold["best_trained_rule_holdout"]["false_positive"] for fold in axis_folds
        ),
        "best_trained_rule_false_negative": sum(
            fold["best_trained_rule_holdout"]["false_negative"] for fold in axis_folds
        ),
        "lowest_fp_rule_false_positive": sum(fold["lowest_fp_rule_holdout"]["false_positive"] for fold in axis_folds),
        "lowest_fp_rule_false_negative": sum(fold["lowest_fp_rule_holdout"]["false_negative"] for fold in axis_folds),
        "full_protocol_false_positive": sum(fold["full_protocol"]["false_positive"] for fold in axis_folds),
        "full_protocol_false_negative": sum(fold["full_protocol"]["false_negative"] for fold in axis_folds),
        "folds_with_best_trained_rule_error": sum(_has_error(fold["best_trained_rule_holdout"]) for fold in axis_folds),
    }


def _has_error(row: dict) -> bool:
    return row["false_positive"] + row["false_negative"] > 0


def _format_report(payload: dict) -> str:
    lines = [
        "# Multi-Axis Holdout Generalization",
        "",
        f"Axes: {payload['axis_count']}",
        f"Holdout folds: {payload['fold_count']}",
        f"Scenario packets: {payload['scenario_count']}",
        f"Qualified packets: {payload['qualified_count']}",
        f"Holdout baseline predictions: {payload['holdout_prediction_count']}",
        f"Training baseline predictions: {payload['training_prediction_count']}",
        f"Full protocol holdout false positives: {payload['full_protocol_holdout_false_positive']}",
        f"Full protocol holdout false negatives: {payload['full_protocol_holdout_false_negative']}",
        f"Best trained simplified rule holdout false positives: {payload['best_trained_rule_holdout_false_positive']}",
        f"Best trained simplified rule holdout false negatives: {payload['best_trained_rule_holdout_false_negative']}",
        f"Lowest-FP trained simplified rule holdout false positives: {payload['lowest_fp_rule_holdout_false_positive']}",
        f"Lowest-FP trained simplified rule holdout false negatives: {payload['lowest_fp_rule_holdout_false_negative']}",
        f"Balanced trained simplified rule holdout false positives: {payload['balanced_rule_holdout_false_positive']}",
        f"Balanced trained simplified rule holdout false negatives: {payload['balanced_rule_holdout_false_negative']}",
        f"Folds where the best trained simplified rule erred: {payload['folds_with_best_trained_rule_error']}/{payload['fold_count']}",
        f"Folds where the lowest-FP trained simplified rule erred: {payload['folds_with_lowest_fp_rule_error']}/{payload['fold_count']}",
        f"Folds where the balanced trained simplified rule erred: {payload['folds_with_balanced_rule_error']}/{payload['fold_count']}",
        "",
        "## Axis Summary",
        "",
        "| Axis | Folds | Holdout packets | Holdout predictions | Best-rule FP | Best-rule FN | Lowest-FP FP | Lowest-FP FN | Full FP/FN | Best-rule error folds |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in payload["axis_summaries"]:
        lines.append(
            f"| {summary['axis']} | {summary['fold_count']} | {summary['holdout_scenario_count']} | "
            f"{summary['holdout_prediction_count']} | {summary['best_trained_rule_false_positive']} | "
            f"{summary['best_trained_rule_false_negative']} | {summary['lowest_fp_rule_false_positive']} | "
            f"{summary['lowest_fp_rule_false_negative']} | {summary['full_protocol_false_positive']}/"
            f"{summary['full_protocol_false_negative']} | {summary['folds_with_best_trained_rule_error']} |"
        )
    lines.extend(
        [
            "",
            "## Holdout Folds",
            "",
            "| Axis | Held-out group | Packets | Qualified | Best trained rule | Best FP | Best FN | Lowest-FP rule | Lowest-FP FP | Lowest-FP FN | Balanced rule | Balanced FP | Balanced FN | Full FP/FN |",
            "| --- | --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for fold in payload["folds"]:
        lines.append(
            f"| {fold['axis']} | {fold['holdout_group']} | {fold['holdout_scenario_count']} | "
            f"{fold['holdout_qualified_count']} | {fold['best_trained_rule']} | "
            f"{fold['best_trained_rule_holdout']['false_positive']} | "
            f"{fold['best_trained_rule_holdout']['false_negative']} | {fold['lowest_fp_rule']} | "
            f"{fold['lowest_fp_rule_holdout']['false_positive']} | "
            f"{fold['lowest_fp_rule_holdout']['false_negative']} | {fold['balanced_rule']} | "
            f"{fold['balanced_rule_holdout']['false_positive']} | {fold['balanced_rule_holdout']['false_negative']} | "
            f"{fold['full_protocol']['false_positive']}/{fold['full_protocol']['false_negative']} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
