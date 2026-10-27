#!/usr/bin/env python3
"""Join staged TX/NC county records to vendored Census-derived county GEOIDs.

No inferred identifiers: missing/ambiguous matches are fatal. Census API is
the authoritative geography crosswalk; turnout remains sourced to Call the Map.
"""
import argparse
import json
import pathlib
import re
import urllib.request
import urllib.parse
import time
import csv
import io
import zipfile

STATES = {"TX": "48", "NC": "37"}
API = "https://api.census.gov/data/2020/dec/pl"
GAZETTEER = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gazetteer_counties_national.zip"

def canonical(value):
    value = value.lower().replace("&", " and ")
    value = re.sub(r"\b(county|parish|borough)\b", "", value)
    return re.sub(r"[^a-z0-9]", "", value)

def crosswalk(code, census_rows, staged, geography_source="2020 Census PL 94-171 county geography API", geography_url=None):
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
    # Partial reporting is valid: retain only observed counties, never zero-fill.
    # Every reported county must still map uniquely to a real Census GEOID.
    return {**staged, "counties": output, "fips_verified": True,
            "coverage_complete": len(output) == len(lookup), "geographic_count": len(lookup), "reported_county_count": len(output), "census_geography_source":
            geography_source,
            "census_geography_url": geography_url or census_url(STATES[code]),
            "status": "staging_only_fips_and_coverage_verified"}

def census_url(state):
    return API + "?" + urllib.parse.urlencode({"get": "NAME", "for": "county:*", "in": "state:" + state})

def fetch_census(state):
    url = census_url(state)
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ElectionHQ-county-fips-audit/1.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read(3_000_000)
                content_type = response.headers.get("Content-Type", "")
                status = response.status
            try:
                return json.loads(raw)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ValueError(f"Census returned non-JSON (HTTP {status}, content-type {content_type!r}, first 250 bytes {raw[:250]!r})") from exc
        except (OSError, ValueError) as exc:
            last = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise ValueError(f"Census county geography unavailable for state {state}: {last}")

def fetch_gazetteer(state):
    req = urllib.request.Request(GAZETTEER, headers={"User-Agent": "ElectionHQ-county-fips-audit/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError("Census Gazetteer archive too large")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        files = [n for n in archive.namelist() if n.lower().endswith(".txt")]
        if len(files) != 1:
            raise ValueError("Unexpected Census Gazetteer archive layout")
        with archive.open(files[0]) as stream:
            records = list(csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"), delimiter="\t"))
    rows = [["NAME", "state", "county"]]
    for record in records:
        geoid = record.get("GEOID", "").strip()
        name = record.get("NAME", "").strip()
        if re.fullmatch(r"\d{5}", geoid) and geoid[:2] == state and name:
            rows.append([name, state, geoid[2:]])
    return rows

def fetch_vendored(code, reference_path="data/sources/tx-nc-county-fips-reference.json"):
    reference = json.loads(pathlib.Path(reference_path).read_text())
    entries = reference["states"][code]
    state = STATES[code]
    rows = [["NAME", "state", "county"]]
    for entry in entries:
        fips = entry["fips"]
        if not re.fullmatch(r"\d{5}", fips) or fips[:2] != state:
            raise ValueError("Invalid vendored GEOID")
        rows.append([entry["name"], state, fips[2:]])
    return rows, reference["source"]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", default="staging-county-pilots")
    p.add_argument("--output-dir", default="staging-county-pilots-fips")
    args = p.parse_args()
    out = pathlib.Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for code, state in STATES.items():
        staged = json.loads((pathlib.Path(args.input_dir) / (code + ".json")).read_text())
        census, reference_url = fetch_vendored(code)
        enriched = crosswalk(code, census, staged,
                             "Vendored Census-derived county FIPS mirror (2020 vintage not independently verified)",
                             reference_url)
        (out / (code + ".json")).write_text(json.dumps(enriched, indent=2) + "\n")
        print(code, len(enriched["counties"]), "counties matched to unique Census FIPS; STAGING ONLY")

if __name__ == "__main__":
    main()
