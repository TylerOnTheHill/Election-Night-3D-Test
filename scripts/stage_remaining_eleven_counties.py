#!/usr/bin/env python3
"""Batch-stage all 11 remaining watchlist states from observed county sources.

This is a non-publication candidate. States with no observed county totals or
unresolvable geography are reported as gaps, never filled with zero.
"""
import argparse
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from audit_remaining_watchlist_county_sources import STATES
from stage_callthemap_county_pilots import BASE
from stage_watchlist_counties import GEOJSON_MIRROR, stage, STATES as STAGING_STATES
from validate_county_publication_candidate import EXPECTED, validate

# The 11-state batch reuses the same verified county normalization and
# reporting-label contract as the four-state adapter.
GEOIDS = {
    "AK": ("02", 30), "AZ": ("04", 15), "KS": ("20", 105),
    "ME": ("23", 16), "MI": ("26", 83), "MN": ("27", 87),
    "MS": ("28", 82), "NE": ("31", 93), "NV": ("32", 17),
    "NH": ("33", 10), "OH": ("39", 88),
}
assert set(GEOIDS) == set(STATES)

def geography(geojson, prefix):
    rows = [["NAME", "state", "county"]]
    seen = set()
    for feature in geojson["features"]:
        properties = feature.get("properties") or {}
        geoid = str(feature.get("id") or (
            str(properties.get("STATE", "")) + str(properties.get("COUNTY", ""))))
        name = properties.get("NAME")
        if len(geoid) != 5 or not geoid.isdigit() or not geoid.startswith(prefix):
            continue
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Missing county-equivalent name for " + geoid)
        if geoid in seen:
            raise ValueError("Duplicate county GEOID " + geoid)
        seen.add(geoid)
        rows.append([name, prefix, geoid[2:]])
    return rows

def build(payloads, geojson):
    candidates = {}
    gaps = {}
    original = dict(STAGING_STATES)
    original_expected = dict(EXPECTED)
    try:
        STAGING_STATES.update(GEOIDS)
        EXPECTED.update(GEOIDS)
        for code in STATES:
            try:
                prefix, expected = GEOIDS[code]
                crosswalk = geography(geojson, prefix)
                if len(crosswalk) - 1 != expected:
                    raise ValueError("Geography crosswalk has %s, expected %s county equivalents" %
                                     (len(crosswalk) - 1, expected))
                candidate = stage(code, payloads[code], crosswalk)
                if candidate is None:
                    gaps[code] = "No county observations with reported totals"
                else:
                    candidates[code] = candidate
            except (ValueError, KeyError, TypeError) as exc:
                gaps[code] = str(exc)
        result = {"schema": "electionhq-county-preview-v1",
                  "publication_approved": False, "review_required": True,
                  "party_counts_mean": "voter registration, never candidate votes",
                  "states": dict(sorted(candidates.items())),
                  "states_without_county_observations": sorted(gaps)}
        if candidates:
            validate(result)
        return result, gaps
    finally:
        STAGING_STATES.clear()
        STAGING_STATES.update(original)
        EXPECTED.clear()
        EXPECTED.update(original_expected)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--geojson", type=Path)
    parser.add_argument("--output", type=Path, default=Path("remaining-eleven-unapproved.json"))
    parser.add_argument("--gaps-output", type=Path, default=Path("remaining-eleven-gaps.json"))
    args = parser.parse_args()
    public = (Path.cwd() / "data/early-vote").resolve()
    for target in (args.output, args.gaps_output):
        if target.resolve().is_relative_to(public):
            raise ValueError("Never write unapproved data to public feeds")
    def download(url):
        request = urllib.request.Request(url, headers={"User-Agent": "ElectionHQ-11-state-staging/1.0"})
        with urllib.request.urlopen(request, timeout=35) as response:
            return json.load(response)
    geojson = json.loads(args.geojson.read_text()) if args.geojson else download(GEOJSON_MIRROR)
    def fetch(code):
        return json.loads((args.input_dir / (code + ".json")).read_text()) if args.input_dir else download(BASE + code + ".json")
    payloads, fetch_gaps = {}, {}
    with ThreadPoolExecutor(max_workers=11) as pool:
        futures = {pool.submit(fetch, code): code for code in STATES}
        for future in as_completed(futures):
            code = futures[future]
            try:
                payloads[code] = future.result()
            except (OSError, ValueError, TimeoutError) as exc:
                fetch_gaps[code] = "Source download failed: " + str(exc)
    # Keep each state independent: a broken endpoint must not suppress the
    # observed counties available from other states.
    result, gaps = build(payloads, geojson) if not fetch_gaps else build_available(payloads, geojson, fetch_gaps)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    args.gaps_output.write_text(json.dumps({"publication_approved": False, "gaps": gaps}, indent=2) + "\n")
    print("11-state batch:", len(result["states"]), "staged,", len(gaps), "source/geography gaps; NOT PUBLISHED")

def build_available(payloads, geojson, missing):
    # Supply an explicit unavailable payload for failed downloads. No totals
    # are invented; build() records the absence as a per-state gap.
    placeholders = {code: {"schema": "ctm-early-vote-download-v1", "state": code,
                           "credit": "unavailable", "license": "unavailable", "counties": []}
                    for code in missing}
    result, gaps = build({**placeholders, **payloads}, geojson)
    gaps.update(missing)
    result["states_without_county_observations"] = sorted(gaps)
    return result, gaps

if __name__ == "__main__":
    main()
