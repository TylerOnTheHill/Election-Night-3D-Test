#!/usr/bin/env python3
"""Join staged TX/NC county records to Census 2020 PL 94-171 county GEOIDs.

No inferred identifiers: missing/ambiguous matches are fatal. Census API is
the authoritative geography crosswalk; turnout remains sourced to Call the Map.
"""
import argparse
import json
import pathlib
import re
import urllib.request

STATES = {"TX": "48", "NC": "37"}
API = "https://api.census.gov/data/2020/dec/pl?get=NAME&for=county:*&in=state:"

def canonical(value):
    value = value.lower().replace("&", " and ")
    value = re.sub(r"\b(county|parish|borough)\b", "", value)
    return re.sub(r"[^a-z0-9]", "", value)

def crosswalk(code, census_rows, staged):
    if code not in STATES or staged.get("state") != code or staged.get("status") != "staging_only_not_approved_for_publication":
        raise ValueError("Unexpected staged state or publication status")
    if not isinstance(census_rows, list) or not census_rows or census_rows[0] != ["NAME", "state", "county"]:
        raise ValueError("Unexpected Census API response")
    lookup = {}
    geoid_seen = set()
    for name, state, county in census_rows[1:]:
        if state != STATES[code] or not re.fullmatch(r"\d{3}", county):
            raise ValueError("Invalid Census geography")
        geoid = state + county
        if geoid in geoid_seen:
            raise ValueError("Duplicate Census GEOID")
        geoid_seen.add(geoid)
        key = canonical(name.split(",", 1)[0])
        if key in lookup:
            raise ValueError("Ambiguous Census county name")
        lookup[key] = geoid
    if len(lookup) != {"TX": 254, "NC": 100}[code]:
        raise ValueError("Census geographic count unexpected")
    output = []
    used = set()
    for row in staged["counties"]:
        key = canonical(row["county"])
        if key not in lookup or key in used:
            raise ValueError("Unmatched/duplicate county: " + row["county"])
        used.add(key)
        enriched = dict(row)
        enriched["fips"] = lookup[key]
        output.append(enriched)
    if len(output) != len(lookup) or used != set(lookup):
        raise ValueError("Staged county coverage incomplete; no zero-filling")
    return {**staged, "counties": output, "fips_verified": True,
            "coverage_complete": True, "census_geography_source":
            "2020 Census PL 94-171 county geography API",
            "census_geography_url": API + STATES[code],
            "status": "staging_only_fips_and_coverage_verified"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", default="staging-county-pilots")
    p.add_argument("--output-dir", default="staging-county-pilots-fips")
    args = p.parse_args()
    out = pathlib.Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for code, state in STATES.items():
        staged = json.loads((pathlib.Path(args.input_dir) / (code + ".json")).read_text())
        req = urllib.request.Request(API + state, headers={"User-Agent": "ElectionHQ-county-fips-audit/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            census = json.load(response)
        enriched = crosswalk(code, census, staged)
        (out / (code + ".json")).write_text(json.dumps(enriched, indent=2) + "\n")
        print(code, len(enriched["counties"]), "counties matched to unique Census FIPS; STAGING ONLY")

if __name__ == "__main__":
    main()
