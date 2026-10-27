# VoteHub 2026 early-vote integration — approved public source

Owner approval: October 27, 2026. VoteHub is **approved as an acceptable reputable third-party data source** for ElectionHQ. No requirement for separate state/county certification when its published geography and metric are clear. No records requests or outreach unless owner explicitly authorizes.

## Confirmed public endpoints

- Tracker: https://votehub.com/2026-early-vote-tracker
- Methodology: https://votehub.com/2026-early-vote-methodology/
- About: https://votehub.com/about/

VoteHub says its tracker is built with L2 and includes mail requests, absentee returns and early in-person voting, with county aggregations and modeled voter characteristics. VoteHub's 2026 tracker distinguishes observed ballot returns from modeled partisanship, race, expected vote choice and forecast quantities.

## Integration approach

1. Use VoteHub's **observed** early-vote counts as an alternative provider, where public machine-readable data or reproducible visible aggregates are available.
2. Store per-state or per-county `source_name`, `source_url`, `counts_through`, `coverage`, `metric_kind`, and `data_kind` (`observed` vs `modeled`).
3. For gaps AL, DC, MA, NH, NY, inspect VoteHub's publicly accessible state views. Only promote a figure if its geography and cutoff are explicit. A missing VoteHub state is still unavailable, not zero.
4. Avoid combining VoteHub and Call the Map counts for the **same** jurisdiction; prefer a single selected provider per geography and explain provider switches.
5. If VoteHub doesn't expose an accessible data feed or export, keep it as an approved cross-check and continue with other public sources. **Approval of VoteHub's credibility is not an assertion that all underlying L2 data is freely redistributable or that an undocumented API exists.**
6. Do not reproduce VoteHub's modeled party/candidate preferences as actual votes. Preserve uncertainty and methodology labels.
7. Keep source links and attribution prominent. Check publicly posted terms before automated republication; a subscription or restricted dataset is not implied to be licensed by a public webpage.

## Status as of October 27

- VoteHub credibility approved by project owner.
- Public tracker and methodology verified.
- No publicly documented early-vote download API, reusable export, or comprehensive machine-readable 2026 state feed verified yet.
- No VoteHub counts imported into ElectionHQ; national 46-state CTM feed remains the operational primary source.
- National-first work remains the priority; county and precinct ingestion follow.
