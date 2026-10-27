#!/usr/bin/env python3
"""Normalize Collin County official ArcGIS precinct GeoJSON to ElectionHQ staging keys.

Requires an already-downloaded GeoJSON FeatureCollection. No voter records.
Source layer: https://maps.collincountytx.gov/server/rest/services/InteractiveMap/Election_Department/MapServer/0
"""
import argparse
import json
from pathlib import Path

COLLIN_FIPS = "48085"

def normalize_precinct(value):
    if type(value) is int and value >= 0:
        return str(value)
    if isinstance(value, str) and value.strip().isdigit():
        return str(int(value.strip()))
    raise ValueError("Invalid Collin precinct number")

def convert(source):
    if source.get("type") != "FeatureCollection" or not isinstance(source.get("features"), list):
        raise ValueError("Expected GeoJSON FeatureCollection")
    if not source["features"]:
        raise ValueError("No precinct polygons")
    seen = set()
    features = []
    for f in source["features"]:
        raw = (f.get("properties") or {}).get("PRECINCT")
        precinct = normalize_precinct(raw)
        if precinct in seen:
            raise ValueError("Duplicate precinct: " + precinct)
        seen.add(precinct)
        geometry = f.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") not in ("Polygon", "MultiPolygon"):
            raise ValueError("Expected precinct polygon")
        if not geometry.get("coordinates"):
            raise ValueError("Missing precinct coordinates")
        features.append({"type": "Feature",
                         "properties": {"county_fips": COLLIN_FIPS, "area_id": precinct},
                         "geometry": geometry})
    return {"type": "FeatureCollection",
            "features": features}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Downloaded official Collin County precinct GeoJSON")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = convert(json.loads(Path(args.input).read_text()))
    Path(args.output).write_text(json.dumps(data, indent=2) + "\n")
    print("Staging only:", len(data["features"]), "Collin precinct polygons normalized")
    print("Boundary vintage and November general-election applicability NOT verified")

if __name__ == "__main__":
    main()
