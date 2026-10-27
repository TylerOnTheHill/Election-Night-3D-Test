# Florida supplemental county-source research — 2026-10-26

## Statewide baseline (verified)
Florida Department of State: https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports/PublicStats
Official documentation: https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports

Counties report by 8 a.m. Eastern, covering **the previous day's activity**. The state normally publishes by 9 a.m. Eastern; noon, 3 p.m., and 6 p.m. refreshes are for delayed submissions, not guaranteed new current-day activity. Poll once daily after 9 a.m. Eastern; optional retry only for known missing counties or a failed download. The staging schedule of 14:30 UTC is 10:30 a.m. EDT in October 2026. Scheduled workflows only execute on GitHub's default branch; this feature-branch workflow is not live.

## County supplemental candidates
| County | Evidence | 2026 machine-readable endpoint verified? | Status |
|---|---|---|---|
| Leon | A 2024 local report cited an election-office **live turnout tracker** showing in-person, mail and provisional counts as of 3:40 p.m.: https://www.wctv.tv/2024/10/31/leon-county-surpasses-90k-early-votes-five-days-before-election-day/ | No | Research |
| Miami-Dade | A 2022 report described figures posted by the county Supervisor of Elections: https://www.wuft.org/fresh-take-florida/2022-11-02/florida-gop-takes-lead-in-early-voting-in-traditionally-blue-miami-dade | No | Research |
| Broward | Official county office / 2026 public feed still to be verified | No | Research |
| Palm Beach | Official county office / 2026 public feed still to be verified | No | Research |
| Hillsborough | Official county office / 2026 public feed still to be verified | No | Research |
| Orange | Official county office / 2026 public feed still to be verified | No | Research |

Historical news reports establish that a county previously published turnout information, **not** that a live, public, machine-readable 2026 feed exists. No supplemental county source is connected yet.

## Integration rules
1. Identify and inspect an actual official 2026 URL or downloadable file, with access/usage terms, before enabling collection.
2. Preserve publisher, retrieval time, activity-through date/time, compilation time, category definitions and geographic FIPS. Do not call a historical source 'live'.
3. County updates replace **only that county's corresponding statewide-snapshot categories**. Do not add them to statewide totals or sum overlapping sources.
4. Never combine early-in-person, mail-returned, and provisional totals unless all source definitions match. Registration party is not candidate choice.
5. If a county source is newer than the Florida state baseline, publish a clearly labeled mixed-cutoff rollup or keep the statewide figure as the official consistent baseline; never quietly claim uniform statewide freshness.
6. Detect corrections and backwards revisions rather than assuming every cumulative counter increases.
7. Fail closed for missing counties, unexpected category names, conflicting timestamps, or ambiguous totals.

## Next engineering gates
- Verify current county-specific reporting pages and machine-readable endpoints.
- Build source-specific adapters with recorded fixtures and reconciliation tests.
- Add county source precedence and per-county freshness metadata.
- Run side-by-side QA before any v7.2 merge to main.
