#!/usr/bin/env python3
"""Validate staging-only Texas subcounty aggregates; never infer precinct counts."""
import argparse
import json
import pathlib
import re

TYPES = {"voting_precinct", "voting_tabulation_district"}
KINDS = {"ballots_cast", "prior_primary_participation"}
def validate(payload):
    if payload.get("schema") != "electionhq-local-returns-v1" or payload.get("state") != "TX":
        raise ValueError("Unexpected schema/state")
    if payload.get("publication_approved") is not False:
        raise ValueError("Local data must remain staging only")
    if payload.get("area_type") not in TYPES or payload.get("metric_kind") not in KINDS:
        raise ValueError("Unrecognized geography/metric")
    for key in ("source_url", "geometry_source_url"):
        if not isinstance(payload.get(key), str) or not payload[key].startswith("https://"):
            raise ValueError("Missing source URL: " + key)
    if not payload.get("geometry_vintage") or not payload.get("file_as_of"):
        raise ValueError("Missing geographic vintage or reporting cutoff")
    rows = payload.get("areas")
    if not isinstance(rows, list) or not rows:
        raise ValueError("No local-area records")
    seen = set()
    total = 0
    for row in rows:
        county = row.get("county_fips")
        area = row.get("area_id")
        if not isinstance(county, str) or not re.fullmatch(r"48[0-9]{3}", county):
            raise ValueError("Invalid Texas county FIPS")
        if not isinstance(area, str) or not area.strip():
            raise ValueError("Missing local area identifier")
        key = (county, area)
        if key in seen:
            raise ValueError("Duplicate local-area identifier")
        seen.add(key)
        count = row.get("ballots_total")
        if type(count) is not int or count < 0:
            raise ValueError("Invalid local ballot total")
        total += count
        for k in ("prior_dem_primary", "prior_rep_primary"):
            n = row.get(k)
            if n is not None and (type(n) is not int or n < 0 or n > count):
                raise ValueError("Invalid primary history count")
        if row.get("candidate_dem_votes") is not None or row.get("candidate_rep_votes") is not None:
            raise ValueError("Candidate vote inference prohibited")
    expected = payload.get("reported_area_total")
    if type(expected) is not int or expected != total:
        raise ValueError("Local rows do not reconcile with their reported subtotal")
    # Subcounty coverage cannot be asserted without a verified full geometry join.
    if payload.get("coverage_complete") is True:
        raise ValueError("Full geographic coverage not verified here")
    return {**payload, "status": "staging_only_unverified_geographic_join",
            "reported_area_count": len(rows)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    output = validate(json.loads(pathlib.Path(args.input).read_text()))
    pathlib.Path(args.output).write_text(json.dumps(output, indent=2) + "\n")
    print("Validated staging-only local areas:", output["reported_area_count"])

if __name__ == "__main__":
    main()
