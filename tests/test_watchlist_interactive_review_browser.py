"""Exercise the packaged, watermarked four-state review against live staged observations.

Runs only in CI staging; no candidate or county data is published.
"""
import http.server
import json
import socketserver
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

import os
root = Path(os.environ.get("COUNTY_REVIEW_DIR","watchlist-interactive-review"))
candidate = json.loads(Path(os.environ.get("COUNTY_CANDIDATE","watchlist-county-candidate-unapproved.json")).read_text())
assert candidate["publication_approved"] is False
assert candidate["review_required"] is True
SUPPORTED_STATES = set("AK AZ FL GA IA KS ME MI MN MS NC NE NH NV OH SC TX VA WI".split())
assert candidate["states"], "No states available for browser regression"
assert set(candidate["states"]) <= SUPPORTED_STATES, "Unknown state in candidate"
assert all(state["county_count"] > 0 for state in candidate["states"].values()), "Empty state candidate"
assert (root / "README.txt").read_text().count("\n") >= 6
assert "UNAPPROVED COUNTY DATA" in (root / "battleground.html").read_text()
feed = json.loads((root / "data/early-vote/battleground-counties.json").read_text())
assert feed["publication_approved"] is True  # Local simulation only.
assert set(feed["states"]) == set(candidate["states"])
assert all(feed["states"][code]["total"] == candidate["states"][code]["total"] for code in candidate["states"])

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(root), **kwargs)
    def log_message(self, *args):
        pass

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

server = Server(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for code, state in candidate["states"].items():
            expected = state["geographic_count"]
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{server.server_address[1]}/battleground.html?state={code}",
                      wait_until="domcontentloaded")
            state = candidate["states"][code]
            page.wait_for_function(
                "(n) => document.querySelectorAll('#county-preview-rows tr').length===n",
                arg=state["county_count"], timeout=45000)
            page.wait_for_function(
                "(n) => document.querySelectorAll('#county-preview-map path').length===n",
                arg=expected, timeout=45000)
            status = page.locator("#county-preview-status").inner_text()
            assert status.startswith(state["reporting_label"]), (code, status)
            assert f'{state["county_count"]} of {expected}' in status
            assert f'{state["total"]:,}' in page.locator("#county-preview-total").inner_text()
            assert page.locator("input[type=file]").count() == 0
            assert not errors, (code, errors)
            page.close()
        # Release regression: exercise the same real eight-state observations on
        # narrow mobile screens, including state switching and county table.
        for code, state in candidate["states"].items():
            page = browser.new_page(viewport={"width":390,"height":844},is_mobile=True,
                                    has_touch=True)
            errors=[]
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{server.server_address[1]}/battleground.html?state={code}",
                      wait_until="domcontentloaded")
            page.wait_for_function(
                "(n) => document.querySelectorAll('#county-preview-rows tr').length===n",
                arg=state["county_count"],timeout=45000)
            page.wait_for_function(
                "(n) => document.querySelectorAll('#county-preview-map path').length===n",
                arg=state["geographic_count"],timeout=45000)
            assert state["reporting_label"] in page.locator("#county-preview-status").inner_text()
            assert page.locator("input[type=file]").count()==0
            assert not errors,(code,errors)
            page.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
