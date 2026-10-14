"""The four trade sheets (S-1, E-1, P-1, M-1): drawing plus the notes, open items and schedules below it."""
import math
import plan as P
import trades as T
from draw import Paper, base_layers, grid, compass, title_block, room_dims, esc, ft_in, r1, locate, wname, wall_pieces, openings_on, wall_rect, nearest, FACES

PAPER = lambda: Paper(15, -4.5, 63.0, -9.0, 51.5, 20, 22, 95, 20)
FONT = 'IBM Plex Sans, Segoe UI, Helvetica, Arial, sans-serif'
ELEC, FRAM, PLUM, COLD, HOT, VENT, DUCT, RET, BLOCK = '#c8650a', '#b8762a', '#3c3a36', '#2c6aa0', '#c8382b', '#4c8c4a', '#d9822b', '#5b8fc7', '#c2369a'
GASC = '#c9a000'


def svg_open(p, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{r1(p.w)}" height="{r1(p.h)}" viewBox="0 0 {r1(p.w)} {r1(p.h)}" font-family="{FONT}" role="img" aria-label="{esc(label)}">\n'
            '<style>.wire{display:none}</style><rect width="100%" height="100%" fill="#fff"/>\n')


def sym(sheet, id_, title, body, **data):
    attrs = ''.join(f' data-{k.replace("_", "-")}="{esc(v)}"' for k, v in data.items() if v not in (None, ''))
    return f'<g id="{sheet}-{esc(id_)}" class="sym" data-id="{esc(id_)}"{attrs}><title>{esc(title)}</title>\n{body}\n</g>'


def hit(x, y, r=11.2):
    return f'<circle class="hit" cx="{r1(x)}" cy="{r1(y)}" r="{r1(r)}" fill="#fff" fill-opacity="0" pointer-events="all"/>'


def tagc(sheet, id_, title, X, Y, text, colour, square=False, r=6.6, fs=5.6):
    shape = (f'<rect x="{r1(X - r)}" y="{r1(Y - r)}" width="{r1(2 * r)}" height="{r1(2 * r)}" fill="#fff" stroke="{colour}" stroke-width="1"/>' if square
             else f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="{r1(r)}" fill="#fff" stroke="{colour}" stroke-width="1"/>')
    return (f'<g id="{sheet}-t{esc(id_)}" class="tag" data-id="{esc(id_)}"><title>{esc(title)}</title>{hit(X, Y, r + 5)}{shape}'
            f'<text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="{fs}" font-weight="700" fill="{colour}" text-anchor="middle" dominant-baseline="middle">{esc(text)}</text></g>')


def table(title, heads, rows, lede='', cls=None):
    """rows: (data-id, [cells]) ; a cell may be (text, class)"""
    o = [f'<h3>{esc(title)}</h3>']
    if lede:
        o.append(f'<p class="lede">{lede}</p>')
    o.append('<div class="tbl"><table><thead><tr>' + ''.join(f'<th scope="col">{esc(h)}</th>' for h in heads) + '</tr></thead><tbody>')
    for rid, cells in rows:
        tds = ''.join(f'<td class="{c[1]}">{esc(c[0])}</td>' if isinstance(c, tuple) else f'<td class="">{esc(c)}</td>' for c in cells)
        o.append(f'<tr data-id="{esc(rid)}" tabindex="0">{tds}</tr>')
    o.append('</tbody></table></div>')
    return '\n'.join(o)


def legend(items):
    return '<ul class="legend">' + ''.join(f'<li><span class="sw" style="background:{c}"></span>{esc(t)}</li>' if c else f'<li>{esc(t)}</li>' for c, t in items) + '</ul>'


def notes(items):
    return '<h3>Notes</h3><ol>' + ''.join(f'<li>{esc(t)}</li>' for t in items) + '</ol>'


def open_items(items):
    return ('<section><h2>Open items</h2><p class="lede">The particulars to settle on this sheet.</p><div class="open"><ul>'
            + ''.join(f'<li>{esc(t)}</li>' for t in items) + '</ul></div></section>')


def tools(sheet_key, packet, name):
    return (f'<div class="tools"><div class="zoom" role="group" aria-label="Zoom"><button type="button" data-zoom="1" aria-pressed="true">Fit</button><button type="button" data-zoom="2" aria-pressed="false">2×</button><button type="button" data-zoom="4" aria-pressed="false">4×</button></div>'
            f'<a class="packet" href="packets/{packet}" target="_blank" rel="noopener"><svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M4 1.5h5.5L13 5v9.5H4z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M9.5 1.5V5H13M8.5 7.5v4.5M6.5 10l2 2 2-2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg><span class="pk-name">{esc(name)} packet </span>PDF</a>'
            '<p class="sel" data-hint="These zoom buttons are your friend.&#10;Everything you see is clickable.">These zoom buttons are your friend.\nEverything you see is clickable.</p></div>')


def plen(pts):
    return sum(abs(pts[i][0] - pts[i - 1][0]) + abs(pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts)))


TB_Y = lambda p: p.h - 75

# ============================================================================ S-1 framing
WALL_COL = {'E': '#7a4f22', 'P': FRAM, 'G': '#a8452a', 'M': FRAM}
WALL_TYPE = {
    'E': '2x6 @ 16" o.c., 7/16" OSB, house wrap, R-21 batts; PT 2x6 bottom plate on sill gasket, 1/2" anchor bolts 6\' o.c. and 12" from each end',
    'P': '2x4 @ 16" o.c. partition, PT bottom plate on the slab',
    'G': '2x4 @ 16" o.c., R-13 batts, 1/2" gypsum on the garage side, taped (IRC R302.6); PT bottom plate',
    'M': '2x4 @ 16" o.c., 1/2" gypsum both sides; PT bottom plate',
}


def wall_len(w):
    """plate length: centre-line length, less half of each wall it butts into"""
    n, x1, y1, x2, y2, typ, _ = w
    L = abs(x2 - x1) + abs(y2 - y1)
    if typ == 'E':
        # east-west exterior walls run through the corners; north-south ones butt between them
        if P.along_x(w):
            return L
        for ex, ey in ((x1, y1), (x2, y2)):
            if any(v[5] == 'E' and P.along_x(v) and wall_rect(v)[0] - 0.01 <= ex <= wall_rect(v)[1] + 0.01 and wall_rect(v)[2] - 0.01 <= ey <= wall_rect(v)[3] + 0.01 for v in P.WALLS):
                L -= P.T_EXT
        return L
    for ex, ey in ((x1, y1), (x2, y2)):
        for v in P.WALLS:
            if v[0] == n or P.along_x(v) == P.along_x(w):
                continue
            vx1, vx2, vy1, vy2 = wall_rect(v)
            if vx1 - 0.01 <= ex <= vx2 + 0.01 and vy1 - 0.01 <= ey <= vy2 + 0.01:
                L -= P.THICK[v[5]] / 2
                break
    return L


def wall_runs(w):
    n, x1, y1, x2, y2, typ, _ = w
    t = P.THICK[typ]
    ax = P.along_x(w)
    ends = []
    for ex, ey in ((x1, y1), (x2, y2)):
        hit_ = None
        for v in P.WALLS:
            if v[0] == n or P.along_x(v) == ax:
                continue
            vx1, vx2, vy1, vy2 = wall_rect(v)
            if vx1 - 0.01 <= ex <= vx2 + 0.01 and vy1 - 0.01 <= ey <= vy2 + 0.01:
                hit_ = v[0]
        ends.append(wname(hit_) if hit_ else 'free end')
    if typ == 'E':
        return P.EXT_RUNS[n]
    mid = ((x1 + x2) / 2, (y1 + y2) / 2)
    if ax:
        f = y1 - t / 2
        best = min((q for q in FACES if q[1] == 'y' and q[0] != n and q[2] < f and q[3] - 0.2 <= mid[0] <= q[4] + 0.2), key=lambda q: f - q[2])
        return f'east–west, {ends[0]} to {ends[1]}; south face {ft_in(f - best[2])} from {wname(best[0])}'
    f = x1 - t / 2
    best = min((q for q in FACES if q[1] == 'x' and q[0] != n and q[2] < f and q[3] - 0.2 <= mid[1] <= q[4] + 0.2), key=lambda q: f - q[2])
    return f'north–south, {ends[0]} to {ends[1]}; west face {ft_in(f - best[2])} from {wname(best[0])}'


def door_ro(d):
    tg, n, c, w, h, kind, *_ = d
    win = round(w * 12)
    hin = round(h * 12)
    if kind == 'overhead':
        return f'{ft_in(w)} x {ft_in(h)} finished, 2x jambs'
    if kind == 'cased':
        return f'{win + 2}" x {hin + 2.5:g}"'
    if kind == 'bifold':
        return f'{win + 2}" x {hin + 2.5:g}"'
    if P.wall(n)[5] == 'E':
        return f'{win + 2.5:g}" x {hin + 1.5:g}"'
    return f'{win + 2}" x {hin + 2.5:g}"'


def header_for(n, w):
    if P.wall(n)[5] == 'E' and P.along_x(P.wall(n)):
        if w > 10:
            return '3-1/2" x 14" LVL (2 plies 1-3/4"), 3 jacks each end; confirm with the truss reactions'
        if w > 3.6:
            return '2-2x12 with 2" XPS, 2 jacks each end'
        return '2-2x8 with 2" XPS, 1 jack each end'
    if P.wall(n)[5] == 'E':
        return '2-2x6 with 2" XPS (non-bearing: gable end or porch / patio return)'
    return 'flat 2x4 with cripples (non-bearing)'


