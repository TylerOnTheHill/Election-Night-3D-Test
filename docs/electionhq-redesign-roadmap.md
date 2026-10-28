# ElectionHQ redesign roadmap — approved direction (2026-10-27)

## Governance
- Development only on `feature/v7-2-national-county-data`; do not publish unapproved county data or alter the live UI without review.
- Proceed autonomously on approved scope; ask only when a new design/functionality decision is required.
- Preserve existing 3D map navigation, geographic drilldowns, verified totals, data safeguards, and green early-vote intensity scale.
- No upload-your-own-data workflow. No paid Google Maps/terrain dependency. No DDHQ branding, proprietary artwork, source code, or pixel-for-pixel copying.
- Show actual source `Updated` date/time only when substantiated; distinguish `Last checked` and partial reporting. Never fabricate source freshness or imply full reporting from partial data.
- Batch work across states instead of one-at-a-time integration; avoid regressions and verify CI/browser behavior.

## Phases
1. **Original ElectionHQ visual identity** — design tokens, navigation, typography, dark analytical panels. Early Vote inspired by DDHQ Votes; Election Night inspired by DDHQ × The Hill, without copying protected expression.
2. **Preserve 3D map + adaptive geographic labels** — major metro labels at national zoom; major cities statewide; smaller cities/towns on county and metro zoom; additional communities at close-up when supported. Prevent collisions, maintain map selection and county overlays. Use appropriately licensed open geographic point data; keep topography optional and avoid paid dependencies. User's Texas and Houston screenshots are visual behavior references.
3. **Early Vote dashboard** — green-intensity map, reported totals, county drilldowns, coverage, source links, honest timestamps, analytical tables.
4. **Election Night dashboard** — distinct public-facing results mode with shared map, branding, reporting status; fictional/demo data must never be represented as live results.
5. **Early Vote timeline** — only when verified historical snapshots exist.
6. **Data transparency** — source `Updated`, `Last checked`, partially reported coverage, attribution and reconciliation; keep publication gate.
7. **Geographic comparisons** — side-by-side consistent metrics and reporting periods, subject to user approval before adding new functionality.
8. **QA and release** — responsive/accessibility/browser validation, performance, source accuracy and explicit user approval before production.

## Parallel blocker: unattended scheduler
- `main` workflow `.github/workflows/temporary-county-staging-scheduler.yml` has `cron: '2-59/5 * * * *'` and calls the development workflow. Manual runs passed, but the user reports **zero scheduled runs**, even after the cron offset change. **Not working / not verified**.
- Do not claim automatic refresh works until a run with event `schedule` is observed and the development verification is successful.
- Investigate GitHub schedule registration, disabled workflow state, Actions settings and default-branch behavior. Keep changes to `main` limited to scheduler repair; do not deploy staging data.
- Once autonomous triggering is proven by two unattended scheduled runs, replace temporary cadence with the approved three-hour schedule.
- Latest development CI verification recorded run `40629646571` at commit `4244faf77d501f36b4300167a0441708e2e4795d`, success, publication_approved=false. This does **not** verify the scheduler.

## Implementation notes
- Frontend `index.html` embeds dark styles and loads Three.js 0.170 via import map. Review `prototype.js`, `unified-ui.js`, and existing geometry/camera coordinate systems before placing geographic labels.
- Keep the base WebGL map functional if external map or label resources fail. Prefer locally bundled, attribution-compliant place-name datasets and zoom-aware sprite/HTML overlays that do not interfere with pointer selection.
- Implement incremental testable changes, inspect results, and do not infer functionality from CI green alone.
