# Collin County 2026 voting precinct boundary verification

## Critical correction (October 27, 2026)

Collin County's official **Notice of Boundary Changes to Voting Precincts** says the Commissioners Court adopted changes **September 22, 2025**, effective **January 1, 2026**. The notice reports 21 oversized precincts needing changes, nine low-population precinct combinations, nine additional precincts resulting from congressional redistricting under PLANC2333, and 51 precincts with congressional district changes.

Official notice: https://www.collincountytx.gov/Elections/PublishingImages/Lists/DeptNews/AllItems/NOTICE%20OF%20BOUNDARY%20CHANGES%20TO%20VOTING%20PRECINCTS.pdf

**Do not use** the county's separately published 2023-adopted / 2024-effective precinct FeatureServer layer as if it were the 2026 general-election geometry. The ArcGIS `InteractiveMap/Election_Department/MapServer` contains both a `Precincts` layer (0) and 2026 PLANC2333 / proposed split / proposed combination layers (8–10), but the public metadata does not alone establish which boundaries are final and effective for the November 2026 general election.

County layer metadata: https://maps.collincountytx.gov/server/rest/services/InteractiveMap/Election_Department/MapServer
2024-effective FeatureServer metadata: https://maps.collincountytx.gov/server/rest/services/Election/VotingPrecincts_Edited_PlanC2333/FeatureServer/layers

Texas Legislative Council offers `Precincts26P.zip` (2026 **primary** voting precincts) and recommends consulting county officials for authoritative boundaries: https://data.capitol.texas.gov/dataset/precincts

## Next verification steps

1. Obtain county-approved **2026 general-election** precinct polygons and effective-date metadata from Collin County Elections/GIS. Prefer an official static downloadable shapefile or GeoJSON because GitHub-hosted runner requests to the county ArcGIS query endpoint returned HTTP 403.
2. Verify exact `PRECINCT` IDs against November 2026 roster registration-precinct IDs; inspect splits and combinations, including leading zeros.
3. Record the geometry vintage, county approval notice, source URL, download date, source license/permission and total feature count. Avoid equating `Precincts26P` with 2026 general election without confirmation.
4. Use the existing staging-only normalizer and geometry checker. Do not publish local returns until all data and geometry joins reconcile and matching-cutoff totals are verified.

## Publication status

No 2026 general-election precinct geometry or roster-derived turnout has been verified and published. Production main remains unchanged.
