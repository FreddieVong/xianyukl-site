#!/usr/bin/env python3
"""Weekly: copy this week's posters from the venue app into the site as light web copies
(540/1024 px, WebP + JPG; app originals untouched), rewrite the page's fallback nights, then
refresh the prerendered Event JSON-LD and the tonight-poster preload.
Usage: python3 tools/sync_posters.py   (then commit + push the printed changes)"""
import re, json, io, datetime, pathlib, subprocess, urllib.request, sys
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
idx = root / "index.html"; h = idx.read_text(encoding="utf-8")
api = re.search(r'"api": "([^"]+)"', h).group(1)
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "site-sync"}), timeout=30).read()
week = json.loads(get(api))
MO = "jan feb mar apr may jun jul aug sep oct nov dec".split(); WD = "mon tue wed thu fri sat sun".split()
WDN = "Mon Tue Wed Thu Fri Sat Sun".split(); MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
out = root / "assets/lineup"; out.mkdir(parents=True, exist_ok=True)
divs, keep = [], set()
for n in week.get("nights", []):
    if not n.get("posterUrl"): continue
    d = datetime.date.fromisoformat(n["date"]); stem = f"{WD[d.weekday()]}-{d.day}{MO[d.month-1]}"
    im = Image.open(io.BytesIO(get(n["posterUrl"]))).convert("RGB")
    for w in (540, 1024):
        r = im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(out / f"{stem}-{w}.webp", "WEBP", quality=82, method=6); r.save(out / f"{stem}-{w}.jpg", "JPEG", quality=82, optimize=True, progressive=True)
        keep |= {f"{stem}-{w}.webp", f"{stem}-{w}.jpg"}
    H = round(im.height * 1024 / im.width) if im.width > 1024 else im.height; W = min(im.width, 1024)
    names = (n.get("names") or "").replace('"', "&quot;"); alt = f"Poster, {WDN[d.weekday()]} {d.day} {MON[d.month-1]}" + (f": {names}" if names else "")
    divs.append(f'<div class="night" data-date="{n["date"]}" data-names="{names}"><a href="assets/lineup/{stem}-1024.jpg" target="_blank" rel="noopener"><picture><source data-defer type="image/webp" data-srcset="assets/lineup/{stem}-540.webp 540w, assets/lineup/{stem}-1024.webp 1024w" sizes="(min-width:900px) 440px, 92vw"><img data-defer data-src="assets/lineup/{stem}-1024.jpg" data-srcset="assets/lineup/{stem}-540.jpg 540w, assets/lineup/{stem}-1024.jpg 1024w" sizes="(min-width:900px) 440px, 92vw" width="{W}" height="{H}" loading="lazy" decoding="async" alt="{alt}"></picture></a></div>')
if not divs: sys.exit("app returned no posters; nothing changed")
h, k = re.subn(r'(?:[ \t]*<div class="night" data-date="[^"]*"[^\n]*</div>\n)+', lambda m: "".join("          " + x + "\n" for x in divs), h, count=1)
if not k: sys.exit("fallback nights block not found; nothing changed")
idx.write_text(h, encoding="utf-8")
for f in out.iterdir():
    if f.name not in keep and re.match(r"(mon|tue|wed|thu|fri|sat|sun)-\d+[a-z]{3}-(540|1024)\.(webp|jpg)$", f.name): f.unlink()
subprocess.run([sys.executable, str(root / "tools/prerender_events.py")], check=True)
print(len(divs), "nights synced from", api)
