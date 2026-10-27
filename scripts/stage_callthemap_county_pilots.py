#!/usr/bin/env python3
"""Stage Texas/North Carolina Call the Map county feeds without publishing.

Verifies count reconciliation, source provenance and row semantics. Does not
claim full geographic coverage or assign FIPS without a verified crosswalk.
"""
import argparse
import json
import pathlib
import urllib.request
from datetime import datetime

BASE = "https://www.callthemap.com/early-vote/data/"
CODES = ("TX", "NC")

def validate(code, payload):
    if code not in CODES or payload.get("state") != code or payload.get("schema") != "ctm-early-vote-download-v1":
        raise ValueError("Unexpected state/schema")
    if not payload.get("license") or not payload.get("credit"):
        raise ValueError("Missing provider attribution")
    rows = payload.get("counties")
    if not isinstance(rows, list) or not rows:
        raise ValueError("No county data")
    names = set()
    normalized = []
    for row in rows:
        name = row.get("county")
        if not isinstance(name, str) or not name.strip() or name in names or row.get("state") != code:
            raise ValueError("Invalid, duplicate, or wrong-state county")
        names.add(name)
        total = row.get("total")
        if type(total) is not int or total < 0:
            raise ValueError("Invalid county turnout total")
        parts = [row.get(k) for k in ("dem", "rep", "unaffiliated_other")]
        if any(v is not None and (type(v) is not int or v < 0) for v in parts):
            raise ValueError("Invalid party-registration breakdown")
        if all(v is not None for v in parts) and sum(parts) != total:
            raise ValueError("Party-registration counts do not reconcile")
        methods = [row.get(k) for k in ("mail", "in_person")]
        if any(v is not None and (type(v) is not int or v < 0) for v in methods):
            raise ValueError("Invalid voting-method breakdown")
        if all(v is not None for v in methods) and sum(methods) != total:
            raise ValueError("Voting methods do not reconcile")
        cutoff = row.get("file_as_of")
        if not isinstance(cutoff, str) or not cutoff:
            raise ValueError("Missing county source cutoff")
        datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
        if not isinstance(row.get("source_url"), str) or not row["source_url"].startswith("https://"):
            raise ValueError("Missing HTTPS source")
        if not row.get("credit"):
            raise ValueError("Missing county credit")
        normalized.append({"county": name, "total": total, "mail": methods[0],
                           "in_person": methods[1], "registered_dem": parts[0],
                           "registered_rep": parts[1], "registered_unaffiliated_other": parts[2],
                           "file_as_of": cutoff, "source_url": row["source_url"],
                           "credit": row["credit"], "fips": None})
    summary = payload.get("summary", {})
    statewide = summary.get("total")
    if type(statewide) is not int or statewide < 0:
        raise ValueError("Invalid statewide summary")
    summed = sum(r["total"] for r in normalized)
    if summed != statewide:
        raise ValueError(f"County total {summed} differs from statewide {statewide}; do not publish")
    return {"schema": "electionhq-county-pilot-v1", "state": code,
            "provider": "Call the Map", "credit": payload["credit"],
            "provider_checked_at": payload.get("checked_at"),
            "statewide_cutoff": summary.get("file_as_of"),
            "county_count": len(normalized), "county_sum": summed,
            "statewide_total": statewide, "counties": normalized,
            "coverage_complete": None, "fips_verified": False,
            "status": "staging_only_not_approved_for_publication"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", help="Optional local provider JSON directory")
    p.add_argument("--output-dir", default="staging-county-pilots")
    args = p.parse_args()
    out = pathlib.Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for code in CODES:
        if args.input_dir:
            payload = json.loads((pathlib.Path(args.input_dir) / (code + ".json")).read_text())
        else:
            req = urllib.request.Request(BASE + code + ".json", headers={"User-Agent": "ElectionHQ-county-pilot/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.load(response)
        result = validate(code, payload)
        (out / (code + ".json")).write_text(json.dumps(result, indent=2) + "\n")
        print(code, result["county_count"], "rows,", result["county_sum"], "ballots; STAGING ONLY")

if __name__ == "__main__":
    main()
