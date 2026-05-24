from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments" / "ai_outputs" / "scenarios"
OUT = ROOT / "experiments" / "model_output_repairs" / "scenarios"
RESULTS = ROOT / "experiments" / "model_output_repairs" / "results"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    count = 0
    for path in sorted(SOURCE.glob("codex55_*.json")):
        scenario = json.loads(path.read_text(encoding="utf-8"))
        repaired = repair(scenario)
        (OUT / f"{repaired['id']}.json").write_text(json.dumps(repaired, indent=2, ensure_ascii=False), encoding="utf-8")
        count += 1
    print(f"Wrote {count} source-supported model-output repair scenarios")
    return 0


def repair(scenario: dict) -> dict:
    repaired = json.loads(json.dumps(scenario))
    repaired["id"] = "source-bound-" + scenario["id"].replace("_", "-")
    repaired["deployment_context"] = (
        scenario["deployment_context"]
        + " Source-supported repair variant: the same visible authorities are validated against hashed issue-manifest source-support evidence."
    )
    repaired["system_role"] = "auditable_procedural_tool"
    source_collection = source_collection_for(scenario["id"])
    repaired["evidence_packet"]["source_collection"] = source_collection
    validation = validate_source_binding(repaired, ROOT / source_collection)
    if validation["all_links_source_bound"]:
        for link in repaired["evidence_packet"].get("output_links", []):
            link["source_tag"] = "tool_verified"
            key = f"{link.get('unit_id')}::{link.get('source_id')}"
            link["support_label"] = "supports"
            evidence = validation["source_support_by_link"].get(key, [])
            link["validated_source_support"] = evidence
            link["validated_support_terms"] = sorted({term for item in evidence for term in item.get("matched_terms", [])})
        validation["source_tag_assignment"] = "assigned_after_manifest_locator_issue_set_and_source_support_validation"
        validation["assigned_procedural_source_tags"] = validation["output_links"]
    else:
        validation["source_tag_assignment"] = "not_assigned_validation_failed"
        validation["assigned_procedural_source_tags"] = 0
    repaired["source_binding_validation"] = validation
    repaired["scores"] = validated_scores(repaired, validation)
    repaired["review_gate"] = {
        "attorney_review_required": True,
        "review_status": "completed",
        "reliance_gate": "attorney_review",
        "jurisdiction_assumptions": scenario.get("review_gate", {}).get("jurisdiction_assumptions", []),
        "irreversible_action": False,
        "human_authorization": False,
    }
    if validation["all_links_source_bound"]:
        repaired["expected_allowed_status"] = "normative_material_screening_output"
        repaired["expected_disposition"] = "none"
    else:
        repaired["expected_allowed_status"] = "reference_information"
        repaired["expected_disposition"] = "downgrade"
    return repaired


