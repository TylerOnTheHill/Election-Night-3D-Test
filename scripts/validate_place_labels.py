#!/usr/bin/env python3
"""Validate nationwide place shards and the bundled major-city fallback."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
folder = root / "data/geography/places-by-state"
report = json.loads((folder / "validation.json").read_text(encoding="utf-8"))
assert report["source_records"] == 29880, report
assert report["accepted_records"] == 29876, report
assert report["invalid_records"] == 0, report
assert report["state_and_territory_shards"] == 52, report
assert report["unknown_population_sentinel"] == 0, report
assert len(report["records_by_state"]) == 52
fips = dict(zip(
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split(),
    "01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56".split()
))
fips["PR"] = "72"
assert len(fips) == 52
total = 0
for state, expected in report["records_by_state"].items():
    filename = folder / (fips[state] + ".json")
    data = json.loads(filename.read_text(encoding="utf-8"))
    assert data["schema"] == "electionhq-place-points-v1", filename
    assert len(data["places"]) == expected, (filename, expected)
    for place in data["places"]:
        assert len(place) == 5, (filename, place)
        name, state_name, population, lat, lon = place
        assert isinstance(name, str) and name and isinstance(state_name, str) and state_name
        assert isinstance(population, (int, float)) and population >= 0
        assert isinstance(lat, (int, float)) and -90 <= lat <= 90
        assert isinstance(lon, (int, float)) and -180 <= lon <= 180
    total += len(data["places"])
assert total == 29876, total
assert len(list(folder.glob("[0-9][0-9].json"))) == 52
fallback = json.loads((root / "data/geography/us-cities-top-1000.json").read_text(encoding="utf-8"))
assert fallback["schema"] == "electionhq-place-points-v1"
assert len(fallback["places"]) == 1000
print(f"PASS: {total:,} community points across 52 state/territory files; 1,000 major-city fallback points")
