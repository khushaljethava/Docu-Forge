#!/usr/bin/env python3
"""Fetch line icons for Icon() (engine.py) from Tabler Icons (MIT licence, 5,000+ outline icons), with sources.

  python3 get_icons.py --project my-film search phone          # names containing "phone"
  python3 get_icons.py --project my-film get notebook phone-call map-pin police-badge handcuffs clock

Browse them at https://tabler.io/icons. Saves assets/icons/<name>.svg and records URL and licence in
assets/icons/sources.json (fetch_commons.py credits adds them to credits.md). In a scene:

  film.add(Icon(doc.icon("phone-call"), x, y, 600, W(3, "number"), badge=RED))   # draws itself on

Each fetched icon is parsed once here, so a file the engine can't draw fails now, not mid-render.
"""
import argparse
import json
import pathlib
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from engine import svg_icon  # noqa: E402

VER = "3.19.0"
BASE = f"https://cdn.jsdelivr.net/npm/@tabler/icons@{VER}"
UA = {"User-Agent": "docu-forge/1.0"}


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("cmd", choices=["get", "search"])
    ap.add_argument("names", nargs="+")
    a = ap.parse_args()
    out = pathlib.Path(a.project) / "assets" / "icons"
    if a.cmd == "search":
        files = json.loads(fetch(f"https://data.jsdelivr.com/v1/packages/npm/@tabler/icons@{VER}?structure=flat"))["files"]
        names = sorted(f["name"].split("/")[-1][:-4] for f in files if f["name"].startswith("/icons/outline/"))
        for q in a.names:
            print(q + ": " + ", ".join(n for n in names if q in n))
        return
    out.mkdir(parents=True, exist_ok=True)
    srcp = out / "sources.json"
    sources = json.loads(srcp.read_text()) if srcp.exists() else {}
    for n in a.names:
        url = f"{BASE}/icons/outline/{n}.svg"
        try:
            svg = fetch(url).decode()
        except Exception as e:
            print(f"  {n}: not found ({e}); try `search`"); continue
        if svg_icon(svg).computeTightBounds().isEmpty():
            print(f"  {n}: parsed to nothing, skipped"); continue
        (out / f"{n}.svg").write_text(svg)
        sources[n] = {"file": f"icons/{n}.svg", "source": url, "credit": "Tabler Icons (tabler.io)", "license": "MIT"}
        print(f"  {n}.svg")
    srcp.write_text(json.dumps(sources, indent=1))


if __name__ == "__main__":
    main()
