#!/usr/bin/env python3
"""Join existing eight-state candidates with non-redistributable UF observations.

This internal diagnostic cannot be passed to the publication validator or
dashboard publisher: the UF source license restricts redistribution.
"""
import argparse
import json
from pathlib import Path
from validate_county_publication_candidate import validate

def merge(approved_for_review, restricted):
    validate(approved_for_review)
    if restricted.get("schema") != "electionhq-county-preview-v1" or restricted.get("redistribution_authorized") is not False:
        raise ValueError("Expected explicitly restricted UF county candidate")
    result = {}
    for code, state in approved_for_review["states"].items():
        result[code] = {"source_class": "standard_staging", "county_count": state["county_count"],
                        "total": state["total"], "reporting_label": state["reporting_label"],
                        "county_fips": [r["fips"] for r in state["counties"]]}
    for code, state in restricted["states"].items():
        if code in result:
            # The existing state candidate is the preferred source; do not sum.
            continue
        rows = state["counties"]
        if len({r["fips"] for r in rows}) != len(rows) or sum(r["total"] for r in rows) != state["total"]:
            raise ValueError(code + ": restricted source totals or FIPS invalid")
        result[code] = {"source_class": "restricted_uf_internal_only",
                        "county_count": len(rows), "total": state["total"],
                        "reporting_label": state["reporting_label"],
                        "county_fips": [r["fips"] for r in rows]}
    return {"schema": "electionhq-internal-nineteen-state-coverage-v1",
            "redistribution_authorized": False, "publication_approved": False,
            "states_with_observations": len(result),
            "states": dict(sorted(result.items())),
            "missing_states": sorted(set(("AK","AZ","FL","GA","IA","KS","ME","MI","MN","MS","NC","NE","NH","NV","OH","SC","TX","VA","WI"))-set(result)),
            "county_totals_added_across_sources": False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--standard",required=True)
    p.add_argument("--restricted",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    target=Path(a.output).resolve()
    if target.is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Internal coverage diagnostics cannot enter public feed")
    result=merge(json.loads(Path(a.standard).read_text()),json.loads(Path(a.restricted).read_text()))
    target.write_text(json.dumps(result,indent=2)+"\n")
    print("Internal combined county coverage:",result["states_with_observations"],"/19; missing:",result["missing_states"])

if __name__=="__main__":
    main()
