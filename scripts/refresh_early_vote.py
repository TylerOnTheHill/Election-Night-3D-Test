#!/usr/bin/env python3
"""Refresh attributed nationwide early-vote observations without stale-state regression.

Each download is a complete source snapshot, never an increment to add to the
previous total. Reject a newer download if it rolls back any previously reported
state's reporting cutoff. Same-cutoff corrections remain permissible.
"""
import json
import os
import pathlib
import tempfile
import urllib.request
from datetime import datetime, date, timezone

SOURCE = "https://www.callthemap.com/early-vote/data/US.json"
DEST = pathlib.Path("data/early-vote/US.json")
FIELDS = ("total", "mail", "in_person", "dem", "rep", "unaffiliated_other")


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Snapshot timestamp must include a timezone")
    return result


def validate_snapshot(payload, previous=None):
    if payload.get("schema") != "ctm-early-vote-download-v1":
        raise ValueError("Unexpected schema")
    states = payload.get("states")
    if not isinstance(states, list) or len(states) < 30:
        raise ValueError("Incomplete state list")
    if not payload.get("credit") or not payload.get("license"):
        raise ValueError("Missing source attribution")
    names, codes = set(), set()
    for row in states:
        name, code = row.get("state_name"), row.get("state")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("Missing or duplicate state name")
        if not isinstance(code, str) or len(code) != 2 or code in codes:
            raise ValueError("Missing or duplicate state code")
        names.add(name)
        codes.add(code)
        if type(row.get("total")) is not int or row["total"] < 0:
            raise ValueError("Invalid state total")
        for field in FIELDS:
            val = row.get(field)
            if val is not None and (type(val) is not int or val < 0):
                raise ValueError("Invalid component for " + code + ": " + field)
        if not row.get("counts_through") or not row.get("source_url") or not row.get("credit"):
            raise ValueError("Missing reporting cutoff/source for " + code)
        date.fromisoformat(row["counts_through"])
    national = payload.get("national", {})
    if sum(row["total"] for row in states) != national.get("total"):
        raise ValueError("National sum mismatch")
    if national.get("states_counted") != len(states):
        raise ValueError("State count mismatch")
    checked = timestamp(payload["checked_at"])
    if checked > datetime.now(timezone.utc):
        raise ValueError("Future timestamp")
    if previous is not None:
        if checked < timestamp(previous["checked_at"]):
            raise ValueError("Refusing older snapshot")
        older = {row["state"]: row for row in previous.get("states", [])}
        for row in states:
            prior = older.get(row["state"])
            if prior and date.fromisoformat(row["counts_through"]) < date.fromisoformat(prior["counts_through"]):
                raise ValueError("Refusing stale state reporting cutoff: " + row["state"])
        missing = set(older) - codes
        if missing:
            raise ValueError("Refusing disappearing reporting states: " + ", ".join(sorted(missing)))
    return len(states)


def refresh(source=SOURCE, destination=DEST):
    destination = pathlib.Path(destination)
    with urllib.request.urlopen(
        urllib.request.Request(source, headers={"User-Agent": "ElectionHQ-aggregate-data-mirror/1.0"}),
        timeout=30,
    ) as response:
        payload = json.load(response)
    previous = json.loads(destination.read_text()) if destination.exists() else None
    count = validate_snapshot(payload, previous)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Never truncate a previously valid snapshot before replacement succeeds.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent,
                                         prefix=".early-vote-", suffix=".json", delete=False) as handle:
            temporary = pathlib.Path(handle.name)
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    print(f"Validated {count} states, {payload['national']['total']:,} ballots, checked {payload['checked_at']}")


if __name__ == "__main__":
    refresh()
