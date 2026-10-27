# Nationwide Call the Map county audit — first live results

**Run:** https://github.com/TylerOnTheHill/ElectionHQ/actions/runs/40452306572
**Run date:** 2026-10-27 UTC. **Scope:** 46 state-specific JSON feeds referenced in ElectionHQ's nationwide Call the Map snapshot.

## Findings

All 46 downloads passed schema and source-attribution checks. **13** states contained at least one county row; **33** had zero county rows. This is availability in the provider's downloadable feed, **not proof of statewide geographic completeness or a complete national county dataset**.

| State | County rows | Statewide summary minus known county-row sum |
|---|---:|---:|
| Texas | 254 | 0 |
| Virginia | 133 | -177,380 |
| North Carolina | 100 | 0 |
| Iowa | 99 | +232,292 |
| Wisconsin | 72 | +200,338 |
| Florida | 67 | +357,636 |
| Pennsylvania | 67 | 0 |
| Colorado | 64 | 0 |
| Louisiana | 64 | 0 |
| California | 58 | 0 |
| South Carolina | 46 | 0 |
| Oregon | 36 | 0 |
| Maryland | 24 | 0 |

**Interpretation:** Zero difference means numerical reconciliation of the downloaded county rows and statewide summary, not proof that every county has reported or that timestamps match. Nonzero differences may reflect mixed cutoffs, coverage, or category definitions; do not allocate the differences to counties. Virginia's negative difference needs investigation before any publication.

## Next integration gates
1. Validate authoritative county/county-equivalent counts and FIPS crosswalk for each state, including Virginia independent cities.
2. Require provenance and per-county freshness checks; do not turn absent counties into zeros.
3. Distinguish source reporting cutoffs from the time the JSON was downloaded.
4. Prioritize Texas and North Carolina as the next candidate county ingestion pilots, followed by Pennsylvania, California and Colorado. The source's exact field semantics must be validated independently.
5. Keep staging separate from the production dashboard until county coverage and reconciliation pass.

The audit is a source feasibility check, not an election-result certification.
