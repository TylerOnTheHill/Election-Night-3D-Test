#!/usr/bin/env python3
"""Fail-closed checks for ElectionHQ's attributed national early-vote snapshot."""
import argparse
import datetime as dt
import json
from pathlib import Path

def validate(doc):
    if doc.get("schema")!="ctm-early-vote-download-v1":raise ValueError("Unsupported national schema")
    if not doc.get("credit") or not doc.get("license"):raise ValueError("Missing source credit or license")
    rows=doc.get("states")
    if not isinstance(rows,list) or not rows:raise ValueError("Missing reporting states")
    seen=set()
    total=0
    dates=[]
    split_count=0
    for row in rows:
        code=row.get("state")
        if not isinstance(code,str) or len(code)!=2 or not code.isalpha() or code in seen:
            raise ValueError("Invalid or duplicate state code")
        seen.add(code)
        count=row.get("total")
        if type(count)!=int or count<0:raise ValueError("Invalid state total for "+code)
        total+=count
        for key in ("mail","in_person"):
            value=row.get(key)
            if value is not None and (type(value)!=int or value<0):
                raise ValueError("Invalid "+key+" for "+code)
        mail,person=row.get("mail"),row.get("in_person")
        if mail is not None and person is not None:
            if mail+person!=count:raise ValueError("Mail and in-person sum mismatch for "+code)
            split_count+=1
        elif mail is not None and mail>count or person is not None and person>count:
            raise ValueError("Reported component exceeds total for "+code)
        if not row.get("source_name") or not str(row.get("source_url","")).startswith("https://"):
            raise ValueError("Missing source for "+code)
        date=row.get("counts_through")
        if not isinstance(date,str):raise ValueError("Missing cutoff for "+code)
        dt.date.fromisoformat(date)
        dates.append(date)
    national=doc.get("national")
    if not isinstance(national,dict) or national.get("total")!=total:
        raise ValueError("National total does not equal sum of reporting states")
    if national.get("states_counted")!=len(rows):
        raise ValueError("National reporting-state count mismatch")
    cutoffs=national.get("counts_through") or {}
    if cutoffs.get("first")!=min(dates) or cutoffs.get("last")!=max(dates):
        raise ValueError("National reporting date range mismatch")
    if len(seen)>51:raise ValueError("Too many states")
    return {"schema":"electionhq-national-source-audit-v1","status":"valid_partial_reporting",
            "publication_approved":False,"reporting_states":len(rows),
            "reported_ballots":total,"states_with_full_mode_split":split_count,
            "earliest_state_cutoff":min(dates),"latest_state_cutoff":max(dates),
            "source_credit":doc["credit"],"limitations":["Partial state coverage","State reporting dates vary","Party registration is not a candidate vote"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/early-vote/US.json")
    p.add_argument("--report",default="data/early-vote/national-source-audit.json")
    a=p.parse_args()
    result=validate(json.loads(Path(a.input).read_text()))
    Path(a.report).parent.mkdir(parents=True,exist_ok=True)
    Path(a.report).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
