from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_harness.model import SYSTEM_ROLE_CAPS, Status
from run_status_certificate_validation import CERTIFICATES, _certificate_hash, _load_certificates, _replay, _validate_certificates


RESULTS = ROOT / "experiments" / "certificate_tamper" / "results"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    base = _load_certificates()
    rows = []
    for index in range(len(base)):
        for family, tamper in _field_tampers().items():
            certificate = copy.deepcopy(base[index])
            tamper(certificate)
            rows.append(_run_field_case(family, certificate))
    for family, certificates in _set_tampers(base).items():
        rows.append(_run_case(family, certificates, "__certificate_set__"))
    rejected = sum(1 for row in rows if row["rejected"])
    payload = {
        "base_certificate_count": len(base),
        "certificates_path": str(CERTIFICATES.relative_to(ROOT)),
        "tamper_family_count": len(_field_tampers()) + len(_set_tampers(base)),
        "tamper_case_count": len(rows),
        "rejected_count": rejected,
        "missed_tamper_count": len(rows) - rejected,
        "by_family": _by_family(rows),
        "rows": rows,
    }
    report = _format_report(payload)
    (RESULTS / "certificate_tamper_analysis.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "certificate_tamper_analysis.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if payload["missed_tamper_count"] == 0 else 1


def _field_tampers():
    return {
        "scenario_id_tamper": lambda item: item.update({"scenario_id": f"{item['scenario_id']}-tampered"}),
        "scenario_hash_tamper": lambda item: item.update({"scenario_sha256": "0" * 64}),
        "policy_hash_tamper": lambda item: item.update({"policy_sha256": "1" * 64}),
        "policy_body_tamper": _tamper_policy_body,
        "claimed_status_tamper": lambda item: item.update({"claimed_status": _different_status(item["claimed_status"])}),
        "jurisdiction_profile_tamper": lambda item: item.update({"jurisdiction_profile": "tampered_profile"}),
        "score_vector_tamper": _tamper_score,
        "total_score_tamper": lambda item: item.update({"total_score": item["total_score"] + 1}),
        "score_candidate_tamper": lambda item: item.update({"score_candidate": _different_status(item["score_candidate"])}),
        "system_role_tamper": lambda item: item.update({"system_role": _different_role(item["system_role"])}),
        "role_cap_tamper": lambda item: item.update({"role_cap": _different_status(item["role_cap"])}),
        "missing_gates_tamper": _tamper_missing_gates,
        "failure_flags_tamper": _tamper_failure_flags,
        "failure_cap_tamper": _tamper_failure_cap,
        "disposition_tamper": _tamper_disposition,
        "allowed_status_tamper": lambda item: item.update({"allowed_status": _different_status(item["allowed_status"])}),
        "claim_supported_tamper": lambda item: item.update({"claim_supported": not item["claim_supported"]}),
        "expected_passed_tamper": lambda item: item.update({"expected_passed": not item["expected_passed"]}),
        "metric_bundle_tamper": _tamper_metric_bundle,
        "proof_obligation_tamper": _tamper_proof_obligation,
        "proof_obligation_count_tamper": lambda item: item.update(
            {"proof_obligation_count": item["proof_obligation_count"] + 1}
        ),
        "derivation_hash_tamper": lambda item: item.update({"derivation_sha256": "2" * 64}),
    }


def _set_tampers(base: list[dict]) -> dict[str, list[dict]]:
    missing = copy.deepcopy(base[:-1])
    duplicate = copy.deepcopy(base)
    duplicate.append(copy.deepcopy(base[0]))
    extra = copy.deepcopy(base)
    extra_item = copy.deepcopy(base[0])
    extra_item["path"] = "experiments/status_certificates/scenarios/nonexistent.json"
    extra_item["scenario_id"] = "nonexistent-certificate"
    extra_item["derivation_sha256"] = _certificate_hash(extra_item)
    extra.append(extra_item)
    return {
        "missing_certificate_row": missing,
        "duplicate_certificate_row": duplicate,
        "extra_certificate_path": extra,
    }


def _tamper_score(item: dict) -> None:
    item["score_vector"]["S"] = 0 if item["score_vector"]["S"] else 2


def _different_status(status: str) -> str:
    statuses = [
        Status.NO_EXTERNAL_LEGAL_EFFECT.value,
        Status.REFERENCE_INFORMATION.value,
        Status.PROFESSIONAL_SUPPORT_OUTPUT.value,
        Status.NORMATIVE_MATERIAL_SCREENING_OUTPUT.value,
        Status.DECISION_SUPPORT_REASON.value,
    ]
    for candidate in statuses:
        if candidate != status:
            return candidate
    raise ValueError(f"Unknown status: {status}")


def _different_role(role: str) -> str:
    for candidate in SYSTEM_ROLE_CAPS:
        if candidate != role:
            return candidate
    raise ValueError(f"Unknown role: {role}")


def _tamper_policy_body(item: dict) -> None:
    item["policy"]["normative_threshold"] += 1


def _tamper_missing_gates(item: dict) -> None:
    if item["missing_gates"]:
        item["missing_gates"] = item["missing_gates"][1:]
    else:
        item["missing_gates"] = ["tampered_gate"]


def _tamper_failure_flags(item: dict) -> None:
    if item["failure_flags"]:
        item["failure_flags"] = item["failure_flags"][1:]
    else:
        item["failure_flags"] = ["source_attribution_gap"]


def _tamper_failure_cap(item: dict) -> None:
    if item["failure_cap"] is None:
        item["failure_cap"] = Status.NO_EXTERNAL_LEGAL_EFFECT.value
    else:
        item["failure_cap"] = _different_status(item["failure_cap"])


def _tamper_disposition(item: dict) -> None:
    dispositions = ["none", "downgrade", "suspension", "withdrawal"]
    for candidate in dispositions:
        if candidate != item["disposition"]:
            item["disposition"] = candidate
            return


def _tamper_metric_bundle(item: dict) -> None:
    for key, value in item["metric_bundle"].items():
        if value is not None:
            item["metric_bundle"][key] = 0 if value else 1
            return
    first_key = next(iter(item["metric_bundle"]))
    item["metric_bundle"][first_key] = 0


def _tamper_proof_obligation(item: dict) -> None:
    item["proof_obligations"][0]["passed"] = False


def _run_field_case(family: str, certificate: dict) -> dict:
    replay = _replay(certificate)
    failed_proof_obligation_count = sum(1 for item in certificate["proof_obligations"] if not item["passed"])
    return {
        "family": family,
        "scenario_id": certificate["scenario_id"],
        "rejected": not replay["passed"] or failed_proof_obligation_count > 0,
        "failed_check_count": replay["failed_check_count"],
        "failed_proof_obligation_count": failed_proof_obligation_count,
        "failed_checks": replay["failed_checks"],
        "missing_certificate_paths": [],
        "extra_certificate_paths": [],
        "duplicate_certificate_paths": [],
    }


def _run_case(family: str, certificates: list[dict], scenario_id: str) -> dict:
    payload = _validate_certificates(certificates)
    rejected = bool(payload["failures"]) or payload["failed_proof_obligation_count"] > 0
    failed_checks: list[str] = []
    for failure in payload["failures"]:
        failed_checks.extend(failure["failed_checks"])
    return {
        "family": family,
        "scenario_id": scenario_id,
        "rejected": rejected,
        "failed_check_count": payload["failed_check_count"],
        "failed_proof_obligation_count": payload["failed_proof_obligation_count"],
        "failed_checks": sorted(set(failed_checks)),
        "missing_certificate_paths": payload.get("missing_certificate_paths", []),
        "extra_certificate_paths": payload.get("extra_certificate_paths", []),
        "duplicate_certificate_paths": payload.get("duplicate_certificate_paths", []),
    }


def _by_family(rows: list[dict]) -> dict[str, dict]:
    families: dict[str, dict] = {}
    for row in rows:
        bucket = families.setdefault(row["family"], {"cases": 0, "rejected": 0, "missed": 0})
        bucket["cases"] += 1
        if row["rejected"]:
            bucket["rejected"] += 1
        else:
            bucket["missed"] += 1
    return dict(sorted(families.items()))


def _format_report(payload: dict) -> str:
    lines = [
        "# Certificate Tamper-Resistance Analysis",
        "",
        f"Base certificates: {payload['base_certificate_count']}",
        f"Certificate file: `{payload['certificates_path']}`",
        f"Tamper families: {payload['tamper_family_count']}",
        f"Tamper cases: {payload['rejected_count']}/{payload['tamper_case_count']} rejected",
        f"Missed tamper cases: {payload['missed_tamper_count']}",
        "",
        "| Tamper family | Cases | Rejected | Missed |",
        "| --- | ---: | ---: | ---: |",
    ]
    for family, row in payload["by_family"].items():
        lines.append(f"| {family} | {row['cases']} | {row['rejected']} | {row['missed']} |")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
