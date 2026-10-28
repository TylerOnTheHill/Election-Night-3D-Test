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
import time

def summarize(jobs):
    result = []
    for job in jobs:
        failed = [{"name": s.get("name"), "conclusion": s.get("conclusion"),
                   "number": s.get("number")}
                  for s in job.get("steps", []) if s.get("conclusion") == "failure"]
        # The current job is still running while this final step executes.
        if failed or job.get("conclusion") == "failure":
            result.append({"job": job.get("name"), "conclusion": job.get("conclusion"),
                           "failed_steps": failed})
    return result

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
    # GitHub can lag behind the currently running job's step conclusions.
    # Retry before reporting that no failed step was visible.
    failures = []
    for attempt in range(4):
        with urllib.request.urlopen(request, timeout=20) as response:
            jobs = json.load(response).get("jobs", [])
        failures = summarize(jobs)
        if failures:
            break
        if attempt < 3:
            time.sleep(3)
    result = {"schema": "electionhq-ci-failure-summary-v1", "run_id": int(run_id),
              "run_url": f"https://github.com/{repo}/actions/runs/{run_id}",
              "head_sha": os.environ.get("GITHUB_SHA"), "jobs": failures,
              "failure_details_pending": not bool(failures),
              "diagnostic_note": ("GitHub has not exposed failed steps yet; open run_url for full logs" if not failures else None)}
    target = Path(args.output)
    if target.resolve().is_relative_to((Path.cwd() / "data/early-vote").resolve()):
        raise ValueError("Diagnostics cannot be written into public vote data")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(f'Captured {len(result["jobs"])} failed jobs to {target}')

if __name__ == "__main__":
    main()
