from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from run_baseline_comparison_analysis import _baseline_rows, _scenario_rows


RESULTS = ROOT / "experiments" / "issue_family_generalization" / "results"
FAMILIES = {
    "us_agency_deference": [
        "us-agency-deference",
        "loper-bright",
        "codex55-us",
        "-us-",
    ],
    "uk_mesothelioma": [
        "uk-mesothelioma",
        "fairchild",
        "codex55-uk",
        "-uk-",
    ],
    "eu_gdpr_article15": [
        "eu-gdpr",
        "gdpr-article15",
        "article15",
        "codex55-eu",
        "-eu-",
    ],
    "canada_vavilov": [
        "canada-vavilov",
        "vavilov",
    ],
    "germany_rtbf": [
        "germany-right-to-be-forgotten",
        "rtbf",
    ],
}


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [_with_family(row) for row in _scenario_rows()]
    rows = [row for row in rows if row["issue_family"] is not None]
    folds = [_fold(family, rows) for family in FAMILIES]
    payload = {
        "issue_family_count": len(folds),
        "scenario_count": len(rows),
        "qualified_count": sum(row["qualified"] for row in rows),
        "holdout_prediction_count": sum(fold["holdout_prediction_count"] for fold in folds),
        "training_prediction_count": sum(fold["training_prediction_count"] for fold in folds),
        "full_protocol_holdout_false_positive": sum(fold["full_protocol"]["false_positive"] for fold in folds),
        "full_protocol_holdout_false_negative": sum(fold["full_protocol"]["false_negative"] for fold in folds),
        "best_trained_rule_holdout_false_positive": sum(fold["best_trained_rule_holdout"]["false_positive"] for fold in folds),
        "best_trained_rule_holdout_false_negative": sum(fold["best_trained_rule_holdout"]["false_negative"] for fold in folds),
        "lowest_fp_rule_holdout_false_positive": sum(fold["lowest_fp_rule_holdout"]["false_positive"] for fold in folds),
        "lowest_fp_rule_holdout_false_negative": sum(fold["lowest_fp_rule_holdout"]["false_negative"] for fold in folds),
        "folds_with_best_trained_rule_error": sum(
            fold["best_trained_rule_holdout"]["false_positive"] + fold["best_trained_rule_holdout"]["false_negative"] > 0
            for fold in folds
        ),
        "folds_with_lowest_fp_rule_error": sum(
            fold["lowest_fp_rule_holdout"]["false_positive"] + fold["lowest_fp_rule_holdout"]["false_negative"] > 0
            for fold in folds
        ),
        "folds": folds,
    }
    report = _format_report(payload)
    (RESULTS / "issue_family_generalization.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "issue_family_generalization.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


def _with_family(row: dict) -> dict:
    text = f"{row['id']} {row['path']}".lower()
    family = None
    for candidate, needles in FAMILIES.items():
        if any(needle in text for needle in needles):
            family = candidate
            break
    return {**row, "issue_family": family}


def _fold(family: str, rows: list[dict]) -> dict:
    holdout = [row for row in rows if row["issue_family"] == family]
    training = [row for row in rows if row["issue_family"] != family]
    training_rules = _baseline_rows(training)
    holdout_rules = {row["id"]: row for row in _baseline_rows(holdout)}
    simplified_training = [row for row in training_rules if row["id"] != "full_audit_gate"]
    best_training = max(simplified_training, key=lambda row: (row["f1"], row["precision"], row["specificity"]))
    lowest_fp_training = min(simplified_training, key=lambda row: (row["false_positive"], -row["recall"]))
    return {
        "issue_family": family,
        "holdout_scenario_count": len(holdout),
        "holdout_qualified_count": sum(row["qualified"] for row in holdout),
        "training_scenario_count": len(training),
        "training_prediction_count": sum(row["denominator"] for row in training_rules),
        "holdout_prediction_count": sum(row["denominator"] for row in holdout_rules.values()),
        "best_trained_rule": best_training["id"],
        "best_trained_rule_training": _compact_rule(best_training),
        "best_trained_rule_holdout": _compact_rule(holdout_rules[best_training["id"]]),
        "lowest_fp_rule": lowest_fp_training["id"],
        "lowest_fp_rule_training": _compact_rule(lowest_fp_training),
        "lowest_fp_rule_holdout": _compact_rule(holdout_rules[lowest_fp_training["id"]]),
        "full_protocol": _compact_rule(holdout_rules["full_audit_gate"]),
        "simplified_rules_with_holdout_error": sum(
            row["false_positive"] + row["false_negative"] > 0
            for rule_id, row in holdout_rules.items()
            if rule_id != "full_audit_gate"
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
        "f1": row["f1"],
        "false_positive": row["false_positive"],
        "false_negative": row["false_negative"],
    }


def _format_report(payload: dict) -> str:
    lines = [
        "# Issue-Family Leave-One-Out Generalization",
        "",
        f"Issue families: {payload['issue_family_count']}",
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
        f"Folds where the best trained simplified rule erred on holdout: {payload['folds_with_best_trained_rule_error']}/{payload['issue_family_count']}",
        f"Folds where the lowest-FP trained simplified rule erred on holdout: {payload['folds_with_lowest_fp_rule_error']}/{payload['issue_family_count']}",
        "",
        "| Held-out issue family | Holdout packets | Qualified | Best trained rule | Best-rule FP | Best-rule FN | Lowest-FP rule | Lowest-FP FP | Lowest-FP FN | Simplified rules with holdout error | Full FP/FN |",
        "| --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for fold in payload["folds"]:
        lines.append(
            f"| {fold['issue_family']} | {fold['holdout_scenario_count']} | {fold['holdout_qualified_count']} | "
            f"{fold['best_trained_rule']} | {fold['best_trained_rule_holdout']['false_positive']} | "
            f"{fold['best_trained_rule_holdout']['false_negative']} | {fold['lowest_fp_rule']} | "
            f"{fold['lowest_fp_rule_holdout']['false_positive']} | {fold['lowest_fp_rule_holdout']['false_negative']} | "
            f"{fold['simplified_rules_with_holdout_error']}/{fold['simplified_rule_count']} | "
            f"{fold['full_protocol']['false_positive']}/{fold['full_protocol']['false_negative']} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
