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

## v4.1 correction
Declared `projectedStates` in the ES module. In v4 this undeclared assignment caused a ReferenceError during `showNational()`, preventing WebGL state meshes from loading while the static SVG fallback remained visible.


## v4.2 inset placement
Alaska moved upward 1.45 projected map units. Hawaii enlarged 50% around its original center and moved upward 1.75 projected units. Static SVG fallback insets were repositioned to match. The 3D interaction code is otherwise unchanged from v4.1.

## v4.3 correction (2026-10-26)
- Mark projected state GeoJSON coordinates explicitly to prevent a second projection in the WebGL renderer (the cause of the miniature/dispersed national map).
- Reproject county polygons into a state-local coordinate system and fit the camera to county geometry instead of preserving the national camera (the cause of blank county views).
- The two JavaScript modules pass `node --check`; a full browser visual check could not be completed because Chromium navigation to the local test server returned `ERR_BLOCKED_BY_ADMINISTRATOR`.


## v4.4 changes
Camera fit rewritten for national and county views; county extrusions reduced to 0.095 map units, with fine bevels; selected lift capped to 0.24 map units. Static fallback remains only while WebGL initializes.


## v4.5 adjustments
- County base extrusion 0.042; selected lift 0.065.
- County 0% framing is closer (factor 0.87); national camera unchanged.
- Alaska 11% larger; Hawaii islands locally enlarged and clustered in their inset.
- The interactive map uses states-projected.geojson; the older SVG files are only fallback previews.
