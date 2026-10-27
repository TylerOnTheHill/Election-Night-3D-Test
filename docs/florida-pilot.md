# Florida 2026 general election: official county statistics pilot

**Official source:** https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports/PublicStats

**Election ID:** 49894; **election date:** 2026-11-03; **geography:** Florida's 67 counties.

## What the public portal reports

The Florida Division of Elections publishes daily cumulative statistics compiled from county submissions. The public statistics distinguish:
- **Voted Vote-by-Mail:** returned ballots counted in the published participation statistics.
- **Voted Early:** ballots cast during in-person early voting.
- **Vote-by-Mail Provided (Not Yet Returned):** issued, *not voted* ballots. These must NEVER be included in turnout.

Party columns refer to **voter registration affiliation, not candidate votes or preferences**. Reported-through dates can lag retrieval time, and counties can update at different times. The state says county submissions are required daily by 8 a.m., with additional publication refreshes as needed.

## Pilot implementation status

- The adapter in `scripts/florida_county_adapter.py` validates **pre-extracted aggregate county statistics JSON**. It does not download or parse the live state portal.
- The adapter checks election ID, source URL, nonnegative counts, party-subtotal reconciliation and duplicate county/category rows.
- It explicitly flags partial county/category coverage instead of imputing missing counties as zero.
- This data is **not yet connected to the public ElectionHQ dashboard**, and no scheduled Florida ingestion is active.
- No voter-level data is required or permitted for this pilot.

## Live source integration release gate

1. Identify and verify the official downloadable county aggregate files or inspect actual portal HTML and test an HTML parser against saved fixtures.
2. Verify that `voted_mail` and `voted_early` are sourced from the correct tabs/files; do not merge with issued-but-not-returned ballots.
3. Map all 67 county names to authoritative five-digit county FIPS codes and reject unknown counties.
4. Reconcile county category sums with the corresponding official statewide category totals **for the same compiled snapshot**.
5. Capture per-category compiled timestamps, report-through dates, and source links.
6. Test against multiple source snapshots, including missing counties, revised totals and schema changes.
7. Enable scheduled updates only after checks pass; fail closed and retain last verified snapshot on source errors.
8. Expose coverage and freshness prominently in the UI; do not claim nationwide coverage until each state is validated.

Official references:
- https://dos.fl.gov/elections/data-statistics/elections-data/absentee-and-early-voting/
- https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports
