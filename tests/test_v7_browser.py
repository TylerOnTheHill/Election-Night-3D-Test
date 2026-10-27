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
    assert snapshot["national"]["total"] > 0
    assert "46 states reporting" in page.locator("#details").text_content(),repr(page.locator("#details").text_content())
    assert page.locator("body").evaluate("(el)=>el.classList.contains('national-early')")
    assert not page.locator(".ev-counties").is_visible()
    assert not page.locator(".ev-gradient").is_visible()
    page.wait_for_function("(expected)=>document.querySelector('#ev-total').textContent === expected",arg=f"{snapshot['national']['total']:,}",timeout=15000)
    assert "Nationwide early ballots" in page.locator(".early-stats").text_content()
    # Select Florida using the same search control a visitor uses.
    florida=next(row for row in snapshot["states"] if row["state_name"]=="Florida")
    page.locator("#search").fill("Florida")
    page.locator("#search").press("Enter")
    page.wait_for_function("document.querySelector('#details').textContent.includes('Florida')",timeout=15000)
    page.wait_for_function("(expected)=>document.querySelector('#ev-total').textContent === expected",arg=f"{florida['total']:,}",timeout=15000)
    assert "Mail ballots" in page.locator(".early-stats").text_content()
    assert f"{florida['mail']:,}" in page.locator(".early-stats").text_content()
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
    texas=next(row for row in snapshot["states"] if row["state_name"]=="Texas")
    page.wait_for_function("(expected)=>document.querySelector('#ev-total').textContent === expected",arg=f"{texas['total']:,}",timeout=15000)
    page.locator("#search").fill("Harris")
    page.locator("#search").press("Enter")
    try:
        page.wait_for_function("document.querySelector('.early-heading strong').textContent.includes('Harris County')",timeout=15000)
    except Exception:
        print("DIAGNOSTIC Harris heading:",repr(page.locator(".early-heading strong").text_content()))
        print("DIAGNOSTIC search:",repr(page.locator("#search").input_value()))
        print("DIAGNOSTIC suggestions:",repr(page.locator("#suggestions").all_text_contents()))
        print("DIAGNOSTIC state:",repr(page.locator("#state-name").text_content()))
        print("DIAGNOSTIC body:",repr(page.locator("body").get_attribute("class")))
        print("DIAGNOSTIC details:",repr(page.locator("#details").text_content()[:1200]))
        print("DIAGNOSTIC errors:",repr(errors))
        page.screenshot(path="/tmp/electionhq-national.png",full_page=True)
        raise
    assert "County participation" in page.locator(".early-stats").text_content()
    assert "Texas official snapshot" in page.locator(".early-stats").text_content()
    assert page.locator("#map-panel-content").evaluate("(el)=>parseFloat(getComputedStyle(el).fontSize)")>=15
    assert "National totals, party composition, historical comparisons and daily trends remain unavailable" not in page.locator(".bottom-races.early-only").last.text_content()
    page.screenshot(path="/tmp/electionhq-national.png",full_page=True)
    page.get_by_role("tab",name="Election Night").click()
    assert not page.locator("body").evaluate("(el)=>el.classList.contains('early')")
    assert not errors, errors
    print("PASS: national totals, Florida selection and attribution, non-Texas isolation, national return, Texas county dashboard, mode toggle")
    mobile=browser.new_page(viewport={"width":390,"height":844},device_scale_factor=1,is_mobile=True,has_touch=True)
    mobile_errors=[]
    mobile.on("pageerror",lambda e: mobile_errors.append(str(e)))
    mobile.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded")
    mobile.wait_for_function("window.__mapWebGLReady===true",timeout=90000)
    mobile.get_by_role("tab",name="Early Vote").click()
    mobile.wait_for_function("document.querySelector('#details').textContent.includes('states reporting')",timeout=30000)
    mobile.wait_for_function("document.querySelector('.early-stats').textContent.includes('Nationwide early ballots')",timeout=15000)
    assert mobile.locator(".early-stats").is_visible()
    assert mobile.locator("#stage").is_visible()
    mobile.screenshot(path="/tmp/electionhq-mobile.png",full_page=True)
    overflow=mobile.evaluate("({scroll:document.documentElement.scrollWidth,viewport:window.innerWidth})")
    assert overflow["scroll"]<=overflow["viewport"]+2,("Mobile horizontal overflow",overflow)
    assert not mobile_errors,mobile_errors
    print("PASS: mobile 390x844, early-vote cards, map, no horizontal overflow or JS errors")
    mobile.close()
    browser.close()
server.shutdown()
