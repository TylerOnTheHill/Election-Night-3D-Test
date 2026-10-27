#!/usr/bin/env python3
"""Reconcile county-first observations for all ten remaining states in one batch.

Official county observations win; otherwise L2/VoteHub county observations.
Official statewide totals are comparison-only, never replacements for counties.
All inputs must be aggregate, dated, attributed and explicitly licensed.
"""
import argparse,json,datetime
from pathlib import Path
STATES=("AK","AZ","KS","ME","MI","MS","NE","NH","NV","OH")
PROVIDERS=("official","l2","votehub")
def choose(state,observations,official_statewide=None):
    candidates=[]
    for row in observations:
        if row.get("state")!=state or row.get("provider_type") not in PROVIDERS:continue
        if row.get("publication_reuse_allowed") is not True:continue
        if row.get("metric") not in ("returned_ballots","accepted_ballots","ballots_cast"):continue
        if not row.get("source_url") or not row.get("credit"):continue
        try:datetime.date.fromisoformat(row["as_of"])
        except (KeyError,ValueError,TypeError):continue
        counties=row.get("counties")
        if not isinstance(counties,list) or not counties:continue
        seen=set();valid=True
        for c in counties:
            fips=c.get("fips")
            if not isinstance(fips,str) or len(fips)!=5 or not fips.isdigit() or fips in seen:valid=False;break
            if type(c.get("total")) is not int or c["total"]<0:valid=False;break
            seen.add(fips)
        if valid:candidates.append(row)
    candidates.sort(key=lambda x:(x["provider_type"]!="official", -datetime.date.fromisoformat(x["as_of"]).toordinal(),
                                  PROVIDERS.index(x["provider_type"])))
    if not candidates:return {"state":state,"status":"county_source_unavailable","county_total":None,
                               "county_reported":0,"official_statewide":official_statewide,
                               "reconciliation":"not_possible"}
    chosen=candidates[0]
    county_total=sum(c["total"] for c in chosen["counties"])
    if type(official_statewide) is not int or official_statewide<0:
        reconciliation="official_statewide_unavailable";difference=None
    else:
        difference=county_total-official_statewide
        reconciliation="matches" if difference==0 else "differs_check_reporting_cutoff_and_metric"
    return {"state":state,"status":"county_observations_staged",
            "provider":chosen["provider_type"],"source_url":chosen["source_url"],
            "credit":chosen["credit"],"as_of":chosen["as_of"],"metric":chosen["metric"],
            "county_total":county_total,"county_reported":len(chosen["counties"]),
            "reporting_label":"Partially reported",
            "counties":chosen["counties"],"official_statewide":official_statewide,
            "difference_from_official":difference,"reconciliation":reconciliation}
def reconcile(observations,statewide):
    return {"schema":"electionhq-ten-state-county-first-reconciliation-v1",
            "publication_approved":False,"default_total_basis":"sum_of_reported_counties",
            "no_double_counting":True,"states":{s:choose(s,observations,statewide.get(s)) for s in STATES}}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--observations",type=Path,required=True)
    p.add_argument("--official-statewide",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.resolve().is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Never publish unapproved candidate")
    rows=json.loads(a.observations.read_text())
    totals=json.loads(a.official_statewide.read_text())
    result=reconcile(rows,totals)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("County observations staged:",sum(x["status"]=="county_observations_staged" for x in result["states"].values()),"of",len(STATES))
if __name__=="__main__":main()
