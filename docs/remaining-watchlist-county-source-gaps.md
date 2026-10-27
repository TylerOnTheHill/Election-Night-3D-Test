# Remaining 12 battleground states — verified source gap (October 27, 2026)

The live Call the Map state-endpoint discovery artifact from [workflow 40517648487](https://github.com/TylerOnTheHill/ElectionHQ/actions/runs/40517648487) contains **zero county observation rows in all 12 remaining states**. This is a provider limitation, not proof that no county election office publishes county-level totals.

| State | County rows in provider endpoint | Provider statewide observation | County status |
| --- | ---: | ---: | --- |
| AK | 0 | 46,204 | Independent source required |
| AZ | 0 | 971,184 | Independent source required |
| GA | 0 | 1,780,239 | Independent source required |
| KS | 0 | 204,155 | Independent source required |
| ME | 0 | 186,169 | Independent source required |
| MI | 0 | 1,082,646 | Independent source required |
| MN | 0 | 419,189 | Independent source required |
| MS | 0 | 56,049 | Independent source required |
| NE | 0 | 151,915 | Independent source required |
| NV | 0 | 148,516 | Independent source required |
| NH | 0 | unavailable | Independent source required |
| OH | 0 | 1,084,305 | Independent source required |

These are **provider observations at its October 27, 2026 13:29:16 UTC check**, not separately independently verified state election-office figures. Do not present them as county subtotals, infer zero counties, or add them to the existing national total again.

## Next source-integration gate

For each state, identify the official state election-office or county reporting portal and its 2026 election-specific aggregate endpoint. Confirm reporting method, observation cutoff, election identity, and whether the county values are ballots cast versus requests/issued ballots. Only then add a state-specific normalized adapter and verified Census FIPS mapping. Partial county coverage is allowed: observed counties display immediately with **Partially reported**, unknown counties remain unknown, and the newest verified statewide total remains separate. Run browser tests and owner review before any public publication.

**No release authorization** is implied by this document or the successful discovery workflow.
