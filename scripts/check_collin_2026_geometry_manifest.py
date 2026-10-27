#!/usr/bin/env python3
"""Fail-closed approval gate for Texas local geography metadata.

This checks *documented attestations*, not the truth of those attestations.
A human/source audit must still verify the referenced official files.
"""
import argparse
import json
from pathlib import Path

def assess(m):
    required=("county_fips","election_date","geometry_source_url","boundary_approval_url",
              "geometry_effective_date","geometry_vintage","downloaded_at")
    missing=[k for k in required if not isinstance(m.get(k),str) or not m[k].strip()]
    if missing: raise ValueError("Missing provenance: "+", ".join(missing))
    if m["county_fips"]!="48085" or m["election_date"]!="2026-11-03":
        raise ValueError("Manifest must describe Collin County November 2026")
    for k in ("geometry_source_url","boundary_approval_url"):
        if not m[k].startswith("https://"):raise ValueError("Source URL must be HTTPS")
    flags=("county_confirmed_for_2026_general","precinct_ids_reconciled",
           "full_geometry_coverage_verified","source_use_permitted")
    return {"schema":"electionhq-collin-geography-gate-v1",
            "publication_approved":False,
            "eligible_for_staging_join":all(m.get(k) is True for k in flags),
            "missing_attestations":[k for k in flags if m.get(k) is not True],
            "geometry_vintage":m["geometry_vintage"],
            "source_url":m["geometry_source_url"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=assess(json.loads(Path(a.manifest).read_text()))
    Path(a.output).write_text(json.dumps(result,indent=2)+"\n")
    print(result["schema"],"staging join eligible:",result["eligible_for_staging_join"])
    if not result["eligible_for_staging_join"]:raise SystemExit(2)

if __name__=="__main__":main()
