#!/usr/bin/env python3
"""Stage VA/IA/WI/SC Call the Map county observations with verified Census GEOIDs.

No publication. Only reported nonnegative county totals are included; missing
county totals are unknown, not zero. A new snapshot replaces observations by FIPS.
"""
import argparse
import json
import urllib.request
from pathlib import Path
from stage_callthemap_county_pilots import BASE
from verify_tx_nc_fips import canonical, fetch_census, fetch_gazetteer
from validate_county_publication_candidate import validate

STATES={"VA":("51",133),"IA":("19",99),"WI":("55",72),"SC":("45",46)}

def stage(code,payload,census):
    if code not in STATES:
        raise ValueError("Unsupported expansion state")
    prefix,expected=STATES[code]
    if payload.get("schema")!="ctm-early-vote-download-v1" or payload.get("state")!=code:
        raise ValueError("Unexpected provider schema/state")
    if not payload.get("credit") or not payload.get("license"):
        raise ValueError("Missing provider attribution")
    if not isinstance(census,list) or census[:1]!=[["NAME","state","county"]]:
        raise ValueError("Invalid Census geography")
    lookup={}
    for name,state,county in census[1:]:
        if state!=prefix or len(county)!=3 or not county.isdigit():
            raise ValueError("Invalid Census GEOID")
        key=canonical(name.split(",",1)[0])
        if key in lookup:
            raise ValueError("Ambiguous county-equivalent Census name")
        lookup[key]=prefix+county
    if len(lookup)!=expected or len(set(lookup.values()))!=expected:
        raise ValueError("Unexpected Census county-equivalent count")
    rows=payload.get("counties")
    if not isinstance(rows,list):
        raise ValueError("Missing provider counties")
    observations={}
    for row in rows:
        if row.get("state")!=code or not isinstance(row.get("county"),str):
            raise ValueError("Invalid county row")
        key=canonical(row["county"])
        if key not in lookup:
            raise ValueError("County does not match Census county-equivalent: "+row["county"])
        fips=lookup[key]
        if fips in observations:
            raise ValueError("Duplicate county observation")
        total=row.get("total")
        if total is None:
            continue
        if type(total)!=int or total<0:
            raise ValueError("Invalid county total")
        source=row.get("source_url")
        credit=row.get("credit")
        if not isinstance(source,str) or not source.startswith("https://") or not credit:
            raise ValueError("Missing county provenance")
        cutoff=row.get("file_as_of")
        if cutoff is not None and (not isinstance(cutoff,str) or not cutoff.strip()):
            raise ValueError("Invalid county reporting cutoff")
        observations[fips]={"fips":fips,"name":row["county"],"total":total,
            "mail":row.get("mail"),"in_person":row.get("in_person"),
            "registered_dem":row.get("dem"),"registered_rep":row.get("rep"),
            "registered_unaffiliated_other":row.get("unaffiliated_other"),
            "file_as_of":cutoff,"source_url":source,"credit":credit}
    if not observations:
        return None
    counties=sorted(observations.values(),key=lambda r:r["fips"])
    summary=payload.get("summary") or {}
    statewide=summary.get("total")
    if statewide is not None and (type(statewide)!=int or statewide<0):
        raise ValueError("Invalid provider statewide total")
    total=sum(r["total"] for r in counties)
    count=len(counties)
    return {"status":"candidate_pending_publication_approval",
        "provider":"Call the Map","credit":payload["credit"],
        "provider_checked_at":payload.get("checked_at"),
        "statewide_cutoff":summary.get("file_as_of"),
        "census_geography_source":"2020 Census county GEOIDs",
        "census_geography_url":"https://api.census.gov/data/2020/dec/pl",
        "county_count":count,"geographic_count":expected,
        "coverage_complete":count==expected,
        "reporting_label":"Fully reported" if count==expected else "Partially reported",
        "total":total,"total_basis":"sum_of_reported_counties",
        "provider_statewide_total":statewide,
        "county_vs_provider_statewide_difference":total-statewide if statewide is not None else None,
        "counties":counties}

def build(payloads,census_by_state):
    states={}
    unavailable=[]
    for code in STATES:
        result=stage(code,payloads[code],census_by_state[code])
        if result is None:
            unavailable.append(code)
        else:
            states[code]=result
    if not states:
        return {"schema":"electionhq-county-preview-v1","publication_approved":False,
                "review_required":True,"states":{},"states_without_county_observations":unavailable}
    candidate={"schema":"electionhq-county-preview-v1","publication_approved":False,
        "review_required":True,"party_counts_mean":"voter registration, never candidate votes",
        "states":states,"states_without_county_observations":unavailable}
    validate(candidate)
    return candidate

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",help="Local provider JSON snapshots instead of live downloads")
    p.add_argument("--census-dir",help="Local Census JSON crosswalks instead of Census API")
    p.add_argument("--output",default="watchlist-county-candidate-unapproved.json")
    args=p.parse_args()
    if Path(args.output).as_posix().lstrip("./").startswith("data/early-vote/"):
        raise ValueError("Never write unapproved data to public feed")
    payloads={}
    census={}
    for code,(prefix,_) in STATES.items():
        if args.input_dir:
            payloads[code]=json.loads((Path(args.input_dir)/(code+".json")).read_text())
        else:
            req=urllib.request.Request(BASE+code+".json",headers={"User-Agent":"ElectionHQ-watchlist-staging/1.0"})
            with urllib.request.urlopen(req,timeout=30) as response:
                payloads[code]=json.load(response)
        if args.census_dir:
            census[code]=json.loads((Path(args.census_dir)/(code+".json")).read_text())
        else:
            try:
                census[code]=fetch_census(prefix)
            except (OSError,ValueError) as exc:
                print(f"{code}: Census API unavailable ({exc}); trying official Census Gazetteer")
                census[code]=fetch_gazetteer(prefix)
    candidate=build(payloads,census)
    Path(args.output).write_text(json.dumps(candidate,indent=2)+"\n")
    print("Staged (unapproved):",", ".join(candidate["states"]) or "no county observations",
          "; unavailable:",", ".join(candidate["states_without_county_observations"]))

if __name__=="__main__":
    main()