BLOCKING = [
    ('B1', 5, 'E', 9.0, 13.0, '30"–72"', 'TV mount, living room: 2x8 flat between studs, 2 rows'),
    ('B2', 15, 'E', 31.0, 35.0, '30"–66"', 'TV mount, primary bedroom'),
    ('B3', 15, 'W', 27.8, 35.0, '54"–96"', 'kitchen upper cabinets, wall run: 2x6 continuous band'),
    ('B4', 3, 'S', 23.229, 27.854, '54"–96"', 'kitchen upper cabinets, rear run, either side of N8'),
    ('B5', 15, 'W', 30.0, 32.0, '66"–84"', 'range hood'),
    ('B6', 9, 'S', 2.6, 7.4, '30"–84"', 'Bath 2 vanity top, mirror and light'),
    ('B7', 8, 'W', 15.146, 17.646, '30"–84"', 'Bath 2 tub: shower valve, grab bar at 33"–36", towel bar'),
    ('B8', 4, 'E', 19.5, 22.5, '24"–40"', 'Bath 2 toilet paper holder and grab bar'),
    ('B9', 16, 'E', 28.4, 33.854, '30"–84"', 'primary vanity, mirrors and lights'),
    ('B10', 17, 'S', 53.542, 57.542, '30"–84"', 'primary shower: valve, grab bar, glass door hinge jamb, niche'),
    ('B11', 13, 'W', 1.0, 6.1, '54"–66"', 'laundry shelf over the washer and dryer'),
    ('B12', 24, 'E', 1.0, 4.0, '18"–72"', 'mud bench and coat hooks; carry the band on along wall 11 to 6\'-0"'),
    ('B13', 6, 'N', 0.458, 7.854, '60"–72"', 'Bedroom 3 closet rod and shelf'),
    ('B14', 10, 'S', 0.458, 7.854, '60"–72"', 'Bedroom 2 closet rod and shelf'),
    ('B15', 3, 'S', 48.646, 57.542, '40"–84"', 'WIC rods and shelves (double hang on the north wall)'),
    ('B16', 19, 'N', 28.146, 33.854, '12"–84"', 'pantry shelves, every 12"'),
]


