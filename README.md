# Election Night — Three-quarter 3D Map Prototype

This is an **isolated prototype**, not a replacement for the existing GitHub Pages site. Open via a local HTTP server (`python -m http.server 8000`) or upload the contents to a separate preview branch/site. Do not upload these files over the live site yet.

It renders actual extruded county polygons with Three.js, real shadows, a tilted camera, click/dropdown selection, and the verified October 23, 2026 county dataset. The congressional district toggle retrieves the 119th Congress boundary layer from Census TIGERweb; confirm legal applicability to the election before using as an authoritative election map.

The Three.js library and geographic boundaries load from external HTTPS services, so an internet connection is required. District-level election results are not estimated. This prototype has not been browser-tested in the user's environment.
