#!/usr/bin/env python3
"""Stage 2026 MI/OH county ballot counts, county-first, without raw voter data.
Official dashboards are preferred if a machine-readable aggregate feed is
configured; civicAPI-backed 50501 Vets county tables are the documented fallback.
"""
import argparse,collections,html.parser,json,re,urllib.request
from pathlib import Path
URL="https://election-watch.50501vets.com/map/{state}?cat={method}"
CENSUS="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
EXPECTED={"MI":83,"OH":88}
STATE_PREFIX={"MI":"26","OH":"39"}
class Table(html.parser.HTMLParser):
    def __init__(self):
        super().__init__();self.cells=[];self.row=[];self.rows=[];self.inside=False;self.cell=False
    def handle_starttag(self,tag,attrs):
        if tag=="table":self.inside=True
        if self.inside and tag=="tr":self.row=[]
        if self.inside and tag in ("td","th"):self.cell=True;self.cells=[]
    def handle_data(self,data):
        if self.cell:self.cells.append(data)
    def handle_endtag(self,tag):
        if self.inside and tag in ("td","th"):
            self.row.append(" ".join(" ".join(self.cells).split()));self.cell=False
        if self.inside and tag=="tr" and self.row:self.rows.append(self.row)
        if tag=="table":self.inside=False
def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"ElectionHQ-aggregate-election-data/1.0"})
    with urllib.request.urlopen(req,timeout=40) as r:return r.read(3000000).decode("utf-8","replace")
def parse_table(html,state,method):
    # Only the HTML after the actual 'By county' heading, not the daily history.
    marker=re.search(r"By county",html,re.I)
    if not marker:raise ValueError(f"{state} {method}: no county heading")
    parser=Table();parser.feed(html[marker.start():])
    counties={}
    for row in parser.rows:
        if len(row)<2:continue
        name=row[0].strip();num=row[1].replace(",","").strip()
        if not re.fullmatch(r"[A-Za-z .'-]{2,48}",name) or not re.fullmatch(r"\d+",num):continue
        if name.lower() in ("county","total","ballots"):continue
        if name in counties:raise ValueError(f"duplicate {name}")
        counties[name]=int(num)
    if len(counties)!=EXPECTED[state]:raise ValueError(f"{state} {method}: {len(counties)} counties; expected {EXPECTED[state]}")
    # Statewide count is separately reported on the page; fail if totals disagree.
    text=re.sub(r"<[^>]+>"," ",html)
    phrase="ballots returned" if method=="returned" else "ballots in person"
    m=re.search(r"([\d,]+)\s+"+phrase,text,re.I)
    if not m:raise ValueError(f"{state} {method}: statewide number absent")
    total=int(m.group(1).replace(",",""))
    if sum(counties.values())!=total:raise ValueError(f"{state} {method}: county sum {sum(counties.values())} != reported {total}")
    return counties,total
def census_map():
    data=json.loads(get(CENSUS));out={}
    for f in data["features"]:
        name=f["properties"].get("NAME","").strip()
        code=str(f.get("id","")).zfill(5)
        if code[:2] in STATE_PREFIX.values():out[(code[:2],name.casefold())]=code
    return out
def build():
    geography=census_map();states={}
    for state in ("MI","OH"):
        methods=("returned","inperson") if state=="OH" else ("returned",)
        found={}
        for method in methods:
            html=get(URL.format(state=state,method=method))
            counties,total=parse_table(html,state,method)
            found[method]=(counties,total)
        names=set().union(*(set(c) for c,t in found.values()))
        if len(names)!=EXPECTED[state]:raise ValueError(f"{state}: incomplete counties")
        rows=[]
        for name in sorted(names):
            fips=geography.get((STATE_PREFIX[state],name.casefold()))
            if not fips:raise ValueError(f"{state}: missing Census FIPS {name}")
            mail=found.get("returned",({},0))[0].get(name,0)
            early=found.get("inperson",({},0))[0].get(name,0)
            rows.append({"fips":fips,"name":name,"mail":mail,"in_person":early,
                         "total":mail+early})
        states[state]={"status":"county_candidate_pending_official_precedence_review",
            "provider":"50501 Vets / civicAPI","credit":"50501 Vets / civicAPI",
            "source_urls":[URL.format(state=state,method=m) for m in methods],
            "as_of":"2026-10-27","county_count":len(rows),
            "total":sum(r["total"] for r in rows),
            "returned_total":found["returned"][1],
            "in_person_total":found.get("inperson",({},0))[1],
            "metric":"returned_absentee_plus_early_in_person" if state=="OH" else "returned_absentee_only",
            "county_total_basis":"sum_of_county_observations",
            "publication_approved":False,"counties":rows}
    return {"schema":"electionhq-mi-oh-county-candidate-v1","publication_approved":False,"states":states}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    result=build();a.output.write_text(json.dumps(result,indent=2)+"\n")
    for k,v in result["states"].items():print(k,v["county_count"],v["total"],v["metric"])
if __name__=="__main__":main()
