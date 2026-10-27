#!/usr/bin/env python3
"""Fail-closed source lead review. Leads are not eligible for county publication."""
import json
from pathlib import Path
from urllib.parse import urlparse
from audit_remaining_watchlist_county_sources import STATES

STATUSES={"official_county_dashboard_identified","secondary_county_dashboard_identified","official_portal_identified_not_early_vote_feed"}

def validate(doc):
    if doc.get("schema")!="electionhq-official-county-source-leads-v1" or doc.get("publication_approved") is not False:
        raise ValueError("Invalid unapproved source lead registry")
    rows=doc.get("leads")
    if not isinstance(rows,list) or not rows:
        raise ValueError("Missing source leads")
    seen=set()
    for row in rows:
        if row.get("state") not in (*STATES,"GA") or row.get("status") not in STATUSES:
            raise ValueError("Unknown state or source status")
        if not row.get("source_name") or not row.get("evidence"):
            raise ValueError("Missing provenance")
        for key in ("source_url","evidence_url"):
            url=urlparse(row.get(key,""))
            if url.scheme!="https" or not url.netloc:
                raise ValueError("Source must use HTTPS")
        key=(row["state"],row["source_url"])
        if key in seen:
            raise ValueError("Duplicate source lead")
        seen.add(key)
        if row.get("machine_readable_endpoint_verified") is not False or row.get("county_ballot_values_verified") is not False:
            raise ValueError("Source discovery must not imply verified ingestible county ballots")
    return {"leads":len(rows),"states":sorted({r["state"] for r in rows}),"approved":False}

if __name__=="__main__":
    path=Path("data/sources/remaining-watchlist-official-source-leads.json")
    print(json.dumps(validate(json.loads(path.read_text()))))
