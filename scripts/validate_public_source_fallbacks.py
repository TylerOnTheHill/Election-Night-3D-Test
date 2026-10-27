#!/usr/bin/env python3
"""Validate secondary observations without silently promoting partial geography."""
import json
from pathlib import Path

EXPECTED={"AL","DC","MA","NH","NY"}
def validate(data):
    if data.get("schema")!="electionhq-public-source-fallbacks-v1":raise ValueError("Schema")
    rows=data.get("jurisdictions")
    if not isinstance(rows,list) or {r.get("state") for r in rows}!=EXPECTED or len(rows)!=len(EXPECTED):
        raise ValueError("Expected five unique missing jurisdictions")
    for r in rows:
        if r.get("eligible_for_national_aggregation") is not False:
            raise ValueError("Fallback not eligible for national aggregation: "+r["state"])
        if not str(r.get("source_url","")).startswith("https://"):raise ValueError("Source URL")
        if r.get("total") is not None:
            if type(r["total"])!=int or r["total"]<0:raise ValueError("Total")
            if not r.get("counts_through") or not r.get("coverage"):raise ValueError("Missing date or coverage")
            parts=[r.get("mail"),r.get("in_person")]
            if all(x is not None for x in parts) and sum(parts)!=r["total"]:
                raise ValueError("Ballot-mode mismatch")
    return {"fallback_jurisdictions":len(rows),"approved_national_additions":0}
if __name__=="__main__":
    d=json.loads(Path("data/early-vote/public-source-fallbacks.json").read_text())
    print(json.dumps(validate(d)))
