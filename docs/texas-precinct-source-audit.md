# Texas precinct source feasibility audit — October 27, 2026

## Source candidates

1. **Texas Legislative Council precinct geography**: https://data.capitol.texas.gov/dataset/precincts
   - The published 2026 file is **2026 primary** (`Precincts26P.zip`), not a verified 2026 general-election precinct snapshot.
   - Companion district workbook documents `FIPS`, `COUNTY`, `PREC`, and unique `PCTKEY`.
   - Council explicitly advises consulting the county election official for the authoritative boundary. A 2026 general-election join is **not approved** from 26P alone.

2. **Collin County 2026 election rosters**: https://www.collincountytx.gov/Elections/rosters
   - Lists daily and cumulative early-voting statistics, by-site totals, absentee returns, and early-voter rosters.
   - By-site totals are **not** voters' home-precinct totals; raw roster format and precinct attribution must be verified before aggregation.
   - Collin GIS precinct map service: https://maps.collincountytx.gov/server/rest/services/InteractiveMap/Election_Department/MapServer

3. **Travis County election site**: https://votetravis.gov/current-election-information/current-election/
   - Advertises daily voter rosters and live turnout tracking; reports 308 precincts, 299 with active voters.
   - Requires verification of roster schema, geographic identifier, reporting cutoff and boundaries.

4. **Bexar early-vote tracker (independent example)**: https://www.bexarearlyvote.online/
   - Documents daily voter-roster aggregation to voters' **home precinct**, with separate polling-site turnout.
   - Its published method is an architectural reference, not a licensed or verified data feed for ElectionHQ.

## Proposed pilot decision

Begin with **Collin County**, which provides both 2026 rosters and a precinct GIS service; inspect file format and map-layer attributes before committing to ingestion. Keep Bexar and Travis as independent comparison/reference candidates.

## Data-integrity gates

- Verify a public, reproducible, permitted download endpoint and schema for daily rosters.
- Process locally or in restricted staging; publish only aggregate counts. Avoid storing or distributing names, addresses, voter IDs, birthdates, or individual voting-history records.
- Attribute votes to **home precinct** only when the roster provides a verified residence-precinct field. Site-level counts must use a separate visualization.
- Require a compatible **November 2026 general-election** precinct geography vintage or county election-office confirmation.
- Verify joins with `(county_fips, precinct_id)` and check all unmatched/duplicate precincts.
- Confirm whether cumulative snapshots or daily incremental rosters are supplied to prevent double-counting.
- Reconcile all mapped precinct totals against a **matching reporting cutoff** and a matching subset of source county returns; never force reconciliation to a different-cutoff statewide feed.
- Never infer Democratic/Republican 2026 candidate votes from primary history.
- Until these gates pass, do not publish any subcounty data or color the map with inferred partisanship.

## Current implementation

`scripts/validate_tx_local_returns.py` and `tests/test_tx_local_returns.py` validate a staging-only local aggregate format, without fetching individual voter records or asserting geographic coverage. This is a validation foundation, **not** an operational 2026 precinct ingestion pipeline.
