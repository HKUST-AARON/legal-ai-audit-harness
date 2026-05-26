from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import STATUS_RANK, evaluate_scenario
from run_full_validation import SUITES

RESULTS = ROOT / "experiments" / "ranked_retrieval_metrics" / "results"
THRESHOLD = 0.8
RESAMPLE_ITERATIONS = 1000
RNG_SEED = 20526
METRICS = (
    "precision_at_5",
    "recall_at_5",
    "recall_at_10",
    "average_precision",
    "reciprocal_rank",
    "ndcg_at_5",
    "ndcg_at_10",
)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = _ranked_rows()
    payload = {
        "scenario_count": len(_all_scenario_paths()),
        "ranked_scenario_count": len(rows),
        "qualified_count": sum(row["qualified"] for row in rows),
        "metric_count": len(METRICS),
        "threshold": THRESHOLD,
        "prediction_count": len(rows) * len(METRICS),
        "point_biserial": {metric: _point_biserial(rows, metric) for metric in METRICS},
        "threshold_tests": [
            _confusion_row(rows, f"{metric}>={THRESHOLD}", lambda row, metric=metric: row[metric] >= THRESHOLD)
            for metric in METRICS
        ],
        "high_metric_blocked": {
            metric: _high_metric_blocked(rows, metric)
            for metric in METRICS
        },
        "best_threshold_rule": _best_rule(rows),
        "bootstrap": _bootstrap(rows),
        "permutation": _permutation(rows),
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "ranked_retrieval_metric_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "ranked_retrieval_metric_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


def _all_scenario_paths() -> list[Path]:
    paths: list[Path] = []
    for suite in SUITES:
        paths.extend(sorted(suite["path"].glob("*.json")))
    return paths


def _ranked_rows() -> list[dict]:
    rows = []
    for path in _all_scenario_paths():
        scenario = json.loads(path.read_text(encoding="utf-8"))
        authority_sets = scenario.get("authority_sets") or {}
        retrieved = authority_sets.get("retrieved") or []
        relevant = set(authority_sets.get("high_authority") or []) | set(authority_sets.get("counter_or_limiting") or [])
        if not retrieved or not relevant:
            continue
        result = evaluate_scenario(scenario)
        qualified = STATUS_RANK[result.allowed_status] >= STATUS_RANK["normative_material_screening_output"]
        metrics = _ranking_metrics(retrieved, relevant, set(authority_sets.get("high_authority") or []))
        rows.append(
            {
                "scenario_id": scenario["id"],
                "path": str(path.relative_to(ROOT)),
                "allowed_status": result.allowed_status,
                "qualified": qualified,
                "failure_flags": result.failure_flags,
                "disposition": result.disposition,
                "retrieved_count": len(retrieved),
                "relevant_count": len(relevant),
                "retrieved_relevant_count": len(set(retrieved) & relevant),
                "retrieved_invalid_treatment_count": len(authority_sets.get("retrieved_invalid_treatments") or []),
                **metrics,
            }
        )
    return rows


def _ranking_metrics(retrieved: list[str], relevant: set[str], high_authority: set[str]) -> dict[str, float]:
    binary = [1 if item in relevant else 0 for item in retrieved]
    graded = [2 if item in high_authority else 1 if item in relevant else 0 for item in retrieved]
    return {
        "precision_at_5": sum(binary[:5]) / min(5, len(retrieved)),
        "recall_at_5": sum(binary[:5]) / len(relevant),
        "recall_at_10": sum(binary[:10]) / len(relevant),
        "average_precision": _average_precision(binary, len(relevant)),
        "reciprocal_rank": _reciprocal_rank(binary),
        "ndcg_at_5": _ndcg(graded, len(high_authority), len(relevant - high_authority), 5),
        "ndcg_at_10": _ndcg(graded, len(high_authority), len(relevant - high_authority), 10),
    }


def _average_precision(binary: list[int], relevant_count: int) -> float:
    hits = 0
    precisions = []
    for index, value in enumerate(binary, start=1):
        if value:
            hits += 1
            precisions.append(hits / index)
    return sum(precisions) / relevant_count if relevant_count else 0.0


def _reciprocal_rank(binary: list[int]) -> float:
    for index, value in enumerate(binary, start=1):
        if value:
            return 1 / index
    return 0.0


def _ndcg(graded: list[int], high_count: int, counter_count: int, k: int) -> float:
    dcg = _dcg(graded[:k])
    ideal = [2] * high_count + [1] * counter_count
    idcg = _dcg(ideal[:k])
    return 0.0 if idcg == 0 else dcg / idcg


def _dcg(values: list[int]) -> float:
    return sum((2**value - 1) / math.log2(index + 1) for index, value in enumerate(values, start=1))


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


def _high_metric_blocked(rows: list[dict], metric: str) -> dict:
    blocked = [
        row
        for row in rows
        if row[metric] >= THRESHOLD
        and STATUS_RANK[row["allowed_status"]] < STATUS_RANK["normative_material_screening_output"]
    ]
    return {
        "metric": metric,
        "count": len(blocked),
        "denominator": sum(row[metric] >= THRESHOLD for row in rows),
        "rate": _safe_div(len(blocked), sum(row[metric] >= THRESHOLD for row in rows)),
        "failure_flags": _flag_counts(blocked),
        "status_distribution": _status_counts(blocked),
        "invalid_treatment_hits": sum(row["retrieved_invalid_treatment_count"] for row in blocked),
    }


def _best_rule(rows: list[dict]) -> dict:
    tests = [_confusion_row(rows, f"{metric}>={THRESHOLD}", lambda row, metric=metric: row[metric] >= THRESHOLD) for metric in METRICS]
    return max(tests, key=lambda row: (2 * row["precision"] * row["recall"]) / (row["precision"] + row["recall"]) if row["precision"] + row["recall"] else 0.0)


def _bootstrap(rows: list[dict]) -> dict:
    rng = random.Random(RNG_SEED)
    samples = []
    for _ in range(RESAMPLE_ITERATIONS):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        ndcg_test = _confusion_row(sample, f"ndcg_at_10>={THRESHOLD}", lambda row: row["ndcg_at_10"] >= THRESHOLD)
        samples.append(
            {
                "ndcg_at_10_point_biserial": _point_biserial(sample, "ndcg_at_10"),
                "ndcg_at_10_threshold_precision": ndcg_test["precision"],
                "ndcg_at_10_blocked_rate": _high_metric_blocked(sample, "ndcg_at_10")["rate"],
            }
        )
    return {
        "iterations": RESAMPLE_ITERATIONS,
        "seed": RNG_SEED,
        "confidence_interval": {
            metric: _interval([sample[metric] for sample in samples])
            for metric in samples[0]
        },
    }


def _permutation(rows: list[dict]) -> dict:
    observed = abs(_point_biserial(rows, "ndcg_at_10"))
    observed_cmp = round(observed, 12)
    scores = [row["ndcg_at_10"] for row in rows]
    labels = [1 if row["qualified"] else 0 for row in rows]
    more_extreme = 0
    for iteration in range(RESAMPLE_ITERATIONS):
        shuffled = _deterministic_permutation(labels, iteration)
        if round(abs(_point_biserial_vectors(scores, shuffled)), 12) >= observed_cmp:
            more_extreme += 1
    return {
        "iterations": RESAMPLE_ITERATIONS,
        "seed": RNG_SEED,
        "metric": "ndcg_at_10_point_biserial",
        "observed_abs": observed,
        "two_sided_p": (more_extreme + 1) / (RESAMPLE_ITERATIONS + 1),
    }


def _point_biserial_vectors(xs: list[float], ys: list[int]) -> float:
    mean_x = mean(xs)
    mean_y = mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator_x = sum((x - mean_x) ** 2 for x in xs)
    denominator_y = sum((y - mean_y) ** 2 for y in ys)
    if denominator_x == 0 or denominator_y == 0:
        return 0.0
    return numerator / ((denominator_x * denominator_y) ** 0.5)


def _deterministic_permutation(values: list[int], iteration: int) -> list[int]:
    order = sorted(
        range(len(values)),
        key=lambda index: hashlib.sha256(f"{RNG_SEED}:{iteration}:{index}".encode("utf-8")).hexdigest(),
    )
    return [values[index] for index in order]


def _interval(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "low": ordered[int(0.025 * (len(ordered) - 1))],
        "median": ordered[int(0.5 * (len(ordered) - 1))],
        "high": ordered[int(0.975 * (len(ordered) - 1))],
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
        "# Ranked Retrieval Metric Analysis",
        "",
        f"Scenario packets: {payload['scenario_count']}",
        f"Ranked packets with known relevant authority sets: {payload['ranked_scenario_count']}",
        f"Procedurally qualified outputs: {payload['qualified_count']}",
        f"Metric threshold predictions: {payload['prediction_count']}",
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
    best = payload["best_threshold_rule"]
    lines.extend(
        [
            "",
            "## Best Single-Metric Rule",
            "",
            f"Best threshold rule: {best['label']} with {best['false_positive']} false positives and {best['false_negative']} false negatives.",
            "",
            "## High-Metric Blocked Outputs",
            "",
            "| Metric | Blocked | Denominator | Blocked rate | Invalid treatment hits |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for metric in METRICS:
        blocked = payload["high_metric_blocked"][metric]
        lines.append(
            f"| {metric} | {blocked['count']} | {blocked['denominator']} | {blocked['rate']:.2f} | {blocked['invalid_treatment_hits']} |"
        )
    lines.extend(
        [
            "",
            "## Bootstrap and Permutation Robustness",
            "",
            f"Bootstrap resamples: {payload['bootstrap']['iterations']} with seed {payload['bootstrap']['seed']}.",
            f"nDCG@10 point-biserial permutation p-value: {payload['permutation']['two_sided_p']:.3f}.",
            "",
            "| Metric | 2.5% | Median | 97.5% |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for metric, interval in sorted(payload["bootstrap"]["confidence_interval"].items()):
        lines.append(
            f"| {metric} | {interval['low']:.2f} | {interval['median']:.2f} | {interval['high']:.2f} |"
        )
    return "\n".join(lines)


def _confusion_line(row: dict) -> str:
    return (
        f"| {row['label']} | {row['true_positive']} | {row['false_positive']} | {row['true_negative']} | "
        f"{row['false_negative']} | {row['precision']:.2f} | {row['recall']:.2f} | {row['specificity']:.2f} |"
    )


if __name__ == "__main__":
    raise SystemExit(main())
