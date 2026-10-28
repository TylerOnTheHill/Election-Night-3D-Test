#!/usr/bin/env python3
"""Read-only release gate for battleground county feeds; never publishes data.

NH remains in the existing national/watchlist datasets but is excluded from
this battleground release decision by explicit project direction.
"""
import argparse
import json
from pathlib import Path

EXCLUDED = {"NH"}

def audit(readiness):
    if readiness.get("schema") != "electionhq-watchlist-readiness-v1":
        raise ValueError("Invalid readiness report schema")
    if readiness.get("publication_approved") is not False:
        raise ValueError("Readiness report must remain unpublished")
    rows = readiness.get("states")
    if not isinstance(rows, list) or len(rows) != 19:
        raise ValueError("Expected 19 original watchlist states")
    codes = [row.get("state") for row in rows]
    if len(set(codes)) != 19 or "NH" not in codes:
        raise ValueError("Invalid watchlist membership")
    assessed = []
    for row in rows:
        code = row["state"]
        if code in EXCLUDED:
            continue
        blockers = []
        if code == "AK" and row.get("district_review_staged"):
            if (row.get("district_review_geography") != "state_house_district"
                or row.get("district_review_reported") != 40
                or row.get("district_review_expected") != 40
                or type(row.get("district_review_ballots")) is not int
                or row["district_review_ballots"] < 0
                or not row.get("district_review_cutoff")):
                blockers.append("invalid_alaska_district_review")
        elif not row.get("county_staged"):
            blockers.append("county_source_not_staged")
        else:
            reported, expected = row.get("county_reported"), row.get("county_expected")
            if type(reported) is not int or type(expected) is not int or not 0 < reported <= expected:
                blockers.append("invalid_county_coverage")
            if type(row.get("county_ballots")) is not int or row["county_ballots"] < 0:
                blockers.append("invalid_county_total")
            if not row.get("county_cutoff"):
                blockers.append("unverified_reporting_cutoff")
        # A staged statewide cutoff alone does not establish county-source freshness.
        # Flag differing or unknown county dates for human review.
        if row.get("county_staged") and row.get("county_vs_statewide_cutoff") != "matching":
            blockers.append("county_source_freshness_not_verified")
        if row.get("county_publication_approved") is not True:
            blockers.append("publication_not_approved")
        assessed.append({"state": code, "ready": not blockers, "blockers": blockers,
                         "district_review_staged":code=="AK" and row.get("district_review_staged") is True,
                         "county_reported": row.get("county_reported"),
                         "county_expected": row.get("county_expected")})
    return {"schema": "electionhq-battleground-release-gate-v1",
            "publication_approved": False,
            "excluded_from_battleground_assessment": ["NH"],
            "states_assessed": len(assessed),
            "ready_count": sum(r["ready"] for r in assessed),
            "release_ready": all(r["ready"] for r in assessed),
            "states": assessed}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--readiness", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    target = Path(args.output).resolve()
    if target.is_relative_to((Path.cwd() / "data/early-vote").resolve()):
        raise ValueError("Internal release audit must not overwrite public data")
    result = audit(json.loads(Path(args.readiness).read_text()))
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(f'{result["ready_count"]}/{result["states_assessed"]} battleground states pass release gate')

if __name__ == "__main__":
    main()
