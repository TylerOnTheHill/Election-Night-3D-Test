#!/usr/bin/env python3
"""Validate Call the Map's state-specific county feed against an official FL snapshot.

Does NOT assume that the latest statewide summary and county rows share a cutoff.
No vote estimation, no county allocation of a statewide-only increase.
"""
import json
import pathlib
import urllib.request
from datetime import datetime

SOURCE = "https://www.callthemap.com/early-vote/data/FL.json"
FIELDS = ("total", "dem", "rep", "unaffiliated_other")
ROOT = pathlib.Path(__file__).resolve().parents[1]

def validate(feed, official):
    if feed.get("schema") != "ctm-early-vote-download-v1" or feed.get("state") != "FL":
        raise ValueError("Unexpected Call the Map Florida schema")
    if not feed.get("credit") or not feed.get("license"):
        raise ValueError("Missing Call the Map attribution/license")
    rows = feed.get("counties")
    if not isinstance(rows, list) or len(rows) != 67:
        raise ValueError("Expected 67 Florida county rows")
    known = {r["county"]: r for r in official["counties"]}
    if len(known) != 67 or len(set(known)) != 67:
        raise ValueError("Invalid official baseline counties")
    seen = set()
    comparison = []
    for row in rows:
        name = row.get("county")
        if name not in known or name in seen or row.get("state") != "FL":
            raise ValueError("Unknown, duplicated or wrong-state county")
        seen.add(name)
        values = [row.get(f) for f in FIELDS]
        if any(type(v) is not int or v < 0 for v in values):
            raise ValueError(f"Missing or invalid county counts: {name}")
        if sum(values[1:]) != values[0]:
            raise ValueError(f"County registration totals do not reconcile: {name}")
        if not row.get("source_url") or not row.get("credit") or not row.get("file_as_of"):
            raise ValueError(f"Missing county provenance or timestamp: {name}")
        datetime.fromisoformat(row["file_as_of"].replace("Z", "+00:00"))
        baseline = known[name]
        baseline_total = baseline["voted_early"]["total"] + baseline["voted_mail"]["total"]
        comparison.append({"county": name, "callthemap_total": row["total"],
                           "official_baseline_total": baseline_total,
                           "difference": row["total"] - baseline_total,
                           "callthemap_file_as_of": row["file_as_of"],
                           "source_url": row["source_url"], "credit": row["credit"]})
    county_sum = sum(r["callthemap_total"] for r in comparison)
    changed = sorted((r for r in comparison if r["difference"] != 0), key=lambda r: abs(r["difference"]), reverse=True)
    summary = feed.get("summary", {})
    statewide = summary.get("total")
    if type(statewide) is not int or statewide < 0:
        raise ValueError("Invalid statewide summary")
    return {
        "schema": "electionhq-fl-ctm-reconciliation-v1",
        "feed_checked_at": feed.get("checked_at"),
        "source_url": SOURCE,
        "credit": feed["credit"],
        "counties_count": len(comparison),
        "county_rows_total": county_sum,
        "county_rows_matching_official_baseline": len(comparison) - len(changed),
        "county_rows_different_from_official_baseline": len(changed),
        "largest_county_differences": changed[:10],
        "statewide_feed_total": statewide,
        "unallocated_statewide_minus_counties": statewide - county_sum,
        "county_cutoffs_may_differ_from_statewide": True,
        "official_baseline_compiled_at_local": official["compiled_at_local"],
        "county_comparison": comparison,
        "status": "staging_only_no_county_allocation",
    }

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--feed", help="Optional local FL.json fixture; otherwise download")
    p.add_argument("--output", default="florida-callthemap-reconciliation.json")
    args = p.parse_args()
    if args.feed:
        feed = json.loads(pathlib.Path(args.feed).read_text())
    else:
        req = urllib.request.Request(SOURCE, headers={"User-Agent": "ElectionHQ-county-validation/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            feed = json.load(response)
    official = json.loads((ROOT / "data/early-vote/FL.json").read_text())
    report = validate(feed, official)
    pathlib.Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print("Matching counties:", report["county_rows_matching_official_baseline"])
    print("Differing counties:", report["county_rows_different_from_official_baseline"])
    print("Largest differences:", [(r["county"], r["difference"]) for r in report["largest_county_differences"]])
    print(f"Compared {report['counties_count']} counties; unallocated statewide difference: {report['unallocated_statewide_minus_counties']:,}")

if __name__ == "__main__":
    main()
