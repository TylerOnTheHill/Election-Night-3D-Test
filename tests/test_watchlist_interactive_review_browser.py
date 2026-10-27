"""Exercise the packaged, watermarked four-state review against live staged observations.

Runs only in CI staging; no candidate or county data is published.
"""
import http.server
import json
import socketserver
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path("watchlist-interactive-review")
candidate = json.loads(Path("watchlist-county-candidate-unapproved.json").read_text())
assert candidate["publication_approved"] is False
assert candidate["review_required"] is True
assert set(candidate["states"]) == {"VA", "IA", "WI", "SC"}
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
        for code, expected in (("VA", 133), ("IA", 99), ("WI", 72), ("SC", 46)):
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
        browser.close()
finally:
    server.shutdown()
    server.server_close()
