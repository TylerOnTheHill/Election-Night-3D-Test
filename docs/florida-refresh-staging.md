# Florida v7.2 staging refresh

Florida publishes cumulative county statistics at https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports/PublicStats.

## Reporting cadence
County submissions are normally due by 8 a.m. Eastern and reflect the previous day's activity. The state generally posts around 9 a.m. and may refresh at noon, 3 p.m. and 6 p.m. Eastern. Source timestamps, not fetch times, must determine data freshness.

## Current status
- The 2026-10-26 08:06 local snapshot in data/early-vote/FL.json is **static**, sourced from three user-downloaded official county aggregate TSVs. It covers 67 counties.
- scripts/fetch_florida_aggregates.py can fetch all three TSVs once their *actual official download URLs* are verified. The statistics-page URL itself is **not** a TSV download URL.
- The staging workflow is intentionally read-only and uploads a validated artifact, never pushes to main or Pages.
- GitHub scheduled workflows execute only from the repository's default branch; therefore the schedule in this feature-branch-only workflow is **not active**. A manual run on the branch also requires configuring the three repository variables below. Do not merge or enable production scheduling until URL verification and review.

## Configuration required
Set repository Actions variables FL_EARLY_TSV_URL, FL_RETURNED_TSV_URL, FL_OUTSTANDING_TSV_URL to the actual three official aggregate download URLs, discovered from the official page's Download File links. Do not guess endpoint patterns. All three must point to the approved Florida host. Run the workflow manually on the feature branch and inspect the artifact, compilation timestamp, all 67 county records, and reconciliation before considering a scheduled production job.

## Safeguards and limitations
The fetcher rejects unexpected hosts, redirects, non-TSV content, oversized responses, incomplete county coverage, inconsistent category timestamps and statewide reconciliation failures. Ballots marked provided/not returned are outstanding and are never counted as turnout. Party labels describe registration only. Returned ballots are not necessarily accepted ballots. A successful fetch does not imply same-day activity; report-through date must be displayed accurately. A future release should reject stale snapshots and should not overwrite newer verified snapshots with older source reports.