def s1():
    p = PAPER()
    o = [svg_open(p, 'S-1 Framing plan'), grid(p)]
    o.append(base_layers(p, walls_colour=lambda w: WALL_COL[w[5]], dims=room_dims(p)))
    # walls as picks
    for w in P.WALLS:
        n, *_ , typ, note = w
        L = wall_len(w)
        ops = openings_on(n)
        txt = f'Wall {n}: {ft_in(L)}, runs {wall_runs(w)}. {WALL_TYPE[typ]}' + (f'. Openings {", ".join(t for *_, t in ops)}' if ops else '') + f'. {note[0].upper() + note[1:]}.'
        body = ''.join(p.rect(*pc, fill=WALL_COL[typ], fill_opacity='0.001', stroke='none') for pc in wall_pieces(w))
        o.append(sym('s1', f'W{n}', txt, body))
        # the tag on the longest solid piece, nudged off the wall
        pcs = wall_pieces(w)
        x1, x2, y1, y2 = max(pcs, key=lambda q: (q[1] - q[0]) + (q[3] - q[2]))
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        off = {1: (0, -1.2), 2: (1.3, 0), 3: (0, 1.2), 4: (-1.3, 0)}.get(n)
        if not off:
            off = (0, 0.75) if P.along_x(w) else (0.75, 0)
        tx, ty = cx + off[0], cy + off[1]
        o.append(tagc('s1', f'W{n}', f'Wall {n}', p.X(tx), p.Y(ty), str(n), WALL_COL[typ]))
    # garage side of the separation: dashed red line
    for n in (13, 14):
        w = P.wall(n)
        x1, x2, y1, y2 = wall_rect(w)
        if n == 13:
            o.append(p.line(x2 + 0.05, 0.458, x2 + 0.05, 23.854, stroke='#c0392b', stroke_width='1', stroke_dasharray='4,2'))
        else:
            o.append(p.line(36.146, y1 - 0.05, 57.542, y1 - 0.05, stroke='#c0392b', stroke_width='1', stroke_dasharray='4,2'))
    # blocking bands
    for b in BLOCKING:
        tg, n, side, a, bb, h, what = b
        w = P.wall(n)
        t = P.THICK[w[5]]
        k = w[2] if P.along_x(w) else w[1]
        off = (t / 2 + 0.06) * (1 if side in 'NE' else -1)
        if P.along_x(w):
            body = p.line(a, k + off, bb, k + off, stroke=BLOCK, stroke_width='2.2', stroke_dasharray='5,2')
        else:
            body = p.line(k + off, a, k + off, bb, stroke=BLOCK, stroke_width='2.2', stroke_dasharray='5,2')
        o.append(sym('s1', tg, f'Blocking {tg}: {what}; {wname(n)}, {h} AFF', body))
    # doors and windows: tags
    for d in P.DOORS:
        tg, n, c, wd, h, kind, room, hinge, swing, note = d
        w = P.wall(n)
        k = w[2] if P.along_x(w) else w[1]
        sg = 1 if swing == '+' else -1
        dist = 1.3 if kind != 'overhead' else 2.2
        if w[5] == 'E':
            sg = -sg
            dist = 1.0
        x, y = ((c, k + sg * dist) if P.along_x(w) else (k + sg * dist, c))
        kind_w = {'swing': 'swing door', 'pair': 'French door pair', 'bifold': 'bifold doors', 'overhead': 'overhead door', 'cased': 'cased opening, no door'}[kind]
        o.append(tagc('s1', tg, f'{"Opening" if kind == "cased" else "Door"} {tg[1:]}: {room}, {kind_w}, {ft_in(wd)} x {ft_in(h)}, RO {door_ro(d)}', p.X(x), p.Y(y), tg, FRAM, square=kind == 'cased'))
    for wn in P.WINDOWS:
        tg, n, c, wd, h, sill, room, typ = wn
        w = P.wall(n)
        k = w[2] if P.along_x(w) else w[1]
        out = (0, 1.1 * P.out_dir(w)) if P.along_x(w) else (1.1 * P.out_dir(w), 0)
        x, y = ((c, k) if P.along_x(w) else (k, c))
        X, Y = p.X(x + out[0]), p.Y(y + out[1])
        o.append(f'<g id="s1-t{tg}" class="tag" data-id="{tg}"><title>Window {tg}: {esc(room)}, {ft_in(wd)} x {ft_in(h)} {esc(typ)}, sill {ft_in(sill)}</title>{hit(X, Y, 11)}'
                 f'<path d="M{r1(X)},{r1(Y - 7)}L{r1(X + 7)},{r1(Y)}L{r1(X)},{r1(Y + 7)}L{r1(X - 7)},{r1(Y)}Z" fill="#fff" stroke="#6f8fa8" stroke-width="1"/>'
                 f'<text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="5" font-weight="700" fill="#4f6f88" text-anchor="middle" dominant-baseline="middle">{tg}</text></g>')
    o.append(compass(p, 61.0, 47.5))
    o.append(p.text(21.0, -7.3, 'FRONT — street side (assumed south)', 7, fill='#888'))
    o.append(title_block(p, 'S-1', 'Framing plan', 'Walls, door and window rough openings, headers, blocking', 'Schematic for pricing and coordination, not a stamped construction document. Verify on site.', TB_Y(p)))
    o.append('</svg>')
    svg = '\n'.join(o)

    # ---- schedules
    wrows = []
    for w in P.WALLS:
        n, x1, y1, x2, y2, typ, note = w
        ops = openings_on(n)
        wrows.append((f'W{n}', [str(n), wall_runs(w), (ft_in(wall_len(w)), 'num'), WALL_TYPE[typ].split(',')[0] + ('' if typ == 'P' else ', ' + ', '.join(WALL_TYPE[typ].split(', ')[1:2])), ', '.join(t for *_, t in ops) or '—', note]))
    drows = []
    for d in P.DOORS:
        tg, n, c, wd, h, kind, room, hinge, swing, note = d
        kind_w = {'swing': 'prehung swing', 'pair': 'French pair', 'bifold': 'bifold', 'overhead': 'overhead', 'cased': 'cased opening'}[kind]
        drows.append((tg, [tg, room, kind_w, f'{ft_in(wd)} x {ft_in(h)}', door_ro(d), wname(n), header_for(n, wd), note]))
    nrows = []
    for wn in P.WINDOWS:
        tg, n, c, wd, h, sill, room, typ = wn
        nrows.append((tg, [tg, room, f'{ft_in(wd)} x {ft_in(h)}', typ, f'{ft_in(sill)} / {ft_in(sill + h)}', f'{round(wd * 12) + 0.5:g}" x {round(h * 12) + 0.5:g}"', wname(n), header_for(n, wd)]))
    brows = [(b[0], [b[0], wname(b[1]), {'N': 'north', 'S': 'south', 'E': 'east', 'W': 'west'}[b[2]] + ' face', f'{ft_in(b[4] - b[3])}', b[5], b[6]]) for b in BLOCKING]

    # ---- quantities
    studs6 = studs4 = 0
    plate6 = plate4 = 0.0
    sheath = 0.0
    for w in P.WALLS:
        L = wall_len(w)
        ops = openings_on(w[0])
        n_st = math.ceil(L * 12 / 16) + 1 + 2 * len(ops) * 2 + 2
        if w[5] == 'E':
            studs6 += n_st
            plate6 += 3 * L
            sheath += L * P.PLATE_H - sum((b - a) * 6.5 for a, b, *_ in ops)
        else:
            studs4 += n_st
            plate4 += 3 * L
    trusses = int(P.W / 2) + 1
    # valley trusses: one every 2' from the gable's front wall line up to where the gable ridge dies into the main roof
    lift = (5.5 / 12 * (0.5 + 0.5 * math.hypot(1, P.PITCH)) + 0.29) / P.PITCH
    valleys = [(g['id'], (g['b'] - g['a']) - 2 * (y + lift)) for g in P.GABLES for y in range(2, int((g['b'] - g['a']) / 2), 2) if (g['b'] - g['a']) - 2 * (y + lift) >= 1]
    lrows = [
        ('L1', ['2x6 x 104-5/8" precut studs (exterior)', str(studs6), 'commons, corners, kings and jacks; +10% waste included in the order']),
        ('L2', ['2x4 x 104-5/8" precut studs (interior)', str(studs4), 'commons, kings, jacks; partition backers at every tee']),
        ('L3', ['2x6 plates, 1 PT bottom + 2 top', f'{math.ceil(plate6)} lf', f'about {math.ceil(plate6 / 16)} 16\' boards']),
        ('L4', ['2x4 plates, 1 PT bottom + 2 top', f'{math.ceil(plate4)} lf', f'about {math.ceil(plate4 / 16)} 16\' boards']),
        ('L5', ['7/16" OSB wall sheathing, 4x9', str(math.ceil(sheath / 36 * 1.1)), 'exterior walls, less openings, +10%']),
        ('L6', ['Roof trusses, 6:12 common, 40\'-0" span, 24" o.c.', str(trusses - 2), '12" overhang, raised heel for R-60 at the walls; engineered by the truss supplier']),
        ('L7', ['Gable end trusses, 16" o.c. verticals', '4', 'east and west ends, and the fronts of the porch and garage gables; 2x4 gable bracing per the truss drawings']),
        ('L7a', ['Front gable trusses and valley sets', f'{len(valleys) + 1}', 'one 18\' common over the porch beam, then valley trusses on the main roof sheathing: ' + ', '.join(f'{g} {ft_in(w)}' for g, w in valleys)]),
        ('L8', ['Porch and patio: 6x6 posts, 2-2x10 beams, 2x6 rafters', f'{len(P.POSTS)} posts', 'porch beam under the porch gable; patio shed from a ledger under the rear eave; post bases on footings']),
        ('L9', ['1/2" anchor bolts, 10" embed', str(math.ceil(2 * (P.W + P.D) / 6) + 12), 'exterior walls and garage separation at 6\' o.c., 12" from ends']),
        ('L10', ['Hurricane / uplift ties at each truss', str(2 * trusses), 'H2.5A or as the truss drawings']),
    ]
    # drywall
    wall_area = 0.0
    for w in P.WALLS:
        L = wall_len(w)
        ops = openings_on(w[0])
        op_area = sum((b - a) * (6.67 if k not in ('window',) else 4.5) for a, b, k, _ in ops)
        sides = 1 if w[5] == 'E' else 2
        if w[0] == 25:
            L = 6.0       # the laundry only: the garage front gets no board
        if w[0] == 2:
            L = 40 - 24   # east wall: the primary suite only (the garage stretch is bare)
        wall_area += sides * (L * P.CEIL - op_area)
    ceil_house = 1800.0
    drows2 = [
        ('Y1', ['1/2" gypsum, walls', f'{math.ceil(wall_area * 1.12 / 48)} sheets 4x12', f'{math.ceil(wall_area)} sq ft net, +12%']),
        ('Y2', ['5/8" gypsum, ceilings (24" o.c. trusses)', f'{math.ceil(ceil_house * 1.1 / 48)} sheets 4x12', '1,800 sq ft house ceilings, +10%']),
        ('Y3', ['5/8" Type X, garage ceiling', f'{math.ceil(528 * 1.1 / 48)} sheets 4x12', 'garage ceiling under the attic (R302.6); fire-tape']),
        ('Y4', ['1/2" gypsum, garage side of walls 13 and 14, mech room both sides', f'{math.ceil((24 + 24 + 2 * 12) * P.CEIL * 1.1 / 48)} sheets 4x12', 'taped (R302.6)']),
        ('Y5', ['1/2" cement board, tub and shower walls', f'{math.ceil((5 + 2.5 * 2) * 5 / 15 + (4 + 4.5) * 7 / 15 + 1)} sheets 3x5', 'Bath 2 tub surround and the primary shower, waterproofed']),
        ('Y6', ['Moisture-resistant 1/2" board in Bath 2, primary bath, laundry', 'included in Y1', '']),
    ]
    roof_rows = [
        ('RF1', ['Common trusses', f'{trusses - 2} @ 24" o.c.', '6:12, 40\'-0" clear span bearing on the front walls (1, 25) and the rear walls (3, 26); interior walls are non-bearing, held 1/2" below the bottom chord with partition clips. Over the porch and patio the trusses bear on walls 23 and 28 and cantilever 4\' to the eave line (truss designer to confirm, or add a flush beam)']),
        ('RF2', ['Gable ends', '2', 'east and west, sheathed, 12" rake overhang on outlookers']),
        ('RF2a', ['Front gables', '2', 'CG1 over the porch (18\' wide, front on the porch beam) and CG2 over the garage (22\' wide, front on wall 25); ridges run north and die into the main roof, valley sets on the main sheathing, ice barrier in both valleys']),
        ('RF3', ['Attic access', '1', '22" x 54" insulated pull-down stair in the garage ceiling (F, near wall 14); the way to FAU-1']),
        ('RF4', ['FAU-1 platform', '1', '3/4" OSB platform over the back hall, 30" service side, catwalk from the access (M1305.1.3)']),
        ('RF5', ['Attic ventilation', '1/300', 'continuous soffit intake, ridge vent; baffles at every bay']),
        ('RF6', ['Ceiling insulation', 'R-60', 'blown cellulose or fibreglass over the house; R-49 minimum over the garage if it is ever heated']),
    ]
    below = ['<div class="below">',
             '<section><h2>S-1 Framing</h2>' + legend([('#7a4f22', 'exterior 2x6 @ 16"'), (FRAM, '2x4 partition @ 16"'), ('#a8452a', 'garage separation, gypsum on the garage side (red dash)'), (BLOCK, 'blocking band'), ('#6f8fa8', 'window (diamond tag)'), ('', 'round tag: door; square tag: cased opening')]) +
             notes([
                 'Plan coordinates: x runs east from the outside face of the west wall framing, y runs north from the outside face of the front wall framing; the grid is 5\'. The front of the house is drawn facing south: confirm the lot orientation.',
                 'Blue dimensions are each room\'s clear size, stud face to stud face: exterior walls to the inside face of the 2x6 studs, interior walls to the stud face 1-3/4" off the centre line.',
                 'Ceilings are 9\'-0" flat throughout, including the garage, on 104-5/8" precut studs with a PT bottom plate and a double top plate.',
                 'The roof is a 6:12 gable, ridge east–west, with two front-facing gables as the front elevation: one over the porch and one over the garage. The main trusses clear-span 40\' front to rear, so the front and rear walls bear and every interior wall is a partition; walls 2 and 4 are gable ends. The front gables are framed with valley sets on top of the main roof.',
                 'The porch and the patio are set 4\' into the house: the walls step in around them (walls 22–24 at the porch, 27–29 at the patio), and the slab follows. The porch is 17\'-6" x 6\' (4\' under the house roof, 2\' under the porch gable on the beam and posts); the patio is 10\'-6" x 10\' (4\' under the house roof, 6\' under a shed).',
                 'Foundation: slab on grade, thickened edge or frost-protected stem wall to the local frost depth; 10-mil vapour retarder; R-10 under-slab perimeter insulation 4\' in (IECC climate zone 6 assumed). Garage slab 4" below the house slab, sloped 1/8"/ft to the door.',
                 'Garage separation (R302.6): 1/2" gypsum on the garage side of walls 13 and 14, 5/8" Type X on the garage ceiling; D3 is 20-minute rated and self-closing. Seal every penetration in those walls.',
                 'Door rough openings: prehung interior 2" over the leaf width x 82-1/2"; exterior per the door maker. Window rough openings 1/2" over the unit size; heads at 8\'-0".',
                 'Bedroom windows N1, N4, N6, N7 and N9 are egress windows: 5.7 sq ft clear opening, 20" min width, 24" min height, sill 44" max (R310). Choose a unit size that meets the clear opening.',
             ]) + '</section>',
             open_items([
                 'Orientation: the drawings assume the porch and garage door face south. Tell us the real compass direction and the sheets will turn.',
                 'Bath 2 is drawn 7\'-5" x 10\'-2" clear: the BuildWise label says 5\' x 11\', which does not fit beside the 3\'-8" hall. Keep, or rework the bedroom wing?',
                 'Interior door height: 6\'-8" drawn. 8\'-0" doors suit 9\' ceilings better (D6–D16, about $40–$90 more each).',
                 'Primary bedroom door D12 opens off the kitchen corner, as on the plan; the garage keeps its full 22\' width. Alternative: shift it to the back-hall alcove and narrow the garage to 21\'.',
                 'Porch and patio insets: drawn 4\' deep, read from the BuildWise plan; the living room is 17\'-8" x 13\'-5" and the dining room 10\'-7" x 17\'-5" as a result. Confirm the depths, and whether the patio should sit wholly under the roof.',
                 'Truss heel height and snow load: confirm the site ground snow load for the truss engineering and the bearing-wall headers.',
             ]),
             '<section class="wide">', table('Wall schedule', ['Wall', 'Runs', 'Length', 'Framing', 'Openings', 'Notes'], wrows, 'One row per wall. Click a row to find it on the plan.'),
             table('Door schedule', ['Door', 'Room', 'Type', 'Size', 'Rough opening', 'In wall', 'Header', 'Notes'], drows),
             table('Window schedule', ['Window', 'Room', 'Size (W x H)', 'Type', 'Sill / head', 'Rough opening', 'In wall', 'Header'], nrows, 'Low-E, U-0.30 or better (zone 6). Sizes are nominal: confirm the maker\'s rough openings before framing.'),
             table('Blocking schedule', ['Tag', 'Wall', 'Face', 'Length', 'Height', 'For'], brows, '2x8 flat between studs unless noted, flush with the stud face.'),
             table('Dimensional lumber and sheathing', ['Item', 'Qty', 'Notes'], lrows, 'Rough-order quantities from the drawing geometry, for pricing. The framer takes off the final list.'),
             table('Drywall estimate', ['Item', 'Qty', 'Notes'], drows2, 'Walls 1/2", ceilings 5/8" (trusses at 24" o.c.). Net of door and window openings.'),
             table('Roof framing', ['Item', 'Qty', 'Notes'], roof_rows),
             '</section></div>']
    return svg, '\n'.join(below)


