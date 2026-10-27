# ElectionHQ v7.2: public-source completion policy and 5 p.m. Central target

Decision from project owner (October 27, 2026): **Do not draft, suggest, submit, or send records requests or contact officials unless the owner explicitly asks.** Use public sources only. Target a usable nationwide tracker by approximately **5 p.m. Central today**. The target is a deadline, not permission to fabricate coverage, merge to main, or label estimates official.

## Revised source acceptance

- **Tier A — government-published**: county/state elections offices, SOS, official GIS, official machine-readable reporting. Display source, as-of date, geography, metric definition.
- **Tier B — named reputable independent data publisher**: e.g. VoteHub/L2, CNN, UF Election Lab, Call the Map, or another traceable publisher. Accept for public-facing aggregates if there is an accessible, reproducible feed and clear cutoff, attribution/reuse rights, geographic coverage, and metric meaning. Label provider estimates as estimates; never silently equate modeled party support with observed votes.
- **Tier C — independent community research/dashboard**: may inform discovery and staging. Before importing values, establish exact downloadable underlying data, refresh schedule, provenance, permissible reuse and completeness; do not scrape graphics or invent missing values.
- **Unknown**: render as unavailable with explanation, not zero. Do not block nationwide launch because some counties lack precinct-level data.

Do not require government-specific certification when a reputable independent source explicitly identifies its geography and methodology. A third-party map or count is not evidence that TLC 2026 *primary* polygons are identical to November 2026 boundaries; label that difference clearly.

## Public leads found October 27

- VoteHub 2026 tracker methodology: https://votehub.com/2026-early-vote-methodology/ (partner L2; county aggregates and modeled electorate; obtain actual data and reuse terms before integration).
- Independent Texas 2026 dashboard with **254 county coverage** and **precinct data in nine counties**: https://jacksonahannan.github.io/early-vote-dashboard/ . It explicitly states precinct in-person-only matching and warns about coverage changes and unpaired mail counts. Inspect public repository/feed and attribution before reuse.
- Texas Legislative Council 2026 primary geometry: https://data.capitol.texas.gov/dataset/precincts (273 Collin polygons extracted; staging only).
- Collin November daily and cumulative site totals: https://www.collincountytx.gov/Elections/rosters . This is site-based, not precinct-based, and voter rosters contain personal information; do not ingest or publish PII.
- Collin GIS voting precincts: https://maps.collincountytx.gov/server/rest/services/InteractiveMap/Election_Department/MapServer . Earlier CI queries returned HTTP 403. Do not keep retrying the same blocked endpoint.

## Mandatory implementation sequence (large to small)

**Phase 1: National and state early-vote reporting.** Validate the live national feed, the 50-state/DC roster, ballot totals and mail/in-person components, as-of timestamps and source provenance. Show reported coverage and avoid presenting partial reporting as a complete national total. Freeze feature work on county and precinct layers until the national view is usable.

**Phase 2: County data nationwide.** Enumerate counties per state, ingest public county feeds where available, reconcile geography keys and distinguish state-vs-county source cutoffs. Display missing county data explicitly rather than inventing values.

**Phase 3: Precinct data.** Join only compatible counts and polygons, start with available states/counties, and label primary-vintage boundaries and third-party estimates correctly. Precinct coverage is not a prerequisite for Phase 1.

## Ship-ready acceptance checklist

- [ ] Nation/state dashboard works and shows state-level values with per-provider as-of cutoffs.
- [ ] County rows show only reported counties; missing counties explicitly labeled unavailable.
- [ ] Distinguish 2026 observed ballots from 2024 comparison and modeled turnout/party composition.
- [ ] Prevent county-vs-state mismatched cutoffs being silently summed as a single total.
- [ ] Source and methodology visible in UI, including independent providers.
- [ ] Precinct layer enabled only where reliable data/geometry join exists, otherwise boundary-only staging or unavailable.
- [ ] Mobile, JS checks, validation workflows green.
- [ ] Owner reviews staging and explicitly authorizes production merge. **Never modify main without approval.**

## Scope

Prioritize nationwide state/county coverage, then precinct overlays where actual compatible data exists. Do not make a full nationwide precinct map a blocking prerequisite for a useful 5 p.m. launch. The completion target cannot guarantee third-party API access, license approval or geographic availability.
