"""Smoke-test the v7.2 Battleground Watch against its checked-in snapshot."""
import http.server
import json
import socketserver
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

snapshot=json.loads(Path("data/early-vote/US.json").read_text())
by_code={s["state"]:s for s in snapshot["states"]}
watch="AK AZ FL GA IA KS ME MI MN MS NE NV NC OH SC TX VA WI".split()
assert len(watch)==18
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
            page.wait_for_function("document.querySelector('#reported-count').textContent.includes('/ 18')",timeout=30000)
            page.wait_for_function("document.querySelector('#battleground-map').dataset.renderReady==='true'",timeout=30000)
            assert page.locator("#battleground-map canvas").count()==1
            assert page.locator("#battleground-map").get_attribute("data-state-meshes")=="50"
            assert page.locator("#map-zoom-in").count()==1
            assert page.locator("#map-reset").count()==1
            assert page.locator("#state-count").inner_text()=="18"
            assert page.locator("#ehq-national-screen .overview > #ehq-state-table").count()==1
            assert page.locator("#ehq-national-screen .overview > .map-panel").count()==1
            # Verify the approved charcoal theme is actually rendered, not merely declared in CSS.
            surfaces=page.evaluate("""() => {
                const rgb=selector=>getComputedStyle(document.querySelector(selector)).backgroundColor;
                return [rgb('body'),rgb('.ehq-metrics > .card'),rgb('.ehq-watch')];
            }""")
            for color in surfaces:
                values=[int(x.strip()) for x in color.removeprefix('rgb(').removesuffix(')').split(',')]
                assert max(values)-min(values)<=8,(color,surfaces)
            if width==1440:
                bounds=page.evaluate("""() => {
                    const box=s=>document.querySelector(s).getBoundingClientRect();
                    const map=box('#ehq-national-screen .overview > .map-panel');
                    const watch=box('#ehq-state-table');
                    return {mapRight:map.right,watchLeft:watch.left,mapTop:map.top,watchTop:watch.top};
                }""")
                assert bounds['mapRight']<=bounds['watchLeft']+2,bounds
                assert abs(bounds['mapTop']-bounds['watchTop'])<12,bounds
            page.get_by_role("tab",name="State explorer").click()
            page.locator("#explorer-state").select_option("FL")
            assert "Florida" in page.locator("#detail-name").inner_text()
            assert page.locator("#detail-share-link").get_attribute("href")=="./battleground.html?state=FL"
            assert "state=FL" in page.url
            assert page.locator("#rows tr.selected-row").count()==1
            assert page.locator("#rows tr.selected-row").get_attribute("data-code")=="FL"
            if by_code["FL"].get("source_url"):
                assert page.locator("#detail-source-link").get_attribute("href")==by_code["FL"]["source_url"]
            if "FL" in by_code:
                assert page.locator("#detail-total").inner_text()==f"{by_code['FL']['total']:,}"
            page.get_by_role("tab",name="National overview").click()
            page.locator("#search").fill("New Hampshire")
            assert page.locator("#rows tr[data-code=NH]").count()==0
            assert "No matching states" in page.locator("#rows").inner_text()
            # NH remains in the national snapshot, but not the battleground watchlist.
            page.locator("#search").fill("Texas")
            assert page.locator("#rows tr").count()==1
            page.locator("#rows tr").click()
            page.get_by_role("tab",name="State explorer").click()
            assert "Texas" in page.locator("#detail-name").inner_text()
            page.get_by_role("tab",name="National overview").click()
            with page.expect_download() as download_info:
                page.locator("#export-watchlist").click()
            download=download_info.value
            assert download.suggested_filename=="electionhq-battleground-watchlist-2026.csv"
            content=Path(download.path()).read_text(encoding="utf-8-sig")
            assert "Texas" in content and "New Hampshire" not in content
            assert "Updated" in content and "Source URL" in content
            assert not errors,errors
            page.locator("#search").fill("")
            page.locator("#sort").select_option("total")
            page.screenshot(path=f"/tmp/electionhq-battleground-{width}.png",full_page=True)
            page.get_by_role("tab",name="State explorer").click()
            # Unpublished county observations must still show real neutral geography.
            page.wait_for_function("document.querySelector('#county-preview-map')?.dataset.county3d==='ready'",timeout=30000)
            assert page.locator("#county-preview-map canvas").is_visible()
            assert page.locator("#county-preview-map").get_attribute("data-county-meshes")=="254"
            assert page.locator("#county-preview-map").get_attribute("data-reported-meshes")=="0"
            assert "awaiting publication" in page.locator("#county-preview-total").inner_text()
            page.screenshot(path=f"/tmp/electionhq-state-explorer-{width}.png",full_page=True)
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
        # Public Battlegrounds never asks visitors to upload a data file.
        public=browser.new_page()
        public.goto("http://127.0.0.1:8766/battleground.html?state=TX",wait_until="domcontentloaded")
        public.wait_for_function("document.querySelector('#detail-name').textContent.includes('Texas')",timeout=30000)
        assert public.locator("input[type=file]").count()==0
        assert public.locator("a[href='./county-review.html']").count()==0
        assert "Statewide" in public.locator("#county-preview-status").inner_text() or "County" in public.locator("#county-preview-status").inner_text()
        public.close()
        # Synthetic approved-feed fixture exercises automatic loading, not a user upload.
        # These are intentionally fabricated test counts and never checked into the public feed.
        approved=json.loads(json.dumps(fixture))
        approved["publication_approved"]=True
        for state in approved["states"].values():
            state["status"]="published"
            state["total_basis"]="sum_of_reported_counties"
            state["geographic_count"]=254 if len(state["counties"])==254 else 100
            state["coverage_complete"]=True
            state["credit"]="Synthetic test"
        automatic=browser.new_page()
        automatic.route("**/data/early-vote/battleground-counties.json",
            lambda route:route.fulfill(status=200,content_type="application/json",body=json.dumps(approved)))
        automatic.goto("http://127.0.0.1:8766/battleground.html?state=NC",wait_until="domcontentloaded")
        automatic.wait_for_function("document.querySelectorAll('#county-preview-map path').length===100",timeout=30000)
        automatic.wait_for_function("['ready','fallback'].includes(document.querySelector('#county-preview-map').dataset.county3d)",timeout=45000)
        assert automatic.locator("#county-preview-map").get_attribute("data-county3d")=="ready",automatic.locator("#county-preview-map").get_attribute("data-county3d-error")
        assert automatic.locator("#county-preview-map canvas.county-3d-canvas").count()==1
        assert automatic.locator("#county-preview-map").get_attribute("data-county-meshes")=="100"
        nc_first=approved["states"]["NC"]["counties"][0]
        automatic.locator(f"#county-preview-rows tr[data-fips='{nc_first['fips']}']").click()
        assert nc_first["name"] in automatic.locator("#county-selected-detail").inner_text()
        assert automatic.locator("#county-preview-map").evaluate(
            "(host) => !!host.querySelector('canvas.county-3d-canvas')"
        )
        assert automatic.locator(f"#county-preview-rows tr[data-fips='{nc_first['fips']}']").get_attribute("class")=="selected-row"
        automatic.wait_for_function("document.querySelector('#county-preview-title').textContent.includes('North Carolina')",timeout=10000)
        assert automatic.locator("#county-preview-total").inner_text()==f"County ballots reported: {approved['states']['NC']['total']:,}"
        assert automatic.locator("#ehq-state-screen").is_visible()
        assert automatic.locator("#ehq-county-view").is_visible()
        assert automatic.locator("#ehq-national-screen").is_hidden()
        automatic.get_by_role("tab",name="County table").click()
        assert automatic.locator("#ehq-county-table-view").is_visible()
        assert automatic.locator("#ehq-county-table-view #county-preview-rows tr").count()==100
        assert automatic.locator("#ehq-county-table-view .scroll").is_visible()
        automatic.get_by_role("tab",name="County map").click()
        assert automatic.locator("#ehq-county-view").is_visible()
        assert automatic.locator("input[type=file]").count()==0
        automatic.locator("#explorer-state").select_option("TX")
        automatic.wait_for_function("document.querySelectorAll('#county-preview-map path').length===254",timeout=30000)
        automatic.wait_for_function("document.querySelector('#county-preview-map').dataset.countyMeshes==='254'",timeout=30000)
        assert automatic.locator("#county-preview-map canvas.county-3d-canvas").count()==1
        automatic.close()
        # Partial TX feed: all geographic shapes remain; missing counties stay gray.
        partial=json.loads(json.dumps(approved))
        tx=partial["states"]["TX"]
        tx["counties"]=tx["counties"][:150]
        tx["county_count"]=150
        tx["coverage_complete"]=False
        tx["total"]=sum(row["total"] for row in tx["counties"])
        partial_page=browser.new_page()
        partial_page.route("**/data/early-vote/battleground-counties.json",
            lambda route:route.fulfill(status=200,content_type="application/json",body=json.dumps(partial)))
        partial_page.goto("http://127.0.0.1:8766/battleground.html?state=TX",wait_until="domcontentloaded")
        partial_page.wait_for_function("document.querySelectorAll('#county-preview-map path').length===254",timeout=30000)
        partial_page.wait_for_function("document.querySelector('#county-preview-map').dataset.reportedMeshes==='150' || document.querySelector('#county-preview-map').dataset.county3d==='fallback'",timeout=45000)
        assert partial_page.locator("#county-preview-map").get_attribute("data-county3d")=="ready",partial_page.locator("#county-preview-map").get_attribute("data-county3d-error")
        assert partial_page.locator("#county-preview-map").get_attribute("data-county-meshes")=="254"
        assert "Partially reported" in partial_page.locator("#county-preview-status").inner_text()
        assert "150 of 254" in partial_page.locator("#county-preview-status").inner_text()
        assert "County ballots reported:" in partial_page.locator("#county-preview-total").inner_text()
        assert partial_page.locator("#county-preview-map path[fill='#30343b']").count()==104
        partial_page.close()
        # Approved county data remains visible when statewide reporting cutoff is unavailable.
        unknown_cutoff=json.loads(json.dumps(partial))
        unknown_cutoff["states"]["TX"]["statewide_cutoff"]=None
        no_cutoff=browser.new_page()
        no_cutoff.route("**/data/early-vote/battleground-counties.json",
            lambda route:route.fulfill(status=200,content_type="application/json",body=json.dumps(unknown_cutoff)))
        no_cutoff.goto("http://127.0.0.1:8766/battleground.html?state=TX",wait_until="domcontentloaded")
        no_cutoff.wait_for_function("document.querySelectorAll('#county-preview-map path').length===254",timeout=30000)
        assert "Reporting cutoff unavailable" in no_cutoff.locator("#county-preview-status").inner_text()
        assert "County ballots reported:" in no_cutoff.locator("#county-preview-total").inner_text()
        no_cutoff.close()
        # Roadmap expansion: Florida renders real geography without invented ballots.
        fl_geography=browser.new_page()
        fl_geography.goto("http://127.0.0.1:8766/battleground.html?state=FL",wait_until="domcontentloaded")
        fl_geography.wait_for_function("document.querySelector('#county-preview-map')?.dataset.county3d==='ready'",timeout=45000)
        assert fl_geography.locator("#county-preview-map").get_attribute("data-county-meshes")=="67"
        assert fl_geography.locator("#county-preview-map").get_attribute("data-reported-meshes")=="0"
        assert "awaiting publication" in fl_geography.locator("#county-preview-total").inner_text()
        fl_geography.close()
        # Synthetic Florida partial feed: two observed counties, 65 still unreported.
        fl_feed=json.loads(json.dumps(approved))
        fl_feed["states"]["FL"]={
            "status":"published","total_basis":"sum_of_reported_counties",
            "provider":"Synthetic test","credit":"Synthetic test",
            "statewide_cutoff":None,"geographic_count":67,
            "coverage_complete":False,"total":300,
            "counties":[
                {"fips":"12001","name":"Alachua","total":100},
                {"fips":"12003","name":"Baker","total":200}
            ]
        }
        fl_partial=browser.new_page()
        fl_partial.route("**/data/early-vote/battleground-counties.json",
            lambda route:route.fulfill(status=200,content_type="application/json",body=json.dumps(fl_feed)))
        fl_partial.goto("http://127.0.0.1:8766/battleground.html?state=FL",wait_until="domcontentloaded")
        fl_partial.wait_for_function("document.querySelector('#county-preview-map')?.dataset.reportedMeshes==='2'",timeout=45000)
        assert fl_partial.locator("#county-preview-map").get_attribute("data-county-meshes")=="67"
        assert "Partially reported" in fl_partial.locator("#county-preview-status").inner_text()
        assert "2 of 67" in fl_partial.locator("#county-preview-status").inner_text()
        assert fl_partial.locator("#county-preview-total").inner_text()=="County ballots reported: 300"
        fl_partial.close()
        # All expansion states render county boundaries without fabricated ballot counts.
        for state_code,expected in [("VA",133),("IA",99),("WI",72),("SC",46)]:
            geography=browser.new_page()
            geography.goto(f"http://127.0.0.1:8766/battleground.html?state={state_code}",wait_until="domcontentloaded")
            geography.wait_for_function("document.querySelector('#county-preview-map')?.dataset.county3d==='ready'",timeout=45000)
            assert geography.locator("#county-preview-map").get_attribute("data-county-meshes")==str(expected)
            assert geography.locator("#county-preview-map").get_attribute("data-reported-meshes")=="0"
            assert "awaiting publication" in geography.locator("#county-preview-total").inner_text()
            geography.close()
        # An optional new state must not require TX/NC in the same approved feed.
        independent={"schema":"electionhq-county-preview-v1","publication_approved":True,
                     "states":{"IA":{"status":"published","total_basis":"sum_of_reported_counties",
                     "provider":"Synthetic test","credit":"Synthetic test","statewide_cutoff":None,
                     "geographic_count":99,"coverage_complete":False,"total":42,
                     "counties":[{"fips":"19001","name":"Adair","total":42}]}}}
        optional=browser.new_page()
        optional.route("**/data/early-vote/battleground-counties.json",
            lambda route:route.fulfill(status=200,content_type="application/json",body=json.dumps(independent)))
        optional.goto("http://127.0.0.1:8766/battleground.html?state=IA",wait_until="domcontentloaded")
        optional.wait_for_function("document.querySelector('#county-preview-map')?.dataset.reportedMeshes==='1'",timeout=45000)
        assert optional.locator("#county-preview-map").get_attribute("data-county-meshes")=="99"
        assert "1 of 99" in optional.locator("#county-preview-status").inner_text()
        assert optional.locator("#county-preview-total").inner_text()=="County ballots reported: 42"
        optional.close()
        # Geographic completeness must not override the approved reporting label.
        mismatched=json.loads(json.dumps(approved))
        mismatched["states"]["NC"]["reporting_label"]="Partially reported"
        mismatch_page=browser.new_page()
        mismatch_page.route("**/data/early-vote/battleground-counties.json",
            lambda route:route.fulfill(status=200,content_type="application/json",body=json.dumps(mismatched)))
        mismatch_page.goto("http://127.0.0.1:8766/battleground.html?state=NC",wait_until="domcontentloaded")
        mismatch_page.wait_for_function("document.querySelector('#county-preview-status')?.textContent.includes('100 of 100')",timeout=30000)
        assert "Partially reported" in mismatch_page.locator("#county-preview-status").inner_text()
        assert mismatch_page.locator("#county-preview-complete-note").is_hidden()
        mismatch_page.close()
        browser.close()
finally:
    server.shutdown()
