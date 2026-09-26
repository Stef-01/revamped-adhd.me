#!/usr/bin/env python3
"""Generate the hand-drawn Australia map on our-story.html: the coast, and a dot for each place in CITIES.
Re-run after editing CITIES. Output is injected between the AU-MAP markers."""
import math, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Simplified coastline, (lon, lat), clockwise from Cape York.
MAINLAND = [(142.5,-10.7),(143.5,-14.0),(145.3,-15.5),(145.8,-16.9),(146.3,-18.3),(146.8,-19.3),(148.6,-20.3),(149.2,-21.1),(150.2,-22.5),(150.8,-23.4),(151.3,-23.9),(152.3,-24.8),(153.2,-25.3),(153.1,-26.5),(153.0,-27.5),(153.4,-28.0),(153.6,-28.6),(153.1,-30.3),(152.9,-31.4),(152.5,-32.2),(151.8,-32.9),(151.2,-33.9),(150.9,-34.4),(150.7,-35.1),(150.1,-36.3),(149.9,-37.1),(149.9,-37.5),(148.0,-37.9),(146.4,-39.1),(145.5,-38.4),(144.9,-38.3),(143.5,-38.9),(142.5,-38.4),(141.6,-38.4),(140.5,-38.0),(139.9,-36.8),(139.6,-36.0),(138.6,-35.0),(138.1,-35.6),(137.5,-35.6),(137.0,-35.4),(137.8,-33.2),(137.3,-33.6),(136.7,-34.6),(135.9,-34.7),(135.2,-33.6),(134.2,-32.9),(133.7,-32.1),(132.5,-31.9),(131.1,-31.5),(128.9,-31.7),(126.0,-32.3),(124.0,-33.0),(121.9,-33.9),(119.9,-34.0),(117.9,-35.0),(116.0,-34.8),(115.1,-34.4),(115.0,-33.5),(115.7,-32.1),(115.5,-30.5),(114.9,-29.6),(114.6,-28.8),(114.1,-27.6),(113.2,-26.2),(113.7,-24.9),(113.6,-23.5),(114.1,-21.9),(115.1,-21.6),(116.7,-20.6),(118.6,-20.3),(120.5,-19.7),(122.2,-18.0),(122.9,-16.4),(123.6,-17.3),(124.4,-16.2),(125.0,-15.5),(126.0,-14.0),(127.2,-14.2),(128.2,-15.0),(129.5,-14.8),(130.0,-13.4),(130.8,-12.4),(131.5,-11.6),(132.5,-11.2),(133.8,-11.8),(135.0,-12.1),(136.0,-12.0),(136.8,-12.2),(136.5,-14.0),(135.5,-15.0),(136.2,-15.8),(137.0,-16.0),(138.0,-16.8),(139.5,-17.5),(140.8,-17.5),(141.5,-15.0),(141.6,-12.7),(142.0,-11.2)]
TASMANIA = [(144.7,-40.7),(145.8,-40.9),(146.5,-41.1),(147.5,-40.9),(148.3,-40.9),(148.3,-42.2),(147.9,-43.2),(146.9,-43.6),(146.0,-43.5),(145.2,-42.2),(144.6,-41.2)]

# live = somebody in the network practises there today (see CLINICIANS in build-profiles.py); the rest are
# planned. A live dot is filled and a planned one is hollow. The caption under the map names the same places,
# because phones hide the labels.
CITIES = [  # name, lon, lat, label position, live
    ('Cairns',          145.77, -16.92, 'right',      False),
    ('Townsville',      146.82, -19.26, 'right',      False),
    ('Brisbane',        153.03, -27.47, 'right-up',   True),
    ('Gold Coast',      153.40, -28.02, 'right-down', True),
    ('Sydney',          151.21, -33.87, 'right',      True),
    ('Snowy Mountains', 148.62, -36.41, 'right',      True),
    ('Melbourne',       144.96, -37.81, 'left-down',  False),
    ('Perth',           115.86, -31.95, 'right',      True),
]

SX, SY = 10.0, 11.2          # x scale, y scale (compensates for latitude)
def proj(lon, lat): return ((lon - 112.0) * SX, (-10.0 - lat) * SY)
W, H = 500, 390

def inside(pt, poly):
    x, y = pt; n = len(poly); ins = False; j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi): ins = not ins
        j = i
    return ins

polys = [[proj(*p) for p in MAINLAND], [proj(*p) for p in TASMANIA]]

# Centre the viewBox on the landmass so a logo centred in the container sits on the country's centre.
xs = [x for poly in polys for x, _ in poly]; ys = [y for poly in polys for _, y in poly]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
LABEL_ROOM = 90                     # room for city labels to the right of the east coast
half_w = max(cx - min(xs), max(xs) + LABEL_ROOM - cx) + 8
half_h = max(cy - min(ys), max(ys) - cy) + 14
VB = (cx - half_w, cy - half_h, 2 * half_w, 2 * half_h)

