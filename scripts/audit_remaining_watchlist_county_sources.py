#!/usr/bin/env python3
"""Discover actual county observations in the remaining 12 battleground states.

This is SOURCE DISCOVERY, not FIPS verification or publication. Never fill
missing counties with zero, and never promote provider totals to verified data.
"""
import argparse
import json
import urllib.request
from pathlib import Path
from stage_callthemap_county_pilots import BASE

STATES=("AK","AZ","GA","KS","ME","MI","MN","MS","NE","NV","NH","OH")

def inspect(code,payload):
    if code not in STATES:
        raise ValueError("Not a remaining watchlist state: "+code)
    if payload.get("schema")!="ctm-early-vote-download-v1" or payload.get("state")!=code:
        raise ValueError("Provider state/schema mismatch for "+code)
    if not payload.get("credit") or not payload.get("license"):
        raise ValueError("Missing provider credit/license for "+code)
    rows=payload.get("counties")
    if not isinstance(rows,list):
        raise ValueError("Missing county collection for "+code)
    observed=[]
    names=set()
    for row in rows:
        if row.get("state")!=code or not isinstance(row.get("county"),str) or not row["county"].strip():
            raise ValueError("Invalid county jurisdiction for "+code)
        name=row["county"].strip()
        if name.casefold() in names:
            raise ValueError("Duplicate county name for "+code+": "+name)
        names.add(name.casefold())
        count=row.get("total")
        if count is None:
            continue
        if type(count)!=int or count<0:
            raise ValueError("Invalid county count for "+code)
        if not str(row.get("source_url","")).startswith("https://") or not row.get("credit"):
            raise ValueError("Missing observation provenance for "+code+": "+name)
        observed.append(row)
    cutoffs=sorted({row["file_as_of"] for row in observed if row.get("file_as_of")})
    return {"state":code,"provider_county_rows":len(rows),
            "county_rows_with_observed_totals":len(observed),
            "observed_county_ballots":sum(row["total"] for row in observed),
            "counties_with_source_cutoff":sum(bool(row.get("file_as_of")) for row in observed),
            "distinct_county_cutoffs":cutoffs,
            "source_urls":sorted({row["source_url"] for row in observed}),
            "provider_statewide_total":(payload.get("summary") or {}).get("total"),
            "provider_checked_at":payload.get("checked_at"),
            "ready_for_fips_crosswalk":bool(observed),
            "fips_verified":False,"freshness_verified":False,
            "publication_approved":False,
            "status":"source_discovery_only"}

def discover(payloads):
    states={code:inspect(code,payloads[code]) for code in STATES}
    return {"schema":"electionhq-remaining-watchlist-source-discovery-v1",
            "publication_approved":False,
            "states":states,
            "states_with_county_observations":[code for code in STATES if states[code]["ready_for_fips_crosswalk"]]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir")
    p.add_argument("--output",required=True)
    args=p.parse_args()
    target=Path(args.output)
    if target.resolve().is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Do not write unapproved observations into public data")
    payloads={}
    for code in STATES:
        if args.input_dir:
            payloads[code]=json.loads((Path(args.input_dir)/(code+".json")).read_text())
        else:
            request=urllib.request.Request(BASE+code+".json",headers={"User-Agent":"ElectionHQ-county-source-discovery/1.0"})
            with urllib.request.urlopen(request,timeout=30) as response:
                payloads[code]=json.load(response)
    report=discover(payloads)
    target.write_text(json.dumps(report,indent=2)+"\n")
    print("County observations found in:",", ".join(report["states_with_county_observations"]) or "none")
    print("SOURCE DISCOVERY ONLY — no county publication or FIPS verification")

if __name__=="__main__":
    main()
