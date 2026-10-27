#!/usr/bin/env python3
"""Convert a verified county candidate into the existing public feed format.

Never called by staging CI. Requires explicit owner approval recorded as a
separate command-line argument; never writes the public path by default.
"""
import argparse
import json
from pathlib import Path
from validate_county_publication_candidate import validate

def prepare(candidate, approval):
    if approval != "OWNER_APPROVED_TX_NC_COUNTY_PUBLICATION":
        raise ValueError("Explicit owner publication approval is required")
    validate(candidate)
    result = json.loads(json.dumps(candidate))
    result["publication_approved"] = True
    result.pop("review_required", None)
    for state in result["states"].values():
        state["status"] = "published"
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--approval", required=True,
                        help="Use only after explicit ElectionHQ owner approval")
    args = parser.parse_args()
    output = Path(args.output)
    if output.as_posix().lstrip("./") == "data/early-vote/battleground-counties.json":
        raise ValueError("Direct public-feed writes are forbidden; review the output before publication")
    candidate = json.loads(Path(args.candidate).read_text())
    approved = prepare(candidate, args.approval)
    output.write_text(json.dumps(approved, indent=2) + "\n")
    print("Owner-approved feed prepared for separate publication review:", output)

if __name__ == "__main__":
    main()
