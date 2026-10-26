# Election Tracker 3D — Verified projection update v4

Two tabs: Election Night (fictional simulation) and Early Vote (verified Texas Oct 23 snapshot).

## Geography
- `states-raw.geojson`: locally bundled state outlines derived from Basemap UScounties shapefile for geographic lookup.
- `states-projected.geojson`: projected map coordinates. CONUS uses EPSG:5070, Alaska EPSG:3338, Hawaii EPSG:26905, each scaled into standard map insets. No longitude-wrap stretching.
- `map-preview.svg`: offline static fallback and visual verification of inset geography. Actual interactive WebGL map is provided by `prototype.js` when Three.js CDN loads.
- The county layer still loads from an external service, as in the prior prototype.

## QA
Run `node --check prototype.js` and `node --check unified-ui.js`. Run a local web server to test; do not open `index.html` via file:// because fetch is required.

## Data
Election-night votes and calls are entirely fictional. The Texas county CSV is unchanged. No live national turnout data is connected.
