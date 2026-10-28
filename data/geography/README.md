# ElectionHQ geographic place labels

The current bundled `us-cities-top-1000.json` is a **fallback** containing 1,000 US cities sourced from [Plotly's US cities dataset](https://github.com/plotly/datasets/blob/master/us-cities-top-1k.csv). It is **not** a complete town or community dataset.

The Three.js label engine now supports optional nationwide expansion through one file per state, `places-by-state/<two-digit state FIPS>.json`, using the same `electionhq-place-points-v1` schema:

```json
{"schema":"electionhq-place-points-v1","places":[["Community name","Texas",12345,29.1234,-95.1234]]}
```

Rows are `[name, full state name, population or priority proxy, latitude, longitude]`. Population must be numeric and should reflect an actual documented population; **do not invent population values**. Where population is unknown, establish a documented nonpopulation ranking approach before import. The UI loads only the selected state's additional file, caches it, and falls back to the existing nationwide 1,000-city dataset if a state file is missing. Source licensing and attribution must be reviewed and documented before adding any external dataset. The source repository [kelvins/US-Cities-Database](https://github.com/kelvins/US-Cities-Database) describes approximately 29,880 cities under an MIT license, but has **not** been imported or validated; its records do not include population, so they cannot be treated as population-ranked without a separately justified ranking system.

The current label renderer operates in state/county mode. National city labels, detailed small-town coverage, browser visual verification, and projection handling for custom insets remain outstanding. No production deployment is authorized by this file.
