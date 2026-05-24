from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "experiments" / "blind_coding" / "packets"
SOURCES = [
    ROOT / "examples" / "scenarios",
    ROOT / "experiments" / "real_cases" / "scenarios",
    ROOT / "experiments" / "public_system_outputs" / "scenarios",
    ROOT / "experiments" / "ai_outputs" / "scenarios",
    ROOT / "experiments" / "issue_gold_sets" / "scenarios",
    ROOT / "experiments" / "issue_ablations" / "scenarios",
]


def main() -> int:
    PACKETS.mkdir(parents=True, exist_ok=True)
    for old in PACKETS.glob("*.json"):
        old.unlink()
    manifest = []
    for source in SOURCES:
        for path in sorted(source.glob("*.json")):
            scenario = json.loads(path.read_text(encoding="utf-8"))
            packet = _packet(scenario, path)
            packet_path = PACKETS / f"{scenario['id']}.json"
            packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
            manifest.append(
                {
                    "packet_id": scenario["id"],
                    "packet_path": str(packet_path.relative_to(ROOT)),
                    "source_path": str(path.relative_to(ROOT)),
                    "claimed_status": scenario["claimed_status"],
                }
            )
    (PACKETS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {len(manifest)} score-blinded packets to {PACKETS.relative_to(ROOT)}")
    return 0


def _packet(scenario: dict, path: Path) -> dict:
    keep = {
        "packet_id": scenario["id"],
        "source_path": str(path.relative_to(ROOT)),
        "claimed_status": scenario["claimed_status"],
        "jurisdiction_profile": scenario.get("jurisdiction_profile"),
        "deployment_context": scenario.get("deployment_context"),
        "authority_sets": scenario.get("authority_sets", {}),
        "upstream_metrics": scenario.get("upstream_metrics", {}),
        "upstream_output": scenario.get("upstream_output", {}),
        "evidence_packet": scenario.get("evidence_packet", {}),
        "review_gate": scenario.get("review_gate", {}),
        "counter_material_complete": scenario.get("counter_material_complete"),
    }
    return {key: value for key, value in keep.items() if value is not None}


if __name__ == "__main__":
    raise SystemExit(main())
