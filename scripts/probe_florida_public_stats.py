#!/usr/bin/env python3
"""Inspect official public aggregate download links, without voter-level data."""
import re
import urllib.request
from html.parser import HTMLParser
URL="https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports/PublicStats"
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.current=None
    def handle_starttag(self,tag,attrs):
        if tag=="a": self.current={"href":dict(attrs).get("href",""),"text":""}
    def handle_data(self,data):
        if self.current is not None: self.current["text"]+=data
    def handle_endtag(self,tag):
        if tag=="a" and self.current is not None:
            self.links.append(self.current); self.current=None
req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 (ElectionHQ official aggregate review)"})
with urllib.request.urlopen(req,timeout=35) as response:
    html=response.read(2_000_000).decode("utf-8","replace")
print("Page bytes:",len(html))
parser=Links();parser.feed(html)
for link in parser.links:
    if any(term in (link["href"]+" "+link["text"]).lower() for term in ("download","voted","early","mail","stat")):
        print("LINK",repr(link["text"].strip()[:90]),repr(link["href"][:260]))
for term in ("Voted Early","Voted Vote-by-Mail","Download File","49894","ElectionNumber"):
    match=re.search(re.escape(term),html,re.I)
    print("CONTEXT",term,repr(html[max(0,match.start()-280):match.end()+350]) if match else "NOT FOUND")
