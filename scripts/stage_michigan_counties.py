#!/usr/bin/env python3
"""Stage Michigan 2026 county ballot observations from a dated public CSV.

Source aggregates Michigan Department of State's voting dashboard.
Never publish raw source data or infer suppressed values.
"""
import argparse,csv,io,json,re,urllib.request
from pathlib import Path
SOURCE="https://michiganrepublicanprimary.com/wp-content/uploads/2026/10/michigan-election-tracker-participation-2026-10-27.csv"
CENSUS="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
def parse(raw,geo):
    rows=list(csv.DictReader(io.StringIO(raw)))
    if not rows:raise ValueError("Empty Michigan county source")
    names={f["properties"]["NAME"].casefold():str(f["id"]).zfill(5) for f in geo["features"] if str(f["id"]).zfill(5).startswith("26")}
    if len(names)!=83:raise ValueError("Michigan county crosswalk incomplete")
    headers=list(rows[0])
    def field(needles):
        found=[x for x in headers if any(n in x.casefold().replace("_"," ") for n in needles)]
        if len(found)!=1:raise ValueError("Ambiguous Michigan CSV field "+repr(needles)+": "+repr(found))
        return found[0]
    county_key=field(["county"])
    total_key=field(["ballots recorded","ballots cast","total ballots","total early"])
    mail_key=field(["absentee returned","absentee ballots returned"])
    early_key=field(["early in person","early in-person"])
    counties=[];seen=set()
    def count(v):
        v=str(v).strip().replace(",","")
        if not re.fullmatch(r"\\d+",v):raise ValueError("Suppressed or invalid count: "+repr(v))
        return int(v)
    for row in rows:
        name=row[county_key].strip().removesuffix(" County")
        fips=names.get(name.casefold())
        if not fips:raise ValueError("Unknown Michigan county: "+name)
        if fips in seen:raise ValueError("Duplicate Michigan county")
        seen.add(fips)
        total,mail,early=map(count,(row[total_key],row[mail_key],row[early_key]))
        if total!=mail+early:raise ValueError("Michigan method reconciliation failed: "+name)
        counties.append({"fips":fips,"name":name,"total":total,"mail":mail,
            "in_person":early,"file_as_of":"2026-10-27","source_url":SOURCE,
            "credit":"Michigan Department of State voting dashboard; Michigan Republican Primary county CSV"})
    counties.sort(key=lambda r:r["fips"])
    if len(counties)!=83:raise ValueError("Expected all 83 Michigan counties")
    return {"schema":"electionhq-county-preview-v1","publication_approved":False,"review_required":True,
        "states":{"MI":{"status":"candidate_pending_publication_approval",
        "provider":"Michigan Department of State (aggregated by Michigan Republican Primary)",
        "credit":"Michigan Department of State / Michigan Republican Primary",
        "statewide_cutoff":"2026-10-27","county_count":len(counties),"geographic_count":83,
        "coverage_complete":True,"reporting_label":"Partially reported",
        "statewide_reconciled":False,"total":sum(c["total"] for c in counties),
        "total_basis":"sum_of_reported_counties","provider_statewide_total":None,"counties":counties}}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.resolve().is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("No public publishing")
    def get(url):
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"ElectionHQ/1.0"}),timeout=35) as r:return r.read().decode("utf-8-sig")
    result=parse(get(SOURCE),json.loads(get(CENSUS)))
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Michigan county rows:",result["states"]["MI"]["county_count"])
if __name__=="__main__":main()
