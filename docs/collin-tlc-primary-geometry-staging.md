# Collin County 2026 precinct geometry: independent TLC source

## Verified in GitHub Actions (October 27, 2026)

- Source: Texas Legislative Council statewide **2026 primary** voting precinct shapefile, downloaded from the TLC data portal (see `scripts/fetch_tlc_collin_2026_primary.py`).
- Successful source extraction: workflow run [40456978711](https://github.com/TylerOnTheHill/ElectionHQ/actions/runs/40456978711), **273 Collin County polygon features**, five extractor tests passed. No voter records were downloaded.
- Successful geometry validation after fixture correction: workflow run [40457165631](https://github.com/TylerOnTheHill/ElectionHQ/actions/runs/40457165631), including geometry checks for county, unique IDs, WGS84 coordinates, polygon rings and bounds.
- Output: downloadable GitHub Actions artifact `tlc-collin-2026-primary-geometry-not-general-verified`, containing `collin-2026-primary.geojson`, `report.json`, and (in updated workflow) `geometry-validation.json`. Artifacts expire after seven days.
- Local map: open `boundary-review.html` from the feature branch, choose the downloaded `collin-2026-primary.geojson` file, then click precincts. This viewer never loads voter records or uploads files.

## Critical limits

1. **Not verified for November 3, 2026 general election.** The TLC source is marked primary. County approval notice confirms 2026 changes, but does not independently establish whether the TLC primary precinct roster and geometries match the general-election boundaries. Do not publish as certified 2026 general-election precinct geography.
2. **No precinct-level early-vote counts obtained or joined.** Geometry alone cannot support turnout maps or partisan classification.
3. `PREC` identifiers are preserved exactly, including leading zeros. Reconcile identifiers with county general-election precinct roster before any join.
4. Geographic validation checks basic structure and region, not topological overlaps, gaps, or legal boundary certification.
5. Neither the staging preview nor the successful CI checks grant publication approval.

## Next source verification

Obtain an official Collin County November 2026 precinct roster or election-specific precinct map. Compare precinct IDs, split/combined precincts and geometry changes against the 273 TLC primary polygons. If different, request county-certified general-election GIS geometry or a licensed replacement. Record source URL, election date, approval evidence and full-coverage reconciliation in the geometry manifest. Only then reconsider the geography publication gate.
