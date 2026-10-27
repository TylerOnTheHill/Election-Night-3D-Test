#!/usr/bin/env python3
"""Convert validated official Florida county/category aggregates to an UNAPPROVED county candidate.

Input is the normalized output of florida_county_adapter.py, never voter-level data.
Census county GEOIDs are verified by name against a supplied authoritative crosswalk.
A county is reported only if BOTH mail and early-vote categories are present.
Missing counties remain absent, not zero. No public feed is written.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

EXPECTED=67
CATEGORIES={"voted_mail","voted_early"}

def canonical(name):
    return re.sub(r"[^a-z0-9]","",re.sub(r"\\b(county)\\b","",name.lower()))

def from_official_tsv_snapshot(snapshot):
    """Adapt the existing scheduled Florida official TSV pipeline output."""
    if snapshot.get("schema")!="electionhq-florida-county-aggregate-v1" or snapshot.get("election_id")!="49894" or snapshot.get("state_fips")!="12":
        raise ValueError("Unexpected official Florida TSV snapshot")
    records=[]
    for county in snapshot["counties"]:
        for category in CATEGORIES:
            observation=county[category]
            records.append({"county":county["county"],"category":category,
                "total":observation["total"],"registration":observation["registration"]})
    return {"schema":"electionhq-county-early-vote-v1","state_fips":"12",
        "source_url":snapshot["source_url"],
        "reported_through":snapshot["compiled_at_local"],
        "county_compiled_at":snapshot["compiled_at_local"],"records":records}

def stage(normalized, census_rows):
    if normalized.get("schema")!="electionhq-county-early-vote-v1" or normalized.get("state_fips")!="12":
        raise ValueError("Florida official normalized input required")
    if not isinstance(census_rows,list) or not census_rows or census_rows[0]!=["NAME","state","county"]:
        raise ValueError("Census NAME/state/county crosswalk required")
    lookup={}
    for name,state,county in census_rows[1:]:
        if state!="12" or not re.fullmatch(r"\\d{3}",county):
            raise ValueError("Invalid Florida Census county GEOID")
        key=canonical(name.split(",",1)[0])
        if key in lookup:
            raise ValueError("Ambiguous Census county name")
        lookup[key]="12"+county
    if len(lookup)!=EXPECTED or len(set(lookup.values()))!=EXPECTED:
        raise ValueError("Florida Census crosswalk must contain 67 distinct counties")
    grouped=defaultdict(dict)
    for row in normalized.get("records",[]):
        county=row["county"].strip()
        key=canonical(county)
        if key not in lookup:
            raise ValueError("Unmatched Florida county: "+county)
        category=row["category"]
        if category not in CATEGORIES or category in grouped[key]:
            raise ValueError("Invalid/duplicate Florida category: "+county)
        total=row["total"]
        if type(total)!=int or total<0:
            raise ValueError("Invalid ballot count")
        registration=row["registration"]
        if set(registration)!={"republican","democrat","other","no_party_affiliation"} or any(type(v)!=int or v<0 for v in registration.values()) or sum(registration.values())!=total:
            raise ValueError("Invalid Florida registration breakdown")
        grouped[key][category]=(county,total,registration)
    counties=[]
    for key,parts in grouped.items():
        if set(parts)!=CATEGORIES:
            # One method alone cannot be represented as a complete county ballot total.
            continue
        name=parts["voted_early"][0]
        mail=parts["voted_mail"][1]
        early=parts["voted_early"][1]
        registration={p:sum(parts[k][2][p] for k in CATEGORIES) for p in parts["voted_early"][2]}
        counties.append({"fips":lookup[key],"name":name,"total":mail+early,
            "mail":mail,"in_person":early,"registered_dem":registration["democrat"],
            "registered_rep":registration["republican"],
            "registered_unaffiliated_other":registration["other"]+registration["no_party_affiliation"],
            "file_as_of":normalized["reported_through"],
            "source_url":normalized["source_url"],"credit":"Florida Department of State"})
    counties.sort(key=lambda row:row["fips"])
    if not counties:
        raise ValueError("No Florida counties with both verified voting categories")
    count=len(counties)
    total=sum(row["total"] for row in counties)
    return {"schema":"electionhq-county-preview-v1","publication_approved":False,"review_required":True,
        "party_counts_mean":"voter registration, never candidate votes",
        "states":{"FL":{"status":"candidate_pending_publication_approval",
            "provider":"Florida Department of State","credit":"Florida Department of State",
            "provider_checked_at":normalized.get("county_compiled_at"),
            "statewide_cutoff":normalized["reported_through"],
            "census_geography_source":"2020 Census county GEOIDs",
            "census_geography_url":"https://api.census.gov/data/2020/dec/pl",
            "county_count":count,"geographic_count":EXPECTED,
            "coverage_complete":count==EXPECTED,
            "reporting_label":"Fully reported" if count==EXPECTED else "Partially reported",
            "total":total,"total_basis":"sum_of_reported_counties",
            "provider_statewide_total":None,
            "county_vs_provider_statewide_difference":None,
            "counties":counties}}}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--normalized",help="Normalized Florida county/category records")
    parser.add_argument("--official-tsv-snapshot",help="Output from existing official Florida TSV ingestion")
    parser.add_argument("--census",required=True,help="Verified Census NAME/state/county JSON")
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    if Path(args.output).as_posix().lstrip("./").startswith("data/early-vote/"):
        raise ValueError("Staging cannot write to public early-vote directory")
    if bool(args.normalized)==bool(args.official_tsv_snapshot):
        parser.error("Provide exactly one Florida input format")
    source=json.loads(Path(args.normalized or args.official_tsv_snapshot).read_text())
    normalized=source if args.normalized else from_official_tsv_snapshot(source)
    candidate=stage(normalized,json.loads(Path(args.census).read_text()))
    Path(args.output).write_text(json.dumps(candidate,indent=2)+"\\n")
    print("FL staged, not published:",candidate["states"]["FL"]["county_count"],"counties")

if __name__=="__main__":
    main()
