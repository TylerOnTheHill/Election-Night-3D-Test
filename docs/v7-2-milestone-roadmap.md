# ElectionHQ v7.2 — Milestone Roadmap

Status: active development on `feature/v7-2-national-county-data`. Production `main` is not to be changed without explicit user approval.

## Operating agreement
- Prioritize visible, working product outcomes rather than staging polish or repeated checks.
- Implement already-approved design and functionality autonomously.
- Ask the owner before introducing or changing public UX/UI or functionality.
- Never require public visitors to upload files. Internal preview and staging tools stay separate.
- Do not contact election officials or draft records requests without permission.
- Perform initial source/schema verification and periodic automated monitoring; reopen passed checks only for meaningful anomalies or changed methodology.
- Give milestone updates: what works, what remains, what is blocked, and what is next.

## Milestone 1 — Battleground foundation
**Target:** Public Battlegrounds page is immediately usable for the 19-state watchlist.
**Acceptance:** Uniform #268CFF watchlist states; nonwatchlist dimmed; state selection, accessible table, source/cutoff, search/sort/filter, shareable state links, CSV export, NH voting-method distinction, responsive layout. No visitor setup or file upload.
**Current status:** Functionality implemented on development branch; final owner-facing visual review outstanding.

## Milestone 2 — Automatic county maps, starting TX/NC
**Target:** County map and table automatically load from a published, approved dataset when a viewer selects Texas or North Carolina.
**Acceptance:** No upload; 254 TX and 100 NC counties, interactive county selection, blue-intensity ballot-volume map, prominent state total with '* Sum of complete county reports', source/cutoff; county sum takes precedence when coverage complete. Fallback to statewide data if county dataset unavailable. No fabricated or silently published data.
**Current status:** Interactive map/table and automatic loader implemented; publication-approved county feed is not yet checked in. This is the immediate engineering blocker. Internal staging previews are not public data.

## Milestone 3 — County expansion and Battleground completion
**Target:** Extend complete county reporting to FL, VA, IA, WI, SC where available, then seek the remaining watchlist states without blocking verified coverage.
**Acceptance:** State-by-state county maps appear only with complete matching reporting; missing coverage clearly communicated; 19-state interface polished on desktop/mobile and reviewed by owner.

## Milestone 4 — Nationwide Early Vote
**Target:** Complete consistent nationwide state map and source-aware reporting.
**Acceptance:** National totals respect partial coverage and reporting dates; missing never equals zero; state drill-down is functional and accessible.

## Milestone 5 — Election Night and release
**Target:** Election Night readiness and production release candidate.
**Acceptance:** Demo data visibly distinguished from live results, final smoke tests pass, owner approves any production merge/deployment.

## Current next action
Produce an approved-data publication path for TX/NC county feed without changing public UX. Do not mark Milestone 2 complete until the public page automatically renders real county observations from that feed.
