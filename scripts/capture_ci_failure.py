#!/usr/bin/env python3
"""Capture GitHub Actions job failures as a small, sanitized, repo-readable JSON.

Uses the workflow's GITHUB_TOKEN; never writes tokens, environment variables,
raw logs, or data feeds. Called in an always() step after the review pipeline.
"""
import argparse
import json
import os
from pathlib import Path
import urllib.request

def summarize(jobs):
    return [{"job": j.get("name"), "conclusion": j.get("conclusion"),
             "failed_steps": [{"name": s.get("name"), "conclusion": s.get("conclusion"),
                               "number": s.get("number")}
                              for s in j.get("steps", []) if s.get("conclusion") == "failure"]}
            for j in jobs if j.get("conclusion") == "failure"]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="data/ci-diagnostics/latest-county-review.json")
    args = p.parse_args()
    repo, run_id, token = (os.environ.get(k) for k in ("GITHUB_REPOSITORY", "GITHUB_RUN_ID", "GITHUB_TOKEN"))
    if not all((repo, run_id, token)):
        raise ValueError("GitHub Actions repository, run ID and token are required")
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100"
    request = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
        "User-Agent": "ElectionHQ-CI-diagnostics"})
    with urllib.request.urlopen(request, timeout=20) as response:
        jobs = json.load(response).get("jobs", [])
    result = {"schema": "electionhq-ci-failure-summary-v1", "run_id": int(run_id),
              "run_url": f"https://github.com/{repo}/actions/runs/{run_id}",
              "head_sha": os.environ.get("GITHUB_SHA"), "jobs": summarize(jobs)}
    target = Path(args.output)
    if target.resolve().is_relative_to((Path.cwd() / "data/early-vote").resolve()):
        raise ValueError("Diagnostics cannot be written into public vote data")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(f'Captured {len(result["jobs"])} failed jobs to {target}')

if __name__ == "__main__":
    main()
