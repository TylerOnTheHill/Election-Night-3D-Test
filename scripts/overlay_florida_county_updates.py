#!/usr/bin/env python3
"""Safely overlay verified county-specific turnout updates on an official FL snapshot.

No network access. This is a staging-only pure transformation; it never silently
alters the authoritative statewide baseline or conflates registration with votes.
"""
import copy
from datetime import datetime
from urllib.parse import urlparse

CATEGORIES = ("voted_early", "voted_mail", "mail_outstanding")
PARTIES = ("republican", "democrat", "other", "no_party_affiliation")

def parse_time(value):
    if not isinstance(value, str) or not value:
        raise ValueError("Missing source timestamp")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid source timestamp") from exc

def overlay(snapshot, updates):
    """Return staged county records and mixed-cutoff totals, retaining baseline.

    Each update must have county, source_url, compiled_at_local and categories.
    Categories contain total + registration counts, matching official definitions.
    """
    result = copy.deepcopy(snapshot)
    baseline_time = parse_time(result["compiled_at_local"])
    names = {c["county"]: c for c in result["counties"]}
    if len(names) != 67 or len(result["counties"]) != 67:
        raise ValueError("Expected 67 unique Florida counties")
    seen = set()
    applied = []
    for update in updates:
        county = update["county"]
        if county not in names or county in seen:
            raise ValueError(f"Unknown or duplicate county: {county}")
        seen.add(county)
        source = urlparse(update["source_url"])
        if source.scheme != "https" or not source.hostname:
            raise ValueError("Supplemental source must have HTTPS provenance")
        cutoff = parse_time(update["compiled_at_local"])
        if cutoff <= baseline_time:
            raise ValueError(f"Supplemental report is not newer than baseline: {county}")
        categories = update["categories"]
        if not categories or set(categories) - set(CATEGORIES):
            raise ValueError("Unknown or empty ballot category")
        target = names[county]
        for category, counts in categories.items():
            registration = counts["registration"]
            if set(registration) != set(PARTIES):
                raise ValueError("Registration groups must match official schema")
            values = [registration[p] for p in PARTIES]
            total = counts["total"]
            if any(type(v) is not int or v < 0 for v in values + [total]):
                raise ValueError("Counts must be nonnegative integers")
            if sum(values) != total:
                raise ValueError("County category total does not reconcile")
            target[category] = copy.deepcopy(counts)
        target["supplemental_source_url"] = update["source_url"]
        target["supplemental_compiled_at_local"] = update["compiled_at_local"]
        target["supplemental_categories"] = sorted(categories)
        applied.append(county)
    totals = {}
    for category in CATEGORIES:
        reg = {p: sum(c[category]["registration"][p] for c in result["counties"]) for p in PARTIES}
        total = sum(c[category]["total"] for c in result["counties"])
        if total != sum(reg.values()):
            raise ValueError("Overlay failed statewide reconciliation")
        totals[category] = {"total": total, "registration": reg}
    result["baseline_statewide"] = copy.deepcopy(snapshot["statewide"])
    result["staged_mixed_cutoff_totals"] = totals
    result["staged_supplemental_counties"] = sorted(applied)
    result["snapshot_type"] = "staging_mixed_cutoff" if applied else result["snapshot_type"]
    result["caveat"] = str(result.get("caveat", "")) + " Supplemental totals are mixed-cutoff staging only, not an official uniformly timed statewide total."
    return result
