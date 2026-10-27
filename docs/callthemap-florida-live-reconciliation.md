# Call the Map Florida county reconciliation — live probe

**Probe run:** https://github.com/TylerOnTheHill/ElectionHQ/actions/runs/40451891989
**Probe date:** 2026-10-27 UTC
**Scope:** All 67 Florida counties, 2026 General Election.

## Verified result
- Live Call the Map `FL.json` county rows: **67**
- County rows matching ElectionHQ's official Florida morning snapshot: **67**
- County rows differing from that official snapshot: **0**
- Sum of Call the Map county rows: **2,785,114**
- Call the Map Florida statewide summary: **3,142,750**
- Statewide-only increment with no county breakdown in the downloaded feed: **357,636**
- CI validation and live staging probe: **passed**

The statewide summary is attributed to a newer civicAPI count, but the feed does not assign the extra 357,636 ballots to counties. **Do not allocate that difference, derive county changes, or label the county data as equally fresh as the statewide figure.** This does not imply votes are missing from the election; it is a mismatch in reporting cutoffs and granularity.

## Operational decision
1. Keep the statewide Call the Map feed for national/state totals with explicit source and cutoff.
2. Keep official Florida's 67-county snapshot as the county-level baseline until a verified newer county-level source exists.
3. Do not add a second Call the Map Florida county ingestion as a supposed freshness improvement: it currently duplicates our official county rows exactly.
4. Continue research into whether civicAPI offers a county-level downloadable feed/API with permitted redistribution, then evaluate actual county timestamps and definitions.
5. Extend county-feed feasibility checks to other states only after identifying their actual downloadable schema and county coverage; don't assume every state has 100% coverage.

**Source artifacts:** Probe workflow and report artifact are linked from the run above. No production publication has been enabled.
