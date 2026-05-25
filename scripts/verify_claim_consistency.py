from __future__ import annotations

import json
import re
import sys
import zlib
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
    baseline = payload["baseline_comparison"]
    repair = payload["repair_frontier"]
    jurisdiction = payload["jurisdiction_profile"]
    ranking = payload["ranking_visibility"]
    certificate = payload["status_certificate"]
    uncertainty = payload["annotation_uncertainty"]
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
        "baseline_predictions": units["baseline_comparison_predictions"],
        "baseline_count": baseline["baseline_count"],
        "baseline_best_fp": baseline["best_simplified"]["false_positive"],
        "baseline_full_fp": baseline["full_gate"]["false_positive"],
        "gate": units["gate_ablation_evaluations"],
        "gate_passed": gate["passed_count"],
        "qualified": gate["qualified_scenario_count"],
        "repair": units["repair_frontier_evaluations"],
        "repairable": repair["repairable_count"],
        "blocked_claims": repair["blocked_claim_count"],
        "jurisdiction": units["jurisdiction_profile_evaluations"],
        "jurisdiction_profile_checks": jurisdiction["profile_check_count"],
        "jurisdiction_supported": jurisdiction["profile_supported_count"],
        "jurisdiction_mutations": jurisdiction["counterfactual_evaluation_count"],
        "jurisdiction_mutations_passed": jurisdiction["passed_count"],
        "jurisdiction_qualified": jurisdiction["qualified_status_count"],
        "ranking": units["ranking_visibility_checks"],
        "ranking_window": units["ranking_visibility_window_checks"],
        "ranking_counterfactuals": units["ranking_visibility_counterfactuals"],
        "ranking_passed": ranking["rank_order_passed_count"],
        "ranking_eligible": ranking["eligible_packet_count"],
        "ranking_front_window": ranking["front_window_packet_count"],
        "ranking_visible": ranking["front_window_counter_visible"],
        "ranking_drifted_visible": ranking["counterfactual_front_window_counter_visible"],
        "ranking_median": ranking["median_first_counter_rank"],
        "certificate_checks": units["status_certificate_replay_checks"],
        "certificate_count": certificate["certificate_count"],
        "certificates_verified": certificate["verified_certificate_count"],
        "certificate_passed": certificate["passed_check_count"],
        "uncertainty": uncertainty["evaluation_count"],
        "uncertainty_stability": uncertainty["status_stability_rate"],
        "uncertainty_qualified_high": uncertainty["qualified_high_status_stability_rate"],
        "uncertainty_boundary": uncertainty["boundary_scenario_count"],
        "expected_passed": payload["expected_passed"],
        "expected_total": payload["expected_total"],
        "source_verified": units["source_text_anchor_verified"],
        "source_total": units["source_text_anchor_checks"],
        "transcript_verified": units["model_output_transcript_locators_verified"],
        "transcript_total": units["model_output_transcript_locator_checks"],
        "metric_high_recall_blocked": metric["high_recall_blocked"]["count"],
        "metric_high_recall_total": metric["high_recall_blocked"]["denominator"],
        "pdf_pages": _pdf_page_count(ROOT / "manuscript" / "ai_law_case_recommendation_verifiability.pdf"),
    }
    expectations = [
        ("ARTIFACT.md", f"- {values['suite_count']} validation suites"),
        ("ARTIFACT.md", f"- {values['scenario_files']} scenario files"),
        ("ARTIFACT.md", f"- {values['embedded']} embedded records or output items"),
        ("ARTIFACT.md", f"- {_comma(values['rows'])} total evaluation rows"),
        ("ARTIFACT.md", f"- {_comma(values['formal'])}/{_comma(values['formal'])} formal invariant checks passed"),
        ("ARTIFACT.md", f"- {values['metric']} metric-separation evaluations"),
        ("ARTIFACT.md", f"- {_comma(values['metric_bootstrap'])} metric bootstrap resamples and {_comma(values['metric_permutation'])} metric permutation shuffles"),
        ("ARTIFACT.md", f"- {_comma(values['baseline_predictions'])} baseline-rule predictions across {values['baseline_count']} alternative status rules"),
        ("ARTIFACT.md", f"- {values['gate_passed']}/{values['gate']} gate-ablation evaluations passed"),
        ("ARTIFACT.md", f"- {values['repairable']}/{values['blocked_claims']} blocked procedural claims repairable across {_comma(values['repair'])} repair-frontier evaluations"),
        ("ARTIFACT.md", f"- {values['jurisdiction_supported']}/{values['jurisdiction_profile_checks']} jurisdiction-profile checks and {values['jurisdiction_mutations_passed']}/{values['jurisdiction_mutations']} profile mutations passed"),
        ("ARTIFACT.md", f"- {values['ranking_window']} rank-window visibility checks over {values['ranking']} high-status claims"),
        ("ARTIFACT.md", f"- {values['ranking_passed']}/{values['ranking_counterfactuals']} rank-order visibility counterfactuals downgraded with coverage preserved"),
        ("ARTIFACT.md", f"- {_comma(values['certificate_passed'])}/{_comma(values['certificate_checks'])} status-certificate replay checks passed over {values['certificate_count']} certificates"),
        ("ARTIFACT.md", f"- {_comma(values['uncertainty'])} annotation-uncertainty perturbations with {values['uncertainty_stability']:.3f} sample stability"),
        ("ARTIFACT.md", f"- {values['expected_passed']}/{values['expected_total']} scenario-regression expectations passed"),
        ("ARTIFACT.md", f"- {values['source_verified']}/{values['source_total']} public source-text anchors verified"),
        ("ARTIFACT.md", f"- {values['transcript_verified']}/{values['transcript_total']} raw model-output transcript locators verified"),
        ("ARTIFACT.md", f"The expected manuscript build is {values['pdf_pages']} pages"),
        ("README.md", f"{values['scenario_files']} scenario files containing {values['embedded']} embedded records/items"),
        ("README.md", f"{_comma(values['formal'])} formal invariant checks"),
        ("README.md", f"{values['metric']} metric-separation evaluations, {_comma(values['metric_resamples'])} metric statistical resamples, {_comma(values['baseline_predictions'])} baseline-rule predictions, {values['gate']} gate-ablation evaluations, {_comma(values['repair'])} repair-frontier evaluations, {values['jurisdiction']} jurisdiction-profile checks, {values['ranking_window']} rank-window visibility checks, {values['ranking_counterfactuals']} rank-order counterfactuals and {_comma(values['certificate_checks'])} status-certificate replay checks"),
        ("README.md", f"{_comma(values['uncertainty'])} score-uncertainty perturbations"),
        ("README.md", f"| Metric separation analysis | {values['metric']} |"),
        ("README.md", f"| Metric statistical robustness | {values['metric_resamples']} |"),
        ("README.md", f"| Baseline rule comparison | {values['baseline_predictions']} |"),
        ("README.md", f"| Qualified-output gate ablations | {values['gate']} |"),
        ("README.md", f"| Blocked-claim repair frontiers | {values['repair']} |"),
        ("README.md", f"| Jurisdiction-profile mutations | {values['jurisdiction']} |"),
        ("README.md", f"| Ranking-visibility diagnostics | {values['ranking_window']} |"),
        ("README.md", f"| Status certificate replay | {values['certificate_checks']} |"),
        ("README.md", f"| Annotation uncertainty Monte Carlo | {values['uncertainty']} |"),
        ("README.md", f"| Out-of-sample holdout validation | {units['holdout_records']} |"),
        ("README.md", "python scripts/run_gate_ablation_analysis.py"),
        ("README.md", "python scripts/run_repair_frontier_analysis.py"),
        ("README.md", "python scripts/run_jurisdiction_profile_analysis.py"),
        ("README.md", "python scripts/run_ranking_visibility_analysis.py"),
        ("README.md", "python scripts/run_status_certificate_validation.py"),
        ("docs/paper_mapping.md", "Qualified-output gate ablations"),
        ("docs/paper_mapping.md", "Metric bootstrap/permutation robustness"),
        ("docs/paper_mapping.md", "Baseline rule comparison"),
        ("docs/paper_mapping.md", "Blocked-claim repair frontiers"),
        ("docs/paper_mapping.md", "Jurisdiction-profile mutations"),
        ("docs/paper_mapping.md", "Ranking-visibility diagnostics"),
        ("docs/paper_mapping.md", "Status certificate replay"),
        ("docs/paper_mapping.md", "Annotation uncertainty Monte Carlo"),
        ("docs/paper_mapping.md", "Out-of-sample holdout validation"),
        ("docs/paper_mapping.md", "bootstrap/permutation robustness"),
        ("docs/paper_mapping.md", "baseline-comparison layer"),
        ("docs/paper_mapping.md", "gate-ablation layer"),
        ("docs/paper_mapping.md", "repair-frontier layer"),
        ("docs/paper_mapping.md", "jurisdiction-profile layer"),
        ("docs/paper_mapping.md", "ranking-visibility layer"),
        ("docs/paper_mapping.md", "status-certificate layer"),
        ("docs/paper_mapping.md", "annotation-uncertainty layer"),
        ("docs/paper_mapping.md", "holdout layer"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['gate_passed']}/{values['gate']} gate-ablation evaluations"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{_comma(values['metric_bootstrap'])} metric bootstrap resamples, {_comma(values['metric_permutation'])} metric permutation shuffles"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{_comma(values['baseline_predictions'])} baseline-rule predictions across {values['baseline_count']} alternative status rules"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['repairable']}/{values['blocked_claims']} blocked procedural claims repairable across {_comma(values['repair'])} repair-frontier evaluations"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['jurisdiction_supported']}/{values['jurisdiction_profile_checks']} jurisdiction-profile checks, {values['jurisdiction_mutations_passed']}/{values['jurisdiction_mutations']} profile mutations"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['ranking_window']} rank-window visibility checks over {values['ranking']} high-status claims"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['ranking_passed']}/{values['ranking_counterfactuals']} rank-order counterfactuals"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{values['certificates_verified']}/{values['certificate_count']} status certificates verified, {_comma(values['certificate_passed'])}/{_comma(values['certificate_checks'])} replay checks"),
        ("skills/legal-ai-audit-harness/SKILL.md", f"{_comma(values['uncertainty'])} annotation-uncertainty perturbations"),
        ("skills/legal-ai-audit-harness/SKILL.md", "holdout file"),
        ("skills/legal-ai-audit-harness/SKILL.md", "baseline-comparison file"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_baseline_comparison_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_gate_ablation_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_repair_frontier_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_jurisdiction_profile_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_ranking_visibility_analysis.py"),
        ("skills/legal-ai-audit-harness/SKILL.md", "python scripts/run_status_certificate_validation.py"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['scenario_files']} scenario packets with {values['embedded']} embedded records or outputs"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['metric_resamples'])} metric bootstrap/permutation resamples"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['baseline_predictions'])} baseline-rule predictions"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Across {values['baseline_count']} alternative status rules"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"still produced {values['baseline_best_fp']} false positives"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['uncertainty'])} annotation-uncertainty perturbations"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['uncertainty_stability']:.3f} sample-level status stability"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"high-status stability was {values['uncertainty_qualified_high']:.3f}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{_comma(values['certificate_checks'])} status-certificate replay checks"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['certificates_verified']}/{values['certificate_count']} status certificates"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Across all {values['qualified']} qualified packets"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['gate_passed']}/{values['gate']} counterfactual downgrades"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"across {values['blocked_claims']} blocked high-status claims"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['jurisdiction_supported']}/{values['jurisdiction_profile_checks']} profile checks"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['jurisdiction_mutations_passed']}/{values['jurisdiction_mutations']} profile mutations"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['ranking_window']} rank-window visibility checks"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"{values['ranking_counterfactuals']} rank-order visibility counterfactuals"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"top-3 counter-material visibility was {values['ranking_visible']}/{values['ranking_front_window']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"drifted top-3 counter-material visibility was {values['ranking_drifted_visible']}/{values['ranking_counterfactuals']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"median first counter-material rank was {values['ranking_median']:.1f}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Qualified-output gate ablations & {values['gate']} ablations & {values['gate_passed']}/{values['gate']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Blocked-claim repair frontiers & {_comma(values['repair'])} counterfactuals & {values['repairable']}/{values['blocked_claims']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Jurisdiction-profile mutations & {values['jurisdiction']} checks & {values['jurisdiction_mutations_passed']}/{values['jurisdiction_mutations']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Ranking-visibility diagnostics & {values['ranking_window']} window checks / {values['ranking_counterfactuals']} counterfactuals & {values['ranking_passed']}/{values['ranking_counterfactuals']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Status certificate replay & {_comma(values['certificate_checks'])} checks & {_comma(values['certificate_passed'])}/{_comma(values['certificate_checks'])}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Baseline rule comparison & {_comma(values['baseline_predictions'])} predictions & Best simplified false positives {values['baseline_best_fp']}; full gate false positives {values['baseline_full_fp']}"),
        ("manuscript/ai_law_case_recommendation_verifiability.tex", f"Annotation uncertainty & {_comma(values['uncertainty'])} perturbations & {values['uncertainty_stability']:.3f} sample stability; {values['uncertainty_qualified_high']:.3f} qualified high-status stability"),
        ("experiments/full_validation/results/full_validation_report.md", f"Validation suites: {values['suite_count']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Scenario files: {values['scenario_files']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Metric statistical resamples: {values['metric_bootstrap']} bootstrap resamples and {values['metric_permutation']} permutation shuffles"),
        ("experiments/full_validation/results/full_validation_report.md", f"Baseline rule comparisons: {values['baseline_predictions']} predictions across {values['baseline_count']} rules; best simplified false positives {values['baseline_best_fp']}; full gate false positives {values['baseline_full_fp']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Gate ablation evaluations: {values['gate_passed']}/{values['gate']} passed over {values['qualified']} qualified packets"),
        ("experiments/full_validation/results/full_validation_report.md", f"Repair frontier evaluations: {values['repairable']}/{values['blocked_claims']} blocked claims repairable across {values['repair']} counterfactual repairs"),
        ("experiments/full_validation/results/full_validation_report.md", f"Jurisdiction-profile evaluations: {values['jurisdiction_supported']}/{values['jurisdiction_profile_checks']} profile checks supported; {values['jurisdiction_mutations_passed']}/{values['jurisdiction_mutations']} counterfactual mutations passed"),
        ("experiments/full_validation/results/full_validation_report.md", f"Ranking-visibility checks: {values['ranking_window']} rank-window checks over {values['ranking']} high-status claims; {values['ranking_passed']}/{values['ranking_counterfactuals']} rank-order counterfactuals downgraded with coverage preserved; top-3 counter visible {values['ranking_visible']}/{values['ranking_front_window']}; drifted top-3 counter visible {values['ranking_drifted_visible']}/{values['ranking_counterfactuals']}; median first counter rank {values['ranking_median']:.1f}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Status certificate replay checks: {values['certificate_passed']}/{values['certificate_checks']} passed over {values['certificate_count']} certificates"),
        ("experiments/full_validation/results/full_validation_report.md", f"Annotation uncertainty: {values['uncertainty']} score perturbations; sample stability {values['uncertainty_stability']:.3f}; qualified high-status stability {values['uncertainty_qualified_high']:.3f}; boundary scenarios {values['uncertainty_boundary']}"),
        ("experiments/full_validation/results/full_validation_report.md", f"Metric separation evaluations: {values['metric']} upstream-metric scenario packets; high-recall blocked outputs {values['metric_high_recall_blocked']}/{values['metric_high_recall_total']}"),
    ]
    checks = []
    for path, expected in expectations:
        text = (ROOT / path).read_text(encoding="utf-8")
        checks.append({"path": path, "expected": expected, "passed": expected in text})
    checks.extend(_forbidden_checks())
    return checks


