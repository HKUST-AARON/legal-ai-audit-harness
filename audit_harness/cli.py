from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

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

    args = parser.parse_args(argv)
    if args.command == "score":
        result = evaluate_scenario(_read_json(args.scenario))
        if args.as_json:
            print(json.dumps(asdict(result), indent=2, sort_keys=True))
        else:
            print(_format_result(result))
        return 0 if result.expected_passed else 1

    results = [evaluate_scenario(_read_json(path)) for path in _scenario_paths(args.path)]
    report = _format_report(results)
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps([asdict(r) for r in results], indent=2, sort_keys=True), encoding="utf-8")
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


if __name__ == "__main__":
    sys.exit(main())
