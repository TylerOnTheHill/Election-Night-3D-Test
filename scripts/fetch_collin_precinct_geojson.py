#!/usr/bin/env python3
"""Fetch public Collin precinct polygons from official ArcGIS REST, staging only.

No voter records, no publication, and no assumption about election vintage.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from normalize_collin_precinct_geojson import convert

LAYER = "https://maps.collincountytx.gov/server/rest/services/InteractiveMap/Election_Department/MapServer/0/query"

def collect(fetch, page_size=500):
    if not 1 <= page_size <= 2000:
        raise ValueError("Invalid page size")
    offset, all_features, seen_ids = 0, [], set()
    for _ in range(100):
        query = urlencode({"where":"1=1","outFields":"OBJECTID,PRECINCT",
                           "returnGeometry":"true","outSR":"4326",
                           "f":"geojson","resultOffset":offset,
                           "resultRecordCount":page_size,"orderByFields":"OBJECTID"})
        page = fetch(LAYER + "?" + query)
        if page.get("error"):
            raise ValueError("ArcGIS error: " + str(page["error"]))
        features = page.get("features")
        if page.get("type") != "FeatureCollection" or not isinstance(features,list):
            raise ValueError("Unexpected ArcGIS response")
        if not features:
            break
        for f in features:
            oid=(f.get("properties") or {}).get("OBJECTID")
            if type(oid) is not int or oid in seen_ids:
                raise ValueError("Missing or duplicate OBJECTID in paginated response")
            seen_ids.add(oid)
            all_features.append(f)
        offset += len(features)
        if len(features) < page_size:
            break
    else:
        raise ValueError("Pagination limit reached")
    if not all_features:
        raise ValueError("No precincts returned")
    return convert({"type":"FeatureCollection","features":all_features})

def get_json(url):
    with urlopen(url,timeout=45) as response:
        return json.load(response)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    p.add_argument("--page-size",type=int,default=500)
    args=p.parse_args()
    result=collect(get_json,args.page_size)
    Path(args.output).write_text(json.dumps(result,separators=(",",":"))+"\n")
    print("Downloaded",len(result["features"]),"precinct polygons from official Collin ArcGIS.")
    print("STAGING ONLY: November 2026 geometry vintage and roster joins remain unverified.")

if __name__=="__main__":main()
