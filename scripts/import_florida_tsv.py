#!/usr/bin/env python3
"""Import Florida's three public county aggregate TSV downloads.

No voter-level data. Never count 'provided, not yet returned' as turnout.
"""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

PARTIES = {"TotalRep": "republican", "TotalDem": "democrat",
           "TotalOth": "other", "TotalNpa": "no_party_affiliation"}
TYPES = {"Voted Early": "voted_early",
         "Voted Vote-by-Mail": "voted_mail",
         "Vote-by-Mail Provided (Not Yet Returned)": "mail_outstanding"}
SOURCE = "https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports/PublicStats"

def integer(value):
    number = int(value.replace(",", ""))
    if number < 0:
        raise ValueError("Negative election count")
    return number

def read_table(path, expected_type):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"ElectionNumber", "ElectionDate", "ElectionName", "CountyName",
                    "StatType", "GrandTotal", "CompileDate", *PARTIES}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Unexpected Florida TSV columns")
        rows = list(reader)
    if len(rows) != 68:
        raise ValueError("Expected 67 counties and one statewide row")
    result = {}
    compiled = set()
    for row in rows:
        if row["ElectionNumber"] != "49894" or row["ElectionDate"] != "11/03/2026":
            raise ValueError("Wrong Florida election")
        if row["StatType"] != expected_type:
            raise ValueError("Wrong Florida statistic")
        name = row["CountyName"].strip()
        if not name or name.casefold() in result:
            raise ValueError("Duplicate or blank county")
        parties = {label: integer(row[key]) for key, label in PARTIES.items()}
        total = integer(row["GrandTotal"])
        if total != sum(parties.values()):
            raise ValueError("Party totals do not reconcile")
        compiled.add(datetime.strptime(row["CompileDate"].strip(), "%m/%d/%Y  %I:%M%p"))
        result[name.casefold()] = {"county": name, "total": total, "registration": parties}
    if len(compiled) != 1:
        raise ValueError("Mixed compilation times in a file")
    statewide = result.pop("state totals", None)
    if statewide is None or len(result) != 67:
        raise ValueError("Missing statewide row or counties")
    if sum(row["total"] for row in result.values()) != statewide["total"]:
        raise ValueError("County totals do not match statewide total")
    for party in PARTIES.values():
        if sum(row["registration"][party] for row in result.values()) != statewide["registration"][party]:
            raise ValueError("County party totals do not match statewide")
    return result, statewide, next(iter(compiled))

def import_files(early, returned, outstanding):
    files = {"voted_early": (early, "Voted Early"),
             "voted_mail": (returned, "Voted Vote-by-Mail"),
             "mail_outstanding": (outstanding, "Vote-by-Mail Provided (Not Yet Returned)")}
    tables = {}
    totals = {}
    times = set()
    for category, (path, label) in files.items():
        table, total, compiled = read_table(path, label)
        tables[category], totals[category] = table, total
        times.add(compiled)
    if len(times) != 1:
        raise ValueError("Category downloads have different compilation times")
    if not (set(tables["voted_early"]) == set(tables["voted_mail"]) == set(tables["mail_outstanding"])):
        raise ValueError("County coverage differs between categories")
    records = []
    for key in sorted(tables["voted_mail"]):
        voted = tables["voted_mail"][key]["total"]
        pending = tables["mail_outstanding"][key]["total"]
        records.append({
            "county": tables["voted_mail"][key]["county"],
            "voted_early": tables["voted_early"][key],
            "voted_mail": tables["voted_mail"][key],
            "mail_outstanding": tables["mail_outstanding"][key],
            "mail_return_rate": round(voted / (voted + pending), 6) if voted + pending else None,
        })
    returned_total = totals["voted_mail"]["total"]
    outstanding_total = totals["mail_outstanding"]["total"]
    return {
        "schema": "electionhq-florida-county-aggregate-v1",
        "election_id": "49894", "state_fips": "12", "source_url": SOURCE,
        "compiled_at_local": next(iter(times)).isoformat(),
        "mail_return_rate_definition": "voted_mail / (voted_mail + mail_outstanding)",
        "statewide": {**totals, "mail_return_rate": round(returned_total / (returned_total + outstanding_total), 6)},
        "coverage": {"counties_reported": len(records), "complete": len(records) == 67},
        "counties": records,
        "caveat": "Party breakdown reflects registration, not votes for candidates. Returned is not necessarily accepted."
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--early", type=Path, required=True)
    parser.add_argument("--returned", type=Path, required=True)
    parser.add_argument("--outstanding", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = import_files(args.early, args.returned, args.outstanding)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Validated", result["coverage"]["counties_reported"], "Florida counties")
