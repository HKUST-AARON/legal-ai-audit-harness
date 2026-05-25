import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from audit_harness.model import STATUS_RANK, evaluate_scenario


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "examples" / "scenarios"
sys.path.insert(0, str(ROOT / "scripts"))
from build_model_output_repairs import matched_source_support, repair


def load(name: str) -> dict:
    return json.loads((SCENARIOS / name).read_text(encoding="utf-8"))


class AuditModelTest(unittest.TestCase):
    def test_normative_screening_threshold(self):
        result = evaluate_scenario(load("court_authority_report.json"))
        self.assertEqual(result.allowed_status, "normative_material_screening_output")
        self.assertEqual(result.total_score, 10)
        self.assertTrue(result.claim_supported)
        self.assertAlmostEqual(result.counter_authority_recall, 0.5)

    def test_professional_support_does_not_upgrade_when_k_is_zero(self):
        result = evaluate_scenario(load("professional_research_support.json"))
        self.assertEqual(result.allowed_status, "professional_support_output")
        self.assertIn("K", result.missing_gates)
        self.assertTrue(result.claim_supported)

    def test_decision_support_requires_full_contestability_and_adoption_logging(self):
        result = evaluate_scenario(load("decision_support_ready.json"))
        self.assertEqual(result.allowed_status, "decision_support_reason")
        self.assertEqual(result.total_score, 12)
        self.assertAlmostEqual(result.counter_authority_recall, 1.0)

    def test_decision_support_requires_normative_gate_and_total_threshold(self):
        scenario = deepcopy(load("decision_support_ready.json"))
        for dimension in ("S", "Q", "H", "K"):
            scenario["scores"][dimension]["score"] = 1
        result = evaluate_scenario(scenario)
        self.assertEqual(result.total_score, 8)
        self.assertEqual(result.allowed_status, "professional_support_output")
        self.assertIn("total_score>=9", result.missing_gates)

    def test_decision_support_requires_authorized_adoption_gate(self):
        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["review_gate"]["reliance_gate"] = "attorney_review"
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")

        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["review_gate"]["human_authorization"] = False
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")

        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["review_gate"]["adoption_reasons_recorded"] = False
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")

        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["review_gate"]["contestation_recorded"] = False
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")

    def test_system_role_caps_highest_available_status(self):
        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["system_role"] = "auditable_procedural_tool"
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")
        self.assertIn("system_role:auditable_procedural_tool->max:normative_material_screening_output", result.missing_gates)

        scenario = deepcopy(load("court_authority_report.json"))
        scenario["system_role"] = "disclosed_assistance_tool"
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "professional_support_output")
        self.assertIn("system_role:disclosed_assistance_tool->max:professional_support_output", result.missing_gates)

    def test_withdrawal_blocks_external_effect(self):
        result = evaluate_scenario(load("unverifiable_legal_output.json"))
        self.assertEqual(result.allowed_status, "no_external_legal_effect")
        self.assertEqual(result.disposition, "withdrawal")
        self.assertFalse(result.claim_supported)

    def test_missing_source_tags_downgrade_external_status(self):
        scenario = deepcopy(load("grounded_output_summary.json"))
        for link in scenario["evidence_packet"]["output_links"]:
            link.pop("source_tag", None)
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "downgrade")
        self.assertAlmostEqual(result.source_tag_coverage, 0.0)

    def test_unverified_source_tags_downgrade_normative_status(self):
        scenario = deepcopy(load("grounded_output_summary.json"))
        for link in scenario["evidence_packet"]["output_links"]:
            link["source_tag"] = "needs_verification"
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "downgrade")
        self.assertAlmostEqual(result.source_tag_coverage, 1.0)
        self.assertAlmostEqual(result.procedural_source_tag_coverage, 0.0)

    def test_normative_status_requires_evidence_packet(self):
        scenario = deepcopy(load("court_authority_report.json"))
        scenario.pop("evidence_packet")
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "downgrade")
        self.assertIn("source_attribution_gap", result.failure_flags)

    def test_normative_status_requires_counter_material_set(self):
        scenario = deepcopy(load("court_authority_report.json"))
        scenario["authority_sets"].pop("counter_or_limiting")
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "suspension")
        self.assertIn("counter_material_suppression", result.failure_flags)

        scenario = deepcopy(load("court_authority_report.json"))
        scenario["authority_sets"]["counter_or_limiting"] = []
        scenario["authority_sets"]["retrieved_counter_or_limiting"] = []
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertIn("counter_material_suppression", result.failure_flags)

    def test_normative_status_requires_counter_material_rank_salience(self):
        scenario = deepcopy(load("court_authority_report.json"))
        units = scenario["evidence_packet"]["output_units"]
        counter_unit = units.pop(1)
        units.insert(
            0,
            {
                "id": "rank-padding-1",
                "claim": "A front-window high-authority proposition.",
                "source_ids": ["binding-precedent-a"],
                "locators": ["[2024] 1 AC 1"],
            },
        )
        units.insert(
            1,
            {
                "id": "rank-padding-2",
                "claim": "A second front-window high-authority proposition.",
                "source_ids": ["statute-b"],
                "locators": ["Statute B s. 12"],
            },
        )
        units.append(counter_unit)
        scenario["evidence_packet"]["output_links"].extend(
            [
                {
                    "unit_id": "rank-padding-1",
                    "source_id": "binding-precedent-a",
                    "locator": "[2024] 1 AC 1",
                    "supports_claim": True,
                    "source_tag": "official_source",
                },
                {
                    "unit_id": "rank-padding-2",
                    "source_id": "statute-b",
                    "locator": "Statute B s. 12",
                    "supports_claim": True,
                    "source_tag": "official_source",
                },
            ]
        )

        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "suspension")
        self.assertIn("ranking_drift", result.failure_flags)

        units.insert(2, units.pop())
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "normative_material_screening_output")
        self.assertNotIn("ranking_drift", result.failure_flags)

        ranked = deepcopy(scenario)
        ranked_units = ranked["evidence_packet"]["output_units"]
        ranked_units.insert(0, ranked_units.pop(2))
        for unit in ranked_units:
            if unit["id"] == counter_unit["id"]:
                unit["output_rank"] = 4
            elif unit["id"] == "rank-padding-1":
                unit["output_rank"] = 2
            elif unit["id"] == "rank-padding-2":
                unit["output_rank"] = 3
            else:
                unit["output_rank"] = 1
        result = evaluate_scenario(ranked)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertIn("ranking_drift", result.failure_flags)

    def test_normative_status_requires_high_authority_set(self):
        scenario = deepcopy(load("court_authority_report.json"))
        scenario["authority_sets"]["high_authority"] = []
        scenario["authority_sets"]["retrieved_high_authority"] = []
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "suspension")
        self.assertIn("authority_omission", result.failure_flags)

    def test_review_gate_blocks_unreviewed_external_reliance(self):
        scenario = deepcopy(load("decision_support_ready.json"))
        scenario["review_gate"]["review_status"] = "pending"
        scenario["review_gate"]["reliance_gate"] = "authorized_adoption"
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "downgrade")

    def test_unauthorized_irreversible_action_is_withdrawn(self):
        scenario = deepcopy(load("odr_authorized_review.json"))
        scenario["review_gate"]["irreversible_action"] = True
        scenario["review_gate"]["human_authorization"] = False
        result = evaluate_scenario(scenario)
        self.assertEqual(result.allowed_status, "no_external_legal_effect")
        self.assertEqual(result.disposition, "withdrawal")

    def test_suspension_downgrades_to_reference(self):
        result = evaluate_scenario(load("suspended_authority_omission.json"))
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "suspension")
        self.assertFalse(result.claim_supported)

    def test_cli_run_examples(self):
        completed = subprocess.run(
            [sys.executable, "-m", "audit_harness.cli", "run", str(SCENARIOS)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("court-authority-report", completed.stdout)
        self.assertIn("unverifiable-legal-output", completed.stdout)

    def test_experiment_reports_high_recall_blocked_cases(self):
        completed = subprocess.run(
            [sys.executable, "-m", "audit_harness.cli", "experiment", str(SCENARIOS)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("High-upstream-performance but procedurally blocked scenarios", completed.stdout)
        self.assertIn("civil-law-statutory-interpretation", completed.stdout)
        self.assertIn("high-coverage-uncontestable-output", completed.stdout)

    def test_metric_separation_analysis_runs(self):
        completed = subprocess.run(
            [sys.executable, "scripts/run_metric_separation_analysis.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Metric Separation Analysis", completed.stdout)
        payload = json.loads(
            (ROOT / "experiments" / "metric_separation" / "results" / "metric_separation_analysis.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["metric_scenario_count"], 201)
        self.assertEqual(payload["bootstrap"]["iterations"], 1000)
        self.assertEqual(payload["permutation"]["iterations"], 1000)
        recall_test = next(row for row in payload["threshold_tests"] if row["label"] == "recall>=0.8")
        self.assertLess(recall_test["precision"], 0.35)
        self.assertLess(payload["bootstrap"]["confidence_interval"]["recall_threshold_precision"]["high"], 0.35)
        self.assertGreater(payload["permutation"]["two_sided_p"], 0.05)
        self.assertEqual(payload["gate_cascade"][-1]["false_positive"], 0)

    def test_baseline_comparison_analysis_runs(self):
        completed = subprocess.run(
            [sys.executable, "scripts/run_baseline_comparison_analysis.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Baseline Rule Comparison", completed.stdout)
        payload = json.loads(
            (ROOT / "experiments" / "baseline_comparisons" / "results" / "baseline_comparison_analysis.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["scenario_count"], 246)
        self.assertEqual(payload["baseline_count"], 12)
        self.assertEqual(payload["baseline_prediction_count"], 2772)
        self.assertTrue(payload["all_simplified_rules_have_errors"])
        self.assertEqual(payload["full_gate"]["false_positive"], 0)
        self.assertEqual(payload["full_gate"]["false_negative"], 0)
        self.assertGreaterEqual(payload["best_simplified"]["false_positive"], 38)

    def test_gate_ablation_analysis_runs(self):
        completed = subprocess.run(
            [sys.executable, "scripts/run_gate_ablation_analysis.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Gate Ablation Analysis", completed.stdout)
        payload = json.loads(
            (ROOT / "experiments" / "gate_ablations" / "results" / "gate_ablation_analysis.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["qualified_scenario_count"], 54)
        self.assertEqual(payload["ablation_count"], 336)
        self.assertEqual(payload["passed_count"], 336)
        self.assertFalse(payload["failures"])

    def test_repair_frontier_analysis_runs(self):
        completed = subprocess.run(
            [sys.executable, "scripts/run_repair_frontier_analysis.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Repair Frontier Analysis", completed.stdout)
        payload = json.loads(
            (ROOT / "experiments" / "repair_frontiers" / "results" / "repair_frontier_analysis.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["blocked_claim_count"], 184)
        self.assertEqual(payload["counterfactual_evaluation_count"], 4474)
        self.assertEqual(payload["repairable_count"], payload["blocked_claim_count"])
        self.assertFalse(payload["unrepairable"])

    def test_jurisdiction_profile_analysis_runs(self):
        completed = subprocess.run(
            [sys.executable, "scripts/run_jurisdiction_profile_analysis.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Jurisdiction Profile Analysis", completed.stdout)
        payload = json.loads(
            (ROOT / "experiments" / "jurisdiction_profiles" / "results" / "jurisdiction_profile_analysis.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["profile_check_count"], 233)
        self.assertEqual(payload["profile_supported_count"], 233)
        self.assertEqual(payload["qualified_status_count"], 54)
        self.assertEqual(payload["counterfactual_evaluation_count"], 162)
        self.assertEqual(payload["passed_count"], 162)
        self.assertFalse(payload["failures"])

    def test_ranking_visibility_analysis_runs(self):
        completed = subprocess.run(
            [sys.executable, "scripts/run_ranking_visibility_analysis.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Ranking Visibility Analysis", completed.stdout)
        payload = json.loads(
            (ROOT / "experiments" / "ranking_visibility" / "results" / "ranking_visibility_analysis.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["eligible_packet_count"], 230)
        self.assertEqual(payload["visibility_check_count"], 230)
        self.assertEqual(payload["window_check_count"], 884)
        self.assertEqual(payload["window_sensitivity"][0]["counter_visible_count"], 14)
        self.assertEqual(payload["window_sensitivity"][1]["counter_visible_count"], 78)
        self.assertEqual(payload["window_sensitivity"][2]["counter_visible_count"], 183)
        self.assertEqual(payload["window_sensitivity"][3]["counter_visible_count"], 189)
        self.assertEqual(payload["first_counter_rank_distribution"], {"1": 14, "2": 64, "3": 110, "4": 9})
        self.assertEqual(payload["median_first_counter_rank"], 3.0)
        self.assertEqual(payload["rank_order_counterfactual_count"], 76)
        self.assertEqual(payload["rank_order_passed_count"], 76)
        self.assertEqual(payload["downgraded_count"], 76)
        self.assertEqual(payload["coverage_preserved_count"], 76)
        self.assertEqual(payload["front_window_packet_count"], 217)
        self.assertEqual(payload["front_window_counter_visible"], 183)
        self.assertEqual(payload["front_window_counter_not_visible"], 34)
        self.assertEqual(payload["counterfactual_front_window_counter_visible"], 0)
        self.assertEqual(payload["rank_intervention_applied_count"], 76)
        self.assertFalse(payload["failures"])

    def test_status_certificate_validation_runs(self):
        completed = subprocess.run(
            [sys.executable, "scripts/run_status_certificate_validation.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Status Certificate Replay Validation", completed.stdout)
        payload = json.loads(
            (ROOT / "experiments" / "status_certificates" / "results" / "status_certificate_validation.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["certificate_count"], 246)
        self.assertEqual(payload["verified_certificate_count"], 246)
        self.assertEqual(payload["replay_check_count"], 3198)
        self.assertEqual(payload["passed_check_count"], 3198)
        self.assertFalse(payload["failures"])

    def test_annotation_uncertainty_analysis_runs(self):
        completed = subprocess.run(
            [sys.executable, "scripts/run_annotation_uncertainty_analysis.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Annotation Uncertainty Analysis", completed.stdout)
        payload = json.loads(
            (ROOT / "experiments" / "annotation_uncertainty" / "results" / "annotation_uncertainty.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["scenario_count"], 246)
        self.assertEqual(payload["iterations_per_scenario"], 250)
        self.assertEqual(payload["evaluation_count"], 61500)
        self.assertGreater(payload["status_stability_rate"], 0.9)
        self.assertGreater(payload["qualified_high_status_stability_rate"], 0.9)

    def test_claim_consistency_verification_runs(self):
        completed = subprocess.run(
            [sys.executable, "scripts/verify_claim_consistency.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Claim Consistency Verification", completed.stdout)
        payload = json.loads(
            (ROOT / "experiments" / "claim_consistency" / "results" / "claim_consistency_verification.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["passed_count"], payload["check_count"])
        self.assertFalse(payload["failures"])

    def test_real_case_fixture_shape(self):
        real_scenarios = ROOT / "experiments" / "real_cases" / "scenarios"
        for path in sorted(real_scenarios.glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            units = scenario.get("evidence_packet", {}).get("output_units", [])
            self.assertEqual(len(units), 20, path.name)
            result = evaluate_scenario(scenario)
            self.assertEqual(result.allowed_status, "professional_support_output", path.name)

    def test_public_system_output_fixture_shape(self):
        scenarios = ROOT / "experiments" / "public_system_outputs" / "scenarios"
        paths = sorted(scenarios.glob("*.json"))
        self.assertEqual(len(paths), 6)
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            units = scenario.get("evidence_packet", {}).get("output_units", [])
            self.assertEqual(len(units), 10, path.name)
            result = evaluate_scenario(scenario)
            self.assertEqual(result.allowed_status, "professional_support_output", path.name)
            self.assertAlmostEqual(result.evidence_fidelity, 1.0, msg=path.name)
            self.assertAlmostEqual(result.source_tag_coverage, 1.0, msg=path.name)

    def test_schema_rejects_missing_scores(self):
        scenario = deepcopy(load("grounded_output_summary.json"))
        scenario["scores"].pop("K")
        with self.assertRaises(ValueError):
            evaluate_scenario(scenario)

    def test_issue_gold_set_qualifies_as_normative_screening(self):
        paths = sorted((ROOT / "experiments" / "issue_gold_sets" / "scenarios").glob("*.json"))
        self.assertGreaterEqual(len(paths), 3)
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertEqual(result.allowed_status, "normative_material_screening_output", path.name)
            self.assertAlmostEqual(result.authority_coverage, 1.0, msg=path.name)
            self.assertAlmostEqual(result.counter_authority_recall, 1.0, msg=path.name)
            self.assertAlmostEqual(result.evidence_fidelity, 1.0, msg=path.name)

    def test_issue_manifests_include_hashed_source_support(self):
        paths = sorted((ROOT / "experiments" / "issue_gold_sets" / "manifests").glob("*.json"))
        self.assertGreaterEqual(len(paths), 5)
        for path in paths:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            for record in manifest["records"]:
                support = record.get("source_support", [])
                self.assertTrue(support, f"{path.name}:{record['id']}")
                for item in support:
                    excerpt = item.get("source_excerpt", "")
                    self.assertTrue(excerpt, f"{path.name}:{record['id']}")
                    self.assertEqual(hashlib.sha256(excerpt.encode("utf-8")).hexdigest(), item.get("excerpt_sha256"))

    def test_issue_ablations_apply_failure_caps(self):
        subprocess.run(
            [sys.executable, "scripts/build_issue_ablations.py"],
            cwd=ROOT,
            check=True,
        )
        paths = sorted((ROOT / "experiments" / "issue_ablations" / "scenarios").glob("*.json"))
        self.assertEqual(len(paths), 20)
        blocked = 0
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertTrue(result.expected_passed, path.name)
            if path.stem.endswith(("missing-high-authority", "counter-material-suppressed", "unverified-source-tags")):
                blocked += 1
                self.assertEqual(result.allowed_status, "reference_information", path.name)
                if path.stem.endswith("counter-material-suppressed"):
                    scenario["failure_flags"] = []
                    self.assertEqual(evaluate_scenario(scenario).disposition, "suspension", path.name)
        self.assertEqual(blocked, 15)

    def test_codex_gpt55_xhigh_raw_outputs_are_source_capped(self):
        paths = sorted((ROOT / "experiments" / "ai_outputs" / "scenarios").glob("codex55_*.json"))
        self.assertEqual(len(paths), 10)
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertEqual(result.claimed_status, "normative_material_screening_output", path.name)
            self.assertEqual(result.allowed_status, "reference_information", path.name)
            expected_disposition = "suspension" if path.name == "codex55_eu_02.json" else "downgrade"
            self.assertEqual(result.disposition, expected_disposition, path.name)
            self.assertFalse(result.claim_supported, path.name)
            self.assertAlmostEqual(result.procedural_source_tag_coverage, 0.0, msg=path.name)
            self.assertGreaterEqual(scenario["upstream_metrics"]["recall"], 0.9, path.name)

    def test_source_bound_model_outputs_can_qualify(self):
        paths = sorted((ROOT / "experiments" / "model_output_repairs" / "scenarios").glob("source-bound-*.json"))
        self.assertEqual(len(paths), 10)
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertEqual(result.allowed_status, "normative_material_screening_output", path.name)
            self.assertEqual(result.disposition, "none", path.name)
            self.assertAlmostEqual(result.procedural_source_tag_coverage, 1.0, msg=path.name)
            validation = scenario.get("source_binding_validation", {})
            self.assertTrue(validation.get("all_links_source_bound"), path.name)
            self.assertTrue(validation.get("claim_support_complete"), path.name)
            self.assertTrue(validation.get("source_support_complete"), path.name)
            self.assertEqual(validation.get("missing_source_ids"), [], path.name)
            self.assertEqual(validation.get("missing_output_links"), [], path.name)
            self.assertEqual(validation.get("unsupported_locators"), [], path.name)
            self.assertEqual(validation.get("unsupported_claims"), [], path.name)
            self.assertTrue(validation.get("source_support_by_link"), path.name)
            self.assertEqual(
                validation.get("source_tag_assignment"),
                "assigned_after_manifest_locator_issue_set_and_source_support_validation",
                path.name,
            )
            self.assertEqual(validation.get("assigned_procedural_source_tags"), len(scenario["evidence_packet"]["output_links"]), path.name)
            for link in scenario["evidence_packet"]["output_links"]:
                self.assertEqual(link.get("support_label"), "supports", path.name)
                self.assertTrue(link.get("validated_source_support"), path.name)
                self.assertTrue(link.get("validated_support_terms"), path.name)

    def test_claim_support_validator_blocks_unmatched_claims(self):
        raw = json.loads((ROOT / "experiments" / "ai_outputs" / "scenarios" / "codex55_us_01.json").read_text(encoding="utf-8"))
        raw["evidence_packet"]["output_units"][0]["claim"] = "This unrelated proposition is not supported by the cited authority."
        repaired = repair(raw)
        validation = repaired["source_binding_validation"]
        self.assertFalse(validation["all_links_source_bound"])
        self.assertFalse(validation["claim_support_complete"])
        self.assertFalse(validation["source_support_complete"])
        self.assertTrue(validation["unsupported_claims"])
        result = evaluate_scenario(repaired)
        self.assertEqual(result.allowed_status, "no_external_legal_effect")
        self.assertEqual(result.disposition, "withdrawal")

    def test_source_support_validator_blocks_same_term_contradictions(self):
        raw = json.loads((ROOT / "experiments" / "ai_outputs" / "scenarios" / "codex55_eu_01.json").read_text(encoding="utf-8"))
        raw["evidence_packet"]["output_units"][1]["claim"] = "C-154/21 does not require specific recipients where recipients are identifiable."
        repaired = repair(raw)
        validation = repaired["source_binding_validation"]
        self.assertFalse(validation["all_links_source_bound"])
        self.assertFalse(validation["source_support_complete"])
        self.assertIn("contradiction_pattern_matched", {item["reason"] for item in validation["unsupported_source_support"]})
        result = evaluate_scenario(repaired)
        self.assertEqual(result.allowed_status, "no_external_legal_effect")
        self.assertEqual(result.disposition, "withdrawal")

    def test_source_support_evidence_item_is_required(self):
        unit = {"claim": "Loper Bright overruled Chevron for statutory interpretation."}
        link = {"locator": "Loper Bright"}
        record = {
            "id": "loper-bright-603-us-369",
            "title": "Loper Bright Enterprises v. Raimondo",
            "citation": "603 U.S. 369 (2024)",
            "support_terms": ["loper bright", "overruled chevron"],
        }
        matches, errors = matched_source_support(unit, link, record)
        self.assertEqual(matches, [])
        self.assertEqual(errors[0]["reason"], "missing_source_support")

    def test_source_support_validator_blocks_missing_output_links(self):
        raw = json.loads((ROOT / "experiments" / "ai_outputs" / "scenarios" / "codex55_us_01.json").read_text(encoding="utf-8"))
        raw["evidence_packet"]["output_links"] = raw["evidence_packet"]["output_links"][1:]
        repaired = repair(raw)
        validation = repaired["source_binding_validation"]
        self.assertFalse(validation["all_links_source_bound"])
        self.assertTrue(validation["missing_output_links"])
        result = evaluate_scenario(repaired)
        self.assertEqual(result.allowed_status, "reference_information")
        self.assertEqual(result.disposition, "downgrade")

    def test_model_output_adversarial_suite_rejects_all_attacks(self):
        subprocess.run(
            [sys.executable, "scripts/build_model_output_adversarial.py"],
            cwd=ROOT,
            check=True,
        )
        paths = sorted((ROOT / "experiments" / "model_output_adversarial" / "scenarios").glob("*.json"))
        self.assertEqual(len(paths), 60)
        attacks = {}
        statuses = {}
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            attack = scenario["adversarial_intervention"]["attack"]
            attacks[attack] = attacks.get(attack, 0) + 1
            validation = scenario.get("source_binding_validation", {})
            self.assertFalse(validation.get("all_links_source_bound"), path.name)
            result = evaluate_scenario(scenario)
            statuses[result.allowed_status] = statuses.get(result.allowed_status, 0) + 1
            self.assertTrue(result.expected_passed, path.name)
            self.assertIn(result.allowed_status, {"reference_information", "no_external_legal_effect"}, path.name)
        self.assertEqual(statuses, {"no_external_legal_effect": 20, "reference_information": 40})
        self.assertEqual(
            attacks,
            {
                "claim_support_gap": 10,
                "contradiction_pattern": 10,
                "counter_material_omission": 10,
                "locator_mismatch": 10,
                "manifest_membership_gap": 10,
                "unit_source_link_gap": 10,
            },
        )

    def test_model_output_evidence_ladder_statuses(self):
        subprocess.run(
            [sys.executable, "scripts/build_model_output_evidence_ladder.py"],
            cwd=ROOT,
            check=True,
        )
        paths = sorted((ROOT / "experiments" / "model_output_evidence_ladder" / "scenarios").glob("*.json"))
        self.assertEqual(len(paths), 70)
        statuses = {}
        dispositions = {}
        steps = {}
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertTrue(result.expected_passed, path.name)
            statuses[result.allowed_status] = statuses.get(result.allowed_status, 0) + 1
            dispositions[result.disposition] = dispositions.get(result.disposition, 0) + 1
            step = scenario["evidence_ladder_step"]["step"]
            steps[step] = steps.get(step, 0) + 1
        self.assertEqual(
            statuses,
            {
                "decision_support_reason": 10,
                "no_external_legal_effect": 10,
                "normative_material_screening_output": 10,
                "professional_support_output": 10,
                "reference_information": 30,
            },
        )
        self.assertEqual(dispositions, {"downgrade": 9, "none": 40, "suspension": 11, "withdrawal": 10})
        self.assertEqual(
            steps,
            {
                "authorized-decision-support": 10,
                "contestable-screening": 10,
                "raw-unverified": 10,
                "source-bound-no-contestability": 10,
                "source-bound-no-counter": 10,
                "source-bound-no-logging": 10,
                "unauthorized-external-action": 10,
            },
        )

    def test_issue_specific_public_outputs_shape(self):
        paths = sorted((ROOT / "experiments" / "issue_public_outputs" / "scenarios").glob("*.json"))
        self.assertEqual(len(paths), 3)
        statuses = {}
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            result = evaluate_scenario(scenario)
            self.assertTrue(result.expected_passed, path.name)
            statuses[result.allowed_status] = statuses.get(result.allowed_status, 0) + 1
        self.assertEqual(statuses["normative_material_screening_output"], 1)
        self.assertEqual(statuses["reference_information"], 2)

    def test_public_retrieval_benchmark_shape(self):
        paths = sorted((ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios").glob("*.json"))
        self.assertEqual(len(paths), 22)
        records = 0
        counter_recalls = []
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn(scenario.get("benchmark_scope"), {"case_law_only", "case_law_known_item"}, path.name)
            endpoint_gold = set(scenario["authority_sets"]["high_authority"]) | set(scenario["authority_sets"]["counter_or_limiting"])
            self.assertFalse(
                {item for item in endpoint_gold if item.startswith(("apa-", "gdpr-", "compensation-act", "charter-", "basic-law-"))},
                path.name,
            )
            self.assertTrue(scenario.get("mixed_authority_required_elsewhere"), path.name)
            records += len(scenario["evidence_packet"]["output_units"])
            result = evaluate_scenario(scenario)
            self.assertTrue(result.expected_passed, path.name)
            self.assertEqual(result.allowed_status, "reference_information", path.name)
            self.assertEqual(result.disposition, "suspension", path.name)
            if result.counter_authority_recall is not None:
                counter_recalls.append(result.counter_authority_recall)
            if path.name.startswith("canada-vavilov"):
                self.assertNotIn("dunsmuir-2008-scc-9", scenario["authority_sets"]["retrieved"], path.name)
            if path.name == "us-agency-deference-after-loper-bright-q02.json":
                by_locator = {
                    unit["locators"][0]: unit["source_ids"][0]
                    for unit in scenario["evidence_packet"]["output_units"]
                    if unit.get("locators") and unit.get("source_ids")
                }
                self.assertNotEqual(by_locator.get("45 F.4th 359"), "loper-bright-603-us-369")
                self.assertIn("us-search-loper-bright-enterprises-inc-v-wilbur-l-ross-jr", scenario["authority_sets"]["retrieved"])
        self.assertEqual(records, 169)
        self.assertTrue(counter_recalls)
        self.assertTrue(all(recall == 0 for recall in counter_recalls))

    def test_holdout_validation_shape(self):
        completed = subprocess.run(
            [sys.executable, "scripts/build_holdout_validation.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        paths = sorted((ROOT / "experiments" / "holdout_validation" / "scenarios").glob("*.json"))
        self.assertEqual(len(paths), 24)
        records = 0
        statuses = {}
        public_retrieval = raw_model = source_bound = 0
        for path in paths:
            scenario = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("expected_allowed_status", scenario, path.name)
            self.assertNotIn("expected_disposition", scenario, path.name)
            records += len(scenario["evidence_packet"]["output_units"])
            result = evaluate_scenario(scenario)
            statuses[result.allowed_status] = statuses.get(result.allowed_status, 0) + 1
            public_retrieval += int(path.name.startswith("holdout-public-retrieval-"))
            raw_model += int(path.name.startswith("holdout-raw-"))
            source_bound += int(path.name.startswith("holdout-source-bound-"))
        self.assertEqual(records, 126)
        self.assertEqual(public_retrieval, 8)
        self.assertEqual(raw_model, 8)
        self.assertEqual(source_bound, 8)
        self.assertEqual(statuses["reference_information"], 16)
        self.assertEqual(statuses["normative_material_screening_output"], 8)

    def test_full_validation_report_shape(self):
        report = json.loads((ROOT / "experiments" / "full_validation" / "results" / "full_validation_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["suite_count"], 27)
        self.assertEqual(report["scenario_files"], 246)
        self.assertEqual(report["validation_units"]["total"], 679)
        self.assertEqual(report["validation_units"]["public_retrieval_records"], 169)
        self.assertEqual(report["validation_units"]["holdout_records"], 126)
        self.assertEqual(report["validation_units"]["source_bound_model_outputs"], 10)
        self.assertEqual(report["validation_units"]["evidence_ladder_model_outputs"], 70)
        self.assertEqual(report["validation_units"]["adversarial_model_outputs"], 60)
        self.assertEqual(report["validation_units"]["issue_public_records"], 19)
        self.assertEqual(report["validation_units"]["issue_gold_sets"], 5)
        self.assertEqual(report["validation_units"]["issue_ablations"], 20)
        self.assertEqual(report["validation_units"]["annotation_recodings"], 492)
        self.assertEqual(report["annotation_uncertainty_evaluations"], 61500)
        self.assertEqual(report["validation_units"]["annotation_uncertainty_evaluations"], 61500)
        self.assertEqual(report["blind_coding_evaluations"], 444)
        self.assertEqual(report["validation_units"]["blind_coding_packets"], 222)
        self.assertEqual(report["threshold_sensitivity_evaluations"], 1230)
        self.assertEqual(report["validation_units"]["threshold_sensitivity_evaluations"], 1230)
        self.assertEqual(report["source_text_anchor_evaluations"], 30)
        self.assertEqual(report["model_output_transcript_evaluations"], 50)
        self.assertEqual(report["formal_invariant_evaluations"], 51643)
        self.assertEqual(report["validation_units"]["source_text_anchor_checks"], 30)
        self.assertEqual(report["validation_units"]["source_text_anchor_verified"], 30)
        self.assertEqual(report["validation_units"]["model_output_transcript_locator_checks"], 50)
        self.assertEqual(report["validation_units"]["model_output_transcript_locators_verified"], 50)
        self.assertEqual(report["validation_units"]["formal_invariant_checks"], 51643)
        self.assertEqual(report["validation_units"]["formal_invariant_passed"], 51643)
        self.assertEqual(report["metric_separation_evaluations"], 201)
        self.assertEqual(report["validation_units"]["metric_separation_evaluations"], 201)
        self.assertEqual(report["metric_statistical_resamples"], 2000)
        self.assertEqual(report["validation_units"]["metric_statistical_resamples"], 2000)
        self.assertEqual(report["baseline_comparison_evaluations"], 2772)
        self.assertEqual(report["validation_units"]["baseline_comparison_predictions"], 2772)
        self.assertEqual(report["gate_ablation_evaluations"], 336)
        self.assertEqual(report["validation_units"]["gate_ablation_evaluations"], 336)
        self.assertEqual(report["source_chain_attack_evaluations"], 270)
        self.assertEqual(report["validation_units"]["source_chain_attack_variants"], 270)
        self.assertEqual(report["validation_units"]["source_chain_attack_passed"], 270)
        self.assertEqual(report["contestation_challenge_evaluations"], 270)
        self.assertEqual(report["validation_units"]["contestation_challenge_variants"], 270)
        self.assertEqual(report["validation_units"]["contestation_challenge_passed"], 270)
        self.assertEqual(report["repair_frontier_evaluations"], 4474)
        self.assertEqual(report["validation_units"]["repair_frontier_evaluations"], 4474)
        self.assertEqual(report["jurisdiction_profile_evaluations"], 395)
        self.assertEqual(report["validation_units"]["jurisdiction_profile_evaluations"], 395)
        self.assertEqual(report["ranking_visibility_checks"], 230)
        self.assertEqual(report["validation_units"]["ranking_visibility_checks"], 230)
        self.assertEqual(report["ranking_visibility_window_checks"], 884)
        self.assertEqual(report["validation_units"]["ranking_visibility_window_checks"], 884)
        self.assertEqual(report["ranking_visibility_counterfactuals"], 76)
        self.assertEqual(report["validation_units"]["ranking_visibility_counterfactuals"], 76)
        self.assertEqual(report["status_certificate_replay_checks"], 3198)
        self.assertEqual(report["validation_units"]["status_certificate_replay_checks"], 3198)
        self.assertEqual(report["validation_units"]["status_certificates_verified"], 246)
        self.assertEqual(report["total_evaluation_rows"], 130944)
        self.assertEqual(report["expected_passed"], 246)
        self.assertEqual(report["expected_total"], 246)
        self.assertEqual(report["annotation_robustness"]["scenario_count"], 246)
        self.assertEqual(report["annotation_uncertainty"]["scenario_count"], 246)
        self.assertEqual(report["annotation_uncertainty"]["evaluation_count"], 61500)
        self.assertGreater(report["annotation_uncertainty"]["status_stability_rate"], 0.9)
        self.assertGreater(report["annotation_uncertainty"]["qualified_high_status_stability_rate"], 0.9)
        self.assertEqual(report["blind_coding"]["packet_count"], 222)
        self.assertIn("base_status_agreement", report["blind_coding"])
        self.assertEqual(report["threshold_sensitivity"]["scenario_count"], 246)
        self.assertEqual(report["threshold_sensitivity"]["runs"][0]["status_flips_from_default"], 0)
        self.assertEqual(report["blocked_reason_distribution"]["authority_omission"], 59)
        self.assertEqual(report["blocked_reason_distribution"]["contestation_failure"], 55)
        self.assertEqual(report["blocked_reason_distribution"]["counter_material_suppression"], 135)
        self.assertEqual(report["blocked_reason_distribution"]["jurisdiction_assumption_gap"], 54)
        self.assertEqual(report["blocked_reason_distribution"]["source_attribution_gap"], 213)
        self.assertEqual(report["blocked_reason_distribution"]["summary_distortion"], 129)
        self.assertEqual(report["source_text_verification"]["support_items_verified"], 30)
        self.assertEqual(report["source_text_verification"]["records_with_text_snapshot"], 30)
        self.assertEqual(report["model_output_transcript_verification"]["locators_verified"], 50)
        self.assertTrue(report["model_output_transcript_verification"]["all_locators_verified"])
        self.assertEqual(report["formal_invariant_verification"]["passed_checks"], 51643)
        self.assertTrue(report["formal_invariant_verification"]["all_passed"])
        self.assertEqual(report["metric_separation"]["metric_scenario_count"], 201)
        self.assertEqual(report["metric_separation"]["bootstrap"]["iterations"], 1000)
        self.assertEqual(report["metric_separation"]["permutation"]["iterations"], 1000)
        self.assertEqual(report["metric_separation"]["high_recall_blocked"]["count"], 144)
        self.assertEqual(report["baseline_comparison"]["baseline_count"], 12)
        self.assertEqual(report["baseline_comparison"]["baseline_prediction_count"], 2772)
        self.assertEqual(report["baseline_comparison"]["best_simplified"]["false_positive"], 38)
        self.assertEqual(report["baseline_comparison"]["full_gate"]["false_positive"], 0)
        self.assertTrue(report["baseline_comparison"]["all_simplified_rules_have_errors"])
        self.assertEqual(report["gate_ablation"]["ablation_count"], 336)
        self.assertEqual(report["gate_ablation"]["passed_count"], 336)
        self.assertEqual(report["source_chain_attacks"]["scenario_count"], 270)
        self.assertEqual(report["source_chain_attacks"]["expected_passed"], 270)
        self.assertEqual(report["source_chain_attacks"]["high_upstream_but_blocked"], 270)
        self.assertEqual(report["source_chain_attacks"]["status_distribution"]["reference_information"], 162)
        self.assertEqual(report["source_chain_attacks"]["status_distribution"]["no_external_legal_effect"], 108)
        self.assertEqual(report["contestation_challenges"]["scenario_count"], 270)
        self.assertEqual(report["contestation_challenges"]["expected_passed"], 270)
        self.assertEqual(report["contestation_challenges"]["high_upstream_but_blocked"], 216)
        self.assertEqual(report["contestation_challenges"]["valid_challenges_blocked"], 216)
        self.assertEqual(report["contestation_challenges"]["unsupported_controls_preserved"], 54)
        self.assertEqual(report["contestation_challenges"]["status_distribution"]["reference_information"], 216)
        self.assertEqual(report["contestation_challenges"]["status_distribution"]["normative_material_screening_output"], 42)
        self.assertEqual(report["contestation_challenges"]["status_distribution"]["decision_support_reason"], 12)
        self.assertEqual(report["repair_frontier"]["blocked_claim_count"], 184)
        self.assertEqual(report["repair_frontier"]["repairable_count"], 184)
        self.assertEqual(report["jurisdiction_profile"]["profile_check_count"], 233)
        self.assertEqual(report["jurisdiction_profile"]["profile_supported_count"], 233)
        self.assertEqual(report["jurisdiction_profile"]["passed_count"], 162)
        self.assertEqual(report["ranking_visibility"]["eligible_packet_count"], 230)
        self.assertEqual(report["ranking_visibility"]["visibility_check_count"], 230)
        self.assertEqual(report["ranking_visibility"]["window_check_count"], 884)
        self.assertEqual(report["ranking_visibility"]["rank_order_counterfactual_count"], 76)
        self.assertEqual(report["ranking_visibility"]["rank_order_passed_count"], 76)
        self.assertEqual(report["ranking_visibility"]["downgraded_count"], 76)
        self.assertEqual(report["ranking_visibility"]["coverage_preserved_count"], 76)
        self.assertEqual(report["ranking_visibility"]["front_window_packet_count"], 217)
        self.assertEqual(report["ranking_visibility"]["front_window_counter_visible"], 183)
        self.assertEqual(report["ranking_visibility"]["front_window_counter_not_visible"], 34)
        self.assertEqual(report["ranking_visibility"]["counterfactual_front_window_counter_visible"], 0)
        self.assertEqual(report["ranking_visibility"]["rank_intervention_applied_count"], 76)
        self.assertEqual(report["ranking_visibility"]["median_first_counter_rank"], 3.0)
        self.assertEqual(report["status_certificate"]["certificate_count"], 246)
        self.assertEqual(report["status_certificate"]["verified_certificate_count"], 246)
        self.assertEqual(report["status_certificate"]["replay_check_count"], 3198)
        self.assertEqual(report["status_certificate"]["passed_check_count"], 3198)

    def test_source_chain_attacks_run(self):
        completed = subprocess.run(
            [sys.executable, "scripts/build_source_chain_attacks.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "audit_harness.cli",
                "experiment",
                "experiments/source_chain_attacks/scenarios",
                "--out",
                "experiments/source_chain_attacks/results/source_chain_attack_experiment.md",
                "--json-out",
                "experiments/source_chain_attacks/results/source_chain_attack_experiment.json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = json.loads((ROOT / "experiments" / "source_chain_attacks" / "results" / "source_chain_attack_experiment.json").read_text(encoding="utf-8"))
        self.assertEqual(report["summary"]["scenario_count"], 270)
        self.assertEqual(report["summary"]["expected_passed"], 270)
        self.assertEqual(report["summary"]["high_upstream_but_blocked"], 270)
        statuses = {item["allowed_status"] for item in report["results"]}
        self.assertEqual(statuses, {"reference_information", "no_external_legal_effect"})

    def test_contestation_challenges_run(self):
        completed = subprocess.run(
            [sys.executable, "scripts/build_contestation_challenges.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "audit_harness.cli",
                "experiment",
                "experiments/contestation_challenges/scenarios",
                "--out",
                "experiments/contestation_challenges/results/contestation_challenge_experiment.md",
                "--json-out",
                "experiments/contestation_challenges/results/contestation_challenge_experiment.json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = json.loads((ROOT / "experiments" / "contestation_challenges" / "results" / "contestation_challenge_experiment.json").read_text(encoding="utf-8"))
        self.assertEqual(report["summary"]["scenario_count"], 270)
        self.assertEqual(report["summary"]["expected_passed"], 270)
        self.assertEqual(report["summary"]["high_upstream_but_blocked"], 216)
        unsupported = [item for item in report["results"] if "unsupported-challenge-control" in item["scenario_id"]]
        valid = [item for item in report["results"] if "unsupported-challenge-control" not in item["scenario_id"]]
        self.assertEqual(len(unsupported), 54)
        self.assertEqual(len(valid), 216)
        self.assertTrue(all(STATUS_RANK[item["allowed_status"]] >= STATUS_RANK["normative_material_screening_output"] for item in unsupported))
        self.assertTrue(all(item["allowed_status"] == "reference_information" for item in valid))

    def test_public_source_text_anchor_verification(self):
        completed = subprocess.run(
            [sys.executable, "scripts/verify_source_text_anchors.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = json.loads((ROOT / "experiments" / "source_text_verification" / "results" / "source_text_anchor_verification.json").read_text(encoding="utf-8"))
        self.assertEqual(report["support_item_count"], 30)
        self.assertEqual(report["support_items_verified"], 30)
        self.assertEqual(report["records_with_text_snapshot"], 30)
        verified = [item for item in report["items"] if item["verified"]]
        self.assertTrue(all(item["snapshot_sha256"] for item in verified))

    def test_model_output_transcript_verification(self):
        completed = subprocess.run(
            [sys.executable, "scripts/verify_model_output_transcripts.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = json.loads((ROOT / "experiments" / "ai_outputs" / "results" / "model_output_transcript_verification.json").read_text(encoding="utf-8"))
        self.assertEqual(report["scenario_count"], 10)
        self.assertEqual(report["scenario_sections_verified"], 10)
        self.assertEqual(report["output_unit_count"], 40)
        self.assertEqual(report["locator_count"], 50)
        self.assertEqual(report["locators_verified"], 50)
        self.assertTrue(report["all_locators_verified"])

    def test_formal_invariant_verification(self):
        completed = subprocess.run(
            [sys.executable, "scripts/verify_formal_invariants.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = json.loads((ROOT / "experiments" / "formal_invariants" / "results" / "formal_invariant_verification.json").read_text(encoding="utf-8"))
        self.assertEqual(report["check_count"], 9)
        self.assertEqual(report["total_checks"], 51643)
        self.assertEqual(report["passed_checks"], 51643)
        self.assertTrue(report["all_passed"])
        self.assertEqual({check["id"] for check in report["checks"]}, {
            "gated_monotonicity",
            "gate_non_substitutability",
            "evidence_packet_necessity",
            "authority_gate_necessity",
            "counter_material_gate_necessity",
            "decision_adoption_necessity",
            "role_cap_dominance",
            "failure_cap_absorption",
            "metric_non_equivalence",
        })

    def test_annotation_robustness_report_shape(self):
        completed = subprocess.run(
            [sys.executable, "scripts/run_annotation_robustness.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = json.loads((ROOT / "experiments" / "annotation_robustness" / "results" / "annotation_robustness.json").read_text(encoding="utf-8"))
        self.assertEqual(report["scenario_count"], 246)
        self.assertEqual(report["recoded_evaluations"], 492)
        self.assertGreaterEqual(report["weighted_status_agreement_base_strict"], 0.9)
        self.assertGreaterEqual(report["all_policy_status_stable"], 210)

    def test_blind_coding_study_report_shape(self):
        subprocess.run(
            [sys.executable, "scripts/build_model_output_adversarial.py"],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [sys.executable, "scripts/build_model_output_evidence_ladder.py"],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [sys.executable, "scripts/build_blind_coding_packets.py"],
            cwd=ROOT,
            check=True,
        )
        completed = subprocess.run(
            [sys.executable, "scripts/run_blind_coding_study.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = json.loads((ROOT / "experiments" / "blind_coding" / "results" / "blind_coding_study.json").read_text(encoding="utf-8"))
        self.assertEqual(report["packet_count"], 222)
        self.assertEqual(report["coder_count"], 2)
        self.assertGreaterEqual(report["pairwise_status"][0]["exact_status_agreement"], 0.9)
        self.assertGreaterEqual(report["pairwise_status"][0]["cohen_kappa"], 0.9)
        self.assertGreaterEqual(report["pairwise_status"][0]["quadratic_weighted_kappa"], 0.9)
        base_agreements = report["base_status_agreement"].values()
        self.assertGreaterEqual(min(item["exact_status_agreement"] for item in base_agreements), 0.8)
        self.assertGreaterEqual(min(item["weighted_status_agreement"] for item in base_agreements), 0.9)
        self.assertGreaterEqual(min(item["cohen_kappa"] for item in base_agreements), 0.85)
        self.assertGreaterEqual(min(item["quadratic_weighted_kappa"] for item in base_agreements), 0.85)

    def test_cli_sensitivity_report(self):
        completed = subprocess.run(
            [sys.executable, "-m", "audit_harness.cli", "sensitivity", str(SCENARIOS)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("Normative threshold", completed.stdout)
        self.assertIn("Decision threshold", completed.stdout)

    def test_real_case_collector_supports_external_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(ROOT / "experiments" / "real_cases" / "downloads", Path(directory) / "downloads")
            completed = subprocess.run(
                [sys.executable, "scripts/collect_real_cases.py", "--out", directory],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

    def test_public_system_output_collector_supports_external_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(ROOT / "experiments" / "public_system_outputs" / "downloads", Path(directory) / "downloads")
            completed = subprocess.run(
                [sys.executable, "scripts/collect_public_system_outputs.py", "--out", directory],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

    def test_issue_public_output_collector_supports_external_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(ROOT / "experiments" / "issue_public_outputs" / "downloads", Path(directory) / "downloads")
            completed = subprocess.run(
                [sys.executable, "scripts/collect_issue_public_outputs.py", "--out", directory],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

    def test_public_retrieval_benchmark_collector_supports_external_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(ROOT / "experiments" / "public_retrieval_benchmark" / "downloads", Path(directory) / "downloads")
            completed = subprocess.run(
                [sys.executable, "scripts/collect_public_retrieval_benchmark.py", "--out", directory],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)


if __name__ == "__main__":
    unittest.main()
