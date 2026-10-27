#!/usr/bin/env python3
"""Build a non-publication county dashboard preview from verified staging files."""
import argparse
import json
from pathlib import Path

EXPECTED = {"TX": 254, "NC": 100}
FIPS_PREFIX = {"TX": "48", "NC": "37"}
def build(files):
    states = {}
    for code in EXPECTED:
        payload = json.loads((Path(files) / (code + ".json")).read_text())
        if payload.get("state") != code or payload.get("status") != "staging_only_fips_and_coverage_verified":
            raise ValueError("Unverified staging state: " + code)
        if payload.get("fips_verified") is not True:
            raise ValueError("Missing FIPS or geographic verification: " + code)
        rows = payload.get("counties")
        if not isinstance(rows, list) or not 0 < len(rows) <= EXPECTED[code]:
            raise ValueError("Incomplete county rows: " + code)
        if any(not isinstance(r.get("fips"), str) or len(r["fips"]) != 5 or
               not r["fips"].isdigit() or not r["fips"].startswith(FIPS_PREFIX[code]) for r in rows):
            raise ValueError("Invalid county FIPS: " + code)
        if len({r["fips"] for r in rows}) != len(rows):
            raise ValueError("Duplicate county FIPS: " + code)
        if any(not isinstance(r.get("total"), int) or isinstance(r["total"], bool) or r["total"] < 0 for r in rows):
            raise ValueError("Invalid county ballot count: " + code)
        if payload.get("coverage_complete") is not (len(rows) == EXPECTED[code]):
            raise ValueError("Inconsistent county coverage flag: " + code)
        if payload.get("geographic_count") is not None and payload["geographic_count"] != EXPECTED[code]:
            raise ValueError("Inconsistent geographic county count: " + code)
        county_total = sum(r["total"] for r in rows)
        reported_statewide = payload.get("statewide_total")
        statewide_reconciled = type(reported_statewide) is int and county_total == reported_statewide
        states[code] = {
            "status": "preview_only_not_approved_for_publication",
            "provider": payload["provider"],
            "credit": payload["credit"],
            "provider_checked_at": payload.get("provider_checked_at"),
            "statewide_cutoff": payload.get("statewide_cutoff"),
            "census_geography_source": payload["census_geography_source"],
            "census_geography_url": payload["census_geography_url"],
            "county_count": len(rows),
            "geographic_count": EXPECTED[code],
            "coverage_complete": len(rows) == EXPECTED[code],
            "reporting_label": "Fully reported" if len(rows) == EXPECTED[code] and statewide_reconciled else "Partially reported",
            "statewide_reconciled": statewide_reconciled,
            "total": county_total,
            "total_basis": "sum_of_reported_counties",
            "provider_statewide_total": reported_statewide,
            "county_vs_provider_statewide_difference": county_total - reported_statewide if isinstance(reported_statewide, int) else None,
            "counties": [{"fips": r["fips"], "name": r["county"], "total": r["total"],
                          "mail": r["mail"], "in_person": r["in_person"],
                          "registered_dem": r["registered_dem"],
                          "registered_rep": r["registered_rep"],
                          "registered_unaffiliated_other": r["registered_unaffiliated_other"],
                          "file_as_of": r["file_as_of"], "source_url": r["source_url"],
                          "credit": r["credit"]} for r in rows]
        }
    return {"schema": "electionhq-county-preview-v1", "publication_approved": False,
            "party_counts_mean": "voter registration, never candidate votes",
            "states": states}

def build_publication_candidate(files):
    """Create a publication-ready candidate, NOT an approved public feed.

    Approval must be an explicit separate step; a successful CI run alone
    cannot turn staged election observations into published data.
    """
    candidate = build(files)
    candidate["publication_approved"] = False
    candidate["review_required"] = True
    candidate["states"] = {
        code: {**state, "status": "candidate_pending_publication_approval"}
        for code, state in candidate["states"].items()
    }
    return candidate

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="staging-county-pilots-fips")
    parser.add_argument("--output", default="staging-county-preview.json")
    parser.add_argument("--candidate", action="store_true", help="Build unapproved publication candidate")
    args = parser.parse_args()
    preview = build_publication_candidate(args.input_dir) if args.candidate else build(args.input_dir)
    Path(args.output).write_text(json.dumps(preview, indent=2) + "\n")
    print("Publication candidate (approval required):" if args.candidate else "Preview-only:", ", ".join(f"{code} {x['county_count']} counties" for code, x in preview["states"].items()))

if __name__ == "__main__":
    main()
