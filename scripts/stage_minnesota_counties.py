#!/usr/bin/env python3
"""Stage official Minnesota county accepted early ballots, never publish automatically."""
import argparse
import json
import re
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

SOURCE="https://sos.mn.gov/election-administration-campaigns/data-maps/absentee-data/"
CENSUS="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
CREDIT="Minnesota Secretary of State, 2026 General Election Absentee Data"
class Tables(HTMLParser):
    def __init__(self):
        super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=="table":self.table=[] 
        elif tag=="tr" and self.table is not None:self.row=[]
        elif tag in ("td","th") and self.row is not None:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ("td","th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()));self.cell=None
        elif tag=="tr" and self.row is not None:
            if self.row:self.table.append(self.row)
            self.row=None
        elif tag=="table" and self.table is not None:
            self.tables.append(self.table);self.table=None

def parse(html,census):
    page=Tables();page.feed(html)
    text=" ".join(re.sub(r"<[^>]*>"," ",html).split())
    date_match=re.search(r"Absentee Counts by County as of\s+(\w+\s+\d{1,2},\s+2026)",text,re.I)
    if not date_match:raise ValueError("Missing 2026 county reporting cutoff")
    cutoff=datetime.strptime(date_match.group(1),"%B %d, %Y").date().isoformat()
    mapping={}
    for feature in census["features"]:
        fips=feature["id"]
        if not fips.startswith("27"):continue
        name=feature["properties"]["NAME"]
        mapping[name.casefold()]=fips
    if len(mapping)!=87:raise ValueError("Minnesota Census crosswalk must contain 87 counties")
    found=None
    for table in page.tables:
        for i,row in enumerate(table):
            headers=" ".join(row).casefold()
            if "county" in headers and "accepted" in headers and "mail" in headers and "person" in headers:
                found=table[i+1:];break
        if found is not None:break
    if found is None:raise ValueError("Official accepted-ballot county table not found")
    counties=[];seen=set()
    def number(s):
        s=s.replace(",","").strip()
        if not re.fullmatch(r"\d+",s):raise ValueError("Non-numeric accepted ballot count")
        return int(s)
    for row in found:
        if len(row)<4:continue
        name=row[0].strip()
        key=name.removesuffix(" County").casefold()
        if key not in mapping:continue
        fips=mapping[key]
        if fips in seen:raise ValueError("Duplicate Minnesota county")
        seen.add(fips)
        mail=number(row[2]);early=number(row[3])
        counties.append({"fips":fips,"name":name,"total":mail+early,"mail":mail,
            "in_person":early,"file_as_of":cutoff,"source_url":SOURCE,"credit":CREDIT})
    if not counties:raise ValueError("No observed Minnesota counties")
    counties.sort(key=lambda x:x["fips"])
    total=sum(x["total"] for x in counties)
    mail_match=re.search(r"Accepted ballots\s*-\s*by mail\s*\\([^)]*\\)\s*:\s*([\\d,]+)",text,re.I)
    early_match=re.search(r"Accepted ballots\s*-\s*in person\s*\\([^)]*\\)\s*:\s*([\\d,]+)",text,re.I)
    statewide= int(mail_match.group(1).replace(",",""))+int(early_match.group(1).replace(",","")) if mail_match and early_match else None
    reconciled=statewide is not None and total==statewide
    return {"schema":"electionhq-county-preview-v1","publication_approved":False,
        "review_required":True,"states":{"MN":{"status":"candidate_pending_publication_approval",
        "provider":"Minnesota Secretary of State","credit":CREDIT,
        "statewide_cutoff":cutoff,"census_geography_source":"US county GeoJSON FIPS crosswalk (Plotly mirror; official Census verification pending)",
        "census_geography_url":CENSUS,"county_count":len(counties),"geographic_count":87,
        "coverage_complete":len(counties)==87,"reporting_label":"Fully reported" if len(counties)==87 and reconciled else "Partially reported",
        "statewide_reconciled":reconciled,"total":total,"total_basis":"sum_of_reported_counties",
        "provider_statewide_total":statewide,"counties":counties}}}

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    a=p.parse_args();target=Path(a.output).resolve()
    if target.is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Staging must not write public county feeds")
    def get(url):
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"ElectionHQ-source-review/1.0"}),timeout=30) as r:return r.read()
    raw=get(CENSUS).decode("utf-8-sig")
    if not raw.lstrip().startswith("["):
        raise ValueError("Census county crosswalk endpoint did not return JSON: "+raw[:160])
    result=parse(get(SOURCE).decode("utf-8"),json.loads(raw))
    target.write_text(json.dumps(result,indent=2)+"\n")
    print("Minnesota official county rows staged:",result["states"]["MN"]["county_count"])
if __name__=="__main__":main()
