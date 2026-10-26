# Election Night 3D Prototype v2.1 — SIMULATED DEMO

Upload the four files together to your GitHub Pages repository root.

**Important:** Every election return, call, lead, flip, and reporting percentage in this version is fabricated for interface testing. Do not present them as actual election results, predictions, or verified returns. The national Senate and House counters are interactive *simulators*, not connected to the geographic fictional calls. Senate simulator baseline uses 34 Democratic-caucus seats and 31 Republican seats with 35 unresolved as a visual test; validate real election and membership data before production. House simulator starts at zero secured seats. The governor and Senate ballot-state lists are illustrative and must be verified against official 2026 ballots before production.

New: inward-growing national congressional bars, centered finish line, fictional seat-call buttons and control announcements, blue-left/red-right individual vote bars, leading labels, simulated reporting %, yellow ties, subdued non-election states, striped synthetic flips, simplified hover cards, Alaska/Hawaii inset adjustments, clicking backdrop/empty map to return nationally, and reduced camera jumping on selected-state-to-county transitions.

Known limitations: Requires internet for geometry and Three.js. Geographic simulation and national call simulator are independent. National-to-county camera can still reframe when entering from an unselected state; select a state first to keep its camera position. House results are geographic placeholders rather than district-accurate results. The original verified Texas October 23 early-vote CSV is unchanged and separate from simulated election returns.


## v2.2 changes (October 26, 2026)
- National camera automatically fits the 50-state geography with margin; Alaska and Hawaii insets re-scaled and repositioned.
- Individual race status/reporting moved to top; leading/hold/gain next to party labels.
- Balance-of-power panel removes redundant center wording; synthetic called/held/flipped counts shown separately.
- Selection outline and recessed footprint glow enhanced.
- Flipped geography uses finer clipped top-surface stripes.
- Zoom distance scale recalibrated for national camera and range input restyled.
- All election totals, race calls, hold/flip labels and reporting figures remain fabricated demo data.
- Browser rendering has not been validated on every device.


## v2.3 camera and inset refinements
- National default and 0% zoom are the same camera position; Reset Camera returns to 0%.
- National camera distance is computed from map bounds and the actual viewport aspect ratio.
- Alaska and Hawaii inset geometry is repositioned and scaled, including antimeridian unwrapping for Alaska.
- Hover card leading/gain labels appear next to the corresponding party.
- State-to-county transitions retain the current camera position; return to national restores national framing.
- All simulated results remain fictional; national call counters are demonstration-only and not connected to the map.

### v2.4 map inset correction
Alaska is reduced and relocated directly below the western continental states; Hawaii is placed immediately east of Alaska, at visible scale. National default camera is the 0% baseline and fits the inset geography with padding.
