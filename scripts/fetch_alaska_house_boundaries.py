#!/usr/bin/env python3
"""Fetch and validate Alaska's 40 official House-district polygons (staging only).

Source: State of Alaska DCCED / Division of Elections ArcGIS MapServer, layer 2.
Does not publish, approve, or merge ballot counts.
"""
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

SERVICE = "https://maps.commerce.alaska.gov/server/rest/services/Govt_Related/Govt_House_and_Senate_Districts/MapServer/2/query"

def validate(data):
    if data.get("type") != "FeatureCollection":
        raise ValueError("Expected GeoJSON FeatureCollection")
    features = data.get("features")
    if not isinstance(features, list) or len(features) != 40:
        raise ValueError("Expected exactly 40 Alaska House district polygons")
    found = set()
    for feature in features:
        props = feature.get("properties") or {}
        district = props.get("HouseDistrict")
        if isinstance(district, bool) or not isinstance(district, int) or district not in range(1, 41) or district in found:
            raise ValueError("Invalid or duplicate HouseDistrict")
        found.add(district)
        geom = feature.get("geometry") or {}
        if geom.get("type") not in ("Polygon", "MultiPolygon") or not geom.get("coordinates"):
            raise ValueError("Missing district polygon")
    if found != set(range(1, 41)):
        raise ValueError("Incomplete House district coverage")
    return data

def fetch():
    params = urllib.parse.urlencode({"where": "1=1", "outFields": "HouseDistrict,DistrictDescription",
                                     "returnGeometry": "true", "outSR": "4326", "f": "geojson"})
    with urllib.request.urlopen(SERVICE + "?" + params, timeout=45) as response:
        return validate(json.load(response))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/staging/alaska-house-districts.geojson"))
    args = parser.parse_args()
    data = fetch()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Validated 40 official Alaska House district boundaries: {args.output}")

if __name__ == "__main__":
    main()
