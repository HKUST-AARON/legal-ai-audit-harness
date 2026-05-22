from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from statistics import mean

from .model import AuditResult, evaluate_scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="legal-ai-audit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    score_parser = subparsers.add_parser("score", help="score one audit scenario")
    score_parser.add_argument("scenario", type=Path)
    score_parser.add_argument("--json", action="store_true", dest="as_json")

    run_parser = subparsers.add_parser("run", help="run a directory of audit scenarios")
    run_parser.add_argument("path", type=Path)
    run_parser.add_argument("--out", type=Path)
    run_parser.add_argument("--json-out", type=Path)

    experiment_parser = subparsers.add_parser("experiment", help="run scenarios and summarize audit/retrieval relationships")
    experiment_parser.add_argument("path", type=Path)
    experiment_parser.add_argument("--out", type=Path)
    experiment_parser.add_argument("--json-out", type=Path)

    args = parser.parse_args(argv)
    if args.command == "score":
        result = evaluate_scenario(_read_json(args.scenario))
        if args.as_json:
            print(json.dumps(asdict(result), indent=2, sort_keys=True))
        else:
            print(_format_result(result))
        return 0 if result.expected_passed else 1

    scenarios = [_read_json(path) for path in _scenario_paths(args.path)]
    results = [evaluate_scenario(scenario) for scenario in scenarios]
    report = _format_experiment(scenarios, results) if args.command == "experiment" else _format_report(results)
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        payload = _experiment_payload(scenarios, results) if args.command == "experiment" else [asdict(r) for r in results]
        args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return 0 if all(result.expected_passed for result in results) else 1


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _scenario_paths(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.glob("*.json"))


def _format_result(result: AuditResult) -> str:
    car = "n/a" if result.counter_authority_recall is None else f"{result.counter_authority_recall:.2f}"
    missing = ", ".join(result.missing_gates) if result.missing_gates else "none"
    return "\n".join(
        [
            f"scenario: {result.scenario_id}",
            f"claimed_status: {result.claimed_status}",
            f"allowed_status: {result.allowed_status}",
            f"claim_supported: {result.claim_supported}",
            f"total_score: {result.total_score}",
            f"scores: {result.scores}",
            f"missing_gates: {missing}",
            f"counter_authority_recall: {car}",
            f"authority_coverage: {_metric(result.authority_coverage)}",
            f"invalid_authority_rate: {_metric(result.invalid_authority_rate)}",
            f"evidence_fidelity: {_metric(result.evidence_fidelity)}",
            f"evidence_coverage: {_metric(result.evidence_coverage)}",
            f"source_tag_coverage: {_metric(result.source_tag_coverage)}",
            f"disposition: {result.disposition}",
            f"expected_passed: {result.expected_passed}",
        ]
    )


def _format_report(results: list[AuditResult]) -> str:
    lines = [
        "# Legal AI Audit Harness Report",
        "",
        "| Scenario | Claimed | Allowed | Score | CAR | Disposition | Claim supported | Expected passed |",
        "| --- | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for result in results:
        car = "n/a" if result.counter_authority_recall is None else f"{result.counter_authority_recall:.2f}"
        lines.append(
            "| "
            + " | ".join(
                [
                    result.scenario_id,
                    result.claimed_status,
                    result.allowed_status,
                    str(result.total_score),
                    car,
                    result.disposition,
                    str(result.claim_supported),
                    str(result.expected_passed),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _format_experiment(scenarios: list[dict], results: list[AuditResult]) -> str:
    rows = _experiment_rows(scenarios, results)
    blocked_despite_recall = [row for row in rows if row["upstream_recall"] is not None and row["upstream_recall"] >= 0.8 and row["allowed_status"] in {"reference_information", "no_external_legal_effect"}]
    allowed_by_status = {}
    for row in rows:
        allowed_by_status[row["allowed_status"]] = allowed_by_status.get(row["allowed_status"], 0) + 1
    lines = [
        "# Legal AI Audit Harness Experiment",
        "",
        f"Scenarios: {len(rows)}",
        f"Expected outcomes passed: {sum(row['expected_passed'] for row in rows)}/{len(rows)}",
        f"Mean audit score: {_metric(mean(row['total_score'] for row in rows))}",
        f"Mean upstream recall: {_metric(_mean_optional(row['upstream_recall'] for row in rows))}",
        f"High-upstream-performance but procedurally blocked scenarios: {len(blocked_despite_recall)}",
        "",
        "## Allowed Status Distribution",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    for status, count in sorted(allowed_by_status.items()):
        lines.append(f"| {status} | {count} |")
    lines.extend(
        [
            "",
            "## Scenario Results",
            "",
            "| Scenario | Profile | Claimed | Allowed | Score | Upstream recall | CAR | Authority coverage | Evidence fidelity | Source tags | Disposition |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["scenario_id"],
                    row["jurisdiction_profile"],
                    row["claimed_status"],
                    row["allowed_status"],
                    str(row["total_score"]),
                    _metric(row["upstream_recall"]),
                    _metric(row["counter_authority_recall"]),
                    _metric(row["authority_coverage"]),
                    _metric(row["evidence_fidelity"]),
                    _metric(row["source_tag_coverage"]),
                    row["disposition"],
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _experiment_payload(scenarios: list[dict], results: list[AuditResult]) -> dict:
    rows = _experiment_rows(scenarios, results)
    return {
        "summary": {
            "scenario_count": len(rows),
            "expected_passed": sum(row["expected_passed"] for row in rows),
            "mean_audit_score": mean(row["total_score"] for row in rows),
            "mean_upstream_recall": _mean_optional(row["upstream_recall"] for row in rows),
            "high_upstream_but_blocked": len([row for row in rows if row["upstream_recall"] is not None and row["upstream_recall"] >= 0.8 and row["allowed_status"] in {"reference_information", "no_external_legal_effect"}]),
        },
        "results": rows,
    }


def _experiment_rows(scenarios: list[dict], results: list[AuditResult]) -> list[dict]:
    rows = []
    for scenario, result in zip(scenarios, results):
        row = asdict(result)
        metrics = scenario.get("upstream_metrics", {})
        row["jurisdiction_profile"] = scenario.get("jurisdiction_profile", "unspecified")
        row["upstream_precision"] = metrics.get("precision")
        row["upstream_recall"] = metrics.get("recall")
        row["upstream_f1"] = metrics.get("f1")
        rows.append(row)
    return rows


def _mean_optional(values) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return mean(present)


def _metric(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


if __name__ == "__main__":
    sys.exit(main())
