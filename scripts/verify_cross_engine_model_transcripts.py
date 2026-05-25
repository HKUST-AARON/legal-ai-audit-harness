from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "experiments" / "cross_engine_model_outputs" / "raw" / "cross_engine_authority_recommendations.md"
SCENARIOS = ROOT / "experiments" / "cross_engine_model_outputs" / "scenarios"
RESULTS = ROOT / "experiments" / "cross_engine_model_outputs" / "results"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    sections = _sections(RAW.read_text(encoding="utf-8"))
    rows = [_row(json.loads(path.read_text(encoding="utf-8")), sections) for path in sorted(SCENARIOS.glob("*.json"))]
    payload = {
        "scenario_count": len(rows),
        "engine_count": len({row["engine"] for row in rows}),
        "issue_count": len({row["issue"] for row in rows}),
        "scenario_sections_verified": sum(row["section_found"] and row["raw_file_anchor_matches"] for row in rows),
        "output_unit_count": sum(row["output_unit_count"] for row in rows),
        "locator_count": sum(row["locator_count"] for row in rows),
        "locators_verified": sum(row["locators_verified"] for row in rows),
        "all_locators_verified": all(row["locators_verified"] == row["locator_count"] for row in rows),
        "rows": rows,
    }
    (RESULTS / "cross_engine_transcript_verification.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (RESULTS / "cross_engine_transcript_verification.md").write_text(_format_report(payload) + "\n", encoding="utf-8")
    print(_format_report(payload))
    return 0 if payload["all_locators_verified"] else 1


def _sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+([\w.-]+--[\w-]+)\s*$", text, re.MULTILINE))
    sections = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.end() : end]
    return sections


def _row(scenario: dict, sections: dict[str, str]) -> dict:
    raw_anchor = scenario.get("upstream_output", {}).get("raw_file", "")
    section_id = raw_anchor.split("#")[-1]
    section = sections.get(section_id, "")
    normalized_section = _normalize(section)
    locator_rows = []
    for unit in scenario.get("evidence_packet", {}).get("output_units", []):
        for locator in unit.get("locators", []):
            locator_rows.append(
                {
                    "unit_id": unit["id"],
                    "locator": locator,
                    "verified": _normalize(locator) in normalized_section,
                }
            )
    engine, issue = section_id.split("--", 1) if "--" in section_id else ("unknown", "unknown")
    return {
        "scenario_id": scenario["id"],
        "engine": engine,
        "issue": issue,
        "raw_file_anchor": raw_anchor,
        "section_found": bool(section),
        "raw_file_anchor_matches": raw_anchor.endswith(f"#{section_id}"),
        "output_unit_count": len(scenario.get("evidence_packet", {}).get("output_units", [])),
        "locator_count": len(locator_rows),
        "locators_verified": sum(row["verified"] for row in locator_rows),
        "locator_rows": locator_rows,
    }


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _format_report(payload: dict) -> str:
    lines = [
        "# Cross-Engine Model Transcript Verification",
        "",
        f"Scenarios: {payload['scenario_count']}",
        f"Engines: {payload['engine_count']}",
        f"Issues: {payload['issue_count']}",
        f"Scenario sections verified: {payload['scenario_sections_verified']}/{payload['scenario_count']}",
        f"Locators verified: {payload['locators_verified']}/{payload['locator_count']}",
        "",
        "| Scenario | Engine | Issue | Section | Units | Locators | Verified |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['scenario_id']} | {row['engine']} | {row['issue']} | {_yes(row['section_found'])} | "
            f"{row['output_unit_count']} | {row['locator_count']} | {row['locators_verified']} |"
        )
    return "\n".join(lines)


def _yes(value: bool) -> str:
    return "yes" if value else "no"


if __name__ == "__main__":
    raise SystemExit(main())
