#!/usr/bin/env python3
"""Compare validated county candidates before any publication decision.

A new source snapshot replaces earlier county observations. Never sum snapshots.
Report newly seen, revised and missing counties and fail on cutoff regressions.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from validate_county_publication_candidate import validate

def cutoff(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)

def compare(previous, current):
    validate(previous)
    validate(current)
    report = {}
    missing_states = set(previous["states"]) - set(current["states"])
    if missing_states:
        raise ValueError("Previously reporting states disappeared: " + ", ".join(sorted(missing_states)))
    for code in sorted(current["states"]):
        new = current["states"][code]
        old = previous["states"].get(code)
        if old is None:
            old = {**new, "counties": [], "total": 0, "statewide_cutoff": None}
        prior = {r["fips"]: r for r in old["counties"]}
        latest = {r["fips"]: r for r in new["counties"]}
        removed = sorted(set(prior) - set(latest))
        if removed:
            raise ValueError(f"{code}: previously reported counties disappeared: {', '.join(removed)}")
        old_state_cutoff, new_state_cutoff = cutoff(old.get("statewide_cutoff")), cutoff(new.get("statewide_cutoff"))
        if old_state_cutoff and (not new_state_cutoff or new_state_cutoff < old_state_cutoff):
            raise ValueError(f"{code}: statewide reporting cutoff regressed")
        for fips in sorted(set(prior) & set(latest)):
            older, newer = cutoff(prior[fips].get("file_as_of")), cutoff(latest[fips].get("file_as_of"))
            if older and (not newer or newer < older):
                raise ValueError(f"{code}: county {fips} reporting cutoff regressed")
        added = sorted(set(latest) - set(prior))
        changed = sorted(f for f in set(prior) & set(latest)
                         if latest[f]["total"] != prior[f]["total"])
        report[code] = {
            "reporting_status": new["reporting_label"],
            "counties_reported": len(latest),
            "counties_expected": new["geographic_count"],
            "new_counties": len(added),
            "revised_counties": len(changed),
            "unchanged_counties": len(latest) - len(added) - len(changed),
            "latest_reported_ballots": new["total"],
            "previous_reported_ballots": old["total"],
            "net_change_in_reported_county_totals": new["total"] - old["total"],
            "new_county_fips": added,
            "revised_county_fips": changed,
        }
    return {"status": "review_only_not_approved_for_publication",
            "method": "replace_latest_county_observation_by_fips_never_add_snapshots",
            "states": report}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    previous = json.loads(Path(args.previous).read_text())
    current = json.loads(Path(args.current).read_text())
    result = compare(previous, current)
    Path(args.report).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
