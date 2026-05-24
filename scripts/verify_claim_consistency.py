from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "claim_consistency" / "results"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    payload = json.loads((ROOT / "experiments" / "full_validation" / "results" / "full_validation_report.json").read_text(encoding="utf-8"))
    checks = _checks(payload)
    failures = [check for check in checks if not check["passed"]]
    report = {
        "check_count": len(checks),
        "passed_count": len(checks) - len(failures),
        "failed_count": len(failures),
        "failures": failures,
        "checks": checks,
    }
    markdown = _format_report(report)
    (RESULTS / "claim_consistency_verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "claim_consistency_verification.md").write_text(markdown + "\n", encoding="utf-8")
    print(markdown)
    return 0 if not failures else 1


def _checks(payload: dict) -> list[dict]:
    units = payload["validation_units"]
    gate = payload["gate_ablation"]
    metric = payload["metric_separation"]
    repair = payload["repair_frontier"]
    values = {
        "suite_count": payload["suite_count"],
        "scenario_files": payload["scenario_files"],
        "embedded": units["total"],
        "rows": payload["total_evaluation_rows"],
        "formal": units["formal_invariant_checks"],
        "metric": units["metric_separation_evaluations"],
        "metric_resamples": units["metric_statistical_resamples"],
        "metric_bootstrap": metric["bootstrap"]["iterations"],
        "metric_permutation": metric["permutation"]["iterations"],
        "gate": units["gate_ablation_evaluations"],
        "gate_passed": gate["passed_count"],
        "qualified": gate["qualified_scenario_count"],
        "repair": units["repair_frontier_evaluations"],
        "repairable": repair["repairable_count"],
        "blocked_claims": repair["blocked_claim_count"],
        "expected_passed": payload["expected_passed"],
        "expected_total": payload["expected_total"],
        "source_verified": units["source_text_anchor_verified"],
        "source_total": units["source_text_anchor_checks"],
        "transcript_verified": units["model_output_transcript_locators_verified"],
        "transcript_total": units["model_output_transcript_locator_checks"],
        "metric_high_recall_blocked": metric["high_recall_blocked"]["count"],
        "metric_high_recall_total": metric["high_recall_blocked"]["denominator"],
    }
    expectations = [
        ("ARTIFACT.md", f"- {values['suite_count']} validation suites"),
        ("ARTIFACT.md", f"- {values['scenario_files']} scenario files"),
        ("ARTIFACT.md", f"- {values['embedded']} embedded records or output items"),
        ("ARTIFACT.md", f"- {_comma(values['rows'])} total evaluation rows"),
        ("ARTIFACT.md", f"- {_comma(values['formal'])}/{_comma(values['formal'])} formal invariant checks passed"),
        ("ARTIFACT.md", f"- {values['metric']} metric-separation evaluations"),
        ("ARTIFACT.md", f"- {_comma(values['metric_bootstrap'])} metric bootstrap resamples and {_comma(values['metric_permutation'])} metric permutation shuffles"),
        ("ARTIFACT.md", f"- {values['gate_passed']}/{values['gate']} gate-ablation evaluations passed"),
        ("ARTIFACT.md", f"- {values['repairable']}/{values['blocked_claims']} blocked procedural claims repairable across {_comma(values['repair'])} repair-frontier evaluations"),
        ("ARTIFACT.md", f"- {values['expected_passed']}/{values['expected_total']} scenario-regression expectations passed"),
        ("ARTIFACT.md", f"- {values['source_verified']}/{values['source_total']} public source-text anchors verified"),
        ("ARTIFACT.md", f"- {values['transcript_verified']}/{values['transcript_total']} raw model-output transcript locators verified"),
        ("ARTIFACT.md", "The expected manuscript build is 33 pages"),
        ("README.md", f"230 scenario files containing {values['embedded']} embedded records/items"),
        ("README.md", f"{_comma(values['formal'])} formal invariant checks"),
        ("README.md", f"{values['metric']} metric-separation evaluations, {_comma(values['metric_resamples'])} metric statistical resamples, {values['gate']} gate-ablation evaluations and {_comma(values['repair'])} repair-frontier evaluations"),
        ("README.md", f"| Metric separation analysis | {values['metric']} |"),
        ("README.md", f"| Metric statistical robustness | {values['metric_resamples']} |"),
        ("README.md", f"| Qualified-output gate ablations | {values['gate']} |"),
        ("README.md", f"| Blocked-claim repair frontiers | {values['repair']} |"),
        ("README.md", "python scripts/run_gate_ablation_analysis.py"),
        ("README.md", "python scripts/run_repair_frontier_analysis.py"),
        ("docs/paper_mapping.md", "Qualified-output gate ablations"),
        ("docs/paper_mapping.md", "Metric bootstrap/permutation robustness"),
        ("docs/paper_mapping.md", "Blocked-claim repair frontiers"),
        ("docs/paper_mapping.md", "bootstrap/permutation robustness"),
        ("docs/paper_mapping.md", "gate-ablation layer"),
        ("docs/paper_mapping.md", "repair-frontier layer"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['gate_passed']}/{values['gate']} gate-ablation evaluations"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{_comma(values['metric_bootstrap'])} metric bootstrap resamples, {_comma(values['metric_permutation'])} metric permutation shuffles"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['repairable']}/{values['blocked_claims']} blocked procedural claims repairable across {_comma(values['repair'])} repair-frontier evaluations"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_gate_ablation_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_repair_frontier_analysis.py"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['scenario_files']} scenario packets with {values['embedded']} embedded records or outputs"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['formal'])} formal invariant checks, {values['metric']} metric-separation evaluations, {_comma(values['metric_resamples'])} metric resamples"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['metric_resamples'])} metric bootstrap/permutation resamples"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Across all {values['qualified']} qualified packets"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['gate_passed']}/{values['gate']} counterfactual downgrades"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"across {values['blocked_claims']} blocked high-status claims"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Qualified-output gate ablations & {values['gate']} ablations & {values['gate_passed']}/{values['gate']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Blocked-claim repair frontiers & {_comma(values['repair'])} counterfactuals & {values['repairable']}/{values['blocked_claims']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Validation suites: {values['suite_count']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Scenario files: {values['scenario_files']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Metric statistical resamples: {values['metric_bootstrap']} bootstrap resamples and {values['metric_permutation']} permutation shuffles"),
        ("experiments/full_validation/results/full_validation_report.md", f"Gate ablation evaluations: {values['gate_passed']}/{values['gate']} passed over {values['qualified']} qualified packets"),
        ("experiments/full_validation/results/full_validation_report.md", f"Repair frontier evaluations: {values['repairable']}/{values['blocked_claims']} blocked claims repairable across {values['repair']} counterfactual repairs"),
        ("experiments/full_validation/results/full_validation_report.md", f"Metric separation evaluations: {values['metric']} upstream-metric scenario packets; high-recall blocked outputs {values['metric_high_recall_blocked']}/{values['metric_high_recall_total']}"),
    ]
    checks = []
    for path, expected in expectations:
        text = (ROOT / path).read_text(encoding="utf-8")
        checks.append({"path": path, "expected": expected, "passed": expected in text})
    return checks


def _comma(value: int) -> str:
    return f"{value:,}"


def _format_report(payload: dict) -> str:
    lines = [
        "# Claim Consistency Verification",
        "",
        f"Checks: {payload['passed_count']}/{payload['check_count']}",
        f"All passed: {payload['failed_count'] == 0}",
    ]
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(f"- {failure['path']}: missing `{failure['expected']}`")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
