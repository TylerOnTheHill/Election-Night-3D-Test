#!/usr/bin/env python3
"""Check a local-return staging file against supplied precinct GeoJSON.

This does not authorize publication or certify boundary vintage.
"""
import argparse
import json
from pathlib import Path
from validate_tx_local_returns import validate

def check_join(payload, geojson, county_field, precinct_field):
    staged = validate(payload)
    if geojson.get("type") != "FeatureCollection" or not isinstance(geojson.get("features"), list):
        raise ValueError("Expected GeoJSON FeatureCollection")
    shapes = {}
    for feature in geojson["features"]:
        props = feature.get("properties") or {}
        county, precinct = props.get(county_field), props.get(precinct_field)
        if county is None or precinct is None:
            raise ValueError("Missing geography join attribute")
        key = (str(county), str(precinct))
        if key in shapes:
            raise ValueError("Duplicate geography key")
        if not isinstance(feature.get("geometry"), dict) or feature["geometry"].get("type") not in ("Polygon", "MultiPolygon"):
            raise ValueError("Invalid polygon geometry")
        shapes[key] = True
    data_keys = {(r["county_fips"], r["area_id"]) for r in staged["areas"]}
    shape_keys = set(shapes)
    return {
        "schema": "electionhq-local-geography-join-report-v1",
        "publication_approved": False,
        "geometry_vintage": staged["geometry_vintage"],
        "source_url": staged["source_url"],
        "geometry_source_url": staged["geometry_source_url"],
        "matched": len(data_keys & shape_keys),
        "unmatched_data": sorted([list(k) for k in data_keys - shape_keys]),
        "unmatched_geometry": sorted([list(k) for k in shape_keys - data_keys]),
        "data_area_count": len(data_keys),
        "geometry_area_count": len(shape_keys),
        "status": "staging_only_join_check_not_publication_approved"
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",required=True)
    p.add_argument("--geojson",required=True)
    p.add_argument("--county-field",required=True)
    p.add_argument("--precinct-field",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    result=check_join(json.loads(Path(args.data).read_text()),json.loads(Path(args.geojson).read_text()),args.county_field,args.precinct_field)
    Path(args.output).write_text(json.dumps(result,indent=2)+"\n")
    print("Matched:",result["matched"],"Unmatched data:",len(result["unmatched_data"]),"Unmatched shapes:",len(result["unmatched_geometry"]))
    if result["unmatched_data"]:
        raise SystemExit("Unmatched data precincts: join not usable")
if __name__=="__main__":main()