# ============================================================================ E-1 electrical
SYM_COL = {'R': ELEC, 'S': '#8a5a00', 'L': '#d9a400', 'A': '#b4462f', 'T': '#2c6aa0', 'X': '#333'}
LETTERS = {'gfci': 'G', 'wp': 'WP', 'usb': 'U', 'ded': 'D', 'r240': '240', 'tv': 'TV', 'rec20': '20', 'opener': 'GD', 'jbox': 'J',
           'sw': 'S', 'sw3': '3', 'dim': 'D', 'fansw': 'F', 'tmr': 'T', 'wet': 'W', 'pend': 'P', 'fanbox': 'F', 'surf': '', 'ef': 'EF', 'hood': 'H',
           'smoke': 'SD', 'combo': 'CO', 'data': 'T', 'wap': 'AP', 'bell': 'DB', 'chime': 'CH', 'media': 'M', 'disc': 'DS', 'attic': 'A'}


def dev_xy(p, d):
    """symbol centre on the sheet: wall devices sit just inside the face they are on"""
    off = {'N': (0, 0.38), 'S': (0, -0.38), 'E': (0.38, 0), 'W': (-0.38, 0)}.get(d['side'], (0, 0))
    return p.X(d['x'] + off[0]), p.Y(d['y'] + off[1])


