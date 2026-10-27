#!/usr/bin/env python3
"""Run the complete TX/NC county-data pipeline in one command, without publication."""
import argparse
import json
import tempfile
from pathlib import Path

from stage_callthemap_county_pilots import validate as validate_provider, BASE, CODES
from verify_tx_nc_fips import fetch_vendored, crosswalk
from build_county_preview import build_publication_candidate
from validate_county_publication_candidate import validate as validate_candidate


def run(input_dir=None, output=None):
    with tempfile.TemporaryDirectory(prefix="electionhq-tx-nc-") as directory:
        root = Path(directory)
        enriched = root / "verified"
        enriched.mkdir()
        for code in CODES:
            if input_dir:
                payload = json.loads((Path(input_dir) / (code + ".json")).read_text())
            else:
                import urllib.request
                request = urllib.request.Request(BASE + code + ".json",
                                                 headers={"User-Agent": "ElectionHQ-county-pipeline/1.0"})
                with urllib.request.urlopen(request, timeout=30) as response:
                    payload = json.load(response)
            staged = validate_provider(code, payload)
            census, source_url = fetch_vendored(code)
            verified = crosswalk(
                code, census, staged,
                "Vendored Census-derived county FIPS mirror (2020 vintage not independently verified)",
                source_url,
            )
            (enriched / (code + ".json")).write_text(json.dumps(verified))
        candidate = build_publication_candidate(enriched)
        summary = validate_candidate(candidate)
        if output:
            Path(output).write_text(json.dumps(candidate, indent=2) + "\n")
        return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", help="Local provider files instead of network downloads")
    parser.add_argument("--output", default="staging-county-publication-candidate.json")
    args = parser.parse_args()
    summary = run(args.input_dir, args.output)
    print(json.dumps({"status": "verified_candidate_not_approved_for_publication",
                      "output": args.output, "states": summary}, indent=2))


if __name__ == "__main__":
    main()
