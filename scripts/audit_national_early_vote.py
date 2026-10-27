#!/usr/bin/env python3
"""Read-only audit of national and watchlist early-vote source coverage.

Never creates missing-state zeroes or sums overlapping county/state totals.
"""
import argparse
import json
from datetime import date
from pathlib import Path
from refresh_early_vote import validate_snapshot

WATCH=("AK","AZ","FL","GA","IA","KS","ME","MI","MN","MS","NE","NV","NH","NC","OH","SC","TX","VA","WI")

def audit(payload):
    validate_snapshot(payload)
    states={s["state"]:s for s in payload["states"]}
    national=payload["national"]
    watch=[]
    for code in WATCH:
        state=states.get(code)
        watch.append({"state":code,"reported":state is not None,
                      "ballots":state["total"] if state else None,
                      "cutoff":state["counts_through"] if state else None,
                      "source_url":state.get("source_url") if state else None})
    reported=[s for s in watch if s["reported"]]
    dates=[date.fromisoformat(s["counts_through"]) for s in payload["states"]]
    return {"schema":"electionhq-national-early-vote-audit-v1",
            "checked_at":payload["checked_at"],
            "national_observed_ballots":national["total"],
            "national_reporting_states":len(states),
            "national_reporting_cutoff_range":{"first":min(dates).isoformat(),"last":max(dates).isoformat()},
            "watchlist_states":watch,
            "watchlist_reported_states":len(reported),
            "watchlist_observed_ballots":sum(s["ballots"] for s in reported),
            "watchlist_missing_states":[s["state"] for s in watch if not s["reported"]],
            "county_totals_added_to_national":False,
            "missing_counts_are_zero":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/early-vote/US.json")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=audit(json.loads(Path(a.input).read_text()))
    Path(a.output).write_text(json.dumps(report,indent=2)+"\n")
    print("National observed:",report["national_observed_ballots"],
          "reporting states:",report["national_reporting_states"],
          "watchlist:",report["watchlist_reported_states"],"/19")

if __name__=="__main__":
    main()
