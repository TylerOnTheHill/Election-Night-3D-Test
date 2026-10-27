#!/usr/bin/env python3
"""Extract Collin County voting precinct polygons from Texas Legislative Council 2026 PRIMARY shapefile.

Official source: https://data.capitol.texas.gov/dataset/precincts
This dataset is NOT certified as November 2026 general-election geometry.
"""
import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

URL="https://data.capitol.texas.gov/dataset/d04c72b9-16c4-4ab2-8c6d-c666d41e04b7/resource/33ec5b30-ee4d-424f-9769-57b87cb5e311/download/precincts26p.zip"
FIPS="48085"

def convert_records(records):
    features=[]
    seen=set()
    for record,geo in records:
        county=str(record.get("FIPS",record.get("CNTY",""))).strip()
        if county not in (FIPS,"085","85"):
            continue
        raw=record.get("PREC")
        if raw is None or not str(raw).strip():
            raise ValueError("Missing official PREC field")
        precinct=str(raw).strip()
        key=(FIPS,precinct)
        if key in seen:
            raise ValueError("Duplicate official Collin PREC: "+precinct)
        seen.add(key)
        if not isinstance(geo,dict) or geo.get("type") not in ("Polygon","MultiPolygon") or not geo.get("coordinates"):
            raise ValueError("Invalid precinct polygon")
        features.append({"type":"Feature","properties":{"county_fips":FIPS,"area_id":precinct},"geometry":geo})
    if not features:
        raise ValueError("No Collin County precinct polygons found; verify source FIPS format")
    return {"type":"FeatureCollection","features":features}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--zip",help="Use already downloaded official Precincts26P.zip")
    p.add_argument("--output",required=True)
    p.add_argument("--report",required=True)
    args=p.parse_args()
    try:
        import shapefile
    except ImportError as e:
        raise SystemExit("Install pyshp: pip install pyshp") from e
    with tempfile.TemporaryDirectory() as temp:
        archive=Path(args.zip) if args.zip else Path(temp)/"precincts26p.zip"
        if not args.zip:
            request=Request(URL,headers={"User-Agent":"ElectionHQ-Research/1.0"})
            with urlopen(request,timeout=120) as response,archive.open("wb") as output:
                while chunk:=response.read(1024*1024):
                    output.write(chunk)
        with zipfile.ZipFile(archive) as z:
            names=z.namelist()
            if any(n.startswith("/") or ".." in Path(n).parts for n in names):
                raise ValueError("Unsafe ZIP path")
            candidates=[n for n in names if n.lower().endswith(".shp")]
            if len(candidates)!=1:
                raise ValueError("Expected one shapefile in official archive")
            stem=candidates[0][:-4]
            for ext in (".shp",".shx",".dbf",".prj"):
                match=next((n for n in names if n.lower()==(stem+ext).lower()),None)
                if match is None:raise ValueError("Missing shapefile component "+ext)
                Path(temp,Path(match).name).write_bytes(z.read(match))
            base=Path(temp,Path(stem).name)
            reader=shapefile.Reader(str(base),encoding="utf-8")
            fields=[x[0] for x in reader.fields[1:]]
            if "PREC" not in fields or not ({"FIPS","CNTY"} & set(fields)):
                raise ValueError("Unexpected TLC fields: "+str(fields))
            try:
                from pyproj import CRS, Transformer
            except ImportError as e:
                raise SystemExit("Install pyproj for CRS conversion") from e
            crs=CRS.from_wkt(base.with_suffix(".prj").read_text())
            transformer=Transformer.from_crs(crs,"EPSG:4326",always_xy=True)
            def transform_coords(coords):
                if isinstance(coords[0],(float,int)):
                    x,y=transformer.transform(coords[0],coords[1])
                    return [x,y]
                return [transform_coords(c) for c in coords]
            def records():
                for sr in reader.iterShapeRecords():
                    props=dict(zip(fields,sr.record))
                    if str(props.get("FIPS",props.get("CNTY",""))).strip() not in (FIPS,"085","85"):
                        continue
                    geom=sr.shape.__geo_interface__
                    geom={"type":geom["type"],"coordinates":transform_coords(geom["coordinates"])}
                    yield props,geom
            result=convert_records(records())
    Path(args.output).write_text(json.dumps(result,separators=(",",":"))+"\n")
    report={"schema":"electionhq-tlc-2026-primary-geometry-report-v1",
            "status":"staging_only_primary_boundaries_not_general_verified",
            "publication_approved":False,"county_fips":FIPS,
            "source_url":URL,"source_election":"2026 primary",
            "verified_for_2026_general":False,
            "precinct_count":len(result["features"]),
            "sample_ids":sorted(f["properties"]["area_id"] for f in result["features"])[:15]}
    Path(args.report).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
