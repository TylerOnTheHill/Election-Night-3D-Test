#!/usr/bin/env python3
"""Audit live expansion-state county totals without authorizing publication.

Geographic coverage and statewide reconciliation are separate checks.
A mismatch is review-required, not a reason to discard valid county observations.
"""
import argparse
import json
from pathlib import Path

def audit(candidate):
    if candidate.get("publication_approved") is not False or candidate.get("review_required") is not True:
        raise ValueError("Expected an unapproved review candidate")
    result={}
    for code,state in sorted(candidate.get("states",{}).items()):
        county_total=sum(row["total"] for row in state["counties"])
        statewide=state.get("provider_statewide_total")
        if county_total!=state["total"]:
            raise ValueError(f"{code}: invalid county aggregation")
        difference=None if statewide is None else county_total-statewide
        county_cutoffs=sorted({str(row["file_as_of"]) for row in state["counties"] if row.get("file_as_of")})
        statewide_cutoff=state.get("statewide_cutoff")
        county_cutoff_relation=("unknown" if not county_cutoffs or not statewide_cutoff else
            "matching" if len(county_cutoffs)==1 and county_cutoffs[0]==statewide_cutoff else
            "county_older" if county_cutoffs[-1]<statewide_cutoff else
            "county_newer" if county_cutoffs[0]>statewide_cutoff else "mixed")
        result[code]={
            "reporting_label":state["reporting_label"],
            "geographic_coverage":f'{len(state["counties"])}/{state["geographic_count"]}',
            "county_total":county_total,
            "provider_statewide_total":statewide,
            "difference":difference,
            "county_vs_statewide_cutoff":county_cutoff_relation,
            "reconciliation_status":("unavailable" if difference is None else
                "matching" if difference==0 else
                "same_cutoff_unreconciled" if county_cutoff_relation=="matching" else
                "different_cutoffs_or_unknown"),
            "statewide_cutoff":statewide_cutoff,
            "distinct_county_cutoffs":county_cutoffs,
            "county_cutoff_missing":sum(not row.get("file_as_of") for row in state["counties"]),
            "source_urls":sorted({row["source_url"] for row in state["counties"]}),
            "reconciled":difference==0 if difference is not None else False,
            "freshness_verified":False,
            "publication_approved":False,
            "review_required":True,
        }
    return {"schema":"electionhq-watchlist-reconciliation-audit-v1",
            "status":"review_only_not_approved_for_publication","states":result}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidate",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    report=audit(json.loads(Path(args.candidate).read_text()))
    Path(args.output).write_text(json.dumps(report,indent=2)+"\n")
    for code,state in report["states"].items():
        print(f'{code}: {state["geographic_coverage"]} counties, {state["reporting_label"]}, difference={state["difference"]}, county cutoffs={len(state["distinct_county_cutoffs"])}; NOT APPROVED')

if __name__=="__main__":
    main()
