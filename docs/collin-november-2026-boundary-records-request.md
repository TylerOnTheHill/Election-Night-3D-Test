# Collin November 2026 precinct geometry: official records request and evidence checklist

Prepared October 27, 2026. **Draft only; not sent.** ElectionHQ is a public-interest election-data visualization project.

## Why a request is necessary

The Texas Legislative Council (TLC) precinct data portal states that council staff collect boundary changes from county officials for **each statewide primary and general election**, but the available 2026 shapefile is explicitly marked **2026 Primary Election Voting Precincts**:

https://data.capitol.texas.gov/dataset/precincts

The county's September 22, 2025 Commissioners Court order and January 1, 2026 effective date document the adoption of precinct boundary changes. However, an adopted boundary order and a TLC **primary** shapefile do not, by themselves, demonstrate that the exact TLC polygons are valid for the **November 3, 2026 general election**.

Texas Election Code §42.037 requires the county clerk to deliver maps of precinct boundary changes to the Secretary of State within 120 days of adoption, and requires SOS retention for 10 years:

https://statutes.capitol.texas.gov/Docs/EL/pdf/EL.42.pdf

## Proposed request to Collin County Elections / County Clerk

Subject: Request for November 3, 2026 voting precinct boundaries and filed map — Court Order 2025-1013-09-22

Hello,

I am researching the voting precinct geography applicable to Collin County's November 3, 2026 general election for a nonpartisan election-data visualization project.

Could you please provide or direct me to:

1. The final official precinct map and machine-readable precinct boundary dataset (preferably GeoJSON, shapefile, or GIS service) in effect for the November 3, 2026 general election, with the data's effective date and precinct identifiers.
2. The precinct boundary maps delivered to the Texas Secretary of State under Texas Election Code §42.037 following Commissioners Court Order No. 2025-1013-09-22 (agenda item AI-58650, approved September 22, 2025).
3. The authoritative precinct identifier roster applicable to the November 3, 2026 general election, including any precinct splits, combinations, or renumbering.
4. Whether any subsequent Commissioners Court orders, corrections, or other changes altered those boundaries after the September 22, 2025 adoption.
5. Whether the Texas Legislative Council `Precincts26P.zip` (2026 primary election) polygon geometry is identical to the county's final November 2026 general-election precinct geometry. If so, would you please identify the confirming document or official record?
6. Any applicable public reuse, attribution, or licensing terms for publishing a map derived from the geometry.

A public download URL or written confirmation identifying the authoritative source would be very helpful. I do not request individual voter records or personal information.

Thank you.

## Independent SOS records request

Subject: Request for Collin County precinct boundary maps filed under Election Code §42.037

Hello,

Please direct me to or provide the voting-precinct boundary map(s) submitted by the Collin County Clerk under Texas Election Code §42.037 after Collin County Commissioners Court Order No. 2025-1013-09-22 (adopted September 22, 2025), including any amended or superseding maps filed before the November 3, 2026 general election.

If available, please provide the received/filing dates, the precinct-number legend, and a digital GIS version or a public records access link.

This request concerns precinct geography only; no voter information is requested.

Thank you.

## Gate checklist

- [x] County adoption documented (court order and effective date).
- [x] TLC 2026 primary shapefile extracted in staging (273 Collin polygons).
- [x] Geometry basic validity and identifier uniqueness checked.
- [ ] Obtain authoritative November 2026 general-election precinct roster.
- [ ] Obtain county/SOS filed map(s), including any superseding maps.
- [ ] Establish TLC primary vs general geometry equivalence or replace source.
- [ ] Verify source publication permissions.
- [ ] Reconcile precinct IDs and full polygon coverage.
- [ ] Confirm no later orders change applicable precinct boundaries.

**No automatic publication authorization.** Matching the number 273 or even matching all precinct identifiers does not prove polygon equivalence. Keep `publication_approved:false` and `verified_for_2026_general:false` until independent official evidence supports both.
