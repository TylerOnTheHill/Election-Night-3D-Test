#!/usr/bin/env python3
"""Find the Maine SOS current 2026 absentee data file without storing voter records.

Source page: https://www.maine.gov/sos/elections-voting/voter-data
Only metadata and aggregate row counts are retained. Never upload raw voter rows.
"""
import argparse
import html.parser
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

URL="https://www.maine.gov/sos/elections-voting/voter-data"
class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.href=None;self.label=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            self.href=dict(attrs).get("href");self.label=[]
    def handle_data(self,data):
        if self.href is not None:self.label.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:
            self.links.append((" ".join(" ".join(self.label).split()),self.href))
            self.href=None;self.label=[]

def discover(page):
    parser=Links();parser.feed(page)
    matches=[(label,urllib.parse.urljoin(URL,href)) for label,href in parser.links
             if "absentee" in label.lower() and ("2026" in label or "2026" in href)]
    if not matches:
        return {"state":"ME","status":"official_file_link_not_exposed","source_page":URL,
                "publication_approved":False}
    return {"state":"ME","status":"official_2026_file_identified",
            "source_page":URL,"candidate_files":[{"label":a,"url":b} for a,b in matches],
            "publication_approved":False,"county_ballots":None}

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    p.add_argument("--input-html",type=Path)
    a=p.parse_args()
    try:
        if a.input_html: page=a.input_html.read_text()
        else:
            req=urllib.request.Request(URL,headers={"User-Agent":"ElectionHQ-official-source-review/1.0"})
            with urllib.request.urlopen(req,timeout=30) as r:page=r.read().decode("utf-8")
        result=discover(page)
    except (OSError,ValueError) as exc:
        result={"state":"ME","status":"official_source_unreachable",
                "source_page":URL,"reason":type(exc).__name__,"publication_approved":False}
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Maine official absentee:",result["status"])
if __name__=="__main__":main()
