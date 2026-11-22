#!/usr/bin/env python3
"""Weekly: copy this week's posters from the venue app into the site as light web copies
(540/1024 px, WebP + JPG; app originals untouched), rewrite the page's fallback nights, then
refresh the prerendered Event JSON-LD and the tonight-poster preload.
Usage: python3 tools/sync_posters.py [week.json]   (then commit + push the printed changes)
22 Nov 2026: only nights of THIS week (Mon to Sun, the night runs till 6am MYT) are used. If the app has
no posters for this week and the page still shows a past week, the page gets 7 plain nights for this week
("Live music nightly, <start> to <end>") and no events, so no stale week is ever left on the site.
Optional week.json = a saved app response, for testing without the network."""
import re, json, io, datetime, pathlib, subprocess, urllib.request, sys
from PIL import Image
root = pathlib.Path(__file__).resolve().parent.parent
idx = root / "index.html"; h = idx.read_text(encoding="utf-8")
api = re.search(r'"api": "([^"]+)"', h).group(1)
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "site-sync"}), timeout=30).read()
week = json.loads(open(sys.argv[1], encoding="utf-8").read()) if len(sys.argv) > 1 else json.loads(get(api))
cfg = re.search(r'"start": "(\d\d):(\d\d)", "end": "(\d\d):(\d\d)"', h)
def clock(hh, mm):
    hh = int(hh); return f"{hh % 12 or 12}{'' if mm == '00' else ':' + mm}{'pm' if hh >= 12 else 'am'}"
NIGHTLY = f"Live music nightly, {clock(*cfg.group(1, 2))} to {clock(*cfg.group(3, 4))}"
night_today = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8 - 6)).date()
monday = night_today - datetime.timedelta(days=night_today.weekday())
this_week = {(monday + datetime.timedelta(days=k)).isoformat() for k in range(7)}
week["nights"] = [n for n in week.get("nights", []) if n.get("date") in this_week]
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
if not divs:
    shown = re.findall(r'<div class="night" data-date="([\d-]+)"', h)
    if shown and max(shown) >= monday.isoformat():
        print("app has no posters for this week yet; the page already shows this week, nothing changed"); sys.exit(0)
    divs = [f'<div class="night" data-date="{(monday + datetime.timedelta(days=k)).isoformat()}" data-names=""><p class="soon">{NIGHTLY}</p></div>' for k in range(7)]
    print("app has no posters for this week: wrote 7 plain nights (" + NIGHTLY + "), no events")
h, k = re.subn(r'(?:[ \t]*<div class="night" data-date="[^"]*"[^\n]*</div>\n)+', lambda m: "".join("          " + x + "\n" for x in divs), h, count=1)
if not k: sys.exit("fallback nights block not found; nothing changed")
idx.write_text(h, encoding="utf-8")
for f in out.iterdir():
    if f.name not in keep and re.match(r"(mon|tue|wed|thu|fri|sat|sun)-\d+[a-z]{3}-(540|1024)\.(webp|jpg)$", f.name): f.unlink()
subprocess.run([sys.executable, str(root / "tools/prerender_events.py")], check=True)
print(sum(1 for d in divs if "<picture>" in d), "nights with posters synced from", api)
