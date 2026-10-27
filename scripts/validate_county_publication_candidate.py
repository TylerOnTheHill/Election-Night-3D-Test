#!/usr/bin/env python3
"""Validate a county publication candidate without authorizing publication.

This command is intentionally read-only. Owner approval and a separate
publication action are required before any public feed is written.
"""
import argparse
import json
from pathlib import Path

EXPECTED = {"TX": (254, "48"), "NC": (100, "37"), "FL": (67, "12"), "VA": (133, "51"), "IA": (99, "19"), "WI": (72, "55"), "SC": (46, "45")}

def validate(candidate):
    if candidate.get("schema") != "electionhq-county-preview-v1":
        raise ValueError("Unexpected county schema")
    if candidate.get("publication_approved") is not False or candidate.get("review_required") is not True:
        raise ValueError("Candidate must remain unapproved and require review")
    states = candidate.get("states")
    if not isinstance(states, dict) or not states or set(states) - set(EXPECTED):
        raise ValueError("Empty or unsupported county candidate states")
    summary = {}
    for code in sorted(states):
        expected, prefix = EXPECTED[code]
        state = candidate["states"][code]
        rows = state.get("counties")
        if state.get("status") != "candidate_pending_publication_approval":
            raise ValueError(code + ": missing pending-approval status")
        if not isinstance(rows, list) or not 0 < len(rows) <= expected:
            raise ValueError(code + ": invalid county coverage")
        if state.get("geographic_count") != expected or state.get("county_count") != len(rows):
            raise ValueError(code + ": inconsistent geographic counts")
        if state.get("coverage_complete") is not (len(rows) == expected):
            raise ValueError(code + ": incorrect completeness flag")
        statewide = state.get("provider_statewide_total")
        reconciled = statewide is not None and state.get("total") == statewide
        expected_label = "Fully reported" if len(rows) == expected and state.get("statewide_reconciled", True) else "Partially reported"
        if state.get("reporting_label") != expected_label:
            raise ValueError(code + ": incorrect reporting label")
        if "statewide_reconciled" in state and state["statewide_reconciled"] is not reconciled:
            raise ValueError(code + ": invalid statewide reconciliation flag")
        if state.get("total_basis") != "sum_of_reported_counties":
            raise ValueError(code + ": incorrect total basis")
        if not all(isinstance(state.get(k), str) and state[k].strip() for k in
                   ("provider", "credit", "census_geography_source", "census_geography_url")):
            raise ValueError(code + ": missing source provenance")
        if state.get("statewide_cutoff") is not None and (not isinstance(state["statewide_cutoff"], str) or not state["statewide_cutoff"].strip()):
            raise ValueError(code + ": invalid provided reporting cutoff")
        if state.get("provider_statewide_total") is not None and (type(state["provider_statewide_total"]) is not int or state["provider_statewide_total"] < 0):
            raise ValueError(code + ": invalid provider statewide total")
        seen = set()
        total = 0
        for row in rows:
            fips = row.get("fips")
            if not isinstance(fips, str) or len(fips) != 5 or not fips.startswith(prefix) or not fips.isdigit() or fips in seen:
                raise ValueError(code + ": invalid or duplicate FIPS")
            seen.add(fips)
            count = row.get("total")
            if type(count) is not int or count < 0:
                raise ValueError(code + ": invalid ballot count")
            if not isinstance(row.get("name"), str) or not row["name"].strip():
                raise ValueError(code + ": missing county name")
            cutoff = row.get("file_as_of")
            if cutoff is not None and (not isinstance(cutoff, str) or not cutoff.strip()):
                raise ValueError(code + ": invalid supplied county reporting cutoff")
            if not isinstance(row.get("source_url"), str) or not row["source_url"].startswith("https://"):
                raise ValueError(code + ": missing county source URL")
            if not isinstance(row.get("credit"), str) or not row["credit"].strip():
                raise ValueError(code + ": missing county attribution")
            total += count
        if type(state.get("total")) is not int or state["total"] != total:
            raise ValueError(code + ": county aggregation mismatch")
        summary[code] = {"reported_counties": len(rows), "expected_counties": expected,
                         "reporting_label": state["reporting_label"], "reported_ballots": total}
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", default="staging-county-publication-candidate.json")
    args = parser.parse_args()
    result = validate(json.loads(Path(args.candidate).read_text()))
    print(json.dumps({"review_status": "validated_candidate_not_approved_for_publication",
                      "states": result}, indent=2))

if __name__ == "__main__":
    main()
