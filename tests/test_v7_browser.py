from playwright.sync_api import sync_playwright
import http.server, socketserver, threading, json
from pathlib import Path

snapshot=json.loads(Path("data/early-vote/US.json").read_text())
assert len(snapshot["states"])>=30
assert sum(s["total"] for s in snapshot["states"])==snapshot["national"]["total"]
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
class Server(socketserver.ThreadingTCPServer): allow_reuse_address=True
server=Server(("127.0.0.1",8765),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--enable-webgl","--use-gl=angle","--use-angle=swiftshader","--disable-web-security"])
    page=browser.new_page(viewport={"width":1440,"height":900})
    errors=[]
    page.on("pageerror",lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded")
    page.wait_for_function("window.__mapWebGLReady===true",timeout=90000)
    page.get_by_role("tab",name="Early Vote").click()
    try:
        page.wait_for_function("document.querySelector('#details').textContent.includes('46 states reporting')",timeout=20000)
    except Exception:
        print("DIAGNOSTIC details:",repr(page.locator("#details").text_content()[:2000]))
        print("DIAGNOSTIC body classes:",page.locator("body").get_attribute("class"))
        print("DIAGNOSTIC console errors:",errors)
        page.screenshot(path="/tmp/electionhq-national.png",full_page=True)
        raise
    # The national map is already the default geography. Its back-navigation button
    # is intentionally hidden there, so do not attempt to click it.
    # Verify the national total in the loaded source, and the state coverage in UI.
    assert snapshot["national"]["total"] == 29398708
    assert "46 states reporting" in page.locator("#details").text_content(),repr(page.locator("#details").text_content())
    assert page.locator("body").evaluate("(el)=>el.classList.contains('national-early')")
    assert not page.locator(".ev-counties").is_visible()
    assert not page.locator(".ev-gradient").is_visible()
    page.wait_for_function("document.querySelector('#ev-total').textContent === '29,398,708'",timeout=15000)
    assert "Nationwide early ballots" in page.locator(".early-stats").text_content()
    # Select Florida using the same search control a visitor uses.
    florida=next(row for row in snapshot["states"] if row["state_name"]=="Florida")
    page.locator("#search").fill("Florida")
    page.locator("#search").press("Enter")
    page.wait_for_function("document.querySelector('#details').textContent.includes('Florida')",timeout=15000)
    page.wait_for_function("document.querySelector('#ev-total').textContent === '3,142,750'",timeout=15000)
    assert "Mail ballots" in page.locator(".early-stats").text_content()
    state_text=page.locator("#details").text_content()
    assert f"{florida['total']:,}" in state_text,("Florida ballot count missing",state_text[:1500])
    assert "Party registration, not candidate preference." in state_text or florida.get("dem") is None
    assert page.locator("#map-results-panel").is_visible()
    # Drill into a non-Texas state: Texas county participation must never appear.
    page.locator("#panel-explore").click()
    page.wait_for_function("document.querySelector('#state-name').textContent==='Florida' && document.querySelector('#loading').style.display==='none'",timeout=45000)
    assert page.locator("body").evaluate("(el)=>el.classList.contains('nontexas-early')")
    assert "No verified county turnout" in page.locator("#details").text_content()
    assert not page.locator(".ev-counties").is_visible()
    # Return to the national map using the now-visible navigation control.
    page.locator("#national").click()
    page.wait_for_function("document.querySelector('#state-name').textContent==='United States' && document.querySelector('#loading').style.display==='none'",timeout=45000)
    assert page.locator("body").evaluate("(el)=>el.classList.contains('national-early')")
    page.wait_for_function("document.querySelector('#ev-total').textContent === '29,398,708'",timeout=15000)
    # Texas county navigation should restore its county-specific dashboard.
    page.locator("#search").fill("Texas")
    page.locator("#search").press("Enter")
    page.locator("#panel-explore").click()
    page.wait_for_function("document.querySelector('#state-name').textContent==='Texas' && document.querySelector('#loading').style.display==='none'",timeout=45000)
    assert not page.locator("body").evaluate("(el)=>el.classList.contains('nontexas-early')")
    assert page.locator(".ev-counties").is_visible()
    assert "Texas" in page.locator(".early-heading").text_content()
    page.screenshot(path="/tmp/electionhq-national.png",full_page=True)
    page.get_by_role("tab",name="Election Night").click()
    assert not page.locator("body").evaluate("(el)=>el.classList.contains('early')")
    assert not errors, errors
    print("PASS: national totals, Florida selection and attribution, non-Texas isolation, national return, Texas county dashboard, mode toggle")
    browser.close()
server.shutdown()
