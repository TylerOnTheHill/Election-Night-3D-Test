#!/usr/bin/env python3
"""Validate TLC Collin 2026 primary polygons before local preview. No publication authorization."""
import argparse
import json
import math
from pathlib import Path

def validate(data):
    if data.get("type")!="FeatureCollection" or not isinstance(data.get("features"),list):
        raise ValueError("Expected FeatureCollection")
    features=data["features"]
    if not features:raise ValueError("Empty Collin geometry")
    ids=set()
    vertices=0
    bounds=[math.inf,math.inf,-math.inf,-math.inf]
    for f in features:
        p=f.get("properties") or {}
        if p.get("county_fips")!="48085" or not isinstance(p.get("area_id"),str) or not p["area_id"]:
            raise ValueError("Unexpected county or precinct key")
        if p["area_id"] in ids:raise ValueError("Duplicate precinct")
        ids.add(p["area_id"])
        g=f.get("geometry") or {}
        typ=g.get("type")
        if typ not in ("Polygon","MultiPolygon"):raise ValueError("Invalid geometry type")
        polys=[g.get("coordinates")] if typ=="Polygon" else g.get("coordinates")
        if not isinstance(polys,list) or not polys:raise ValueError("Missing polygons")
        for poly in polys:
            if not isinstance(poly,list) or not poly:raise ValueError("Missing rings")
            for ring in poly:
                if not isinstance(ring,list) or len(ring)<4:raise ValueError("Invalid ring")
                if ring[0]!=ring[-1]:raise ValueError("Unclosed ring")
                for pt in ring:
                    if not isinstance(pt,list) or len(pt)<2:raise ValueError("Invalid point")
                    x,y=pt[:2]
                    if any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in (x,y)):
                        raise ValueError("Nonfinite coordinate")
                    if not (-180<=x<=180 and -90<=y<=90):raise ValueError("Not WGS84")
                    bounds[0]=min(bounds[0],x);bounds[1]=min(bounds[1],y)
                    bounds[2]=max(bounds[2],x);bounds[3]=max(bounds[3],y)
                    vertices+=1
    if not (-98<bounds[0]<-95 and -98<bounds[2]<-95 and 32<bounds[1]<35 and 32<bounds[3]<35):
        raise ValueError("Geometry bounds outside Collin County region")
    return {"schema":"electionhq-collin-tlc-geometry-validation-v1",
            "publication_approved":False,"verified_for_2026_general":False,
            "source_election":"2026 primary","precinct_count":len(features),
            "unique_precinct_ids":len(ids),"vertex_count":vertices,
            "bbox_wgs84":bounds,"status":"staging_only_geometry_valid_not_general_certified"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--geojson",required=True)
    p.add_argument("--report",required=True)
    a=p.parse_args()
    result=validate(json.loads(Path(a.geojson).read_text()))
    Path(a.report).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
