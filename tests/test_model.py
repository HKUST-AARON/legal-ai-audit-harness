import json
import subprocess
import sys
import unittest
from pathlib import Path

from audit_harness.model import evaluate_scenario


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "examples" / "scenarios"


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

    def test_withdrawal_blocks_external_effect(self):
        result = evaluate_scenario(load("unverifiable_rag_output.json"))
        self.assertEqual(result.allowed_status, "no_external_legal_effect")
        self.assertEqual(result.disposition, "withdrawal")
        self.assertFalse(result.claim_supported)

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
        self.assertIn("unverifiable-rag-output", completed.stdout)


if __name__ == "__main__":
    unittest.main()
