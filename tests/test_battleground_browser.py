"""Smoke-test the v7.2 Battleground Watch against its checked-in snapshot."""
import http.server
import json
import socketserver
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

snapshot=json.loads(Path("data/early-vote/US.json").read_text())
by_code={s["state"]:s for s in snapshot["states"]}
watch="AK AZ FL GA IA KS ME MI MN MS NE NV NH NC OH SC TX VA WI".split()
assert len(watch)==19
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
server=Server(("127.0.0.1",8766),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for width,height in [(1440,900),(390,844)]:
            page=browser.new_page(viewport={"width":width,"height":height})
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto("http://127.0.0.1:8766/battleground.html",wait_until="domcontentloaded")
            page.wait_for_function("document.querySelector('#reported-count').textContent.includes('/ 19')",timeout=30000)
            page.wait_for_function("document.querySelectorAll('#battleground-map svg path.watch').length===19",timeout=30000)
            assert page.locator("#battleground-map svg path.watch").count()==19
            colors=page.locator("#battleground-map svg path.watch").evaluate_all("(els)=>[...new Set(els.map(e=>e.getAttribute('fill')))]")
            assert colors==["#268cff"],colors
            assert page.locator("#battleground-map svg path.nonwatch").count()>=25
            assert page.locator("#state-count").inner_text()=="19"
            page.locator("#battleground-map path[data-code='FL']").focus()
            page.keyboard.press("Enter")
            assert "Florida" in page.locator("#detail-name").inner_text()
            if "FL" in by_code:
                assert page.locator("#detail-total").inner_text()==f"{by_code['FL']['total']:,}"
            page.locator("#search").fill("New Hampshire")
            assert page.locator("#rows tr").count()==1
            assert "Not offered" in page.locator("#rows tr").inner_text()
            page.locator("#rows tr").focus()
            page.keyboard.press("Enter")
            assert "Excuse-required absentee" in page.locator("#detail-description").inner_text()
            page.locator("#search").fill("Texas")
            assert page.locator("#rows tr").count()==1
            page.locator("#rows tr").click()
            assert "Texas" in page.locator("#detail-name").inner_text()
            assert not errors,errors
            page.screenshot(path=f"/tmp/electionhq-battleground-{width}.png",full_page=True)
            page.close()
        browser.close()
finally:
    server.shutdown()
