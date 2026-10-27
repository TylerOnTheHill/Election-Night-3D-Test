#!/usr/bin/env python3
"""Normalize Florida's official *county statistics* tables into safe aggregates.

Input is a manually extracted JSON table of county statistics, not voter-level records.
The upstream HTML page is not a stable public API; fetching/parsing it is a separate task.
"""
import argparse
import json
from datetime import date
from pathlib import Path

CATEGORIES = {"voted_mail", "voted_early"}
PARTIES = ("republican", "democrat", "other", "no_party_affiliation")
COUNTIES_EXPECTED = 67

def normalize(payload):
    assert payload["source_url"] == "https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports/PublicStats"
    assert payload["election_id"] == "49894"
    assert date.fromisoformat(payload["reported_through"]) <= date.today()
    rows = payload["rows"]
    assert isinstance(rows, list) and rows
    seen = set()
    output = []
    for row in rows:
        county = row["county"].strip()
        kind = row["category"]
        assert county and kind in CATEGORIES
        key = (county.casefold(), kind)
        assert key not in seen, key
        seen.add(key)
        parts = {}
        for party in PARTIES:
            value = row[party]
            assert type(value) is int and value >= 0, (key, party)
            parts[party] = value
        assert type(row["total"]) is int and row["total"] == sum(parts.values()), key
        output.append({"county": county, "category": kind, "total": row["total"],
                       "registration": parts, "reported_through": payload["reported_through"]})
    counties = {r["county"].casefold() for r in output}
    full_categories = all({r["category"] for r in output if r["county"].casefold() == county} == CATEGORIES for county in counties)
    complete = len(counties) == COUNTIES_EXPECTED and full_categories
    return {"schema": "electionhq-county-early-vote-v1", "state_fips": "12",
            "source_url": payload["source_url"], "election_id": payload["election_id"],
            "reported_through": payload["reported_through"],
            "coverage": {"county_category_rows": len(output), "counties_reported": len(counties),
                         "complete_both_categories": complete},
            "records": sorted(output, key=lambda r: (r["county"], r["category"]))}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    normalized = normalize(json.loads(args.input.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(normalized, indent=2) + "\n")
    print("Validated", len(normalized["records"]), "county/category rows")
