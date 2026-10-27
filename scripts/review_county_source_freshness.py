#!/usr/bin/env python3
"""Produce an auditable, non-publication county readiness report.

A passed structural validation does not prove the provider's data is current.
Report actual observation dates and source reconciliation without inventing
freshness, and keep approval strictly separate.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from validate_county_publication_candidate import validate


def parsed(value):
    if value is None:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid source timestamp: {value!r}") from exc
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


def review(candidate, now=None):
    validate(candidate)
    now = now or datetime.now(timezone.utc)
    states = {}
    for code, state in candidate["states"].items():
        rows = state["counties"]
        provider_checked = parsed(state.get("provider_checked_at"))
        statewide_cutoff = parsed(state.get("statewide_cutoff"))
        county_cutoffs = [parsed(row.get("file_as_of")) for row in rows]
        dated = [d for d in county_cutoffs if d is not None]
        for name, value in [("provider_checked_at", provider_checked), ("statewide_cutoff", statewide_cutoff)]:
            if value and value > now:
                raise ValueError(f"{code}: {name} is in the future")
        if any(d > now for d in dated):
            raise ValueError(f"{code}: county observation cutoff is in the future")
        provider_total = state.get("provider_statewide_total")
        difference = state["total"] - provider_total if provider_total is not None else None
        county_vs_statewide_cutoff = ("unknown" if not dated or statewide_cutoff is None else
            "county_older" if max(dated) < statewide_cutoff else
            "county_newer" if min(dated) > statewide_cutoff else
            "matching" if len(dated) == len(rows) and all(d == statewide_cutoff for d in dated) else
            "mixed")
        states[code] = {
            "status": state["reporting_label"],
            "counties_reported": len(rows),
            "counties_expected": state["geographic_count"],
            "county_ballots_observed": state["total"],
            "county_total_basis": "sum_of_reported_counties",
            "provider_statewide_total": provider_total,
            "county_minus_provider_statewide": difference,
            "county_vs_statewide_cutoff": county_vs_statewide_cutoff,
            "reconciliation_status": ("unavailable" if difference is None else
                "matching" if difference == 0 else
                "cutoffs_unknown" if county_vs_statewide_cutoff == "unknown" else
                "different_cutoffs" if county_vs_statewide_cutoff in ("county_older", "county_newer") else
                "mixed_cutoffs_unreconciled" if county_vs_statewide_cutoff == "mixed" else
                "same_cutoff_unreconciled"),
            "provider_checked_at": provider_checked.isoformat() if provider_checked else None,
            "statewide_source_cutoff": statewide_cutoff.isoformat() if statewide_cutoff else None,
            "counties_with_source_cutoff": len(dated),
            "counties_without_source_cutoff": len(rows) - len(dated),
            "earliest_county_cutoff": min(dated).isoformat() if dated else None,
            "latest_county_cutoff": max(dated).isoformat() if dated else None,
            "freshness_verified": False,
            "freshness_reason": "Source timestamps are disclosed, but current authoritative freshness has not been independently verified",
            "publication_approved": False,
        }
    return {
        "review_status": "source_freshness_review_required_not_approved_for_publication",
        "generated_at": now.isoformat(),
        "states": states,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = review(json.loads(Path(args.candidate).read_text()))
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
