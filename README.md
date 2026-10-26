# Election Night — Three-quarter 3D Map Prototype

This is an **isolated prototype**, not a replacement for the existing GitHub Pages site. Open via a local HTTP server (`python -m http.server 8000`) or upload the contents to a separate preview branch/site. Do not upload these files over the live site yet.

It renders actual extruded county polygons with Three.js, real shadows, a tilted camera, click/dropdown selection, and the verified October 23, 2026 county dataset. The congressional district toggle retrieves the 119th Congress boundary layer from Census TIGERweb; confirm legal applicability to the election before using as an authoritative election map.

The Three.js library and geographic boundaries load from external HTTPS services, so an internet connection is required. District-level election results are not estimated. This prototype has not been browser-tested in the user's environment.


## v1.4 changes
Reduced OrbitControls sensitivity and constrained vertical orbit; half-height extrusions; illuminated cavity footprints; smooth double-click-to-zoom; closer default camera.

## v1.5
Z-up orbit camera with genuine polar-angle constraints, slower rotation, closer zoom, smooth selection framing for every county and district, and soft pearl-white raised geography with pale cavity illumination. Hard-refresh after deploying to bypass cached JavaScript.


## v1.6 refinements
- Default/reset framing now fills substantially more of the viewport.
- County/district selection uses contextual camera distance instead of extreme close-ups.
- Darker midnight-blue geography increases contrast with pearl-white raised selections.
- Bright white and subtle icy-blue cavity rim remain visible even in shadow.
- Close manual zoom and double-click zoom are preserved.

After uploading, hard-refresh the GitHub Pages site (Ctrl+Shift+R) to avoid cached JavaScript.


v1.7: closer home view, closer selected-county framing, brighter cavities, synchronized zoom slider and typed location search.


## v1.8 updates
- National floating map with 50 state shapes; Alaska/Hawaii displayed as insets.
- Select a state to lift it, select again to lower, or Explore to open county geography.
- All-state county geography sourced from Plotly county FIPS geometry; verified October 23 voting figures remain Texas-only.
- Simultaneous interruptible selection animations; metallic reflective selection and animated lighting.
- Socket outline depth tested behind raised regions; Home/Deselect, Escape, / search shortcut.
- Removed redundant location dropdown and ground plane.
- Uses external state, county, and Three.js assets; test in GitHub Pages (not file://).
- National data availability is geography-only; 2026 election results are NOT provided for other states.