def validate_source_binding(scenario: dict, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = {record["id"]: record for record in manifest.get("records", [])}
    units = {unit.get("id"): unit for unit in scenario.get("evidence_packet", {}).get("output_units", [])}
    links = scenario.get("evidence_packet", {}).get("output_links", [])
    missing_source_ids = sorted({link.get("source_id") for link in links if link.get("source_id") not in records})
    expected_pairs = {
        (unit.get("id"), source_id)
        for unit in units.values()
        for source_id in unit.get("source_ids", [])
    }
    actual_pairs = {(link.get("unit_id"), link.get("source_id")) for link in links}
    missing_output_links = [
        {"unit_id": unit_id, "source_id": source_id}
        for unit_id, source_id in sorted(expected_pairs - actual_pairs)
    ]
    unsupported_locators = []
    unsupported_claims = []
    unsupported_source_support = []
    source_support_by_link = {}
    for link in links:
        record = records.get(link.get("source_id"))
        if record and not locator_matches_record(str(link.get("locator", "")), record):
            unsupported_locators.append({"source_id": link.get("source_id"), "locator": link.get("locator")})
        if record:
            source_support, source_support_errors = matched_source_support(units.get(link.get("unit_id"), {}), link, record)
            if source_support:
                source_support_by_link[f"{link.get('unit_id')}::{link.get('source_id')}"] = source_support
            else:
                unsupported_claims.append(
                    {
                        "unit_id": link.get("unit_id"),
                        "source_id": link.get("source_id"),
                        "locator": link.get("locator"),
                    }
                )
                unsupported_source_support.extend(source_support_errors)
    authority_sets = scenario.get("authority_sets", {})
    high = set(authority_sets.get("high_authority", []))
    retrieved_high = set(authority_sets.get("retrieved_high_authority", []))
    counter = set(authority_sets.get("counter_or_limiting", []))
    retrieved_counter = set(authority_sets.get("retrieved_counter_or_limiting", []))
    high_complete = high.issubset(retrieved_high)
    counter_complete = counter.issubset(retrieved_counter)
    locator_bound = not missing_source_ids and not unsupported_locators and not missing_output_links
    claim_bound = not unsupported_claims
    return {
        "manifest": str(manifest_path.relative_to(ROOT)),
        "manifest_records": len(records),
        "output_links": len(links),
        "missing_source_ids": missing_source_ids,
        "missing_output_links": missing_output_links,
        "unsupported_locators": unsupported_locators,
        "unsupported_claims": unsupported_claims,
        "unsupported_source_support": unsupported_source_support,
        "source_support_by_link": source_support_by_link,
        "all_links_source_bound": locator_bound and claim_bound and high_complete and counter_complete,
        "high_authority_complete": high_complete,
        "counter_material_complete": counter_complete,
        "claim_support_complete": claim_bound,
        "source_support_complete": claim_bound,
    }


def validated_scores(scenario: dict, validation: dict) -> dict:
    source_bound = validation["all_links_source_bound"]
    high_complete = validation["high_authority_complete"]
    counter_complete = validation["counter_material_complete"]
    return {
        "S": {
            "score": 2 if source_bound else 1,
            "evidence": "Source-support validator checked each output link against the issue manifest, locator, hashed manifest source-support evidence and procedural source tag.",
        },
        "Q": {
            "score": 2,
            "evidence": "The prompt, model capture, repair layer and output identifier are recorded.",
        },
        "H": {
            "score": 2 if high_complete else 1,
            "evidence": "Authority coverage is recomputed against the issue-defined high-authority set.",
        },
        "K": {
            "score": 2 if counter_complete else 1,
            "evidence": "Counter/limiting material coverage is recomputed against the issue-defined counter-material set.",
        },
        "T": {
            "score": 2 if source_bound else 1,
            "evidence": "A reviewer can inspect, challenge and supplement every source-supported output unit only if all links validate.",
        },
        "L": {
            "score": 1,
            "evidence": "The repaired output is logged for audit, but no authorized decision-maker adopted it as a decision reason.",
        },
    }


def locator_matches_record(locator: str, record: dict) -> bool:
    locator_tokens = tokens(locator)
    record_text = " ".join(str(record.get(key, "")) for key in ("id", "title", "citation", "source_url"))
    record_tokens = tokens(record_text)
    title_words = [word for word in tokens(str(record.get("title", ""))) if word.isalpha()]
    if title_words:
        record_tokens.add("".join(word[0] for word in title_words))
    title = str(record.get("title", "")).lower()
    if "administrative procedure act" in title:
        record_tokens.add("apa")
    if not locator_tokens:
        return False
    return bool(locator_tokens & record_tokens)


def matched_source_support(unit: dict, link: dict, record: dict) -> tuple[list[dict], list[dict]]:
    claim = str(unit.get("claim", "")).lower()
    if not claim:
        return [], [{"reason": "missing_claim", "source_id": record.get("id")}]
    matches = []
    errors = []
    source_support_items = record.get("source_support", [])
    if not source_support_items:
        return [], [{"reason": "missing_source_support", "source_id": record.get("id")}]
    for item in source_support_items:
        excerpt = str(item.get("source_excerpt", ""))
        expected_hash = item.get("excerpt_sha256")
        if not excerpt or not expected_hash:
            errors.append({"reason": "missing_source_excerpt_or_hash", "support_id": item.get("id")})
            continue
        if hashlib.sha256(excerpt.encode("utf-8")).hexdigest() != expected_hash:
            errors.append({"reason": "source_excerpt_hash_mismatch", "support_id": item.get("id")})
            continue
        if not source_support_locator_matches_link(str(link.get("locator", "")), record, item):
            errors.append({"reason": "locator_mismatch", "support_id": item.get("id")})
            continue
        if claim_matches_contradiction(claim, item):
            errors.append({"reason": "contradiction_pattern_matched", "support_id": item.get("id")})
            continue
        matched_terms = [
            str(term).lower()
            for term in item.get("support_terms", [])
            if str(term).lower() in claim and str(term).lower() in excerpt.lower()
        ]
        if matched_terms:
            matches.append({"support_id": item.get("id"), "locator": item.get("locator"), "matched_terms": matched_terms})
        else:
            errors.append({"reason": "support_terms_not_shared_by_claim_and_excerpt", "support_id": item.get("id")})
    return matches, errors


def claim_matches_contradiction(claim: str, support: dict) -> bool:
    return any(str(pattern).lower() in claim for pattern in support.get("contradiction_patterns", []))


def source_support_locator_matches_link(locator: str, record: dict, support: dict) -> bool:
    support_text = " ".join(str(support.get(key, "")) for key in ("id", "locator", "source_url"))
    support_tokens = tokens(support_text) | tokens(str(record.get("citation", ""))) | tokens(str(record.get("title", "")))
    if "administrative procedure act" in str(record.get("title", "")).lower():
        support_tokens.add("apa")
    return bool(tokens(locator) & support_tokens)


def tokens(value: str) -> set[str]:
    return {token for token in value.lower().replace(".", " ").replace(",", " ").replace("(", " ").replace(")", " ").split() if len(token) > 1}


def source_collection_for(scenario_id: str) -> str:
    if "-us-" in scenario_id:
        return "experiments/issue_gold_sets/manifests/us_agency_deference_after_loper_bright.json"
    if "-uk-" in scenario_id:
        return "experiments/issue_gold_sets/manifests/uk_mesothelioma_causation_after_fairchild.json"
    return "experiments/issue_gold_sets/manifests/eu_gdpr_article15_access_rights.json"


if __name__ == "__main__":
    raise SystemExit(main())
