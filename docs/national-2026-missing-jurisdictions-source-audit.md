# National 2026 early-vote gap audit — October 27, 2026

Scope: 50 states **plus the District of Columbia** = 51 jurisdictions. The checked-in Call the Map US.json has 46 reporting states and **five missing jurisdictions**: AL, DC, MA, NH, NY. Do not describe these as four missing states without mentioning DC.

| Jurisdiction | Public source / lead | What is actually supported | Ingestion decision |
| --- | --- | --- | --- |
| Alabama (AL) | [Call the Map limitations](https://www.callthemap.com/early-vote), [Alabama SOS absentee information](https://www.sos.alabama.gov/alabama-votes/voter/absentee-voting) | No no-excuse early in-person voting; excuse-only absentee. No verified live statewide absentee returns total identified. | Display **Not reported**; do not use zero. |
| District of Columbia (DC) | [DC Board of Elections](https://www.dcboe.org/), [independent state tracker](https://early.professorbutts.com/) | Independent tracker links to a daily DC tracker, but statewide-equivalent total and reuse terms must be extracted and checked. | Source candidate; **not yet integrated**. |
| Massachusetts (MA) | [Secretary of the Commonwealth](https://www.sec.state.ma.us/), [Call the Map limitations](https://www.callthemap.com/early-vote) | Election office publishes counts in difficult-to-automate form according to CTM; statewide current ballots-cast figure not yet extracted. | Source candidate; **not yet integrated**. |
| New Hampshire (NH) | [Call the Map limitations](https://www.callthemap.com/early-vote) | No no-excuse early in-person voting; excuse-only absentee. No verified live statewide absentee returns total identified. | Display **Not reported**; do not use zero. |
| New York (NY) | [NYC Board of Elections 2026 daily check-ins](https://www.vote.nyc/page/early-voting-check-ins), [independent New York tracker](https://early.professorbutts.com/) | NYC BOE reports **224,894 cumulative early in-person check-ins through October 26, 2026**. This covers **New York City only**, excludes the rest of New York State and mail returns. | Keep state total **Not reported** until statewide source verified. NYC figure may be presented only as a separately labeled city observation, not as NY statewide or added to national total. |

## Findings and integrity rules

- Call the Map 2026 early-vote page explains DC, MA and NY counts may exist but are not machine-readable by its automation. Its separate categorization for AL and NH reflects voting methods, not zero ballots.
- [Early Vote 2026 by Professor Butts](https://early.professorbutts.com/) currently lists DC and NY daily trackers; **it does not list Massachusetts** on its tracker index. Verify per-state source, geographic coverage, timestamp and reuse rights before any import.
- [NYC BOE official daily check-ins](https://www.vote.nyc/page/early-voting-check-ins) includes October 24 (86,215), October 25 (165,143 cumulative) and October 26 (224,894 cumulative).
- 46 of 51 jurisdictions reporting is **90.2% jurisdiction coverage**, not 90.2% voter coverage or completeness.
- Do not fabricate totals or silently add partial city counts to the national tally. Null is different from zero.
- Alternate national cross-check: [civicAPI-based 50501 Vets tracker](https://election-watch.50501vets.com/map?cat=returned), which reports different totals and reporting-state coverage; do not combine with CTM without compatible metric and cutoff checks.

## Next integration actions

1. Examine public DC daily tracker output and the underlying published BOE reports for a statewide-equivalent ballots-cast total and clear permitted reuse.
2. Locate a dated statewide Massachusetts early-vote total from the Secretary of the Commonwealth or another reputable data publisher.
3. Check the independent NY tracker for statewide coverage and mail/in-person definitions; separately preserve the NYC official series.
4. Continue checking for any AL/NH publicly published absentee-ballot-return totals, without blocking launch if absent.
5. Once verified, add each new jurisdiction through a source-aware ingestion adapter, recalculate national total and rerun validation. **Do not insert unverifiable figures.**
