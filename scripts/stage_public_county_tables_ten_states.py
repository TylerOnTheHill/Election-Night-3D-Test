#!/usr/bin/env python3
"""Retrieve dated county early-vote tables for all ten states, in parallel.

County totals are combined across disjoint voting methods only (returned mail
and in-person). Source attribution and licensing must be reviewed before reuse.
"""
import argparse,concurrent.futures,datetime as dt,html.parser,json,re,urllib.request
from pathlib import Path
STATES=("AK","AZ","KS","ME","MI","MS","NE","NH","NV","OH")
BASE="https://election-watch.50501vets.com/map/"
class Text(html.parser.HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)
def retrieve(code,method):
    url=f"{BASE}{code}?cat={method}"
    req=urllib.request.Request(url,headers={"User-Agent":"ElectionHQ-2026-aggregate-review/1.0"})
    with urllib.request.urlopen(req,timeout=35) as r:raw=r.read(900000).decode("utf-8","replace")
    parser=Text();parser.feed(raw)
    lines=[re.sub(r"\\s+"," ",x).strip() for x in parser.parts]
    lines=[x for x in lines if x]
    try:start=lines.index("By county")
    except ValueError:return {"state":code,"method":method,"url":url,"status":"county_table_absent"}
    section=lines[start+1:]
    pairs=[];seen=set()
    for i,v in enumerate(section):
        if v in ("By day","Why the numbers move after polls close","Share","County","Ballots"):continue
        if v.startswith("See ") or v.startswith("How ") or v.startswith("Why "):break
        if re.fullmatch(r"[\\d,]+",v) and i>0:
            name=section[i-1]
            if not re.fullmatch(r"[A-Za-z .'-]{2,45}",name) or name in seen:continue
            seen.add(name);pairs.append({"name":name,"total":int(v.replace(",",""))})
    return {"state":code,"method":method,"url":url,
            "status":"county_table_found" if pairs else "county_table_unparsed",
            "diagnostic_text_sample":section[:36] if not pairs else None,
            "counties":pairs,"county_rows":len(pairs),
            "attribution":"50501 Vets / civicAPI (reported from election sources)",
            "publication_approved":False,"reuse_rights_verified":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        jobs={(code,method):pool.submit(retrieve,code,method) for code in STATES for method in ("returned","inperson")}
        results=[]
        for (code,method),future in jobs.items():
            try:results.append(future.result())
            except (OSError,ValueError,TimeoutError) as exc:
                results.append({"state":code,"method":method,"status":"source_unavailable","error":type(exc).__name__})
    a.output.write_text(json.dumps({"schema":"electionhq-ten-state-real-county-table-review-v1",
      "publication_approved":False,"license_review_required":True,
      "methods_not_summed_until_validated":True,"observations":results},indent=2)+"\n")
    print("County tables retrieved:",sum(r.get("status")=="county_table_found" for r in results),"of",len(results))
if __name__=="__main__":main()
