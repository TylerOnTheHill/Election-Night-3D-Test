#!/usr/bin/env python3
"""Aggregate CC BY 4.0 Maine 2026 absentee returns by town into counties."""
import argparse
import csv
import io
import json
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE="https://mainepoliticaldata.com/data/"
SOURCE=BASE+"absentee/absentee_by_town.csv"
UNITS=BASE+"registration/units.csv"
ELECTION="2026-11-03"

def pick(columns, names):
    return next((c for c in names if c in columns),None)

def aggregate(ballots, units):
    if not ballots or not units:
        raise ValueError("Maine source tables empty")
    uc=units[0].keys()
    bc=ballots[0].keys()
    unit=pick(uc,("unit_id","unit"))
    county=pick(uc,("county","county_name"))
    bunit=pick(bc,("unit_id","unit"))
    election=pick(bc,("election_date","date"))
    returned=pick(bc,("returned","ballots_returned","returned_count"))
    accepted=pick(bc,("accepted","ballots_accepted","accepted_count"))
    if not all((unit,county,bunit,election)) or not (returned or accepted):
        raise ValueError("Unrecognized Maine absentee or geography schema: "+str((list(bc),list(uc))))
    crosswalk={}
    for row in units:
        key=row[unit].strip()
        name=row[county].strip()
        if key and name:
            if key in crosswalk and crosswalk[key]!=name:
                raise ValueError("Conflicting Maine unit-to-county mapping: "+key)
            crosswalk[key]=name
    totals=defaultdict(int)
    count=0
    metric=accepted or returned
    for row in ballots:
        if row[election].strip()!=ELECTION:
            continue
        key=row[bunit].strip()
        raw=row[metric].strip().replace(",","")
        if not raw or not raw.isdigit():
            raise ValueError("Invalid Maine 2026 "+metric+" value for unit "+key)
        if key not in crosswalk:
            raise ValueError("Unmapped Maine town: "+key)
        totals[crosswalk[key]]+=int(raw)
        count+=1
    if not count:
        raise ValueError("No 2026 general-election Maine absentee observations")
    return {"state":"ME","election":ELECTION,"source_url":SOURCE,
            "geography_url":UNITS,"credit":"Maine Political Data / Maine Policy Institute (CC BY 4.0)",
            "metric":metric,"reporting_label":"Partially reported",
            "town_party_rows":count,"county_count":len(totals),
            "total":sum(totals.values()),
            "counties":dict(sorted(totals.items())),
            "publication_approved":False}

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"ElectionHQ-2026-source-adapter/1.0"})
    with urllib.request.urlopen(req,timeout=45) as response:
        return list(csv.DictReader(io.StringIO(response.read().decode("utf-8-sig"))))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ballots",type=Path)
    p.add_argument("--units",type=Path)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    try:
        ballots=list(csv.DictReader(a.ballots.open())) if a.ballots else fetch(SOURCE)
        units=list(csv.DictReader(a.units.open())) if a.units else fetch(UNITS)
        result=aggregate(ballots,units)
    except (OSError,ValueError) as exc:
        result={"state":"ME","status":"source_unavailable_or_schema_review_required",
                "reason":str(exc)[:300],"source_url":SOURCE,"publication_approved":False}
    a.output.write_text(json.dumps(result,indent=2)+chr(10))
    print("Maine:",result.get("county_count",result["status"] if "status" in result else "unknown"))
if __name__=="__main__":
    main()
