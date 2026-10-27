#!/usr/bin/env python3
"""Verify Florida's full county source audit has no coverage gaps."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def validate():
    snapshot = json.loads((ROOT / "data/early-vote/FL.json").read_text())
    audit = json.loads((ROOT / "data/sources/florida-county-audit.json").read_text())
    names = [r["county"] for r in snapshot["counties"]]
    audited = [r["county"] for r in audit["counties"]]
    if len(names) != 67 or len(audited) != 67 or set(names) != set(audited):
        raise ValueError("County audit does not cover exactly the 67 snapshot counties")
    if len(set(audited)) != len(audited):
        raise ValueError("Duplicate county in source audit")
    for row in audit["counties"]:
        if not row["baseline_available"] or not row["official_supervisor_directory_verified"]:
            raise ValueError(f"Missing baseline or official directory for {row['county']}")
        if row["county_source_status"] == "verified" and not row.get("official_county_url"):
            raise ValueError(f"Verified county source missing official URL: {row['county']}")
        if row.get("county_feed_ingesting") and row["county_source_status"] != "ingesting":
            raise ValueError(f"County incorrectly marked as ingesting: {row['county']}")
    return len(audited)

if __name__ == "__main__":
    print(f"Validated Florida source audit: {validate()} counties")
