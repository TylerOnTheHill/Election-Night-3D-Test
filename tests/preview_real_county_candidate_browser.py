"""Render actual staged TX/NC county observations in the existing dashboard.

This test serves an in-memory approved copy to a local browser route only.
It does not modify the source candidate, write a public feed, or publish data.
"""
import http.server
import json
import socketserver
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

candidate_path = Path("staging-county-publication-candidate.json")
candidate = json.loads(candidate_path.read_text())
assert candidate["publication_approved"] is False
assert candidate["review_required"] is True
for code, expected in (("TX", 254), ("NC", 100)):
    state = candidate["states"][code]
    assert state["status"] == "candidate_pending_publication_approval"
    assert 0 < state["county_count"] <= expected
    assert sum(row["total"] for row in state["counties"]) == state["total"]

# Browser fixture only: simulate the existing publication contract without
# changing or publishing the staged candidate.
browser_fixture = json.loads(json.dumps(candidate))
browser_fixture["publication_approved"] = True
for state in browser_fixture["states"].values():
    state["status"] = "published"

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

server = Server(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_address[1]}"
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for code, expected in (("TX", 254), ("NC", 100)):
            state = browser_fixture["states"][code]
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("**/data/early-vote/battleground-counties.json",
                       lambda route: route.fulfill(status=200, content_type="application/json",
                                                   body=json.dumps(browser_fixture)))
            page.goto(f"{base}/battleground.html?state={code}", wait_until="domcontentloaded")
            page.wait_for_function(
                "(count) => document.querySelectorAll('#county-preview-rows tr').length === count",
                arg=state["county_count"], timeout=30000)
            assert page.locator("#county-preview-total").inner_text().find(f"{state['total']:,}") >= 0
            assert page.locator("#county-preview-status").inner_text().startswith(state["reporting_label"])
            assert f"{state['county_count']} of {expected}" in page.locator("#county-preview-status").inner_text()
            assert page.locator("input[type=file]").count() == 0
            # Check the actual geography/map rendering, not just table values.
            page.wait_for_function(
                "(count) => document.querySelectorAll('#county-preview-map path').length === count",
                arg=expected, timeout=30000)
            assert not errors, errors
            Path("staging-county-browser-preview").mkdir(exist_ok=True)
            page.screenshot(path=f"staging-county-browser-preview/{code}.png", full_page=True)
            print(code, state["county_count"], "counties rendered;", state["total"],
                  "reported ballots; browser-only, not published")
            page.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
