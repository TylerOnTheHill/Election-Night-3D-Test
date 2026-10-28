#!/usr/bin/env python3
"""Build a fail-closed, unpublished Alaska House district browser review from CSV."""
import argparse
import json
from pathlib import Path

from stage_alaska_house_districts import parse

def build(csv_path, source_url):
    parsed = parse(csv_path, source_url)
    rows = [{"district": r["district"], "received": r["received_ballots"],
             "absentee_received": r["absentee_received"],
             "early_vote_received": r["early_vote_received"],
             "as_of": parsed["source_cutoff"]} for r in parsed["districts"]]
    return {
        "schema": "electionhq-alaska-house-district-review-v1",
        "publication_approved": False,
        "source": "Alaska Division of Elections Combined Ballot Count Report",
        "source_url": source_url,
        "as_of": parsed["source_cutoff"],
        "geographic_count": 40,
        "nongeographic_district": 99,
        "geographic_total": parsed["geographic_received_ballots"],
        "nongeographic_total": parsed["nongeographic_received_ballots"],
        "statewide_total": parsed["total_received_ballots"],
        "districts": rows,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--output", type=Path, default=Path("data/staging/alaska-house-district-review.json"))
    args = parser.parse_args()
    if not args.source_url.startswith("https://"):
        raise ValueError("HTTPS source attribution required")
    if args.output.resolve().is_relative_to((Path.cwd() / "data/early-vote").resolve()):
        raise ValueError("Unpublished district review must not be written to live feeds")
    result = build(args.input_csv, args.source_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Alaska review:", result["statewide_total"], "ballots; 40 geographic districts + District 99")

if __name__ == "__main__":
    main()
