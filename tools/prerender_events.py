#!/usr/bin/env python3
"""Write this week's MusicEvent JSON-LD into index.html as static HTML (id="events-static"),
from the fallback .night[data-date] posters, so crawlers and AI bots see events without JS.
Run after the weekly line-up refresh:  python3 tools/prerender_events.py"""
import re, json, datetime, pathlib
p = pathlib.Path(__file__).resolve().parent.parent / "index.html"
h = p.read_text(encoding="utf-8")
place = {"@type": "BarOrPub", "@id": "https://xianyukl.com/#venue", "name": "Xianyu 咸鱼酒馆",
         "address": {"@type": "PostalAddress", "streetAddress": "Unit A-G-03, Union Tower, Jalan Desa Bakti, Taman Desa",
                     "addressLocality": "Kuala Lumpur", "addressRegion": "Kuala Lumpur", "postalCode": "58000", "addressCountry": "MY"}}
ev = []
for d, names, img in re.findall(r'<div class="night" data-date="([\d-]+)" data-names="([^"]*)"><a href="([^"]+)"', h):
    who = [w.strip() for w in names.split("·") if w.strip()]
    nxt = (datetime.date.fromisoformat(d) + datetime.timedelta(days=1)).isoformat()
    ev.append({"@type": "MusicEvent", "name": ("Live music: " + " · ".join(who)) if who else "Live music at Xianyu",
      "description": (", ".join(who) + " live at Xianyu 咸鱼酒馆, Taman Desa KL. Live music 9:30pm–12:45am. Strictly 18+.").lstrip(", "),
      "startDate": d + "T21:30:00+08:00", "endDate": nxt + "T00:45:00+08:00",
      "eventStatus": "https://schema.org/EventScheduled", "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
      "isAccessibleForFree": True, "image": "https://xianyukl.com/" + img,
      "performer": [{"@type": "Person", "name": w} for w in who], "location": place,
      "organizer": {"@type": "Organization", "name": "Xianyu 咸鱼酒馆", "url": "https://xianyukl.com/"},
      "offers": {"@type": "Offer", "price": "0", "priceCurrency": "MYR", "availability": "https://schema.org/InStock",
                 "url": "https://xianyukl.com/#" + d, "validFrom": d + "T00:00:00+08:00"}})
block = '<script type="application/ld+json" id="events-static">' + json.dumps({"@context": "https://schema.org", "@graph": ev}, ensure_ascii=False) + '</script>'
h = re.sub(r'\n?<script type="application/ld\+json" id="events-static">.*?</script>', '', h, flags=re.S)
h = h.replace("</head>", block + "\n</head>", 1)
p.write_text(h, encoding="utf-8"); print(len(ev), "events prerendered")
