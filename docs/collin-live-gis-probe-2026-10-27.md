# Collin County official GIS live probe — 2026-10-27

## Observed result

GitHub Actions run [40456184408](https://github.com/TylerOnTheHill/ElectionHQ/actions/runs/40456184408) executed the official Collin County precinct geometry downloader. All five downloader unit tests passed, but the live request to `https://maps.collincountytx.gov/server/rest/services/InteractiveMap/Election_Department/MapServer/0/query` failed with **HTTP 403 Forbidden** from the GitHub-hosted runner.

The ArcGIS layer metadata is publicly viewable and confirms a `PRECINCT` integer attribute and polygon geometry. This **does not** prove the `query` endpoint permits automated bulk retrieval. No precinct polygon file was obtained in that run. Do not treat the job as proof of geographic coverage.

The probe workflow now uploads a machine-readable blocked-source report rather than fabricating polygon counts. The report status is `source_fetch_failed_no_geography` and its `precinct_count` is `null`.

## Follow-up research / engineering

- Confirm with Collin County GIS whether automated download is permitted and whether an alternate official downloadable precinct GeoJSON/shapefile exists.
- Cross-check the separate official Collin FeatureServer `Election/VotingPrecincts_Edited_PlanC2333`, which includes a layer explicitly described as approved September 25, 2023 and effective January 1, 2024. This is not, by itself, verification of November 2026 applicability.
- If an authorized file is obtained, normalize with `scripts/normalize_collin_precinct_geojson.py`, validate against a real 2026 general-election roster aggregate, and run `scripts/check_tx_precinct_geometry.py`.
- Keep all local data staging-only until full identifier reconciliation, matching reporting cutoffs, and boundary-vintage confirmation.

## Scope

No voter-level records were downloaded or committed. No live precinct totals were published. Production `main` remains unchanged.
