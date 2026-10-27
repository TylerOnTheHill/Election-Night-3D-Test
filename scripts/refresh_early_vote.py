#!/usr/bin/env python3
"""Validate and mirror Call the Map's public aggregate early-vote JSON for GitHub Pages.

Only aggregate totals; no voter-level data. Invalid or regressing feeds are rejected.
"""
import json
import pathlib
import urllib.request
from datetime import datetime, timezone

SOURCE = "https://www.callthemap.com/early-vote/data/US.json"
DEST = pathlib.Path("data/early-vote/US.json")
FIELDS = ("total", "mail", "in_person", "dem", "rep", "unaffiliated_other")
with urllib.request.urlopen(urllib.request.Request(SOURCE, headers={"User-Agent": "ElectionHQ-aggregate-data-mirror/1.0"}), timeout=30) as response:
    payload = json.load(response)
assert payload.get("schema") == "ctm-early-vote-download-v1", "Unexpected schema"
states = payload.get("states")
assert isinstance(states, list) and len(states) >= 30, "Incomplete state list"
assert payload.get("credit") and payload.get("license"), "Missing source attribution"
names = set()
for row in states:
    assert isinstance(row.get("state_name"), str) and row["state_name"] not in names
    names.add(row["state_name"])
    assert isinstance(row.get("total"), int) and row["total"] >= 0
    for field in FIELDS:
        val = row.get(field)
        assert val is None or (isinstance(val, int) and val >= 0), (row["state_name"], field)
    assert row.get("counts_through") and row.get("source_url") and row.get("credit")
assert sum(row["total"] for row in states) == payload["national"]["total"], "National sum mismatch"
assert payload["national"]["states_counted"] == len(states), "State count mismatch"
checked = datetime.fromisoformat(payload["checked_at"].replace("Z", "+00:00"))
assert checked <= datetime.now(timezone.utc), "Future timestamp"
if DEST.exists():
    old = json.loads(DEST.read_text())
    previous = datetime.fromisoformat(old["checked_at"].replace("Z", "+00:00"))
    assert checked >= previous, "Refusing older snapshot"
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
print(f"Validated {len(states)} states, {payload['national']['total']:,} ballots, checked {payload['checked_at']}")
