#!/usr/bin/env python3
"""Check VoteHub and L2 early-vote availability for all 19 watchlist states.

Discovery only: a reachable HTML dashboard is NOT evidence of a licensed
machine-readable county feed or a verified 2026 ballot count.
"""
import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from audit_national_early_vote import WATCH

VOTEHUB="https://votehub.com/2026-early-vote-tracker"
L2="https://early.l2datamapping.com/"
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
    return {"schema":"electionhq-votehub-l2-discovery-v1","publication_approved":False,
            "ballot_counts_extracted":False,"county_feed_verified":False,
            "license_review_required":True,"sources":sources}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();result=discover()
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("VoteHub/L2: checked",len(result["sources"]),"dashboard URLs; no totals published")
if __name__=="__main__":main()
