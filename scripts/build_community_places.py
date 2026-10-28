#!/usr/bin/env python3
"""Convert kelvins/US-Cities-Database CSV to ElectionHQ state place shards.

MIT source: https://github.com/kelvins/US-Cities-Database
Population is NOT provided by this source. Zero is an unknown-population sentinel.
"""
import argparse
import collections
import csv
import json
from pathlib import Path

FIPS = dict(zip(
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split(),
    "01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56".split()
))
FIPS["PR"] = "72"


def build(source, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    groups = collections.defaultdict(list)
    seen = collections.defaultdict(set)
    invalid = []
    count = 0
    with open(source, encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"ID", "STATE_CODE", "STATE_NAME", "CITY", "COUNTY", "LATITUDE", "LONGITUDE"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CSV missing required columns")
        for row in reader:
            count += 1
            code, name, state = row["STATE_CODE"].strip(), row["CITY"].strip(), row["STATE_NAME"].strip()
            try:
                lat, lon = float(row["LATITUDE"]), float(row["LONGITUDE"])
            except (ValueError, TypeError):
                invalid.append(row["ID"])
                continue
            if code not in FIPS or not name or not state or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                invalid.append(row["ID"])
                continue
            key = (name.casefold(), round(lat, 6), round(lon, 6))
            if key in seen[code]:
                continue
            seen[code].add(key)
            groups[code].append([name, state, 0, lat, lon])
    for code, places in sorted(groups.items()):
        (destination / (FIPS[code] + ".json")).write_text(
            json.dumps({"schema": "electionhq-place-points-v1", "places": places}, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8"
        )
    report = {
        "source_records": count,
        "invalid_records": len(invalid),
        "invalid_ids": invalid[:100],
        "state_and_territory_shards": len(groups),
        "accepted_records": sum(map(len, groups.values())),
        "records_by_state": {code: len(places) for code, places in sorted(groups.items())},
        "unknown_population_sentinel": 0,
    }
    (destination / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv")
    parser.add_argument("destination")
    args = parser.parse_args()
    build(args.csv, args.destination)
