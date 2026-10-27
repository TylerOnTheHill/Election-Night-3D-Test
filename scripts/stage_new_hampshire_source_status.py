#!/usr/bin/env python3
"""Track New Hampshire 2026 excuse-required absentee returns via L2 source discovery."""
import argparse
import json
from pathlib import Path

def status():
    return {"state":"NH","election":"2026-11-03",
            "status":"l2_returned_ballot_source_identified_integration_pending",
            "reporting_label":"Not reported",
            "county_ballots":None,"county_count":0,
            "source_url":"https://early.l2datamapping.com/?state=NH&type=returned",
            "source_type":"third_party_l2_absentee_returns",
            "reason":"L2 returned-ballot dashboard identified. County totals, source cutoff, API access and reuse permissions require verification before ingestion.",
            "voting_method":"excuse_required_absentee_only",
            "in_person_early_voting_offered":False,
            "metric":"returned_absentee_ballots",
            "publication_approved":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(status(),indent=2)+chr(10))
    print("New Hampshire: L2 returned-ballot source identified; integration pending")
if __name__=="__main__":
    main()
