#!/usr/bin/env python3
"""Combine independently validated county candidates for LOCAL REVIEW only.

Never marks a candidate approved or writes a public feed. Duplicate states
require explicit resolution; never add overlapping county snapshots together.
"""
import argparse
import json
from pathlib import Path
from validate_county_publication_candidate import validate

def combine(candidates):
    states={}
    for candidate in candidates:
        validate(candidate)
        for code,state in candidate["states"].items():
            if code in states:
                raise ValueError("Overlapping state candidates must not be summed: "+code)
            states[code]=state
    if not states:
        raise ValueError("No county observations to combine")
    result={"schema":"electionhq-county-preview-v1",
            "publication_approved":False,"review_required":True,
            "party_counts_mean":"voter registration, never candidate votes",
            "states":dict(sorted(states.items()))}
    validate(result)
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidate",action="append",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    target=Path(args.output)
    if target.resolve().is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Unapproved data must never enter the public feed directory")
    result=combine([json.loads(Path(p).read_text()) for p in args.candidate])
    target.write_text(json.dumps(result,indent=2)+"\n")
    print("Combined local review, NOT PUBLISHED:",", ".join(result["states"]))

if __name__=="__main__":
    main()