# ---------------------------------------------------------------- hand-drawn rendering
# Deterministic, so the drawing is identical on every build.
import random
INK, PAPER, GOLD = '#1a1c1c', '#fdfbf7', '#f1bc31'

def smooth(poly, per=2):
    """Closed Catmull-Rom through the coastline points, so corners read as pen curves."""
    n = len(poly); out = []
    for i in range(n):
        p0, p1, p2, p3 = poly[i - 1], poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
        for k in range(per):
            t = k / per; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2 + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3) for d in (0, 1)))
    return out

def wobble(pts, seed, amp):
    """Low-frequency drift, like a hand that never quite retraces its own line."""
    r = random.Random(seed); ph = [r.uniform(0, 6.28) for _ in range(4)]; n = len(pts)
    return [(x + amp * (math.sin(i * 0.21 + ph[0]) * 0.6 + math.sin(i * 0.057 + ph[1])),
             y + amp * (math.cos(i * 0.19 + ph[2]) * 0.6 + math.sin(i * 0.071 + ph[3]))) for i, (x, y) in enumerate(pts)]

def closed_path(pts):
    mids = [((pts[i][0] + pts[(i + 1) % len(pts)][0]) / 2, (pts[i][1] + pts[(i + 1) % len(pts)][1]) / 2) for i in range(len(pts))]
    d = f'M{mids[-1][0]:.1f} {mids[-1][1]:.1f}'
    for p, m in zip(pts, mids): d += f' Q{p[0]:.1f} {p[1]:.1f} {m[0]:.1f} {m[1]:.1f}'
    return d + ' Z'

def open_path(pts):
    d = f'M{pts[0][0]:.1f} {pts[0][1]:.1f}'
    for i in range(1, len(pts) - 1):
        mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
        d += f' Q{pts[i][0]:.1f} {pts[i][1]:.1f} {mx:.1f} {my:.1f}'
    return d + f' L{pts[-1][0]:.1f} {pts[-1][1]:.1f}'

lands = [smooth(poly) for poly in polys]
base = ''.join(f'<path id="au-land-{k}" d="{closed_path(l)}"/>' for k, l in enumerate(lands))   # defined once, reused below
clip = ''.join(f'<use href="#au-land-{k}"/>' for k in range(len(lands)))
fill = clip
ink_a = ''.join(f'<path d="{closed_path(wobble(l, 21 + k, 1.3))}"/>' for k, l in enumerate(lands))

def loop(x, y, rad, seed):
    """A dot circled by hand: one and a bit turns, never quite closing."""
    rr = random.Random(seed); start = rr.uniform(0, 6.28); pts = []
    for k in range(27):
        a = start + k * (2 * math.pi * 1.22 / 26); q = rad + rr.uniform(-0.7, 0.7) + k * 0.05
        pts.append((x + q * math.cos(a), y + q * math.sin(a) * 0.94))
    return open_path(pts)

markers = []
for idx, (name, lon, lat, pos, live) in enumerate(CITIES):
    x, y = proj(lon, lat)
    slug = name.lower().replace(' ', '-')
    dx, dy, anchor = {'right': (16, 5, 'start'), 'right-up': (16, -2, 'start'), 'right-down': (16, 14, 'start'), 'left-down': (-15, 16, 'end')}[pos]
    markers.append(f'''<g class="au-marker{'' if live else ' au-marker--planned'}" data-city-marker="{slug}">
<g class="au-dot" style="transform-origin:{x:.1f}px {y:.1f}px"><circle cx="{x:.1f}" cy="{y:.1f}" r="5.6" fill="{GOLD if live else PAPER}"/><path d="{loop(x, y, 7.6, 100 + idx)}" fill="none" stroke="{INK}" stroke-width="1.9" stroke-linecap="round"/></g>
<text x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}" class="au-label">{name}</text></g>''')

svg = f'''<svg class="au-map" viewBox="{VB[0]:.1f} {VB[1]:.1f} {VB[2]:.1f} {VB[3]:.1f}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hand-drawn map of Australia with dots marking where ADHDme clinicians practise now ({', '.join(c[0] for c in CITIES if c[4])}) and where the network plans to grow ({', '.join(c[0] for c in CITIES if not c[4])})">
<defs>{base}<clipPath id="au-land">{clip}</clipPath></defs>
<g fill="{PAPER}" transform="translate(2.5 3)">{fill}</g>
<g fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{ink_a}</g>
{''.join(markers)}
</svg>'''

p = ROOT / 'our-story.html'; s = p.read_text(encoding='utf-8')
s = re.sub(r'<!-- AU-MAP -->.*?<!-- /AU-MAP -->', '<!-- AU-MAP -->' + svg + '<!-- /AU-MAP -->', s, count=1, flags=re.S)
with open(p, 'w', encoding='utf-8', newline='') as fh:  # newline= on write_text needs Python 3.10+
    fh.write(s)
print(f'map: hand-drawn, {len(CITIES)} dots, viewBox {tuple(round(v) for v in VB)}')
