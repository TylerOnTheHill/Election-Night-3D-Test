#!/usr/bin/env python3
"""Discover UF Election Lab 2026 county observations across 11 states in parallel.

UF Election Lab data is CC BY-NC-ND 4.0. This output is a restricted
internal source-review artifact; do not redistribute its data or publish it.
County measures are NOT additive unless their definitions explicitly permit it.
"""
import argparse
import csv
import io
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from audit_remaining_watchlist_county_sources import STATES

BASE = "https://election.lab.ufl.edu/data-downloads/earlyvote/2026/"
CREDIT = "University of Florida Election Lab (2026 early vote; CC BY-NC-ND 4.0)"

def parse(code, raw):
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if not rows:
        return {"state":code, "status":"no_rows", "rows":0, "columns":[]}
    columns = list(rows[0])
    county_key = next((c for c in ("county","County","COUNTY") if c in columns), None)
    if not county_key:
        return {"state":code,"status":"county_column_missing","rows":len(rows),"columns":columns}
    # Use only explicitly named cumulative cast-ballot metrics. Never add
    # returned mail and in-person when 'voted_total' already includes both.
    candidates = ("voted_all", "voted_total")
    metric = next((m for m in candidates if m in columns), None)
    if metric is None:
        return {"state":code,"status":"metric_mapping_required","rows":len(rows),
                "columns":columns,"sample_county_names":[r.get(county_key) for r in rows[:4]]}
    # Maine's county file is actually a municipality/district table; its
    # "county" column contains town names. Do not mislabel towns as counties.
    if code == "ME":
        return {"state":code,"status":"municipal_rows_not_counties",
                "rows":len(rows),"columns":columns,
                "reason":"County-labelled CSV contains municipal/district observations; county crosswalk needed"}
    observations = []
    seen = set()
    for row in rows:
        name = (row.get(county_key) or "").strip()
        value = (row.get(metric) or "").replace(",","").strip()
        if not name or value in ("", "NA", "N/A", "-"):
            continue
        if not value.isdigit():
            raise ValueError(code+": invalid county ballot metric for "+name)
        key = name.casefold()
        if key in seen:
            raise ValueError(code+": duplicate county "+name)
        seen.add(key)
        observations.append({"county":name,"ballots":int(value)})
    return {"state":code,"status":"observations_for_review" if observations else "no_observed_totals",
            "rows":len(rows),"columns":columns,"metric":metric,
            "observations":observations,"source_url":BASE+code+"_county.csv",
            "credit":CREDIT,"license":"CC BY-NC-ND 4.0",
            "publication_approved":False}

def to_internal_candidate(review, geojson):
    """Build a restricted, non-publication FIPS-matched candidate from UF review."""
    from stage_remaining_eleven_counties import GEOIDS, geography
    from verify_tx_nc_fips import canonical
    states = {}
    gaps = {}
    for code in STATES:
        source = review["states"][code]
        if source["status"] != "observations_for_review":
            gaps[code] = source["status"]
            continue
        prefix, expected = GEOIDS[code]
        crosswalk = geography(geojson, prefix)
        names = {}
        for name, st, county in crosswalk[1:]:
            key = canonical(name)
            if key in names:
                raise ValueError(code+": ambiguous geographic name "+name)
            names[key] = st + county
        if len(names) != expected:
            gaps[code] = "Census geography count mismatch"
            continue
        observations = []
        for row in source["observations"]:
            key = canonical(row["county"])
            if key not in names:
                raise ValueError(code+": UF county cannot match GEOID: "+row["county"])
            observations.append({"fips":names[key],"name":row["county"],
                                 "total":row["ballots"],"file_as_of":None,
                                 "source_url":source["source_url"],"credit":CREDIT})
        if len(set(row["fips"] for row in observations)) != len(observations):
            raise ValueError(code+": duplicate county GEOID")
        if not observations:
            gaps[code] = "No observed county ballots"
            continue
        states[code] = {"status":"restricted_source_review_only",
                        "provider":"University of Florida Election Lab",
                        "credit":CREDIT,"license":"CC BY-NC-ND 4.0",
                        "county_count":len(observations),"geographic_count":expected,
                        "coverage_complete":len(observations)==expected,
                        "reporting_label":"Partially reported",
                        "statewide_reconciled":False,
                        "total":sum(row["total"] for row in observations),
                        "total_basis":"sum_of_reported_counties",
                        "counties":sorted(observations,key=lambda row:row["fips"])}
    return {"schema":"electionhq-county-preview-v1",
            "publication_approved":False,"redistribution_authorized":False,
            "review_required":True,"states":states,
            "states_without_county_observations":sorted(gaps)}, gaps

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",type=Path)
    p.add_argument("--output",type=Path,default=Path("uf-eleven-county-source-review.json"))
    p.add_argument("--candidate-output",type=Path)
    a=p.parse_args()
    if a.output.resolve().is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Internal source review cannot be a public feed")
    def fetch(code):
        if a.input_dir:
            return (a.input_dir/(code+"_county.csv")).read_bytes()
        req=urllib.request.Request(BASE+code+"_county.csv",headers={"User-Agent":"ElectionHQ-source-review/1.0"})
        with urllib.request.urlopen(req,timeout=35) as response:
            return response.read(8_000_001)
    results={}
    with ThreadPoolExecutor(max_workers=11) as pool:
        jobs={pool.submit(fetch,code):code for code in STATES}
        for future in as_completed(jobs):
            code=jobs[future]
            try:
                raw=future.result()
                if len(raw)>8_000_000:
                    raise ValueError("File exceeds review size limit")
                results[code]=parse(code,raw)
            except (OSError,ValueError,UnicodeError) as exc:
                results[code]={"state":code,"status":"source_unavailable_or_invalid",
                               "reason":str(exc),"publication_approved":False}
    output={"schema":"electionhq-uf-eleven-county-source-review-v1",
            "license":"CC BY-NC-ND 4.0","redistribution_authorized":False,
            "publication_approved":False,"states":dict(sorted(results.items()))}
    a.output.write_text(json.dumps(output,indent=2)+"\n")
    if a.candidate_output:
        if a.candidate_output.resolve().is_relative_to((Path.cwd()/"data/early-vote").resolve()):
            raise ValueError("Restricted candidate cannot be a public feed")
        from stage_remaining_eleven_counties import GEOJSON_MIRROR
        geo_request=urllib.request.Request(GEOJSON_MIRROR,headers={"User-Agent":"ElectionHQ-geography-review/1.0"})
        with urllib.request.urlopen(geo_request,timeout=35) as response:
            geojson=json.load(response)
        candidate, gaps=to_internal_candidate(output,geojson)
        a.candidate_output.write_text(json.dumps(candidate,indent=2)+"\\n")
        print("Restricted FIPS-matched UF county candidates:",len(candidate["states"]),"gaps:",gaps)
    print("UF source review:",{code:row["status"] for code,row in sorted(results.items())})

if __name__=="__main__":
    main()
