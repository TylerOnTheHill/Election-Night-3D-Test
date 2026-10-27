#!/usr/bin/env python3
"""Stage official Alaska 2026 received-ballot statewide snapshot.

Alaska's official ballot-type totals are statewide, NOT county-equivalent
observations. Preserve the distinction until geographic source data exists.
"""
import argparse
import json
import re
import urllib.request
from html import unescape
from pathlib import Path

URL="https://www.elections.alaska.gov/research/statistics/"

def parse(html):
    text=unescape(re.sub(r"<[^>]+>", " ", html))
    text=re.sub(r"\s+", " ", text)
    start=text.find("2026 General Election")
    end=text.find("2026 Primary Election", start+1)
    if start<0 or end<0:
        raise ValueError("Official 2026 general election section not found")
    section=text[start:end]
    def value(pattern):
        match=re.search(pattern,section,re.I)
        if not match:
            raise ValueError("Missing Alaska received-ballot field: "+pattern)
        return int(match.group(1).replace(",",""))
    issued=value(r"Total Ballots Issued:\s*([\d,]+)")
    received=value(r"Total Ballots Received:\s*([\d,]+)")
    if received>issued:
        raise ValueError("Received ballots exceed issued ballots")
    cutoff=re.search(r"Table last updated\s+([A-Za-z]+\s+\d{1,2},\s+2026\s+at\s+\d{1,2}:\d{2}\s*[ap]m)",section,re.I)
    if not cutoff:
        raise ValueError("Missing official update timestamp")
    return {"state":"AK","source":"Alaska Division of Elections",
            "source_url":URL,"election":"2026 General Election",
            "issued_ballots":issued,"received_ballots":received,
            "source_cutoff":cutoff.group(1),"geography":"statewide",
            "county_equivalent_observations":None,
            "county_coverage_status":"county_data_unavailable",
            "publication_approved":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-html",type=Path)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.resolve().is_relative_to((Path.cwd()/"data/early-vote").resolve()):
        raise ValueError("Official statewide review is not a county feed")
    if a.input_html:
        raw=a.input_html.read_text()
    else:
        req=urllib.request.Request(URL,headers={"User-Agent":"ElectionHQ-AK-official-source/1.0"})
        with urllib.request.urlopen(req,timeout=35) as response:
            raw=response.read().decode("utf-8")
    result=parse(raw)
    a.output.write_text(json.dumps(result,indent=2)+chr(10))
    print("Alaska official statewide received:",result["received_ballots"],"cutoff:",result["source_cutoff"])

if __name__=="__main__":
    main()
