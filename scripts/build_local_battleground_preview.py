"""Create a LOCAL-ONLY interactive v7.2 preview from a validated, unapproved candidate.

The dashboard requires the published-feed JSON contract. This package simulates
that contract ONLY inside a clearly watermarked, downloadable local preview.
It never changes the repository's public data or deploys a website.
"""
import argparse
import json
import shutil
from pathlib import Path
from validate_county_publication_candidate import validate

ROOT = Path(__file__).resolve().parents[1]
ASSETS = [
    "battleground.html", "battleground.js", "battleground-layout.js",
    "battleground-map.js", "battleground-map-3d.js",
    "battleground-county-preview.js", "battleground-county-3d.js",
    "battleground-studio.css", "electionhq-theme.css",
    "electionhq-map-controls.js", "states-projected.geojson",
    "data/early-vote/US.json",
]

def build(candidate_path: Path, output: Path):
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    if candidate.get("publication_approved") is not False or candidate.get("review_required") is not True:
        raise ValueError("Only unapproved review candidates may be packaged")
    validate(candidate)
    codes = sorted(candidate["states"])
    output.mkdir(parents=True, exist_ok=True)
    for asset in ASSETS:
        target = output / asset
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / asset, target)
    fixture = json.loads(json.dumps(candidate))
    fixture["publication_approved"] = True
    for state in fixture["states"].values():
        state["status"] = "published"
    feed = output / "data/early-vote/battleground-counties.json"
    feed.write_text(json.dumps(fixture, separators=(",", ":")), encoding="utf-8")
    html_path = output / "battleground.html"
    html = html_path.read_text(encoding="utf-8")
    banner = ('<div role="status" style="position:sticky;top:0;z-index:9999;'
              'background:#60431a;color:#fff;padding:9px 15px;text-align:center;'
              'font:700 13px system-ui">LOCAL STAGING PREVIEW ONLY — '
              'UNAPPROVED COUNTY DATA — NOT PUBLISHED</div>')
    if "<body>" not in html:
        raise ValueError("Dashboard body insertion point missing")
    html_path.write_text(html.replace("<body>", "<body>" + banner, 1), encoding="utf-8")
    links = "\n".join(
        f"{code}: http://127.0.0.1:8766/battleground.html?state={code}" for code in codes)
    (output / "README.txt").write_text(
        "ElectionHQ v7.2 LOCAL INTERACTIVE STAGING PREVIEW\n"
        "County totals are UNAPPROVED staging observations, not a public release.\n"
        "This preview simulates the approved-feed interface ONLY inside the local package.\n"
        "Never upload or deploy this package as a public website.\n\n"
        "From the extracted folder run: python -m http.server 8766 --bind 127.0.0.1\n"
        + links + "\n"
        "The browser needs internet access to load existing map libraries.\n",
        encoding="utf-8")
    print(f"Built LOCAL-ONLY staging preview: {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.candidate, args.output)
