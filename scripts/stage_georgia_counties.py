#!/usr/bin/env python3
"""Stage 2026 Georgia accepted-ballot county aggregates; NEVER publish automatically.

Source: VoteGA county-totals.json, derived from GA Secretary of State files.
The statewide total is kept separate from county subtotal. Each run is a
replacement snapshot keyed by five-digit FIPS, not additive daily increments.
"""
import argparse
import json
import re
import urllib.request
from datetime import date
from pathlib import Path

SOURCE="https://raw.githubusercontent.com/Votega/ga-races-elections/main/early-vote/2026-general/county-totals.json"
CREDIT="Georgia Civic Data (georgiacivicdata.org, CC BY 4.0); Georgia Secretary of State absentee and early-voting files; distributed by VoteGA"
EXPECTED=159

def stage(doc):
    meta=doc.get("metadata",{})
    election=meta.get("election",{})
    if election!={"date":"2026-11-03","year":2026,"type":"general"}:
        raise ValueError("Not the 2026 Georgia general election")
    cutoff=meta.get("asOf")
    try:
        if date.fromisoformat(cutoff)>date(2026,11,3):
            raise ValueError("Future election cutoff")
    except (TypeError,ValueError) as e:
        raise ValueError("Invalid reporting cutoff") from e
    statewide=doc.get("statewide",{})
    statewide_total=statewide.get("ballots")
    if type(statewide_total)!=int or statewide_total<0:
        raise ValueError("Invalid statewide ballot total")
    rows=doc.get("counties")
    if not isinstance(rows,list) or len(rows)>EXPECTED:
        raise ValueError("Invalid Georgia county collection")
    counties=[]
    seen=set()
    for row in rows:
        fips=row.get("county_fips")
        if not isinstance(fips,str) or not re.fullmatch(r"13\d{3}",fips) or fips in seen:
            raise ValueError("Invalid/duplicate Georgia county FIPS")
        seen.add(fips)
        name=row.get("county")
        if not isinstance(name,str) or not name.strip():
            raise ValueError("Missing county name")
        if row.get("as_of")!=cutoff:
            raise ValueError("Mixed reporting cutoffs")
        total,early,mail=(row.get(k) for k in ("ballots","in_person","mail"))
        if any(type(x)!=int or x<0 for x in (total,early,mail)) or total!=early+mail:
            raise ValueError("Invalid county ballot method reconciliation")
        counties.append({"fips":fips,"name":name.strip(),"total":total,
            "mail":mail,"in_person":early,"file_as_of":cutoff,
            "source_url":SOURCE,"credit":CREDIT})
    counties.sort(key=lambda r:r["fips"])
    county_sum=sum(r["total"] for r in counties)
    if county_sum>statewide_total:
        raise ValueError("County totals exceed provider statewide total")
    reconciled=county_sum==statewide_total
    matching=len(counties)==EXPECTED and reconciled
    return {"schema":"electionhq-county-preview-v1","publication_approved":False,
        "review_required":True,"party_counts_mean":"not provided; no candidate vote inference",
        "states":{"GA":{"status":"candidate_pending_publication_approval",
            "provider":"VoteGA.org / Georgia Secretary of State",
            "credit":CREDIT,"provider_checked_at":meta.get("dataGeneratedAt"),
            "statewide_cutoff":cutoff,"census_geography_source":"Source-provided 5-digit Georgia county FIPS (Census cross-check pending)",
            "census_geography_url":"https://api.census.gov/data/2020/dec/pl",
            "county_count":len(counties),"geographic_count":EXPECTED,
            "coverage_complete":len(counties)==EXPECTED,
            "reporting_label":"Fully reported" if matching else "Partially reported",
            "statewide_reconciled":reconciled,"total":county_sum,
            "total_basis":"sum_of_reported_counties",
            "provider_statewide_total":statewide_total,
            "county_vs_provider_statewide_difference":county_sum-statewide_total,
            "counties":counties}}}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",help="Downloaded source JSON fixture (otherwise fetch live)")
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    target=Path(args.output).resolve()
    if target.is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Never write staging observations into public early-vote directory")
    if args.input:
        doc=json.loads(Path(args.input).read_text())
    else:
        with urllib.request.urlopen(urllib.request.Request(SOURCE,headers={"User-Agent":"ElectionHQ-county-aggregate-staging/1.0"}),timeout=30) as response:
            doc=json.load(response)
    result=stage(doc)
    target.write_text(json.dumps(result,indent=2)+"\n")
    state=result["states"]["GA"]
    print("Georgia staged for internal review:",state["county_count"],"counties;",state["reporting_label"])

if __name__=="__main__":
    main()
