#!/usr/bin/env python3
"""Validate a legitimately obtained Alaska House-district ballot report.

No challenge bypass. No statewide-to-district imputation. Review artifact only.
Accepts a normalized CSV export with district, received, and as_of columns.
"""
import argparse
import csv
import datetime as dt
import json
from pathlib import Path

def parse(path, source_url):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {"district", "received", "as_of"}.issubset(reader.fieldnames):
            raise ValueError("Expected CSV columns: district, received, as_of")
        rows = list(reader)
    if len(rows) != 40:
        raise ValueError("Alaska requires exactly 40 House-district rows")
    seen = set()
    cutoff = None
    output = []
    for row in rows:
        raw = row["district"].strip()
        if raw.upper().startswith("HD"):
            raw = raw[2:].strip()
        if not raw.isdigit() or not 1 <= int(raw) <= 40:
            raise ValueError("Invalid House district")
        district = int(raw)
        if district in seen:
            raise ValueError("Duplicate House district")
        seen.add(district)
        value = row["received"].strip().replace(",", "")
        if not value.isdigit():
            raise ValueError("Invalid received-ballot total")
        received = int(value)
        stamp = row["as_of"].strip()
        dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if cutoff is None:
            cutoff = stamp
        if cutoff != stamp:
            raise ValueError("Mixed district reporting cutoffs")
        output.append({"district": district, "received_ballots": received})
    if seen != set(range(1, 41)):
        raise ValueError("Incomplete House-district coverage")
    return {"schema": "electionhq-ak-house-district-review-v1",
            "state": "AK", "geography": "state_house_district",
            "geographic_count": 40, "reported_districts": 40,
            "source_url": source_url, "source_cutoff": cutoff,
            "total_received_ballots": sum(r["received_ballots"] for r in output),
            "districts": sorted(output, key=lambda r: r["district"]),
            "publication_approved": False,
            "county_equivalent_observations": None}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.source_url.startswith("https://"):
        raise ValueError("HTTPS source attribution required")
    target = args.output.resolve()
    if target.is_relative_to((Path.cwd() / "data/early-vote").resolve()):
        raise ValueError("District review must not be published as a county feed")
    result = parse(args.input_csv, args.source_url)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("Validated", len(result["districts"]), "Alaska House districts at", result["source_cutoff"])

if __name__ == "__main__":
    main()