def _forbidden_checks() -> list[dict]:
    forbidden = [
        "62,497",
        "62,641",
        "64,996",
        "65,528",
        "2,236",
        "3,886",
        "174 rank-window",
        "46 high-status packets",
        "214 high-status packets",
        "11/11 rank-order",
        "11 rank-order visibility counterfactuals",
        "top-3 counter-material visibility was 31/41",
        "33 pages",
        "23 validation suites",
        "24 validation suites",
        "230 scenario files",
        "609 embedded records",
        "123,028",
        "127,632",
        "126,953",
        "57,500",
        "2,990",
        "1,150",
        "4,418",
        "820 rank-window",
        "70/70 rank-order",
        "225 returned records",
        "30 public retrieval outputs",
    ]
    paths = [
        "ARTIFACT.md",
        "README.md",
        "docs/paper_mapping.md",
        "skills/legal-ai-audit-harness/SKILL.md",
        "manuscript/ai_law_case_recommendation_verifiability.tex",
    ]
    checks = []
    for path in paths:
        text = (ROOT / path).read_text(encoding="utf-8")
        for item in forbidden:
            checks.append({"path": path, "expected": f"absence of stale claim `{item}`", "passed": item not in text})
    return checks


def _comma(value: int) -> str:
    return f"{value:,}"


def _pdf_page_count(path: Path) -> int:
    log = path.with_suffix(".log")
    if log.exists():
        match = re.search(r"Output written on .+ \((\d+) pages", log.read_text(encoding="utf-8", errors="ignore"))
        if match:
            return int(match.group(1))
    data = path.read_bytes()
    chunks = [data.decode("latin-1", errors="ignore")]
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            chunks.append(zlib.decompress(match.group(1).strip()).decode("latin-1", errors="ignore"))
        except zlib.error:
            pass
    text = "\n".join(chunks)
    return len(re.findall(r"/Type\s*/Page\b", text))


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
