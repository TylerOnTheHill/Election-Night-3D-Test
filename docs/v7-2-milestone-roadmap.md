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
**Acceptance:** No upload; ingest and display verified partial county reports immediately (for example 150 of 254 TX counties), interactive county selection, blue-intensity ballot-volume map, reporting coverage and source/cutoff. Missing counties are unknown, not zero. Prefer the freshest verified statewide total when available; do not sum county and statewide counts or claim a partial county sum represents the entire state. When complete county reports are the freshest authoritative observation, their sum may take precedence. No fabricated or silently published data.
**Current status:** Interactive map/table and automatic loader implemented; publication-approved county feed is not yet checked in. This is the immediate engineering blocker. Internal staging previews are not public data.

## Milestone 3 — County expansion and Battleground completion
**Target:** Extend partial and complete verified county reporting to FL, VA, IA, WI, SC where available, then seek the remaining watchlist states without blocking verified coverage.
**Acceptance:** State-by-state county maps appear as soon as verified observations exist, even with partial coverage; unreported counties are visually and numerically distinguished from zero; 19-state interface polished on desktop/mobile and reviewed by owner.

## Milestone 4 — Nationwide Early Vote
**Target:** Complete consistent nationwide state map and source-aware reporting.
**Acceptance:** National totals respect partial coverage and reporting dates; missing never equals zero; state drill-down is functional and accessible.

## Milestone 5 — Election Night and release
**Target:** Election Night readiness and production release candidate.
**Acceptance:** Demo data visibly distinguished from live results, final smoke tests pass, owner approves any production merge/deployment.

## Reporting freshness rule (owner correction, 2026-10-27)
County geographic completeness is NOT a prerequisite for displaying verified early-vote observations. Show partial reporting as it arrives; distinguish reporting coverage from the statewide headline and compare source cutoffs before choosing the headline. Never add county sums to a statewide total. When county coverage is incomplete, label the reporting status **Partially reported** and display the reported/expected county count. Any county sum must remain explicitly identified as a partial county aggregation, not a complete statewide total; do not use “reported-county subtotal” as the user-facing status label. The earlier full-county gate is superseded.

## Engineering checkpoint — national refresh safeguards (2026-10-27)
- The national refresh now treats every source download as a **replacement snapshot**, never an additive increment.
- It validates state-specific reporting cutoffs against the previous snapshot and rejects regressions or disappearing reporting states.
- It writes validated data atomically, preserving the prior snapshot on failure.
- Regression tests cover newer cutoffs, same-cutoff corrections, stale states, failed refresh preservation, and no double counting; the refresh workflow runs these tests before ingestion.
- **Verification pending:** The workflow tests must pass before this checkpoint is marked verified. No changes have been deployed to production.

## Current next action
Complete the TX/NC county publication readiness gate and source freshness verification, then expand verified county coverage without waiting for geographic completeness. Keep the owner-approval requirement for public county data. Do not mark Milestone 2 complete until the public page automatically renders approved real county observations.
