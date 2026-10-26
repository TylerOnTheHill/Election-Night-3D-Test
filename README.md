# Election Night 3D Prototype — v1.9

Upload all four files to the root of the separate Election-Night-3D-Test GitHub Pages repository. Do not replace the production Early Vote Tracker.

## Changes
- Dark charcoal/gray theme with reserved results palette: Republican `#8A232D`, Democratic `#1E488A`, other `#62447B`, unavailable `#3A3D42`.
- Single-click any state to enter its county map immediately. Statewide/federal major-races overview appears before any county is selected.
- Click a county to raise and inspect; click it again to lower. The Texas panel retains the verified October 23 early-vote statistics.
- Hover state or county to preview name and available figures; candidate returns are clearly marked unavailable.
- Left-drag pans; right-drag orbits; mouse wheel zooms. National and state camera framing adjusted.
- Alaska geometry handles the international date line consistently; Alaska and Hawaii are separated in national insets.
- Softer, restrained metallic selection and a diagonal sheen (~4.5 seconds of travel, with a pause); no sweeping directional spotlight.
- A map race selector is included. It does not fabricate candidate leads or recolor geography without verified results.

## Data limitations
- Texas county cumulative early voting is from the October 23, 2026 official SOS dataset, 254 counties, 3,724,290 ballots.
- These early-vote figures are *not* candidate election results. There is currently no connected live election-results feed; the all-major-races panel is a labeled placeholder until results are integrated.
- Geographic boundaries load at runtime from Plotly, PublicaMundi, and Census TIGERweb (congressional district layer availability may vary). Non-Texas county geometry is geographic only.
- No district candidate totals are estimated from county aggregates.
- The prototype requires internet access to load Three.js and boundary datasets.

## QA
The JavaScript was syntax checked. A complete live-browser/remote-service verification has not been performed. Please test in the separate GitHub Pages preview.