def dev_symbol(p, d):
    t, col = d['type'], SYM_COL[d['id'][0]]
    X, Y = dev_xy(p, d)
    L = LETTERS.get(t, '')
    o = [hit(X, Y)]
    if d['id'][0] == 'R':
        if t == 'floor':
            o.append(f'<rect x="{r1(X - 5.5)}" y="{r1(Y - 5.5)}" width="11" height="11" fill="#fff" stroke="{col}" stroke-width="1.1"/>')
            o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="3" fill="none" stroke="{col}" stroke-width="0.9"/>')
        else:
            o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="5.9" fill="#fff" stroke="{col}" stroke-width="1.1"/>')
            # two short lines toward the wall
            dx, dy = {'N': (0, 1), 'S': (0, -1), 'E': (-1, 0), 'W': (1, 0)}.get(d['side'], (0, 0))
            if dx or dy:
                for s in (-1.8, 1.8):
                    ax, ay = X + dx * 5.9 + (dy * s), Y + dy * 5.9 * -1 * -1 + (dx * s)
                    o.append(f'<line x1="{r1(X + dx * 5.9 + dy * s)}" y1="{r1(Y - dy * 5.9 + dx * s)}" x2="{r1(X + dx * 9.5 + dy * s)}" y2="{r1(Y - dy * 9.5 + dx * s)}" stroke="{col}" stroke-width="0.9"/>')
            if L:
                o.append(f'<text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="{4.2 if len(L) > 1 else 5.5}" font-weight="700" fill="{col}" text-anchor="middle" dominant-baseline="middle">{L}</text>')
    elif d['id'][0] == 'S':
        o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="5.4" fill="{col}" stroke="#fff" stroke-width="0.8"/>')
        o.append(f'<text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="6" font-weight="700" fill="#fff" text-anchor="middle" dominant-baseline="middle">{L}</text>')
    elif d['id'][0] == 'L':
        if t == 'shop':
            o.append(f'<rect x="{r1(X - 12)}" y="{r1(Y - 3)}" width="24" height="6" fill="#fff" stroke="{col}" stroke-width="1.2"/>')
        elif t == 'strip':
            o.append(f'<rect x="{r1(X - 3)}" y="{r1(Y - 14)}" width="6" height="28" fill="#fff7d6" stroke="{col}" stroke-width="1"/>' if d['side'] in 'EW' else f'<rect x="{r1(X - 14)}" y="{r1(Y - 3)}" width="28" height="6" fill="#fff7d6" stroke="{col}" stroke-width="1"/>')
        elif t == 'sconce':
            o.append(f'<rect x="{r1(X - 3)}" y="{r1(Y - 8)}" width="6" height="16" fill="#fff" stroke="{col}" stroke-width="1.2"/>' if d['side'] in 'EW' else f'<rect x="{r1(X - 8)}" y="{r1(Y - 3)}" width="16" height="6" fill="#fff" stroke="{col}" stroke-width="1.2"/>')
        elif t in ('ef', 'hood'):
            o.append(f'<rect x="{r1(X - 6)}" y="{r1(Y - 6)}" width="12" height="12" fill="#fff" stroke="#8d8d8d" stroke-width="1.1"/>')
            o.append(f'<text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="4.5" font-weight="700" fill="#6d6d6d" text-anchor="middle" dominant-baseline="middle">{L}</text>')
        elif t == 'ext':
            o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="5" fill="#fff" stroke="{col}" stroke-width="1.2"/>')
            for a in range(0, 360, 45):
                ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                o.append(f'<line x1="{r1(X + ca * 6.5)}" y1="{r1(Y + sa * 6.5)}" x2="{r1(X + ca * 8.5)}" y2="{r1(Y + sa * 8.5)}" stroke="{col}" stroke-width="0.8"/>')
        elif t == 'chand':
            o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="7" fill="#fff" stroke="{col}" stroke-width="1.2"/>')
            o.append(f'<path d="M{r1(X - 4)},{r1(Y)}L{r1(X + 4)},{r1(Y)}M{r1(X)},{r1(Y - 4)}L{r1(X)},{r1(Y + 4)}M{r1(X - 3)},{r1(Y - 3)}L{r1(X + 3)},{r1(Y + 3)}M{r1(X - 3)},{r1(Y + 3)}L{r1(X + 3)},{r1(Y - 3)}" stroke="{col}" stroke-width="0.9"/>')
        elif t == 'fanbox':
            o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="9" fill="#fff" stroke="{col}" stroke-width="1.1" stroke-dasharray="3,1.5"/>')
            o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="4.5" fill="#fff" stroke="{col}" stroke-width="1.2"/>')
            o.append(f'<text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="5" font-weight="700" fill="{col}" text-anchor="middle" dominant-baseline="middle">F</text>')
        elif t == 'surf' or t == 'attic':
            o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="5.5" fill="#fff" stroke="{col}" stroke-width="1.2"/>')
            o.append(f'<path d="M{r1(X - 3.9)},{r1(Y - 3.9)}L{r1(X + 3.9)},{r1(Y + 3.9)}M{r1(X - 3.9)},{r1(Y + 3.9)}L{r1(X + 3.9)},{r1(Y - 3.9)}" stroke="{col}" stroke-width="0.9"/>')
            if t == 'attic':
                o.append(f'<text x="{r1(X + 9)}" y="{r1(Y)}" font-size="5" fill="{col}" dominant-baseline="middle">attic</text>')
        else:
            o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="5" fill="#fff" stroke="{col}" stroke-width="1.2"/>')
            if L:
                o.append(f'<text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="5" font-weight="700" fill="{col}" text-anchor="middle" dominant-baseline="middle">{L}</text>')
            else:
                o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="1.4" fill="{col}"/>')
            if t == 'soffit':
                o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="7.5" fill="none" stroke="{col}" stroke-width="0.7" stroke-dasharray="2,1.5"/>')
    elif d['id'][0] == 'A':
        o.append(f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="6" fill="#fff" stroke="{col}" stroke-width="1.2"/>')
        o.append(f'<text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="4.6" font-weight="700" fill="{col}" text-anchor="middle" dominant-baseline="middle">{L}</text>')
    elif d['id'][0] == 'T':
        o.append(f'<path d="M{r1(X)},{r1(Y - 6.5)}L{r1(X + 6.5)},{r1(Y + 5)}L{r1(X - 6.5)},{r1(Y + 5)}Z" fill="#fff" stroke="{col}" stroke-width="1.1"/>')
        o.append(f'<text x="{r1(X)}" y="{r1(Y + 1.6)}" font-size="4" font-weight="700" fill="{col}" text-anchor="middle" dominant-baseline="middle">{L}</text>')
    else:  # X: panels and disconnects
        if t == 'panel':
            o.append(f'<rect x="{r1(X - 4)}" y="{r1(Y - 11)}" width="8" height="22" fill="#333"/>' if d['side'] in 'EW' else f'<rect x="{r1(X - 11)}" y="{r1(Y - 4)}" width="22" height="8" fill="#333"/>')
            o.append(f'<text x="{r1(X + 13)}" y="{r1(Y)}" font-size="6" font-weight="700" fill="#333" dominant-baseline="middle">MP</text>')
        else:
            o.append(f'<rect x="{r1(X - 6)}" y="{r1(Y - 6)}" width="12" height="12" fill="#fff" stroke="#333" stroke-width="1.1"/>')
            o.append(f'<text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="4.6" font-weight="700" fill="#333" text-anchor="middle" dominant-baseline="middle">{L}</text>')
    return '\n'.join(o)


def dev_title(d):
    pos = locate(d['x'], d['y'], d['side']) if d['side'] != 'c' else locate(d['x'], d['y'], 'c')
    h = f', {d["h"]}" AFF' if d['h'] else ''
    c = f', circuit {d["ckt"]}' if d['ckt'] not in ('data', 'panel') else ''
    return f'{d["id"]} {d["legend"]}{h}{c}' + (f' — {d["note"]}' if d['note'] else '') + f' ({d["room"]}; {pos})'


def chain(start, pts):
    """nearest-neighbour order from start through pts"""
    left, cur, out = list(pts), start, []
    while left:
        nxt = min(left, key=lambda q: math.hypot(q[0] - cur[0], q[1] - cur[1]))
        out.append(nxt)
        left.remove(nxt)
        cur = nxt
    return out


def e1():
    p = PAPER()
    o = [svg_open(p, 'E-1 Electrical plan'), grid(p), base_layers(p, faint=True)]
    panel = next(d for d in T.DEVICES if d['type'] == 'panel')
    PX, PY = dev_xy(p, panel)
    # cable runs, one group per circuit
    for key, load, *_ in T.CIRCUITS:
        ds = [d for d in T.DEVICES if d['ckt'] == key]
        if not ds:
            continue
        pts = [dev_xy(p, d) for d in ds]
        order = chain((PX, PY), pts)
        dash = ' stroke-dasharray="5,3"' if 'Lighting' in load else ''
        path = f'M{r1(PX)},{r1(PY)}' + ''.join(f'L{r1(x)},{r1(y)}' for x, y in order)
        o.append(f'<g class="wire" data-ckt="{key}">\n<path d="{path}" fill="none" stroke="{ELEC}" stroke-width="1.1" stroke-linecap="round"{dash}/>\n</g>')
    ds = [d for d in T.DEVICES if d['ckt'] == 'data' and d['type'] != 'media']
    media = next(d for d in T.DEVICES if d['type'] == 'media')
    MX, MY = dev_xy(p, media)
    o.append('<g class="wire" data-ckt="data">' + ''.join(f'<path d="M{r1(MX)},{r1(MY)}L{r1(dev_xy(p, d)[0])},{r1(dev_xy(p, d)[1])}" fill="none" stroke="#2c6aa0" stroke-width="0.9" stroke-dasharray="3,2"/>' for d in ds) + '</g>')
    for d in T.DEVICES:
        o.append(sym('e1', d['id'], dev_title(d), dev_symbol(p, d), ckt=d['ckt'], leg=d['leg'], net='1' if d['ckt'] == 'data' else None))
    o.append(compass(p, 61.0, 47.5))
    o.append(title_block(p, 'E-1', 'Electrical plan', 'Receptacles, switches, lights, alarms, data; circuits from panel MP', 'Schematic for pricing and coordination, not a stamped construction document. Verify on site.', TB_Y(p)))
    o.append('</svg>')
    svg = '\n'.join(o)

    sub = ['<div class="subtabs" id="ckt-tabs" role="group" aria-label="Circuit sheets"><button type="button" data-ckt="all" aria-pressed="true">E-1 all</button>']
    for i, (key, load, brk, *_r) in enumerate(T.CIRCUITS, 1):
        sub.append(f'<button type="button" data-ckt="{key}" aria-pressed="false" title="{esc(load)}, {esc(brk)}">E-1.{i} <span>{key}</span></button>')
    sub.append('<button type="button" data-ckt="data" aria-pressed="false" title="Cat6 and low voltage">E-1.D <span>data</span></button></div>')
    sub.append('<p class="ckt-name" id="ckt-name">All circuits. Pick a circuit sheet to see just its devices and the cable run from MP.</p>')

    crow = []
    for key, load, brk, wire, serves in T.CIRCUITS:
        n = sum(1 for d in T.DEVICES if d['ckt'] == key)
        crow.append((f'C{key}', [key, load, brk, wire, serves, (str(n), 'num')]))
    legs = []
    for lid, what, room, ctl in T.LEGS:
        sws = [d for d in T.DEVICES if d['leg'] == lid and d['id'][0] == 'S']
        lts = [d for d in T.DEVICES if d['leg'] == lid and d['id'][0] == 'L']
        legs.append((f'LEG:{lid}', [lid, what, room, '; '.join(f'{d["id"]} {d["legend"]}' for d in sws) or '—', ', '.join(f'{d["id"]} {d["legend"].split(",")[0]}' for d in lts), ctl]))
    devrows = [(d['id'], [d['id'], d['legend'], (locate(d['x'], d['y'], d['side']), 'loc'), (f'{d["h"]}"' if d['h'] else '—', 'num'), d['ckt'] if d['ckt'] not in ('data', 'panel') else '—', d['room'] + (f'. {d["note"]}' if d['note'] else '')]) for d in T.DEVICES]
    bom = {}
    for d in T.DEVICES:
        bom[d['legend']] = bom.get(d['legend'], 0) + 1
    bomrows = [(k, [k, str(v), '']) for k, v in sorted(bom.items(), key=lambda kv: -kv[1])]
    # cable estimate: chain length per circuit + 10' per device drop
    nm14 = nm12 = 0.0
    for key, load, brk, wire, serves in T.CIRCUITS:
        ds = [d for d in T.DEVICES if d['ckt'] == key]
        if not ds:
            continue
        pts = chain((panel['x'], panel['y']), [(d['x'], d['y']) for d in ds])
        L = 0
        cur = (panel['x'], panel['y'])
        for q in pts:
            L += abs(q[0] - cur[0]) + abs(q[1] - cur[1]) + 8
            cur = q
        L *= 1.15
        if '#14' in wire:
            nm14 += L
        elif '#12' in wire:
            nm12 += L
    bomrows += [
        ('NM14', ['14/2 NM-B (and 14/3 for 3-ways)', f'{math.ceil(nm14 / 250)} x 250\' rolls', f'about {math.ceil(nm14)}\' from the runs on the circuit sheets, +15%']),
        ('NM12', ['12/2 NM-B', f'{math.ceil(nm12 / 250)} x 250\' rolls', f'about {math.ceil(nm12)}\'']),
        ('NM6', ['10/3 NM-B (dryer), 10/2 (AC-1)', 'by the run', 'measure on site']),
        ('BOX', ['Device boxes, new-work, with covers', str(len([d for d in T.DEVICES if d['id'][0] in 'RS']) + 4), 'fan-rated pancake boxes at the fan locations']),
        ('CAT6', ['Cat6 CMR', f'{math.ceil(sum(abs(d["x"] - media["x"]) + abs(d["y"] - media["y"]) + 15 for d in ds) / 1000 + 0.5)} x 1000\' box', 'home runs to the media enclosure']),
    ]
    below = ['<div class="below">',
             '<section><h2>E-1 Electrical</h2>' + legend([(ELEC, 'receptacles R#'), ('#8a5a00', 'switches S#'), ('#d9a400', 'lights and fans L#'), ('#b4462f', 'alarms A#'), ('#2c6aa0', 'data and low voltage T#'), ('#333', 'panel and disconnects X#')]) +
             notes([
                 'Positions are taped from the nearest wall framing: interior walls to the face of the studs, exterior walls to the inside face of the exterior studs. W# is the wall number on S-1. Ceiling items give two distances, one to each nearest wall.',
                 'Code basis: NEC 2023 (confirm the edition the county has adopted). AFCI on every 120V 15A and 20A branch circuit in dwelling rooms (210.12); GFCI in bathrooms, kitchen, laundry, garage, outdoors, and for the dishwasher (210.8). Tamper-resistant receptacles throughout (406.12).',
                 'Mounting heights: receptacles 16" AFF to centre; switches 48"; counter and vanity receptacles 42"–44"; TV boxes 54". Every receptacle position meets the 6\'/12\' rule along the wall line (210.52(A)); kitchen counters have no point more than 24" from a receptacle (210.52(C)).',
                 'Panel MP is in the garage mechanical room on wall 20, 200A main breaker. Service entrance from the meter on the east wall; grounding electrode: Ufer in the footing plus a ground rod.',
                 'Smoke alarms in every bedroom, smoke/CO alarms outside the bedrooms and at the garage entry, all hardwired, interconnected, with battery backup (R314, R315).',
                 'Circuit sheets E-1.1 onward show one circuit each with its cable run drawn as a chain from MP through every device in nearest-neighbour order (solid for receptacle and appliance circuits, dashed for lighting). The run is a proposed order, not a required one. E-1.D shows the Cat6 home runs to the media enclosure.',
                 'Switch plan: every light belongs to one switch leg (table below). Clicking a light lights up every device on its leg in blue; clicking a leg row does the same.',
                 'Natural gas for the furnace, range and water heater; each needs only a 120V circuit. The dryer is electric (240V 30A). NEC 220.82 estimate: about 15 kVA, 65A, well inside the 200A service. Bond CSST gas piping to the electrode system with #6 Cu (G2411, NEC 250.104(B)).',
             ]) + '</section>',
             open_items([
                 'Dryer drawn electric. A gas dryer would need a 1/2" tee from the attic line and a 120V receptacle in place of circuit 3-4.',
                 'EV charging: add a 240V 50A circuit to the garage now (about $350 rough-in), or leave a spare 2-pole space and conduit?',
                 'Ceiling fans in the three bedrooms drawn on fan-rated boxes. Add one in the living room?',
                 'Data: Cat6 to each bedroom, both TVs and two ceiling access points drawn. Add cameras at the doors or more drops?',
                 'A/C and furnace breakers are placeholders until the HVAC contractor picks the equipment (nameplate MCA / MOCP).',
             ]),
             '<section class="wide">', table('Circuit schedule, panel MP', ['Ckt', 'Load', 'Breaker', 'Wire', 'Serves', 'Devices'], crow, '<span class="feed">MP: 200A main breaker load centre, 40 spaces, in the garage mechanical room. Circuit numbers are breaker positions; 2-pole loads take two.</span>'),
             table('Switch plan', ['Leg', 'What', 'Room', 'Switch(es)', 'Lights', 'Control'], legs, 'One row per switch leg. Click a row to light up its switch and lights on the drawing.'),
             table('Device schedule', ['Tag', 'Device', 'Position', 'AFF', 'Circuit', 'Notes'], devrows),
             table('Bill of materials', ['Item', 'Qty', 'Notes'], bomrows, 'Rough-order quantities from the drawing geometry, for pricing. The contractor takes off the final list.'),
             '</section></div>']
    return svg, '\n'.join(sub), '\n'.join(below)


# ============================================================================ P-1 plumbing
SZ_W = {'4"': 3.4, '3"': 2.8, '2"': 2.1, '1-1/2"': 1.7, '1-1/4"': 1.5}


def p1():
    p = PAPER()
    o = [svg_open(p, 'P-1 Plumbing plan'), grid(p), base_layers(p, faint=True)]
    # supply first (under), then drains, vents, fixtures
    for t in T.TRUNKS:
        body = p.path([(x - 0.12, y - 0.12) for x, y in t['pts']], stroke=COLD, stroke_width='1.6') + p.path([(x + 0.12, y + 0.12) for x, y in t['pts']], stroke=HOT, stroke_width='1.6')
        o.append(sym('p1', t['id'], f'Supply bundle {t["id"]}: PEX-A home runs, {ft_in(plen(t["pts"]))} — {t["note"]}', body))
    for b in T.BRANCHES:
        f = next(q for q in T.PFIX if q['id'] == b['fixture'])
        body = ''
        if f['cold']:
            body += p.path([(x - 0.08, y - 0.08) for x, y in b['pts']], stroke=COLD, stroke_width='0.9')
        if f['hot']:
            body += p.path([(x + 0.08, y + 0.08) for x, y in b['pts']], stroke=HOT, stroke_width='0.9')
        sz = '3/4"' if f['kind'] in ('tub', 'washer', 'wh') else '1/2"'
        o.append(sym('p1', f'H{f["id"]}', f'Home run to {f["id"]} {f["name"]}: {sz} PEX-A {"hot and cold" if f["hot"] and f["cold"] else "cold" if f["cold"] else "hot"}, about {ft_in(plen(b["pts"]) + 4)} from the manifold bundle', body))
    for dr in T.DRAINS:
        body = p.path(dr['pts'], stroke=PLUM, stroke_width=str(SZ_W.get(dr['size'], 1.6)), stroke_linecap='round')
        o.append(sym('p1', dr['id'], f'Drain {dr["id"]}: {dr["size"]} PVC DWV under the slab, {ft_in(plen(dr["pts"]))} — {dr["note"]}', body))
    for v in T.VENTS:
        bx, by = v['base']
        body = p.path(v['attic'], stroke=VENT, stroke_width='1.5', stroke_dasharray='6,3') + f'<circle cx="{r1(p.X(bx))}" cy="{r1(p.Y(by))}" r="4" fill="#fff" stroke="{VENT}" stroke-width="1.4"/>'
        o.append(sym('p1', v['id'], f'Vent {v["id"]}: {v["size"]} PVC, rises in {wname(v["wall"])} to the attic, then to the 3" VTR — {v["note"]}', body))
    X, Y = p.X(T.VTR['x']), p.Y(T.VTR['y'])
    o.append(sym('p1', 'VTR', f'VTR: {T.VTR["note"]}', hit(X, Y) + f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="6" fill="{VENT}" stroke="#fff" stroke-width="1"/><text x="{r1(X + 9)}" y="{r1(Y)}" font-size="6" font-weight="700" fill="{VENT}" dominant-baseline="middle">VTR 3"</text>'))
    X, Y = p.X(T.AAV['x']), p.Y(T.AAV['y'])
    o.append(sym('p1', 'AAV', f'AAV: {T.AAV["note"]}', hit(X, Y) + f'<rect x="{r1(X - 4)}" y="{r1(Y - 4)}" width="8" height="8" fill="#fff" stroke="{VENT}" stroke-width="1.2"/><text x="{r1(X)}" y="{r1(Y - 8)}" font-size="5" font-weight="700" fill="{VENT}" text-anchor="middle">AAV</text>'))
    for tg, x, y, note in T.CLEANOUTS:
        X, Y = p.X(x), p.Y(y)
        o.append(sym('p1', tg, f'Cleanout {tg}: {note}', hit(X, Y, 9) + f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="3.6" fill="#fff" stroke="{PLUM}" stroke-width="1.2"/><path d="M{r1(X - 2.5)},{r1(Y)}L{r1(X + 2.5)},{r1(Y)}" stroke="{PLUM}" stroke-width="1"/>'))
    X, Y = p.X(T.MANIFOLD['x']), p.Y(T.MANIFOLD['y'])
    o.append(sym('p1', 'MF', f'Manifold MF: {T.MANIFOLD["note"]}', hit(X, Y) + f'<rect x="{r1(X - 4)}" y="{r1(Y - 12)}" width="8" height="24" fill="#fff" stroke="{COLD}" stroke-width="1.3"/><text x="{r1(X - 7)}" y="{r1(Y)}" font-size="6" font-weight="700" fill="{COLD}" text-anchor="end" dominant-baseline="middle">MF</text>'))
    X, Y = p.X(T.SERVICE['x']), p.Y(T.SERVICE['y'])
    o.append(sym('p1', 'WS', f'Water service WS: {T.SERVICE["note"]}', hit(X, Y) + p.path([(T.SERVICE['x'], T.SERVICE['y']), (62.5, T.SERVICE['y'])], stroke=COLD, stroke_width='2.4') + f'<text x="{r1(p.X(62.6))}" y="{r1(Y - 6)}" font-size="6" fill="{COLD}" text-anchor="end">water service</text>'))
    for f in T.PFIX:
        X, Y = p.X(f['x']), p.Y(f['y'])
        o.append(sym('p1', f['id'], f'{f["id"]} {f["name"]}: trap {f["trap"]}, {f["dfu"]} DFU, vent {f["vent"]} — {f["note"]}',
                     hit(X, Y) + f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="6.4" fill="#fff" stroke="{COLD}" stroke-width="1.1"/><text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="5.2" font-weight="700" fill="{COLD}" text-anchor="middle" dominant-baseline="middle">{f["id"]}</text>'))
    o.append(compass(p, 61.0, 47.5))
    o.append(title_block(p, 'P-1', 'Plumbing plan', 'Drains and vents (DWV), PEX supply home runs, fixtures', 'Schematic for pricing and coordination, not a stamped construction document. Verify on site.', TB_Y(p)))
    o.append('</svg>')
    svg = '\n'.join(o)

    frows = [(f['id'], [f['id'], f['name'], f['trap'], (str(f['dfu']), 'num'), f['vent'], ('hot + cold' if f['hot'] and f['cold'] else 'cold' if f['cold'] else 'hot'), f'{f["h"]}"' if f['h'] else '—', f['note']]) for f in T.PFIX]
    drows = [(d['id'], [d['id'], d['size'], (ft_in(plen(d['pts'])), 'num'), '1/4"/ft' if d['size'] != '4"' else '1/4"/ft (1/8" min)', d['note']]) for d in T.DRAINS]
    vrows = [(v['id'], [v['id'], v['size'], wname(v['wall']), (ft_in(plen(v['attic']) + P.CEIL), 'num'), v['note']]) for v in T.VENTS]
    vrows.append(('VTR', ['VTR', '3"', 'roof, rear slope', '—', T.VTR['note']]))
    vrows.append(('AAV', ['AAV', '1-1/2"', 'island sink base', '—', T.AAV['note']]))
    srows = [(t['id'], [t['id'], 'bundle', (ft_in(plen(t['pts'])), 'num'), t['note']]) for t in T.TRUNKS]
    for b in T.BRANCHES:
        f = next(q for q in T.PFIX if q['id'] == b['fixture'])
        srows.append((f'H{f["id"]}', [f'H{f["id"]}', f'{"3/4" if f["kind"] in ("tub", "washer", "wh") else "1/2"}" to {f["id"]} {f["name"]}', (ft_in(plen(b['pts']) + 4), 'num'), 'hot and cold' if f['hot'] and f['cold'] else 'cold only' if f['cold'] else 'hot only']))
    corows = [(tg, [tg, note]) for tg, x, y, note in T.CLEANOUTS]
    dfu = sum(f['dfu'] for f in T.PFIX)
    pex = sum(plen(b['pts']) + 4 for b in T.BRANCHES) * 2 + sum(plen(t['pts']) for t in T.TRUNKS)
    pipe = {}
    for d in T.DRAINS:
        pipe[d['size']] = pipe.get(d['size'], 0) + plen(d['pts'])
    for v in T.VENTS:
        pipe['2" vent'] = pipe.get('2" vent', 0) + plen(v['attic']) + P.CEIL
    bom = [(f'PVC{k}', [f'PVC DWV {k} sch 40', f'{math.ceil(v * 1.15 / 10)} x 10\'', f'{math.ceil(v)}\' measured +15%']) for k, v in sorted(pipe.items())]
    bom += [
        ('PEX', ['PEX-A 1/2" (red and blue)', f'{math.ceil(pex * 1.15 / 100)} x 100\' coils', f'about {math.ceil(pex)}\' of home runs']),
        ('PEX34', ['PEX-A 3/4" and 1"', 'by the run', 'tub, washer and water heater runs, service']),
        ('MAN', ['PEX manifold, 12-port hot / 12-port cold, with valves', '1', 'MF in the mech room']),
        ('WH', ['Water heater, 50 gal gas, power direct vent, pan, stand, expansion tank', '1', 'gas and vent on M-1']),
        ('SLV', ['Sleeves for PEX through the slab and the garage foundation', str(len(T.BRANCHES) + 4), 'protect every run where it leaves the slab']),
        ('SC', ['Frost-free sillcocks, 12"', '2', 'F13, F14']),
        ('WB', ['Washer box with valves and 2" drain', '1', 'F7']),
    ]
    below = ['<div class="below">',
             '<section><h2>P-1 Plumbing</h2>' + legend([(PLUM, 'drains under the slab (thicker = larger)'), (VENT, 'vents: rise in the wall, run in the attic (dashed)'), (COLD, 'cold PEX'), (HOT, 'hot PEX'), ('', 'F# fixture, CO# cleanout, MF manifold')]) +
             notes([
                 'Code basis: IRC 2021 chapters 25–33 (confirm the adopted edition). Drains PVC DWV schedule 40 under the slab at 1/4"/ft; the building drain is 4" (19 DFU, well under the 3" limit, 4" for a septic connection).',
                 'Every drain run is under the slab, laid before the pour, tested with a 10\' head (P2503.5). Fixture drain positions are where the trap arm meets the wall or the floor.',
                 'Vents: each bathroom group is wet-vented through its lavatory (P3108), with one 2" dry vent rising in an interior wall. The three vents join in the attic and leave through one 3" vent on the rear roof slope, out of sight from the street.',
                 'Supply: PEX-A home runs from the manifold MF in the garage mech room, 1/2" to each fixture (3/4" to the tub and washer), under the slab in sleeves with no fittings below the slab. The bundle crosses under the garage slab: insulate it there, and keep every line on the warm side of the insulation in walls 13 and 14.',
                 'No supply lines in exterior walls: the toilets are fed up through the slab and the tub valve is on wall 8 (interior).',
                 'Water heater: 50 gal gas, power direct vent (sealed combustion, so the closed mech room needs no combustion-air openings), on an 18" stand because it is in the garage (G2408.2), in a pan with a drain, thermal expansion tank, T&P discharge to within 6" of the floor. Gas piping and the roof vent are on M-1.',
             ]) + '</section>',
             open_items([
                 'Sewer or septic, and which side of the lot? The building drain is drawn leaving the front wall under the laundry.',
                 'Water source: city or well? A well adds a pressure tank in the mech room (about 3\' x 3\' beside the water heater).',
                 'Island sink vent: an AAV is drawn. Some jurisdictions want an island loop vent instead; confirm with the inspector.',
                 'Water softener or filter at the service entry?',
                 'Tub in Bath 2 (drawn) or a walk-in shower?',
             ]),
             '<section class="wide">', table('Fixture schedule', ['Tag', 'Fixture', 'Trap', 'DFU', 'Vent', 'Supply', 'Rough-in', 'Notes'], frows, f'{dfu} DFU in all (IRC Table P3004.1).'),
             table('Drain schedule', ['Run', 'Size', 'Length', 'Slope', 'Notes'], drows),
             table('Vent schedule', ['Vent', 'Size', 'Rises in', 'Length', 'Notes'], vrows),
             table('Supply runs', ['Run', 'What', 'Length', 'Notes'], srows, 'Lengths are along the drawn route plus 4\' for the rise; order by the coil.'),
             table('Cleanouts', ['Tag', 'Where'], corows),
             table('Bill of materials', ['Item', 'Qty', 'Notes'], bom, 'Rough-order quantities from the drawing geometry, for pricing. The plumber takes off the final list.'),
             '</section></div>']
    return svg, '\n'.join(below)


# ============================================================================ M-1 HVAC
def m1():
    p = PAPER()
    o = [svg_open(p, 'M-1 HVAC plan'), grid(p), base_layers(p, faint=True)]
    W_ = lambda size: int(size.split('x')[0]) / 12
    for t in T.DTRUNKS:
        w = W_(t['size'])
        body = ''
        for i in range(1, len(t['pts'])):
            (ax, ay), (bx, by) = t['pts'][i - 1], t['pts'][i]
            if abs(ay - by) < 1e-6:
                body += p.rect(min(ax, bx), max(ax, bx), ay - w / 2, ay + w / 2, fill='#f6c99c', stroke=DUCT, stroke_width='0.8', fill_opacity='0.75')
            else:
                body += p.rect(ax - w / 2, ax + w / 2, min(ay, by), max(ay, by), fill='#f6c99c', stroke=DUCT, stroke_width='0.8', fill_opacity='0.75')
        o.append(sym('m1', t['id'], f'Supply trunk {t["id"]} {t["size"]} in the attic, {ft_in(plen(t["pts"]))} — {t["note"]}', body))
    x1, x2, y1, y2 = T.SUPPLY_PLENUM
    o.append(sym('m1', 'SP', 'Supply plenum on the FAU-1 discharge, sheet metal, R-8', p.rect(x1, x2, y1, y2, fill='#f6c99c', stroke=DUCT, stroke_width='1')))
    x1, x2, y1, y2 = T.RETURN_PLENUM
    o.append(sym('m1', 'RP', 'Return plenum with the filter rack, on the FAU-1 intake', p.rect(x1, x2, y1, y2, fill='#cfe0f2', stroke=RET, stroke_width='1')))
    a = T.AH
    o.append(sym('m1', 'FAU-1', a['note'], p.rect(a['x1'], a['x2'], a['y1'], a['y2'], fill='#fff', stroke='#333', stroke_width='1.3') + p.text((a['x1'] + a['x2']) / 2, (a['y1'] + a['y2']) / 2, 'FAU-1 (attic)', 6.5, fill='#333', font_weight='700')))
    h = T.HP
    o.append(sym('m1', 'AC-1', h['note'], p.rect(h['x1'], h['x2'], h['y1'], h['y2'], fill='#fff', stroke='#333', stroke_width='1.3') + p.text((h['x1'] + h['x2']) / 2, (h['y1'] + h['y2']) / 2, 'AC-1', 6.5, fill='#333', font_weight='700')))
    o.append(sym('m1', 'LS', 'Refrigerant line set, insulated, AC-1 to FAU-1: through the east wall into the mech room, up into the attic and west over the garage ceiling; 35\' approx.', p.path(T.LINESET, stroke='#7a4fa0', stroke_width='1.3', stroke_dasharray='6,2,1,2')))
    for g in T.GAS:
        if len(g['pts']) > 1:
            body = p.path(g['pts'], stroke=GASC, stroke_width='1.4', stroke_dasharray='8,2,2,2')
        else:
            X, Y = p.X(g['pts'][0][0]), p.Y(g['pts'][0][1])
            body = hit(X, Y, 8) + f'<path d="M{r1(X - 4)},{r1(Y - 4)}L{r1(X + 4)},{r1(Y + 4)}M{r1(X - 4)},{r1(Y + 4)}L{r1(X + 4)},{r1(Y - 4)}" stroke="{GASC}" stroke-width="1.6"/><circle cx="{r1(X)}" cy="{r1(Y)}" r="5.5" fill="none" stroke="{GASC}" stroke-width="1"/>'
        o.append(sym('m1', g['id'], f'Gas {g["id"]}, {g["size"]}: {g["note"]}', body))
    gm = T.GAS_METER
    X, Y = p.X(gm['x']), p.Y(gm['y'])
    o.append(sym('m1', 'GM', gm['note'], hit(X, Y, 9) + f'<rect x="{r1(X - 5)}" y="{r1(Y - 7)}" width="10" height="14" fill="#fff" stroke="{GASC}" stroke-width="1.3"/><text x="{r1(X + 8)}" y="{r1(Y + 2)}" font-size="5.5" font-weight="700" fill="{GASC}">GAS METER</text>'))
    for fl in T.FLUES:
        X, Y = p.X(fl['pts'][-1][0]), p.Y(fl['pts'][-1][1])
        o.append(sym('m1', fl['id'], fl['note'], p.path(fl['pts'], stroke='#555', stroke_width='1.6') + hit(X, Y, 9) + f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="4.5" fill="#fff" stroke="#555" stroke-width="1.4"/><circle cx="{r1(X)}" cy="{r1(Y)}" r="2" fill="#555"/><text x="{r1(X - 7 if fl['pts'][-1][0] > 50 else X + 7)}" y="{r1(Y + 9 if fl['pts'][-1][0] > 50 else Y - 4)}" font-size="5" fill="#555" text-anchor="{'end' if fl['pts'][-1][0] > 50 else 'start'}">{fl["id"]} {fl["name"].lower()}</text>'))
    o.append(sym('m1', 'CD', 'Condensate: 3/4" PVC from FAU-1, 1/4"/ft, down wall 13 to the washer standpipe with an air gap; the auxiliary pan has a float switch that stops the unit', p.path(T.CONDENSATE, stroke='#2a9d8f', stroke_width='1.1', stroke_dasharray='3,2')))
    for gid, room, x, y, cfm, flex, frm in T.REGISTERS:
        X, Y = p.X(x), p.Y(y)
        body = p.path([frm, (x, y)], stroke=DUCT, stroke_width='1.1') + hit(X, Y) + f'<rect x="{r1(X - 7)}" y="{r1(Y - 5)}" width="14" height="10" fill="#fff" stroke="{DUCT}" stroke-width="1.2"/><path d="M{r1(X - 7)},{r1(Y - 5)}L{r1(X + 7)},{r1(Y + 5)}M{r1(X - 7)},{r1(Y + 5)}L{r1(X + 7)},{r1(Y - 5)}" stroke="{DUCT}" stroke-width="0.6"/>' + f'<text x="{r1(X)}" y="{r1(Y + 11)}" font-size="5.5" font-weight="700" fill="{DUCT}" text-anchor="middle">{gid} {cfm}</text>'
        o.append(sym('m1', gid, f'{gid} ceiling diffuser, {room}: {cfm} CFM on {flex} insulated flex (R-8) from the trunk; {locate(x, y, "c")}', body))
    for r in T.RETURNS:
        X, Y = p.X(r['x']), p.Y(r['y'])
        w, l = r['w'] * p.s, r['l'] * p.s
        body = p.path(r['route'], stroke=RET, stroke_width='2.2') + hit(X, Y, 14) + f'<rect x="{r1(X - w / 2)}" y="{r1(Y - l / 2)}" width="{r1(w)}" height="{r1(l)}" fill="#e8f0f9" stroke="{RET}" stroke-width="1.2"/>' + ''.join(f'<line x1="{r1(X - w / 2)}" y1="{r1(Y - l / 2 + k * l / 6)}" x2="{r1(X + w / 2)}" y2="{r1(Y - l / 2 + k * l / 6)}" stroke="{RET}" stroke-width="0.5"/>' for k in range(1, 6)) + f'<text x="{r1(X + w / 2 + 3)}" y="{r1(Y)}" font-size="5.5" font-weight="700" fill="{RET}" dominant-baseline="middle">{r["id"]}</text>'
        o.append(sym('m1', r['id'], f'{r["id"]} return, {r["room"]}: {r["size"]}, {r["cfm"]} CFM — {r["note"]}', body))
    for jid, room, a_, b_, size in T.JUMPS:
        body = p.path([a_, b_], stroke=RET, stroke_width='1.2', stroke_dasharray='3,2') + ''.join(f'<rect x="{r1(p.X(q[0]) - 4)}" y="{r1(p.Y(q[1]) - 3)}" width="8" height="6" fill="#fff" stroke="{RET}" stroke-width="0.9"/>' for q in (a_, b_))
        o.append(sym('m1', jid, f'Jump duct {jid}: {room} to the hall, {size} insulated flex, ceiling grille to ceiling grille, so the room returns air with its door shut', body))
    for t in T.TSTATS:
        X, Y = p.X(t['x'] + 0.4), p.Y(t['y'])
        o.append(sym('m1', t['id'], f'Thermostat {t["id"]}: {t["note"]}', hit(X, Y) + f'<circle cx="{r1(X)}" cy="{r1(Y)}" r="5" fill="#fff" stroke="#333" stroke-width="1"/><text x="{r1(X)}" y="{r1(Y + 0.3)}" font-size="5.5" font-weight="700" fill="#333" text-anchor="middle" dominant-baseline="middle">T</text>'))
    for e in T.EXHAUST:
        X, Y = p.X(e['pts'][0][0]), p.Y(e['pts'][0][1])
        X2, Y2 = p.X(e['pts'][-1][0]), p.Y(e['pts'][-1][1])
        body = p.path(e['pts'], stroke='#8d8d8d', stroke_width='1.4') + hit(X, Y, 9) + f'<circle cx="{r1(X2)}" cy="{r1(Y2)}" r="3.5" fill="#8d8d8d"/>' + f'<text x="{r1(X2 + 5)}" y="{r1(Y2 - 5)}" font-size="5" fill="#6d6d6d">{e["id"]}</text>'
        o.append(sym('m1', e['id'], f'{e["id"]} {e["name"]}: {e["size"]} duct to a {e["cap"]}' + (f', {e["cfm"]} CFM' if e['cfm'] else ''), body))
    o.append(compass(p, 61.0, 47.5))
    o.append(title_block(p, 'M-1', 'HVAC plan', 'Gas furnace FAU-1 in the attic, A/C AC-1, gas piping, ducts, registers, exhaust', 'Schematic for pricing and coordination; equipment and duct sizes need a Manual J/S/D.', TB_Y(p)))
    o.append('</svg>')
    svg = '\n'.join(o)

    eq = [
        ('FAU-1', ['FAU-1', 'Gas furnace, condensing, with A/C coil', 'attic over the back hall', '60,000 BTU/h input, 96% AFUE, two-stage; 1,000 CFM variable speed; 2.5-ton coil', T.AH['note']]),
        ('AC-1', ['AC-1', 'Air conditioner, outdoor', 'east side, by the mech room', '2.5 ton, 15.2 SEER2 or better', T.HP['note']]),
        ('GM', ['GM', 'Gas meter', 'garage east wall', 'by the utility', T.GAS_METER['note']]),
        ('V1', ['V1', 'Furnace vent', 'rear roof slope', '2" PVC, concentric', T.FLUES[0]['note']]),
        ('V2', ['V2', 'Water heater vent', 'rear roof slope, over the mech room', 'PVC per the manual, concentric', T.FLUES[1]['note']]),
        ('T1', ['T1', 'Thermostat', 'wall 5, living room', 'communicating, with outdoor sensor', T.TSTATS[0]['note']]),
    ]
    for e in T.EXHAUST:
        eq.append((e['id'], [e['id'], e['name'], '', f'{e["cfm"]} CFM' if e['cfm'] else '—', f'{e["size"]} duct to a {e["cap"]}']))
    regs = [(g[0], [g[0], g[1], (str(g[4]), 'num'), g[5], '10x6 4-way ceiling diffuser' if g[4] >= 70 else '8x6 ceiling diffuser', locate(g[2], g[3], 'c')]) for g in T.REGISTERS]
    rets = [(r['id'], [r['id'], r['room'], (str(r['cfm']), 'num'), r['size'], r['note']]) for r in T.RETURNS]
    rets += [(j[0], [j[0], j[1], '—', f'{j[4]} jump duct', 'ceiling grille to the hall, so the room returns with its door shut']) for j in T.JUMPS]
    ducts = [(t['id'], [t['id'], t['size'], (ft_in(plen(t['pts'])), 'num'), t['note']]) for t in T.DTRUNKS]
    flex = {}
    for g in T.REGISTERS:
        flex[g[5]] = flex.get(g[5], 0) + plen([g[6], (g[2], g[3])]) + 3
    bom = [(f'FX{k}', [f'{k} insulated flex, R-8', f'{math.ceil(v * 1.2 / 25)} x 25\' bags', f'{math.ceil(v)}\' measured +20%']) for k, v in sorted(flex.items())]
    bom += [
        ('SM', ['Sheet metal trunk 14x8 / 10x8, R-8 wrap', f'{math.ceil(sum(plen(t["pts"]) for t in T.DTRUNKS) * 1.1)}\'', 'plus take-off collars with dampers, one per register']),
        ('REG', ['Ceiling diffusers', str(len(T.REGISTERS)), 'with boots, sealed to the drywall']),
        ('RG', ['Filter return grilles 20x30 and 16x25', '2', 'MERV 8 filters']),
        ('JD', ['Jump ducts, 10" flex with 2 grilles each', str(len(T.JUMPS)), '']),
        ('EF', ['Bath fans 80 CFM with roof caps', '2', 'EF2 with a continuous-ventilation control']),
        ('GAS', ['Gas piping: 3/4" black steel or CSST, 1/2" CSST', f'{math.ceil(sum(plen(g["pts"]) for g in T.GAS if len(g["pts"]) > 1) * 1.15)}\'', 'shutoffs, sediment traps, CSST bonding clamp and #6 Cu; pressure test 3 psi for 10 min (G2417)']),
        ('PVC', ['2" PVC sch 40 intake and exhaust, concentric roof kit', '1 kit + 20\'', 'per the furnace manual']),
        ('MST', ['Mastic, UL 181 tape, duct straps', 'lot', 'every joint sealed; total leakage ≤ 4 CFM25 per 100 sq ft (IECC R403.3.5)']),
    ]
    below = ['<div class="below">',
             '<section><h2>M-1 HVAC</h2>' + legend([(DUCT, 'supply trunks and flex, ceiling diffusers G#'), (RET, 'returns RG# and jump ducts J#'), ('#7a4fa0', 'refrigerant line set'), ('#2a9d8f', 'condensate'), (GASC, 'natural gas'), ('#555', 'appliance vents V#'), ('#8d8d8d', 'exhaust ducts EF#')]) +
             notes([
                 'The gas furnace FAU-1 sits in the attic on a platform over the back hall, as the owner asked; the mechanical room is in the garage (water heater, panel, manifold). The way to FAU-1 is the pull-down stair in the garage ceiling, with a catwalk and a 30" service space (M1305.1.3), a light switched at the access and a receptacle at the unit.',
                 'Every duct is in the attic: sheet-metal trunks with R-8 wrap, R-8 flex to ceiling diffusers, every joint sealed with mastic. Keep the flex runs short and straight, and pull them tight. Bury the ducts in the attic insulation where they cross the ceiling.',
                 'Airflow (1,000 CFM) is shared by room area and exposure for pricing; the HVAC contractor\'s Manual J (loads), S (equipment) and D (ducts) set the final numbers. Two filtered returns: RG1 under the unit and RG2 in the bedroom hall; the bedrooms return through jump ducts J1–J3.',
                 'Heat: natural gas. FAU-1 is a sealed-combustion condensing furnace (direct vent), so it takes no combustion air from the attic; its 2" PVC intake and exhaust leave through the rear roof slope (V1). Cooling from AC-1 through the coil on the furnace. Zone 6 assumed; confirm the design temperature.',
                 'Gas: the meter is on the garage east wall. The line runs up the inside of that wall into the mech room (main shutoff, capped tee for later), up into the attic and west to FAU-1, with a shutoff and sediment trap at the unit. Size it for the furnace, range and water heater (about 175 CFH at 7" w.c.: 3/4" to the mech room, 1/2" branches). The range branch GS5 tees off in the attic and drops inside wall 15 to a shutoff behind the range; the water heater branch GS4 stays in the mech room. CSST is bonded to the electrode system; the gas fitter does the pressure test.',
                 'Ventilation: EF2 in the primary bath runs continuously at 50 CFM to meet IRC M1505.4 whole-house ventilation, boosting to 80 for showers. An ERV is the better choice in a tight cold-climate house (open item).',
                 'Range hood 300 CFM over the gas range, ducted 6" to a roof cap; under 400 CFM, so no makeup air is required (M1503.6). Dryer vent rigid 4", 11\' developed length with two elbows, roof cap on the front slope.',
             ]) + '</section>',
             open_items([
                 'Furnace in the attic: in a cold climate, the condensate lines need protection from freezing (route inside the insulation or add heat tape). Confirm, or move FAU-1 into a conditioned closet (the back hall alcove fits an upflow unit).',
                 'Water heater: 50 gal power direct vent tank drawn. A gas tankless (about $1,500 more) saves the stand and space but needs a larger gas line.',
                 'Whole-house ventilation: continuous bath fan (drawn) or an ERV (about $2,500–$4,000 installed)?',
                 'Manual J/S/D from the HVAC contractor before ordering equipment; the 2.5-ton size is an estimate for 1,800 sq ft.',
             ]),
             '<section class="wide">', table('Equipment schedule', ['Tag', 'Equipment', 'Where', 'Size', 'Notes'], eq),
             table('Register schedule', ['Tag', 'Room', 'CFM', 'Flex', 'Diffuser', 'Position'], regs, f'{sum(g[4] for g in T.REGISTERS)} CFM supply in all.'),
             table('Return schedule', ['Tag', 'Room', 'CFM', 'Size', 'Notes'], rets),
             table('Duct schedule', ['Trunk', 'Size', 'Length', 'Notes'], ducts),
             table('Bill of materials', ['Item', 'Qty', 'Notes'], bom, 'Rough-order quantities from the drawing geometry, for pricing. The HVAC contractor takes off the final list.'),
             '</section></div>']
    return svg, '\n'.join(below)
