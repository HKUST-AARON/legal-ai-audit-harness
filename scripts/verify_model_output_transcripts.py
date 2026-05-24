from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "experiments" / "ai_outputs" / "raw" / "codex_gpt55_xhigh_first10.md"
SCENARIOS = ROOT / "experiments" / "ai_outputs" / "scenarios"
RESULTS = ROOT / "experiments" / "ai_outputs" / "results"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    sections = _sections(RAW.read_text(encoding="utf-8"))
    rows = [_row(json.loads(path.read_text(encoding="utf-8")), sections) for path in sorted(SCENARIOS.glob("codex55_*.json"))]
    payload = {
        "scenario_count": len(rows),
        "scenario_sections_verified": sum(row["section_found"] and row["raw_file_anchor_matches"] for row in rows),
        "output_unit_count": sum(row["output_unit_count"] for row in rows),
        "locator_count": sum(row["locator_count"] for row in rows),
        "locators_verified": sum(row["locators_verified"] for row in rows),
        "all_locators_verified": all(row["locators_verified"] == row["locator_count"] for row in rows),
        "rows": rows,
    }
    (RESULTS / "model_output_transcript_verification.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (RESULTS / "model_output_transcript_verification.md").write_text(_format_report(payload) + "\n", encoding="utf-8")
    print(_format_report(payload))
    return 0


def _sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(codex55-[\w-]+)\s*$", text, re.MULTILINE))
    sections = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.end() : end]
    return sections


def _row(scenario: dict, sections: dict[str, str]) -> dict:
    scenario_id = scenario["id"]
    section = sections.get(scenario_id, "")
    normalized_section = _normalize(section)
    raw_anchor = scenario.get("upstream_output", {}).get("raw_file", "")
    locator_rows = []
    for unit in scenario.get("evidence_packet", {}).get("output_units", []):
        for locator in unit.get("locators", []):
            verified = _normalize(locator) in normalized_section
            locator_rows.append({"unit_id": unit["id"], "locator": locator, "verified": verified})
    return {
        "scenario_id": scenario_id,
        "raw_file_anchor": raw_anchor,
        "section_found": bool(section),
        "raw_file_anchor_matches": raw_anchor.endswith(f"#{scenario_id}"),
        "output_unit_count": len(scenario.get("evidence_packet", {}).get("output_units", [])),
        "locator_count": len(locator_rows),
        "locators_verified": sum(row["verified"] for row in locator_rows),
        "locator_rows": locator_rows,
    }


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _format_report(payload: dict) -> str:
    lines = [
        "# Model Output Transcript Verification",
        "",
        f"Scenarios: {payload['scenario_count']}",
        f"Scenario sections verified: {payload['scenario_sections_verified']}/{payload['scenario_count']}",
        f"Output units: {payload['output_unit_count']}",
        f"Locators verified: {payload['locators_verified']}/{payload['locator_count']}",
        "",
        "| Scenario | Section | Anchor | Units | Locators | Verified |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['scenario_id']} | {_yes(row['section_found'])} | {_yes(row['raw_file_anchor_matches'])} | "
            f"{row['output_unit_count']} | {row['locator_count']} | {row['locators_verified']} |"
        )
    return "\n".join(lines)


def _yes(value: bool) -> str:
    return "yes" if value else "no"


if __name__ == "__main__":
    raise SystemExit(main())
