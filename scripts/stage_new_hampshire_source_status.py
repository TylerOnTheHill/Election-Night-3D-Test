#!/usr/bin/env python3
"""Report New Hampshire's 2026 absentee county data availability."""
import argparse
import json
from pathlib import Path

def status():
    return {"state":"NH","election":"2026-11-03",
            "status":"no_verified_public_county_absentee_aggregate",
            "reporting_label":"Not reported",
            "county_ballots":None,"county_count":0,
            "source_url":"https://www.sos.nh.gov/elections",
            "source_type":"official_election_administration",
            "reason":"The state does not publish a verified live county-level absentee ballot aggregate; local clerk status lookups are individual-voter services, not public aggregate feeds.",
            "publication_approved":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(status(),indent=2)+chr(10))
    print("New Hampshire: no verified county absentee aggregates")
if __name__=="__main__":
    main()
