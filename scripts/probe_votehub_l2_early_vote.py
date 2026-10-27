#!/usr/bin/env python3
"""Check VoteHub and L2 early-vote availability for all 19 watchlist states.

Discovery only: a reachable HTML dashboard is NOT evidence of a licensed
machine-readable county feed or a verified 2026 ballot count.
"""
import argparse
import json
import html.parser
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from audit_national_early_vote import WATCH

VOTEHUB="https://votehub.com/2026-early-vote-tracker"
L2="https://early.l2datamapping.com/"
class ScriptLinks(html.parser.HTMLParser):
    def __init__(self):
        super().__init__();self.scripts=[]
    def handle_starttag(self,tag,attrs):
        if tag=="script":
            src=dict(attrs).get("src")
            if src:self.scripts.append(src)

def inspect_dashboard(url):
    request=urllib.request.Request(url,headers={"User-Agent":"ElectionHQ-source-discovery/1.0"})
    with urllib.request.urlopen(request,timeout=25) as response:
        body=response.read(400000).decode("utf-8","replace")
    parser=ScriptLinks();parser.feed(body)
    scripts=list(dict.fromkeys(urllib.parse.urljoin(url,x) for x in parser.scripts))
    # Only same-host assets: never follow arbitrary cross-origin scripts.
    scripts=[x for x in scripts if urllib.parse.urlsplit(x).hostname==urllib.parse.urlsplit(url).hostname][:25]
    candidates=[]
    for script in scripts:
        try:
            req=urllib.request.Request(script,headers={"User-Agent":"ElectionHQ-source-discovery/1.0"})
            with urllib.request.urlopen(req,timeout=20) as response:
                js=response.read(900000).decode("utf-8","replace")
            endpoints=set(re.findall(r'https?://[^\\s"\\x27<>]{8,160}',js))
            relevant=[x for x in endpoints if any(k in x.lower() for k in ("api","early","ballot","vote"))]
            if relevant:
                candidates.append({"script_url":script,"endpoint_candidates":sorted(relevant)[:20]})
        except (OSError,ValueError):
            continue
    return {"script_assets_found":len(scripts),"endpoint_candidates_unverified":candidates,
            "county_feed_verified":False,"license_review_required":True}

def check(url):
    request=urllib.request.Request(url,headers={"User-Agent":"ElectionHQ-source-discovery/1.0"})
    try:
        with urllib.request.urlopen(request,timeout=25) as response:
            body=response.read(250000)
            return {"status":"page_reachable","http_status":response.status,
                    "content_type":response.headers.get("Content-Type","").split(";")[0],
                    "bytes_inspected":len(body)}
    except urllib.error.HTTPError as exc:
        return {"status":"http_error","http_status":exc.code}
    except (OSError,ValueError) as exc:
        return {"status":"unreachable","error_type":type(exc).__name__}
def discover(checker=check):
    sources={"VoteHub":{"url":VOTEHUB,**checker(VOTEHUB)}}
    for state in sorted(WATCH):
        url=L2+"?"+urllib.parse.urlencode({"state":state,"type":"returned"})
        sources["L2_"+state]={"url":url,**checker(url)}
    try:
        sources["VoteHub"]["script_inspection"]=inspect_dashboard(VOTEHUB)
    except (OSError,ValueError):
        sources["VoteHub"]["script_inspection"]={"status":"inspection_unavailable"}
    try:
        sources["L2_NH"]["script_inspection"]=inspect_dashboard(L2+"?state=NH&type=returned")
    except (OSError,ValueError):
        sources["L2_NH"]["script_inspection"]={"status":"inspection_unavailable"}
    return {"schema":"electionhq-votehub-l2-discovery-v1","publication_approved":False,
            "ballot_counts_extracted":False,"county_feed_verified":False,
            "license_review_required":True,"sources":sources}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();result=discover()
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("VoteHub/L2: checked",len(result["sources"]),"dashboard URLs; no totals published")
if __name__=="__main__":main()
