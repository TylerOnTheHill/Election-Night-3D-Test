"""Validate public source registry metadata; no network calls."""
import json
from pathlib import Path
from urllib.parse import urlparse

root = Path(__file__).resolve().parents[1]
registry = json.loads((root / "data/sources/registry.schema.json").read_text())
assert registry["schema_version"] == "1.0.0"
seen = set()
for row in registry["sources"]:
    key = row["source_id"]
    assert key not in seen
    seen.add(key)
    assert len(row["state_fips"]) == 2 and row["state_fips"].isdigit()
    assert row["geography_level"] in ("county", "municipality", "precinct", "state")
    assert row["status"] in ("candidate", "verified", "active", "paused")
    assert row["measurement"] in ("daily", "cumulative")
    assert urlparse(row["source_url"]).scheme == "https"
    assert isinstance(row["official"], bool)
    if row["status"] == "active":
        assert row["adapter"], key
print("Source registry validated:", len(seen), "sources")
