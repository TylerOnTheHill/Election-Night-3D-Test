# Subcounty early-vote geography: source and integrity requirements (v7.2)

The Houston-area example supplied during development depicts areas smaller than counties, with city labels and red/blue shading. A screenshot does **not** establish whether the units are precincts, census blocks, ZIPs, or a modeled surface, nor whether colors mean voter registration, modeled party support, or actual votes. No such interpretation is authorized without the source legend and methodology.

## Scope
- Preserve the existing national/state/county reporting; add a separately labeled **local reporting area** level only where boundaries and tabular returns can be joined by a stable source-defined geographic ID.
- City names are orientation labels, not necessarily aggregation units.
- Prefer official county election-administration precinct returns or other explicitly documented local reporting areas; confirm election year, reporting cutoff, mail/early ballot semantics, and whether reporting units are residence precincts or voting locations.
- Record the geometry vintage, identifier crosswalk, source URLs, extraction time, reporting cutoff, geographic coverage and any suppressed or unmatched rows.
- Reject unmatched polygons, duplicate IDs, ambiguous crosswalks and inconsistent totals. Do not allocate county totals proportionally or treat absent precincts as zero.
- Distinguish *registered-party ballot returns* from *candidate votes* and *modeled partisan estimates*. Texas voter registration does not generally encode party affiliation as a standard registration field; do not color Texas precincts as D/R early returns absent a verified method/source.
- Include explicit legends and accessible tooltips: metric, numerator, denominator, date, geographic unit, source, coverage.
- Only compare shades when the denominator and reporting cutoff are comparable. Use a neutral unavailable fill where no valid subcounty data exists.

## Proposed staged schema
Each local area: `state_fips`, `county_fips`, `area_id`, `area_name`, `area_type`, `geometry_source`, `geometry_vintage`, `ballots_total`, `registered_dem`, `registered_rep`, `mail`, `in_person`, `metric_kind`, `file_as_of`, `source_url`, `credit`. Unknown quantities must be `null`, never inferred. Store geometry separately and require a validated join.

## Next steps
1. Identify the screenshot's source and exact legend before treating its colors as party ballot returns.
2. Audit a candidate official precinct-level feed in a pilot county for 2026 early-vote returns and matching precinct boundaries.
3. Build and test a staging-only local geography adapter, then a neutral local map prototype; no production changes without explicit approval.
