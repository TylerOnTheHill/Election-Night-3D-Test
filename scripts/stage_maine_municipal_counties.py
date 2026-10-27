#!/usr/bin/env python3
"""Aggregate 50501 Vets Maine municipal ballots into county totals using
Maine Political Data's published town/county geography crosswalk.
Never guess ambiguous town-to-county matches.
"""
import argparse,csv,io,json,re,urllib.request,collections
from pathlib import Path
from validate_county_publication_candidate import validate
UNITS="https://mainepoliticaldata.com/data/registration/units.csv"
CENSUS="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
SOURCE="https://election-watch.50501vets.com/map/ME?cat=returned"
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"ElectionHQ/1.0"}),timeout=45) as r:return r.read().decode("utf-8-sig")
def norm(s):return re.sub(r"[^a-z0-9]","",s.casefold().replace("town of ","").replace("city of ",""))
def build(source,units,geo):
    methods={r["method"]:r["counties"] for r in source["observations"] if r["state"]=="ME" and r.get("status")=="county_table_found"}
    if "returned" not in methods:raise ValueError("Maine returned municipal source absent")
    if not units:raise ValueError("Maine crosswalk empty")
    cols=list(units[0])
    county_col=next((k for k in cols if k.casefold() in ("county","county_name")),None)
    town_cols=[k for k in cols if k.casefold() in ("town","town_name","municipality","municipality_name","unit_name","name","city","place")]
    if not county_col or not town_cols:raise ValueError("Maine crosswalk columns require mapping: "+str(cols))
    lookup=collections.defaultdict(set)
    for r in units:
        county=r[county_col].strip()
        for key in town_cols:
            if r[key].strip() and county:lookup[norm(r[key])].add(county)
    fips={norm(f["properties"]["NAME"]):str(f["id"]).zfill(5) for f in geo["features"] if str(f["id"]).zfill(5).startswith("23")}
    totals=collections.defaultdict(lambda:{"mail":0,"in_person":0})
    unmatched=set();ambiguous={}
    for method,items in methods.items():
        for item in items:
            name=item["name"]
            counties=lookup.get(norm(name),set())
            if len(counties)!=1:
                if not counties:unmatched.add(name)
                else:ambiguous[name]=sorted(counties)
                continue
            county=next(iter(counties))
            code=fips.get(norm(county))
            if not code:raise ValueError("Unknown Maine county: "+county)
            totals[code]["mail" if method=="returned" else "in_person"]+=item["total"]
    if unmatched or ambiguous:raise ValueError("Unmapped Maine municipalities: "+str(sorted(unmatched)[:25])+"; ambiguous: "+str(list(ambiguous.items())[:10])+"; crosswalk columns: "+str(cols))
    if len(totals)!=16:raise ValueError("Expected 16 Maine counties, found "+str(len(totals)))
    rows=[]
    for f in geo["features"]:
        code=str(f["id"]).zfill(5)
        if code not in totals:continue
        m=totals[code]
        rows.append({"fips":code,"name":f["properties"]["NAME"],"total":m["mail"]+m["in_person"],**m,
                     "file_as_of":"2026-10-27","source_url":SOURCE,
                     "credit":"50501 Vets / civicAPI; Maine Political Data town/county geography"})
    total=sum(r["total"] for r in rows)
    state={"status":"candidate_pending_publication_approval","provider":"50501 Vets / civicAPI",
      "credit":"50501 Vets / civicAPI; Maine Political Data geography","census_geography_source":"Plotly US Census county GeoJSON",
      "census_geography_url":CENSUS,"statewide_cutoff":"2026-10-27","county_count":16,
      "geographic_count":16,"coverage_complete":True,"reporting_label":"Fully reported",
      "statewide_reconciled":True,"provider_statewide_total":total,"total":total,
      "total_basis":"sum_of_reported_counties","counties":rows}
    result={"schema":"electionhq-county-preview-v1","publication_approved":False,"review_required":True,"states":{"ME":state}}
    validate(result);return result
def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    units=list(csv.DictReader(io.StringIO(get(UNITS))))
    geo=json.loads(get(CENSUS))
    result=build(json.loads(a.source.read_text()),units,geo)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Maine county total:",result["states"]["ME"]["total"])
if __name__=="__main__":main()
