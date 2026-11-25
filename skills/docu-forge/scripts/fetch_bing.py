#!/usr/bin/env python3
"""Search Bing Images with bing-image-downloader, keep every image's source, and add picks to photos.json.

  python3 fetch_bing.py --project my-film search "Raigad district road" --limit 8
  python3 fetch_bing.py --project my-film search "police officer cartoon" --filter clipart --limit 8
  python3 fetch_bing.py --project my-film search "old diary page" --cc --limit 8      # Creative Commons only
  python3 fetch_bing.py --project my-film use bing/raigad-district-road/03.jpg --id P01 --kind color \
          --what "Road through Raigad district"

`search` saves images to assets/photos/bing/<slug>/NN.<ext>, records image URL, page URL, page title,
query and filters for each one in assets/photos/bing/sources.json, and writes <slug>/_sheet.jpg, a
numbered contact sheet to choose from. Look at the sheet before using anything.

`use` copies the record into photos.json (file, url, source = page URL, credit = site, licence), so
prep_assets.py grades it like any photo and `fetch_commons.py credits` lists it in credits.md.

Filters: photo, clipart (cartoons, illustrations), line (line drawings), transparent (cut-outs), gif.

Rights: Bing indexes the open web and most results are copyrighted. --cc keeps Bing's Creative
Commons results only (still confirm the licence on the source page). Everything else is recorded as
"Unknown - verify rights" with license_ok false, and credits.md flags it. Prefer Wikimedia Commons
(fetch_commons.py) when it has the picture. For true crime never use photos of victims, suspects or
private people (SKILL rule 7): use places, objects, maps, icons and cartoons.
"""
import argparse
import fcntl
import html
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw

try:
    from bing_image_downloader.bing import Bing
except ImportError:
    sys.exit("needs bing-image-downloader: pip install bing-image-downloader")

CC = "+filterui:license-L2_L3_L4_L5_L6_L7"
EXTS = {"jpg", "jpeg", "png", "webp", "gif", "bmp"}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "query"


class SourcedBing(Bing):
    """The package's Bing (headers, filters, image validation), plus the page URL and title per result."""

    def __init__(self, query, limit, output_dir, filter="", cc=False, timeout=20):
        super().__init__(query, limit, output_dir, "off", timeout, filter, verbose=False)
        self.cc = cc

    def results(self, pages=4):
        qft = self.get_filter(self.filter or "") + (CC if self.cc else "")
        out, seen = [], set()
        for page in range(pages):
            params = urllib.parse.urlencode({"q": self.query, "first": page * 35, "count": 35, "adlt": self.adult, "qft": qft})
            req = urllib.request.Request("https://www.bing.com/images/async?" + params, None, headers=self.headers)
            text = urllib.request.urlopen(req, timeout=self.timeout).read().decode("utf8", "replace")
            new = 0
            for m in re.findall(r'\bm="(\{[^"]*\})"', text):
                try:
                    d = json.loads(html.unescape(m))
                except ValueError:
                    continue
                if d.get("murl") and d["murl"] not in seen:
                    seen.add(d["murl"]); out.append(d); new += 1
            if not new or len(out) >= self.limit * 3:
                break
        return out


def contact_sheet(files, out, cell=320):
    cols = 4
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (24, 22, 20))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB"); im.thumbnail((cell - 12, cell - 40))
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.paste(im, (x + 6, y + 34))
        d.rectangle((x + 6, y + 4, x + 70, y + 30), fill=(246, 206, 46))
        d.text((x + 12, y + 8), f.stem, fill=(0, 0, 0))
    sheet.save(out, quality=85)


def cmd_search(a):
    proj = pathlib.Path(a.project)
    root = proj / "assets" / "photos" / "bing"
    folder = root / slug(a.query); folder.mkdir(parents=True, exist_ok=True)
    srcp = root / "sources.json"
    sources = {}
    b = SourcedBing(a.query, a.limit, folder, a.filter, a.cc)
    got = []
    for d in b.results():
        if len(got) >= a.limit:
            break
        url = html.unescape(d["murl"]).replace(" ", "%20")
        ext = pathlib.PurePosixPath(urllib.parse.urlsplit(url).path).suffix.lower().lstrip(".")
        f = folder / f"{len(got) + 1:02d}.{ext if ext in EXTS else 'jpg'}"
        try:
            b.save_image(url, f)                      # the package's download + magic-byte check
            Image.open(f).verify()
        except Exception as e:                        # dead links and hotlink blocks are common: skip them
            f.unlink(missing_ok=True); print(f"  skip {url[:90]} ({type(e).__name__})"); continue
        rel = f.relative_to(proj / "assets" / "photos").as_posix()
        sources[rel] = {"file": rel, "query": a.query, "filter": a.filter or "", "cc_filter": a.cc,
                        "image_url": url, "page_url": d.get("purl", ""), "title": d.get("t", ""),
                        "site": urllib.parse.urlsplit(d.get("purl") or url).netloc}
        got.append(f)
        print(f"  {f.name}  {sources[rel]['site']}  {sources[rel]['title'][:60]}")
    with open(root / ".sources.lock", "w") as lock:    # several searches may run at once: merge under a lock
        fcntl.flock(lock, fcntl.LOCK_EX)
        merged = json.loads(srcp.read_text()) if srcp.exists() else {}
        merged.update(sources)
        srcp.write_text(json.dumps(merged, indent=1, ensure_ascii=False))
    if got:
        contact_sheet(got, folder / "_sheet.jpg")
    print(f"{len(got)} images -> {folder}  (sheet: {folder / '_sheet.jpg'}; sources: {srcp})")


def cmd_use(a):
    proj = pathlib.Path(a.project)
    srcp = proj / "assets" / "photos" / "bing" / "sources.json"
    sources = json.loads(srcp.read_text()) if srcp.exists() else {}
    rec = sources.get(a.file)
    if not rec:
        sys.exit(f"{a.file} is not in {srcp}: pass the path printed by search (bing/<slug>/NN.jpg)")
    specp = proj / "photos.json"
    spec = json.loads(specp.read_text()) if specp.exists() else {"grade": "natural", "photos": []}
    entry = {"id": a.id, "file": a.file, "kind": a.kind, "what": a.what, "url": rec["image_url"],
             "source": rec["page_url"] or rec["image_url"], "credit": rec["site"],
             "license": "Creative Commons (Bing filter) - confirm on source page" if rec["cc_filter"] else "Unknown - verify rights",
             "license_ok": False, "found_via": f"Bing: {rec['query']}"}
    if a.crop:
        entry["crop"] = [float(v) for v in a.crop.split(",")]
    spec["photos"] = [p for p in spec["photos"] if p["id"] != a.id] + [entry]
    specp.write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    print(f"{a.id} <- {a.file}  ({rec['site']}); run prep_assets.py, then fetch_commons.py credits")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--limit", type=int, default=8)
    s.add_argument("--filter", choices=["photo", "clipart", "line", "transparent", "gif"], default="")
    s.add_argument("--cc", action="store_true", help="Creative Commons results only")
    u = sub.add_parser("use"); u.add_argument("file"); u.add_argument("--id", required=True)
    u.add_argument("--kind", default="color", choices=["photo", "paper", "doc", "color"])
    u.add_argument("--what", default=""); u.add_argument("--crop", help="left,top,right,bottom fractions")
    a = ap.parse_args()
    {"search": cmd_search, "use": cmd_use}[a.cmd](a)


if __name__ == "__main__":
    main()
