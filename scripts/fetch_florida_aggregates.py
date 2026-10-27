#!/usr/bin/env python3
"""Fetch three official Florida aggregate TSV downloads and validate a snapshot.

URLs must be verified from the official portal before use. This script never
fetches voter-level files and never silently publishes incomplete data.
"""
import argparse
import json
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

try:
    from scripts.import_florida_tsv import import_files
except ModuleNotFoundError:
    from import_florida_tsv import import_files

ALLOWED_HOST = "countyfilesvbm-ev.floridados.gov"
MAX_BYTES = 5_000_000

def fetch_official(url, target):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST or parsed.username or parsed.password:
        raise ValueError("Only verified HTTPS Florida election-host downloads are allowed")
    request = urllib.request.Request(url, headers={"User-Agent": "ElectionHQ-public-aggregate-fetch/1.0"})
    with urllib.request.urlopen(request, timeout=35) as response:
        final = urlparse(response.geturl())
        if final.scheme != "https" or final.hostname != ALLOWED_HOST:
            raise ValueError("Official download redirected to unapproved host")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Official aggregate download exceeds size limit")
        if not data.startswith(b"ElectionNumber\t"):
            raise ValueError("Unexpected download format; refusing non-aggregate file")
        target.write_bytes(data)

def run(early_url, returned_url, outstanding_url, output):
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        paths = [base / "early.txt", base / "returned.txt", base / "outstanding.txt"]
        for url, path in zip((early_url, returned_url, outstanding_url), paths):
            fetch_official(url, path)
        snapshot = import_files(*paths)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    return snapshot

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--early-url", required=True)
    parser.add_argument("--returned-url", required=True)
    parser.add_argument("--outstanding-url", required=True)
    parser.add_argument("--output", type=Path, default=Path("data/early-vote/FL.json"))
    args = parser.parse_args()
    snapshot = run(args.early_url, args.returned_url, args.outstanding_url, args.output)
    print(f"Validated {snapshot['coverage']['counties_reported']} counties, "
          f"compiled {snapshot['compiled_at_local']}")
