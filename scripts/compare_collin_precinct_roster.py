#!/usr/bin/env python3
"""Compare a vetted November general-election precinct ID roster with TLC primary geometry.

No voter names, addresses or roster PII are needed: one precinct ID per line.
A matching identifier set does not certify that boundaries are unchanged.
"""
import argparse
import json
from pathlib import Path

def compare(geometry,roster_ids):
    if geometry.get("type")!="FeatureCollection" or not isinstance(geometry.get("features"),list):
        raise ValueError("Expected GeoJSON FeatureCollection")
    geo_ids=[f.get("properties",{}).get("area_id") for f in geometry["features"]]
    if not geo_ids or any(not isinstance(x,str) or not x.strip() for x in geo_ids):
        raise ValueError("Missing geometry precinct IDs")
    if len(set(geo_ids))!=len(geo_ids):raise ValueError("Duplicate geometry precinct ID")
    roster=[x.strip() for x in roster_ids if x.strip() and not x.lstrip().startswith("#")]
    if not roster or any(not x or any(c.isspace() for c in x) for x in roster):
        raise ValueError("Invalid precinct ID roster")
    if len(set(roster))!=len(roster):raise ValueError("Duplicate roster precinct ID")
    a,b=set(geo_ids),set(roster)
    return {"schema":"electionhq-collin-2026-primary-vs-general-id-audit-v1",
            "publication_approved":False,"boundary_equivalence_verified":False,
            "primary_geometry_precincts":len(a),"general_roster_precincts":len(b),
            "id_sets_match":a==b,"missing_from_primary_geometry":sorted(b-a),
            "missing_from_general_roster":sorted(a-b),
            "status":"identifiers_match_boundaries_still_unverified" if a==b else "precinct_identifiers_differ_requires_review"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--geometry",required=True)
    p.add_argument("--general-roster-ids",required=True,help="Text file of non-PII precinct IDs, one per line")
    p.add_argument("--source-url",required=True)
    p.add_argument("--report",required=True)
    a=p.parse_args()
    if not a.source_url.startswith("https://"):raise SystemExit("Official roster source URL required")
    result=compare(json.loads(Path(a.geometry).read_text()),Path(a.general_roster_ids).read_text().splitlines())
    result["general_roster_source_url"]=a.source_url
    Path(a.report).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if not result["id_sets_match"]:raise SystemExit(2)
if __name__=="__main__":main()
