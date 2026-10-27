#!/usr/bin/env python3
"""Fail-closed reconciliation of all 19 watchlist states across staged and missing feeds."""
import argparse
import json
from pathlib import Path
from audit_national_early_vote import WATCH
from audit_remaining_watchlist_county_sources import STATES as MISSING

def audit(readiness, discovery):
    if readiness.get("schema") != "electionhq-watchlist-readiness-v1" or readiness.get("publication_approved") is not False:
        raise ValueError("Invalid unapproved readiness matrix")
    if discovery.get("schema") != "electionhq-remaining-watchlist-source-discovery-v1" or discovery.get("publication_approved") is not False:
        raise ValueError("Invalid unapproved discovery report")
    rows=readiness.get("states")
    if not isinstance(rows,list) or len(rows)!=19 or set(r.get("state") for r in rows)!=set(WATCH):
        raise ValueError("Exactly 19 unique watchlist states required")
    discovered=discovery.get("states")
    if not isinstance(discovered,dict) or set(discovered)!=set(MISSING):
        raise ValueError("Exactly 11 unstaged states must be checked")
    staged={r["state"] for r in rows if r.get("county_staged") is True}
    if staged & set(MISSING):
        raise ValueError("Discovered state is also staged; source review must reconcile overlap")
    if staged | set(MISSING) != set(WATCH):
        raise ValueError("Coverage gap: each state must be staged or source-discovered")
    for row in rows:
        if row.get("county_publication_approved") is not False:
            raise ValueError("Unexpected publication approval")
        if row["state"] in MISSING:
            if row.get("county_ballots") is not None or row.get("county_reported") is not None:
                raise ValueError("Missing county source must not become zero or a fabricated subtotal")
            if discovered[row["state"]].get("publication_approved") is not False:
                raise ValueError("Discovery must remain unapproved")
        elif row.get("county_ballots") is None:
            raise ValueError("Staged county subtotal missing")
    return {"schema":"electionhq-nineteen-state-coverage-audit-v1",
            "publication_approved":False,"states_checked":len(rows),
            "staged_count":len(staged),"source_discovery_count":len(MISSING),
            "staged_states":sorted(staged),"discovery_states":sorted(MISSING),
            "county_values_imputed":False,"county_totals_added_to_statewide":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--readiness",required=True)
    p.add_argument("--discovery",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    target=Path(a.output).resolve()
    if target.is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Never publish internal audits to public election data")
    result=audit(json.loads(Path(a.readiness).read_text()),json.loads(Path(a.discovery).read_text()))
    target.write_text(json.dumps(result,indent=2)+"\n")
    print("Audited",result["states_checked"],"states:",result["staged_count"],"staged,",result["source_discovery_count"],"source discovery")
if __name__=="__main__":
    main()
