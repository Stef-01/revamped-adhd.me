#!/usr/bin/env python3
"""Generate the solid Australia map used behind the logo on the-doctors.html.
Re-run after editing CITIES. Output is injected between the AU-MAP markers."""
import math, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Simplified coastline, (lon, lat), clockwise from Cape York.
MAINLAND = [(142.5,-10.7),(143.5,-14.0),(145.3,-15.5),(145.8,-16.9),(146.3,-18.3),(146.8,-19.3),(148.6,-20.3),(149.2,-21.1),(150.2,-22.5),(150.8,-23.4),(151.3,-23.9),(152.3,-24.8),(153.2,-25.3),(153.1,-26.5),(153.0,-27.5),(153.4,-28.0),(153.6,-28.6),(153.1,-30.3),(152.9,-31.4),(152.5,-32.2),(151.8,-32.9),(151.2,-33.9),(150.9,-34.4),(150.7,-35.1),(150.1,-36.3),(149.9,-37.1),(149.9,-37.5),(148.0,-37.9),(146.4,-39.1),(145.5,-38.4),(144.9,-38.3),(143.5,-38.9),(142.5,-38.4),(141.6,-38.4),(140.5,-38.0),(139.9,-36.8),(139.6,-36.0),(138.6,-35.0),(138.1,-35.6),(137.5,-35.6),(137.0,-35.4),(137.8,-33.2),(137.3,-33.6),(136.7,-34.6),(135.9,-34.7),(135.2,-33.6),(134.2,-32.9),(133.7,-32.1),(132.5,-31.9),(131.1,-31.5),(128.9,-31.7),(126.0,-32.3),(124.0,-33.0),(121.9,-33.9),(119.9,-34.0),(117.9,-35.0),(116.0,-34.8),(115.1,-34.4),(115.0,-33.5),(115.7,-32.1),(115.5,-30.5),(114.9,-29.6),(114.6,-28.8),(114.1,-27.6),(113.2,-26.2),(113.7,-24.9),(113.6,-23.5),(114.1,-21.9),(115.1,-21.6),(116.7,-20.6),(118.6,-20.3),(120.5,-19.7),(122.2,-18.0),(122.9,-16.4),(123.6,-17.3),(124.4,-16.2),(125.0,-15.5),(126.0,-14.0),(127.2,-14.2),(128.2,-15.0),(129.5,-14.8),(130.0,-13.4),(130.8,-12.4),(131.5,-11.6),(132.5,-11.2),(133.8,-11.8),(135.0,-12.1),(136.0,-12.0),(136.8,-12.2),(136.5,-14.0),(135.5,-15.0),(136.2,-15.8),(137.0,-16.0),(138.0,-16.8),(139.5,-17.5),(140.8,-17.5),(141.5,-15.0),(141.6,-12.7),(142.0,-11.2)]
TASMANIA = [(144.7,-40.7),(145.8,-40.9),(146.5,-41.1),(147.5,-40.9),(148.3,-40.9),(148.3,-42.2),(147.9,-43.2),(146.9,-43.6),(146.0,-43.5),(145.2,-42.2),(144.6,-41.2)]

CITIES = [  # name, lon, lat, label position
    ('Cairns',      145.77, -16.92, 'right'),
    ('Townsville',  146.82, -19.26, 'right'),
    ('Brisbane',    153.03, -27.47, 'right-up'),
    ('Gold Coast',  153.40, -28.02, 'right-down'),
    ('Sydney',      151.21, -33.87, 'right'),
    ('Melbourne',   144.96, -37.81, 'left-down'),
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

def path(poly):
    return 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in poly) + ' Z'

markers = []
for name, lon, lat, pos in CITIES:
    x, y = proj(lon, lat)
    dx, dy, anchor = {'right': (13, 4, 'start'), 'right-up': (13, -2, 'start'), 'right-down': (13, 12, 'start'), 'left-down': (-12, 14, 'end')}[pos]
    markers.append(f'''<g class="au-marker" transform="translate({x:.1f} {y:.1f})">
<circle r="12" class="au-pulse"/><circle r="5" fill="#1a1c1c" stroke="#fdfbf7" stroke-width="2.5"/>
<text x="{dx}" y="{dy}" text-anchor="{anchor}" class="au-label">{name}</text></g>''')

svg = f'''<svg class="au-map" viewBox="{VB[0]:.1f} {VB[1]:.1f} {VB[2]:.1f} {VB[3]:.1f}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="au-map-title">
<title id="au-map-title">Map of Australia showing planned ADHDme service locations: {', '.join(c[0] for c in CITIES)}</title>
<g fill="#f1bc31" stroke="#e2ac24" stroke-width="1.5" stroke-linejoin="round"><path d="{path(polys[0])}"/><path d="{path(polys[1])}"/></g>
{''.join(markers)}
</svg>'''

p = ROOT / 'the-doctors.html'; s = p.read_text()
s = re.sub(r'<!-- AU-MAP -->.*?<!-- /AU-MAP -->', '<!-- AU-MAP -->' + svg + '<!-- /AU-MAP -->', s, count=1, flags=re.S)
p.write_text(s)
print(f'map: solid fill, viewBox {VB}, landmass centre ({cx:.0f},{cy:.0f}), {len(CITIES)} markers')
