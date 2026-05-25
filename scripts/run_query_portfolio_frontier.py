from __future__ import annotations

import copy
import json
import re
import sys
from itertools import combinations
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))

from audit_harness.model import STATUS_RANK, evaluate_scenario


RESULTS = ROOT / "experiments" / "query_portfolios" / "results"
PUBLIC_RETRIEVAL = ROOT / "experiments" / "public_retrieval_benchmark" / "scenarios"
HOLDOUT = ROOT / "experiments" / "holdout_validation" / "scenarios"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [_variant_row(path) for path in _scenario_paths()]
    groups = _groups(rows)
    portfolios = [
        _portfolio_row(group_id, tuple(portfolio_rows))
        for group_id, group_rows in groups.items()
        for size in range(1, len(group_rows) + 1)
        for portfolio_rows in combinations(group_rows, size)
    ]
    group_rows = [_group_frontier(group_id, group_rows, portfolios) for group_id, group_rows in groups.items()]
    payload = {
        "issue_group_count": len(groups),
        "query_variant_count": len(rows),
        "portfolio_count": len(portfolios),
        "qualified_portfolio_count": sum(row["qualified"] for row in portfolios),
        "full_high_authority_portfolio_count": sum(row["full_high_authority"] for row in portfolios),
        "full_counter_material_portfolio_count": sum(row["full_counter_material"] for row in portfolios),
        "full_screening_material_portfolio_count": sum(
            row["full_high_authority"] and row["full_counter_material"] for row in portfolios
        ),
        "mean_authority_coverage": mean(row["authority_coverage"] for row in portfolios),
        "max_authority_coverage": max(row["authority_coverage"] for row in portfolios),
        "mean_counter_recall": mean(row["counter_authority_recall"] for row in portfolios),
        "max_counter_recall": max(row["counter_authority_recall"] for row in portfolios),
        "query_expansion_repairs_any_high_authority": sum(
            group["single_query_best_authority_coverage"] < group["portfolio_best_authority_coverage"]
            for group in group_rows
        ),
        "query_expansion_repairs_counter_material": sum(group["portfolio_best_counter_recall"] > 0 for group in group_rows),
        "groups": group_rows,
        "portfolios": portfolios,
    }
    report = _format_report(payload)
    (RESULTS / "query_portfolio_frontier.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (RESULTS / "query_portfolio_frontier.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


def _scenario_paths() -> list[Path]:
    return sorted(PUBLIC_RETRIEVAL.glob("*.json")) + sorted(HOLDOUT.glob("holdout-public-retrieval-*.json"))


def _variant_row(path: Path) -> dict:
    scenario = json.loads(path.read_text(encoding="utf-8"))
    result = evaluate_scenario(scenario)
    authority_sets = scenario["authority_sets"]
    retrieved = set(authority_sets.get("retrieved") or [])
    high = set(authority_sets.get("high_authority") or [])
    counter = set(authority_sets.get("counter_or_limiting") or [])
    return {
        "scenario": scenario,
        "scenario_id": scenario["id"],
        "group_id": _group_id(scenario["id"]),
        "query": _query(scenario),
        "path": str(path.relative_to(ROOT)),
        "allowed_status": result.allowed_status,
        "retrieved": retrieved,
        "high_authority": high,
        "counter_or_limiting": counter,
        "authority_coverage": _recall(high, retrieved),
        "counter_authority_recall": _recall(counter, retrieved),
    }


def _portfolio_row(group_id: str, rows: tuple[dict, ...]) -> dict:
    scenario = _portfolio_scenario(group_id, rows)
    result = evaluate_scenario(scenario)
    authority_coverage = 0.0 if result.authority_coverage is None else result.authority_coverage
    counter_recall = 0.0 if result.counter_authority_recall is None else result.counter_authority_recall
    return {
        "portfolio_id": scenario["id"],
        "group_id": group_id,
        "query_count": len(rows),
        "query_ids": [row["scenario_id"] for row in rows],
        "allowed_status": result.allowed_status,
        "disposition": result.disposition,
        "failure_flags": result.failure_flags,
        "authority_coverage": authority_coverage,
        "counter_authority_recall": counter_recall,
        "full_high_authority": authority_coverage == 1.0,
        "full_counter_material": counter_recall == 1.0,
        "qualified": STATUS_RANK[result.allowed_status] >= STATUS_RANK["normative_material_screening_output"],
        "retrieved_record_count": len(scenario["authority_sets"]["retrieved"]),
    }


def _portfolio_scenario(group_id: str, rows: tuple[dict, ...]) -> dict:
    base = copy.deepcopy(rows[0]["scenario"])
    retrieved = sorted(set().union(*(row["retrieved"] for row in rows)))
    high = sorted(set().union(*(row["high_authority"] for row in rows)))
    counter = sorted(set().union(*(row["counter_or_limiting"] for row in rows)))
    query_numbers = "-".join(_query_number(row["scenario_id"]) for row in rows)
    base["id"] = f"query-portfolio-{group_id}-{query_numbers}"
    base["deployment_context"] = "Query portfolio over public retrieval variants: " + " | ".join(
        row["query"] for row in rows
    )
    base["authority_sets"]["high_authority"] = high
    base["authority_sets"]["retrieved_high_authority"] = sorted(set(retrieved) & set(high))
    base["authority_sets"]["counter_or_limiting"] = counter
    base["authority_sets"]["retrieved_counter_or_limiting"] = sorted(set(retrieved) & set(counter))
    base["authority_sets"]["retrieved"] = retrieved
    base["upstream_metrics"] = {
        "precision": None,
        "recall": _recall(set(high) | set(counter), set(retrieved)),
        "f1": None,
    }
    base["evidence_packet"] = _merged_evidence_packet(rows)
    base.pop("expected_allowed_status", None)
    base.pop("expected_disposition", None)
    return base


def _merged_evidence_packet(rows: tuple[dict, ...]) -> dict:
    seen: set[str] = set()
    output_units = []
    output_links = []
    for row in rows:
        scenario = row["scenario"]
        tag_by_source = _source_tags(scenario)
        for unit in _ranked_units(scenario.get("evidence_packet", {}).get("output_units", [])):
            source_ids = unit.get("source_ids") or []
            locators = unit.get("locators") or []
            for index, source_id in enumerate(source_ids):
                if source_id in seen:
                    continue
                seen.add(source_id)
                unit_id = f"portfolio-rank-{len(output_units) + 1:02d}"
                locator = locators[index] if index < len(locators) else (locators[0] if locators else source_id)
                output_units.append(
                    {
                        "id": unit_id,
                        "claim": f"Query portfolio makes this material visible: {source_id}",
                        "source_ids": [source_id],
                        "locators": [locator],
                        "output_rank": len(output_units) + 1,
                    }
                )
                output_links.append(
                    {
                        "unit_id": unit_id,
                        "source_id": source_id,
                        "locator": locator,
                        "supports_claim": True,
                        "source_tag": tag_by_source.get(source_id, "public_metadata"),
                    }
                )
    return {
        "source_collection": "query portfolio over committed public retrieval and holdout snapshots",
        "output_units": output_units,
        "output_links": output_links,
    }


def _group_frontier(group_id: str, variants: list[dict], portfolios: list[dict]) -> dict:
    group_portfolios = [row for row in portfolios if row["group_id"] == group_id]
    return {
        "group_id": group_id,
        "variant_count": len(variants),
        "portfolio_count": len(group_portfolios),
        "single_query_best_authority_coverage": max(row["authority_coverage"] for row in variants),
        "portfolio_best_authority_coverage": max(row["authority_coverage"] for row in group_portfolios),
        "single_query_best_counter_recall": max(row["counter_authority_recall"] for row in variants),
        "portfolio_best_counter_recall": max(row["counter_authority_recall"] for row in group_portfolios),
        "minimal_queries_for_full_high_authority": _minimal_queries(
            group_portfolios, lambda row: row["full_high_authority"]
        ),
        "minimal_queries_for_full_counter_material": _minimal_queries(
            group_portfolios, lambda row: row["full_counter_material"]
        ),
        "minimal_queries_for_full_screening_material": _minimal_queries(
            group_portfolios, lambda row: row["full_high_authority"] and row["full_counter_material"]
        ),
        "qualified_portfolio_count": sum(row["qualified"] for row in group_portfolios),
    }


def _source_tags(scenario: dict) -> dict[str, str]:
    tags = {}
    for link in scenario.get("evidence_packet", {}).get("output_links", []):
        tags.setdefault(link.get("source_id"), link.get("source_tag", "public_metadata"))
    return tags


def _groups(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["group_id"], []).append(row)
    return dict(sorted(grouped.items()))


def _group_id(scenario_id: str) -> str:
    stripped = scenario_id.removeprefix("holdout-public-retrieval-").removeprefix("public-retrieval-")
    return re.sub(r"-q\d+$", "", stripped)


def _query_number(scenario_id: str) -> str:
    match = re.search(r"q\d+$", scenario_id)
    return match.group(0) if match else "qxx"


def _query(scenario: dict) -> str:
    match = re.search(r"query: (.+)$", scenario.get("deployment_context", ""))
    return match.group(1) if match else scenario["id"]


def _ranked_units(units: list[dict]) -> list[dict]:
    if any("output_rank" in unit for unit in units):
        return sorted(units, key=lambda unit: unit.get("output_rank", len(units) + 1))
    return units


def _recall(known: set[str], retrieved: set[str]) -> float:
    if not known:
        return 0.0
    return len(known & retrieved) / len(known)


def _minimal_queries(portfolios: list[dict], predicate) -> int | None:
    matches = [row["query_count"] for row in portfolios if predicate(row)]
    return min(matches) if matches else None


def _format_report(payload: dict) -> str:
    lines = [
        "# Query Portfolio Frontier",
        "",
        f"Issue groups: {payload['issue_group_count']}",
        f"Query variants: {payload['query_variant_count']}",
        f"Query portfolios evaluated: {payload['portfolio_count']}",
        f"Qualified portfolios: {payload['qualified_portfolio_count']}/{payload['portfolio_count']}",
        f"Full high-authority portfolios: {payload['full_high_authority_portfolio_count']}/{payload['portfolio_count']}",
        f"Full counter-material portfolios: {payload['full_counter_material_portfolio_count']}/{payload['portfolio_count']}",
        f"Full screening-material portfolios: {payload['full_screening_material_portfolio_count']}/{payload['portfolio_count']}",
        f"Mean authority coverage: {payload['mean_authority_coverage']:.2f}; max {payload['max_authority_coverage']:.2f}",
        f"Mean counter-material recall: {payload['mean_counter_recall']:.2f}; max {payload['max_counter_recall']:.2f}",
        f"Groups where query expansion improves high-authority coverage: {payload['query_expansion_repairs_any_high_authority']}/{payload['issue_group_count']}",
        f"Groups where query expansion retrieves counter-material: {payload['query_expansion_repairs_counter_material']}/{payload['issue_group_count']}",
        "",
        "| Issue group | Variants | Portfolios | Single-query high | Portfolio high | Single-query counter | Portfolio counter | Min full high | Min full counter | Min full screening | Qualified portfolios |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in payload["groups"]:
        lines.append(
            f"| {group['group_id']} | {group['variant_count']} | {group['portfolio_count']} | "
            f"{group['single_query_best_authority_coverage']:.2f} | {group['portfolio_best_authority_coverage']:.2f} | "
            f"{group['single_query_best_counter_recall']:.2f} | {group['portfolio_best_counter_recall']:.2f} | "
            f"{_na(group['minimal_queries_for_full_high_authority'])} | "
            f"{_na(group['minimal_queries_for_full_counter_material'])} | "
            f"{_na(group['minimal_queries_for_full_screening_material'])} | "
            f"{group['qualified_portfolio_count']} |"
        )
    return "\n".join(lines)


def _na(value: int | None) -> str:
    return "n/a" if value is None else str(value)


if __name__ == "__main__":
    raise SystemExit(main())
