#!/usr/bin/env python3
"""One fail-closed 19-state readiness matrix, including partial county staging.

Never promotes staging to production or adds county counts to statewide counts.
"""
import argparse
import json
from pathlib import Path
from audit_national_early_vote import WATCH, audit
from validate_county_publication_candidate import validate

def build(national, candidates=(), leads=None):
    national_audit=audit(national)
    national_rows={row["state"]:row for row in national_audit["watchlist_states"]}
    county={}
    for candidate in candidates:
        validate(candidate)
        for code, state in candidate["states"].items():
            if code in county:
                raise ValueError("Duplicate staged state; snapshots must not be summed: "+code)
            if code not in WATCH:
                raise ValueError("Non-watchlist county candidate: "+code)
            county[code]=state
    source_leads={}
    if leads is not None:
        from validate_official_county_source_leads import validate as validate_leads
        validate_leads(leads)
        for row in leads["leads"]:
            source_leads.setdefault(row["state"],[]).append({"name":row["source_name"],"status":row["status"]})
    states=[]
    for code in WATCH:
        statewide=national_rows[code]
        staged=county.get(code)
        states.append({"state":code,
            "statewide_reporting":statewide["reported"],
            "statewide_ballots":statewide["ballots"],
            "statewide_cutoff":statewide["cutoff"],
            "statewide_source_url":statewide["source_url"],
            "county_staged":staged is not None,
            "county_reported":staged["county_count"] if staged else None,
            "county_expected":staged["geographic_count"] if staged else None,
            "county_ballots":staged["total"] if staged else None,
            "county_reporting_label":staged["reporting_label"] if staged else "Not available",
            "county_cutoff":staged.get("statewide_cutoff") if staged else None,
            "county_reconciled_to_own_provider":staged.get("statewide_reconciled") if staged else None,
            "county_publication_approved":False,
            "source_leads":source_leads.get(code,[])})
    return {"schema":"electionhq-watchlist-readiness-v1",
        "publication_approved":False,"states_expected":19,
        "statewide_reporting_count":sum(s["statewide_reporting"] for s in states),
        "county_staging_count":sum(s["county_staged"] for s in states),
        "states":states,
        "county_totals_added_to_statewide":False,
        "missing_counts_treated_as_zero":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--national",default="data/early-vote/US.json")
    p.add_argument("--candidate",action="append",default=[])
    p.add_argument("--leads",default="data/sources/remaining-watchlist-official-source-leads.json")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    target=Path(a.output).resolve()
    if target.is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Readiness reports are staging artifacts, not public vote feeds")
    result=build(json.loads(Path(a.national).read_text()),
        [json.loads(Path(f).read_text()) for f in a.candidate],
        json.loads(Path(a.leads).read_text()))
    target.write_text(json.dumps(result,indent=2)+"\n")
    print(f'{result["statewide_reporting_count"]}/19 statewide; {result["county_staging_count"]}/19 county staged; publication unchanged')

if __name__=="__main__":
    main()
