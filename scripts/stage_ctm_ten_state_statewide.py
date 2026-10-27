#!/usr/bin/env python3
"""Ingest credited current statewide early-vote snapshots for 10 unstaged states.

Never turn statewide totals into county totals. Never add overlapping providers.
"""
import argparse
import datetime as dt
import json
import urllib.request
from pathlib import Path

STATES=("AK","AZ","KS","ME","MI","MS","NE","NH","NV","OH")
BASE="https://www.callthemap.com/early-vote/data/"
def parse(code,data):
    if data.get("schema")!="ctm-early-vote-download-v1" or data.get("state")!=code:
        raise ValueError("Unexpected source schema or state")
    summary=data.get("summary") or {}
    total=summary.get("total")
    if type(total) is not int or total<0:
        return {"state":code,"status":"no_usable_statewide_total","total":None}
    if not summary.get("counts_through") or not summary.get("source_name"):
        raise ValueError("Missing source date or provenance")
    dt.date.fromisoformat(summary["counts_through"])
    county_rows=data.get("counties") or []
    return {"state":code,"status":"statewide_observed","total":total,
            "counts_through":summary["counts_through"],
            "checked_at":data.get("checked_at"),
            "mail":summary.get("mail"),"in_person":summary.get("in_person"),
            "source_name":summary["source_name"],"source_url":summary.get("source_url"),
            "credit":summary.get("credit") or data.get("credit"),
            "county_rows_available":len(county_rows),
            "county_staged":False,"county_ballots":None,
            "county_reporting_label":"Not reported","publication_approved":False}
def run(fetch):
    rows=[]
    for code in STATES:
        try:rows.append(parse(code,fetch(code)))
        except (OSError,ValueError,KeyError,TimeoutError) as exc:
            rows.append({"state":code,"status":"source_unavailable",
                         "reason":type(exc).__name__,"total":None,
                         "county_staged":False,"publication_approved":False})
    return {"schema":"electionhq-ten-state-credited-statewide-review-v1",
            "publication_approved":False,"county_totals_imputed":False,
            "statewide_totals_added_to_counties":False,
            "source":"Call the Map (callthemap.com/early-vote)",
            "states":{x["state"]:x for x in rows}}
def fetch(code):
    req=urllib.request.Request(BASE+code+".json",
        headers={"User-Agent":"ElectionHQ-statewide-review/1.0"})
    with urllib.request.urlopen(req,timeout=25) as response:
        return json.load(response)
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();result=run(fetch)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Credited statewide observations:",sum(x["status"]=="statewide_observed" for x in result["states"].values()),"of",len(STATES))
if __name__=="__main__":main()
