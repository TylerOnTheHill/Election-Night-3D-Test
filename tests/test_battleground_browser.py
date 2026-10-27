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
            assert page.locator("#detail-share-link").get_attribute("href")=="./battleground.html?state=FL"
            assert "state=FL" in page.url
            assert page.locator("#rows tr.selected-row").count()==1
            assert page.locator("#rows tr.selected-row").get_attribute("data-code")=="FL"
            if by_code["FL"].get("source_url"):
                assert page.locator("#detail-source-link").get_attribute("href")==by_code["FL"]["source_url"]
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
            with page.expect_download() as download_info:
                page.locator("#export-watchlist").click()
            download=download_info.value
            assert download.suggested_filename=="electionhq-battleground-watchlist-2026.csv"
            content=Path(download.path()).read_text(encoding="utf-8-sig")
            assert "Texas" in content and "New Hampshire" not in content
            assert "Reporting cutoff" in content and "Source URL" in content
            assert not errors,errors
            page.screenshot(path=f"/tmp/electionhq-battleground-{width}.png",full_page=True)
            page.close()
        deep=browser.new_page()
        deep.goto("http://127.0.0.1:8766/battleground.html?state=NH",wait_until="domcontentloaded")
        deep.wait_for_function("document.querySelector('#detail-name').textContent.includes('New Hampshire')",timeout=30000)
        assert "Not offered" in deep.locator("#detail-inperson").inner_text()
        assert deep.locator("#detail-share-link").get_attribute("href")=="./battleground.html?state=NH"
        deep.close()
        # Synthetic fixture: verify staging-only county geography and selection.
        # Values below are test fixtures, not election observations.
        reference=json.loads(Path("data/sources/tx-nc-county-fips-reference.json").read_text())
        states={}
        for code,items in reference["states"].items():
            rows=[{"fips":item["fips"],"name":item["name"],"total":i+1,
                   "mail":None,"in_person":None,"file_as_of":"TEST FIXTURE",
                   "source_url":"https://example.org","credit":"Synthetic test"}
                  for i,item in enumerate(items)]
            states[code]={"status":"preview_only_not_approved_for_publication",
                          "county_count":len(rows),"total":sum(r["total"] for r in rows),
                          "provider":"Synthetic test","statewide_cutoff":"TEST FIXTURE",
                          "census_geography_source":"FIPS reference","counties":rows}
        fixture={"schema":"electionhq-county-preview-v1","publication_approved":False,"states":states}
        page=browser.new_page(viewport={"width":1440,"height":900})
        errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.goto("http://127.0.0.1:8766/county-review.html",wait_until="domcontentloaded")
        page.locator("#file").set_input_files({"name":"staging-county-preview.json",
            "mimeType":"application/json","buffer":json.dumps(fixture).encode()})
        page.wait_for_function("document.querySelectorAll('#county-map svg path').length===254",timeout=30000)
        page.wait_for_function("document.querySelector('#county-map-legend').textContent.includes('254 of 254')",timeout=15000)
        first=states["TX"]["counties"][0]
        page.locator(f"#county-map path[data-fips='{first['fips']}']").focus()
        page.keyboard.press("Enter")
        assert page.locator("#rows tr").count()==1
        assert first["name"] in page.locator("#rows tr").inner_text()
        page.locator("#search").fill("")
        page.locator("#rows tr").first.focus()
        selected=page.locator("#rows tr").first.locator("td").nth(1).inner_text()
        page.keyboard.press("Enter")
        assert page.locator(f"#county-map path[data-fips='{selected}']").get_attribute("stroke")=="#ffffff"
        page.locator("#state").select_option("NC")
        page.wait_for_function("document.querySelectorAll('#county-map svg path').length===100",timeout=30000)
        page.wait_for_function("document.querySelector('#county-map-legend').textContent.includes('100 of 100')",timeout=15000)
        assert not errors,errors
        page.screenshot(path="/tmp/electionhq-county-staging.png",full_page=True)
        page.close()
        # Integrated Battlegrounds county explorer: local staging fixture, not public data.
        integrated=browser.new_page(viewport={"width":1440,"height":900})
        errors=[]
        integrated.on("pageerror",lambda e:errors.append(str(e)))
        integrated.goto("http://127.0.0.1:8766/battleground.html?state=TX",wait_until="domcontentloaded")
        integrated.wait_for_function("document.querySelector('#detail-name').textContent.includes('Texas')",timeout=30000)
        integrated.locator("#county-preview-file").set_input_files({"name":"staging-county-preview.json",
            "mimeType":"application/json","buffer":json.dumps(fixture).encode()})
        integrated.wait_for_function("document.querySelectorAll('#county-preview-map svg path').length===254",timeout=30000)
        assert integrated.locator("#county-preview-total").inner_text()==f"State total: {states['TX']['total']:,}*"
        assert "Sum of complete county reports" in integrated.locator("#battleground-county-preview").inner_text()
        integrated.locator(f"#county-preview-map path[data-fips='{first['fips']}']").focus()
        integrated.keyboard.press("Enter")
        assert first["name"] in integrated.locator("#county-selected-detail").inner_text()
        assert integrated.locator(f"#county-preview-rows tr[data-fips='{first['fips']}']").get_attribute("class")=="selected-row"
        integrated.locator("#battleground-map path[data-code='NC']").focus()
        integrated.keyboard.press("Enter")
        integrated.wait_for_function("document.querySelectorAll('#county-preview-map svg path').length===100",timeout=30000)
        assert integrated.locator("#county-preview-total").inner_text()==f"State total: {states['NC']['total']:,}*"
        integrated.locator("#battleground-map path[data-code='FL']").focus()
        integrated.keyboard.press("Enter")
        assert integrated.locator("#battleground-county-preview").is_hidden()
        assert "Texas and North Carolina" in integrated.locator("#county-preview-status").inner_text()
        assert not errors,errors
        integrated.close()
        browser.close()
finally:
    server.shutdown()
