# Election Tracker 3D — Unified design prototype

This is a local GitHub Pages-ready prototype with two top-level tabs: **Election Night** and **Early Vote**. It preserves the existing Three.js interactive map and adds a VoteHub/DDHQ-inspired dark dashboard layout.

**Election Night**: all election returns, seat counters, and race calls are entirely fictional test data. The top Senate/House summaries mirror the existing fictional call simulator (open the details accordion to operate it).

**Early Vote**: only the bundled Texas Secretary of State October 23, 2026 county turnout CSV is used. The file reconciles to 254 counties and 3,724,290 ballots. The national map highlights Texas; other states show no turnout data. Historical comparisons and timelines are intentionally empty rather than fabricated. County colors show relative raw ballot totals, not turnout rates.

The original 3D map, geographic services, and navigation code remain in `prototype.js`. The new dashboard controls are in `unified-ui.js`. Requires internet for Three.js and GeoJSON.

This is a functional visual approximation of the approved mockups, not a pixel-perfect implementation. In particular, nationwide early vote data, real election results, and fully accurate congressional race mapping are not connected. Do not publish the simulated results without prominent DEMO labels.
