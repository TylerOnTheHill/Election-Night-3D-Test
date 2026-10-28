#!/usr/bin/env python3
"""Normalize real AZ KS MS NE NV civicAPI county observations for ElectionHQ."""
import argparse,json,urllib.request
from pathlib import Path
from validate_county_publication_candidate import validate
STATES={"AZ":(15,"04"),"KS":(105,"20"),"MS":(82,"28"),"NE":(93,"31"),"NV":(17,"32")}
CENSUS="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
BASE="https://election-watch.50501vets.com/map/"
def build(source,geo):
    states={}
    for code,(expected,prefix) in STATES.items():
        methods={r["method"]:r for r in source["observations"] if r["state"]==code and r.get("status")=="county_table_found"}
        if "returned" not in methods:raise ValueError(code+": no returned county observations")
        for method,r in methods.items():
            if len(r["counties"])!=expected:raise ValueError(code+" "+method+": incomplete county observations")
        lookup={f["properties"]["NAME"].casefold():str(f["id"]).zfill(5) for f in geo["features"] if str(f["id"]).zfill(5).startswith(prefix)}
        counts={}
        for method,r in methods.items():
            for c in r["counties"]:
                name=c["name"].strip().removesuffix(" County")
                fips=lookup.get(name.casefold())
                if not fips:raise ValueError(code+": unknown county "+name)
                entry=counts.setdefault(fips,{"fips":fips,"name":name,"mail":0,"in_person":0})
                key="mail" if method=="returned" else "in_person"
                entry[key]=c["total"]
        if len(counts)!=expected:raise ValueError(code+": missing county observations")
        rows=[]
        for c in sorted(counts.values(),key=lambda c:c["fips"]):
            rows.append({**c,"total":c["mail"]+c["in_person"],
                "file_as_of":None,"source_url":BASE+code+"?cat=returned",
                "credit":"50501 Vets / civicAPI"})
        total=sum(r["total"] for r in rows)
        states[code]={"status":"candidate_pending_publication_approval",
            "provider":"50501 Vets / civicAPI","credit":"50501 Vets / civicAPI",
            "census_geography_source":"Plotly US Census county GeoJSON",
            "census_geography_url":CENSUS,
            "statewide_cutoff":None,
            "county_count":expected,"geographic_count":expected,
            "coverage_complete":True,"reporting_label":"Fully reported",
            "statewide_reconciled":True,"provider_statewide_total":total,
            "total":total,"total_basis":"sum_of_reported_counties",
            "method_coverage":"returned_and_in_person" if "inperson" in methods else "returned_only",
            "counties":rows}
    result={"schema":"electionhq-county-preview-v1","publication_approved":False,"review_required":True,"states":states}
    validate(result)
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.resolve().is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Staging only")
    req=urllib.request.Request(CENSUS,headers={"User-Agent":"ElectionHQ/1.0"})
    with urllib.request.urlopen(req,timeout=40) as response:geo=json.load(response)
    result=build(json.loads(a.source.read_text()),geo)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Additional states:",{k:(v["county_count"],v["total"]) for k,v in result["states"].items()})
if __name__=="__main__":main()
