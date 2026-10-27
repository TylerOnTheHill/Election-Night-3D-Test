#!/usr/bin/env python3
"""Audit county-level coverage across Call the Map state JSON downloads.

Staging only. Never infer that absent counties have zero votes or that
county totals share the statewide summary's cutoff.
"""
import argparse
import json
import pathlib
import urllib.request
from datetime import datetime, timezone

BASE = "https://www.callthemap.com/early-vote/data/"
ROOT = pathlib.Path(__file__).resolve().parents[1]

def audit_state(code, payload):
    if payload.get("schema") != "ctm-early-vote-download-v1" or payload.get("state") != code:
        raise ValueError("Unexpected state/schema for " + code)
    if not payload.get("credit") or not payload.get("license"):
        raise ValueError("Missing attribution for " + code)
    rows = payload.get("counties")
    if not isinstance(rows, list):
        raise ValueError("Missing county array for " + code)
    seen = set()
    total = 0
    missing = 0
    cutoff_values = set()
    for row in rows:
        county = row.get("county")
        if not isinstance(county, str) or not county.strip() or county in seen:
            raise ValueError("Invalid or duplicate county in " + code)
        if row.get("state") != code:
            raise ValueError("County in wrong state: " + code)
        seen.add(county)
        value = row.get("total")
        if value is None:
            missing += 1
        elif type(value) is not int or value < 0:
            raise ValueError("Invalid county total: " + code)
        else:
            total += value
        cutoff = row.get("file_as_of")
        if cutoff:
            cutoff_values.add(str(cutoff))
    summary = payload.get("summary")
    if not isinstance(summary, dict) or type(summary.get("total")) is not int:
        raise ValueError("Missing statewide summary: " + code)
    return {
        "state": code,
        "county_rows": len(rows),
        "counties_with_unknown_total": missing,
        "county_rows_sum_known": total,
        "statewide_summary_total": summary["total"],
        "statewide_minus_known_county_sum": summary["total"] - total,
        "county_cutoffs": sorted(cutoff_values),
        "statewide_cutoff": summary.get("file_as_of"),
        "summary_count_via": summary.get("count_via"),
        "has_county_rows": bool(rows),
        "county_coverage_complete": None,
        "coverage_note": "No authoritative county-equivalent count crosswalk verified; row count is not proof of complete coverage.",
        "credit": payload["credit"],
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="national-county-source-audit.json")
    p.add_argument("--input-dir", help="Use local state JSON fixtures instead of network")
    args = p.parse_args()
    national = json.loads((ROOT / "data/early-vote/US.json").read_text())
    codes = sorted({r["state"] for r in national["states"]})
    results = []
    failures = []
    for code in codes:
        try:
            if args.input_dir:
                payload = json.loads((pathlib.Path(args.input_dir) / (code + ".json")).read_text())
            else:
                req = urllib.request.Request(BASE + code + ".json", headers={"User-Agent": "ElectionHQ-county-coverage-audit/1.0"})
                with urllib.request.urlopen(req, timeout=20) as response:
                    payload = json.load(response)
            row = audit_state(code, payload)
            results.append(row)
            print(code, "county rows:", row["county_rows"], "unknown totals:", row["counties_with_unknown_total"], "statewide difference:", row["statewide_minus_known_county_sum"])
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            failures.append({"state": code, "error": str(exc)})
            print(code, "FAILED:", exc)
    output = {
        "schema": "electionhq-national-county-source-audit-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": "Call the Map",
        "provider_url": BASE,
        "states_in_national_feed": len(codes),
        "states_audited": len(results),
        "states_failed": len(failures),
        "states": results,
        "failures": failures,
        "status": "staging_only_not_approved_for_publication",
    }
    pathlib.Path(args.output).write_text(json.dumps(output, indent=2) + "\n")
    if failures:
        raise SystemExit(f"{len(failures)} state downloads/validations failed")
    print("Audited", len(results), "state feeds without publishing")

if __name__ == "__main__":
    main()
