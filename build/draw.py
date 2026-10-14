"""SVG drawing helpers shared by every sheet: the paper transform, the base plan (rooms, walls,
doors, windows, fixtures, labels, room dimensions) and the small symbols."""
import html
import math
import plan as P

esc = lambda s: html.escape(str(s), quote=True)


def ft_in(v):
    neg = v < 0
    v = abs(v)
    f = math.floor(v + 1e-9)
    i = round((v - f) * 12)
    if i == 12:
        f, i = f + 1, 0
    return ('-' if neg else '') + f"{f}'-{i}\""


def r1(v):
    return f'{v:.1f}'


class Paper:
    """plan feet -> sheet px. North up, west on the left, like the BuildWise plan."""

    def __init__(self, s, x0, x1, y0, y1, ml, mt, mb=0, mr=0):
        self.s, self.x0, self.x1, self.y0, self.y1, self.ml, self.mt = s, x0, x1, y0, y1, ml, mt
        self.w = ml + (x1 - x0) * s + mr
        self.h = mt + (y1 - y0) * s + mb

    def X(self, x):
        return self.ml + (x - self.x0) * self.s

    def Y(self, y):
        return self.mt + (self.y1 - y) * self.s

    def pt(self, x, y):
        return f'{r1(self.X(x))},{r1(self.Y(y))}'

    def rect(self, x1, x2, y1, y2, **a):
        X1, X2, Y1, Y2 = self.X(min(x1, x2)), self.X(max(x1, x2)), self.Y(max(y1, y2)), self.Y(min(y1, y2))
        return tag('rect', x=r1(X1), y=r1(Y1), width=r1(X2 - X1), height=r1(Y2 - Y1), **a)

    def line(self, x1, y1, x2, y2, **a):
        return tag('line', x1=r1(self.X(x1)), y1=r1(self.Y(y1)), x2=r1(self.X(x2)), y2=r1(self.Y(y2)), **a)

    def path(self, pts, **a):
        return tag('path', d='M' + 'L'.join(self.pt(x, y) for x, y in pts), fill='none', **a)

    def text(self, x, y, t, size=8, **a):
        a.setdefault('fill', '#333')
        a.setdefault('text-anchor', 'middle')
        a.setdefault('dominant-baseline', 'middle')
        return f'<text x="{r1(self.X(x))}" y="{r1(self.Y(y))}" font-size="{size}"' + ''.join(f' {k.replace("_", "-")}="{esc(v)}"' for k, v in a.items()) + f'>{esc(t)}</text>'


def tag(name, **a):
    return f'<{name}' + ''.join(f' {k.replace("_", "-")}="{esc(v)}"' for k, v in a.items() if v is not None) + '/>'


COLORS = {'bed': '#dcefe6', 'wet': '#e6eef6', 'serv': '#e9e6e0', 'circ': '#ffffff', 'live': '#f7f4ec', 'fixed': '#e3e0d8', 'garage': '#eceae6'}
WALL_INK = {'E': '#4a4744', 'P': '#5c5853', 'G': '#5c5853', 'M': '#5c5853'}


def wall_rect(w):
    n, x1, y1, x2, y2, typ, _ = w
    t = P.THICK[typ]
    if P.along_x(w):
        return min(x1, x2), max(x1, x2), y1 - t / 2, y1 + t / 2
    return x1 - t / 2, x1 + t / 2, min(y1, y2), max(y1, y2)


def openings_on(n):
    """doors and windows in wall n as (lo, hi, kind, tag) along the wall"""
    out = []
    for d in P.DOORS:
        if d[1] == n:
            out.append((d[2] - d[3] / 2, d[2] + d[3] / 2, d[5], d[0]))
    for w in P.WINDOWS:
        if w[1] == n:
            out.append((w[2] - w[3] / 2, w[2] + w[3] / 2, 'window', w[0]))
    return sorted(out)


def wall_pieces(w):
    """the solid pieces of a wall between its openings, as plan rectangles"""
    x1, x2, y1, y2 = wall_rect(w)
    ax = P.along_x(w)
    lo, hi = (x1, x2) if ax else (y1, y2)
    cur, out = lo, []
    for a, b, kind, _ in openings_on(w[0]):
        if a > cur:
            out.append((cur, a))
        cur = max(cur, b)
    if hi > cur:
        out.append((cur, hi))
    return [((a, b, y1, y2) if ax else (x1, x2, a, b)) for a, b in out]


def base_layers(p, walls_colour=None, faint=False, fixtures=True, labels=True, dims=None, outdoor=True):
    """the plan every sheet is drawn on. walls_colour: fn(wall) -> colour, else dark grey."""
    o = []
    if outdoor:
        for name, x1, x2, y1, y2, note in P.OUTDOOR:
            o.append(p.rect(x1, x2, y1, y2, fill='#ece9e3', stroke='#b9b3a8', stroke_width='0.8'))
        # AC pad and porch / patio posts
        o.append(p.rect(58.4, 61.6, 19.4, 22.6, fill='#e2ded6', stroke='#b9b3a8', stroke_width='0.6'))
    o.append(tag('path', d='M' + 'L'.join(p.pt(x, y) for x, y in P.FOOTPRINT) + 'Z', fill='#fff'))
    for r in P.ROOMS:
        cx1, cx2, cy1, cy2 = P.clear(r)
        o.append(p.rect(cx1, cx2, cy1, cy2, fill=COLORS[r[5]]))
    if fixtures:
        for f in P.FIXTURES:
            o.append(fixture_svg(p, f, faint))
    for w in P.WALLS:
        col = walls_colour(w) if walls_colour else WALL_INK[w[5]]
        for (x1, x2, y1, y2) in wall_pieces(w):
            o.append(p.rect(x1, x2, y1, y2, fill=col))
    o += [door_svg(p, d) for d in P.DOORS] + [window_svg(p, w) for w in P.WINDOWS]
    if outdoor:
        for x, y, _ in P.POSTS:
            o.append(p.rect(x - 0.25, x + 0.25, y - 0.25, y + 0.25, fill='#8a7a64'))
    if dims:
        o.append(dims)
    if labels:
        for t, x, y, sz in P.LABELS:
            o.append(p.text(x, y, t, sz, fill='#6f685d'))
    return '\n'.join(o)


def fixture_svg(p, f, faint=False):
    kind, x1, x2, y1, y2, front, label, note = f
    st = dict(fill='#fff', stroke='#b5aea2' if not faint else '#d2ccc2', stroke_width='0.7')
    o = []
    if kind in ('tub',):
        o.append(p.rect(x1, x2, y1, y2, **st))
        o.append(p.rect(x1 + 0.25, x2 - 0.25, y1 + 0.25, y2 - 0.25, rx=6, **st))
    elif kind == 'toilet':
        # tank on the wall, bowl out into the room
        if front in 'EW':
            tx = (x1, x1 + 0.6) if front == 'E' else (x2 - 0.6, x2)
            o.append(p.rect(*tx, y1 + 0.05, y2 - 0.05, **st))
            cx = (x1 + 0.6 + 0.85) if front == 'E' else (x2 - 0.6 - 0.85)
            o.append(f'<ellipse cx="{r1(p.X(cx))}" cy="{r1(p.Y((y1 + y2) / 2))}" rx="{r1(0.9 * p.s)}" ry="{r1(0.65 * p.s)}" fill="#fff" stroke="{st["stroke"]}" stroke-width="0.7"/>')
        else:
            ty = (y1, y1 + 0.6) if front == 'N' else (y2 - 0.6, y2)
            o.append(p.rect(x1 + 0.05, x2 - 0.05, *ty, **st))
            cy = (y1 + 0.6 + 0.85) if front == 'N' else (y2 - 0.6 - 0.85)
            o.append(f'<ellipse cx="{r1(p.X((x1 + x2) / 2))}" cy="{r1(p.Y(cy))}" rx="{r1(0.65 * p.s)}" ry="{r1(0.9 * p.s)}" fill="#fff" stroke="{st["stroke"]}" stroke-width="0.7"/>')
    elif kind == 'vanity':
        o.append(p.rect(x1, x2, y1, y2, **st))
        n = 2 if max(x2 - x1, y2 - y1) > 5 else 1
        for k in range(n):
            if front in 'EW':
                cy = y1 + (y2 - y1) * (k + 0.5) / n
                o.append(f'<ellipse cx="{r1(p.X((x1 + x2) / 2))}" cy="{r1(p.Y(cy))}" rx="{r1(0.55 * p.s)}" ry="{r1(0.7 * p.s)}" fill="#fff" stroke="{st["stroke"]}" stroke-width="0.7"/>')
            else:
                cx = x1 + (x2 - x1) * (k + 0.5) / n
                o.append(f'<ellipse cx="{r1(p.X(cx))}" cy="{r1(p.Y((y1 + y2) / 2))}" rx="{r1(0.7 * p.s)}" ry="{r1(0.55 * p.s)}" fill="#fff" stroke="{st["stroke"]}" stroke-width="0.7"/>')
    elif kind == 'shower':
        o.append(p.rect(x1, x2, y1, y2, **st))
        o.append(p.line(x1, y1, x2, y2, stroke=st['stroke'], stroke_width='0.5'))
        o.append(p.line(x1, y2, x2, y1, stroke=st['stroke'], stroke_width='0.5'))
    elif kind == 'bed':
        o.append(p.rect(x1, x2, y1, y2, **st))
        # pillows at the head
        if front in 'EW':
            hx = x1 if front == 'E' else x2 - 1.2
            w = (y2 - y1)
            for k in range(2):
                o.append(p.rect(hx + 0.2, hx + 1.0, y1 + 0.25 + k * w / 2, y1 + w / 2 * (k + 1) - 0.25, **st))
            o.append(p.line(x1 + (2.0 if front == 'E' else 0), y1, x1 + (2.0 if front == 'E' else 0), y2, stroke=st['stroke'], stroke_width='0.5') if front == 'E' else p.line(x2 - 2.0, y1, x2 - 2.0, y2, stroke=st['stroke'], stroke_width='0.5'))
    elif kind == 'table':
        o.append(p.rect(x1, x2, y1, y2, rx=4, **st))
        n = 3
        for k in range(n):
            yy = y1 + (y2 - y1) * (k + 0.5) / n
            o.append(p.rect(x1 - 1.0, x1 - 0.2, yy - 0.4, yy + 0.4, **st))
            o.append(p.rect(x2 + 0.2, x2 + 1.0, yy - 0.4, yy + 0.4, **st))
        xx = (x1 + x2) / 2
        o.append(p.rect(xx - 0.4, xx + 0.4, y1 - 1.0, y1 - 0.2, **st))
        o.append(p.rect(xx - 0.4, xx + 0.4, y2 + 0.2, y2 + 1.0, **st))
    elif kind == 'island':
        o.append(p.rect(x1, x2, y1, y2, **st))
        o.append(p.rect(x2 - 2.0, x2 - 0.3, 27.6, 29.9, rx=3, **st))   # sink
        o.append(p.text((x1 + x2) / 2, y1 + 0.8, 'DW', 5, fill='#9a9387'))
        for k in range(4):
            yy = y1 + 0.9 + k * 1.6
            o.append(f'<circle cx="{r1(p.X(x1 - 0.6))}" cy="{r1(p.Y(yy))}" r="{r1(0.55 * p.s)}" fill="#fff" stroke="{st["stroke"]}" stroke-width="0.6"/>')
    elif kind == 'range':
        o.append(p.rect(x1, x2, y1, y2, **st))
        for dx in (0.6, 1.4):
            for dy in (0.6, 1.9):
                o.append(f'<circle cx="{r1(p.X(x1 + dx))}" cy="{r1(p.Y(y1 + dy))}" r="{r1(0.3 * p.s)}" fill="none" stroke="{st["stroke"]}" stroke-width="0.6"/>')
    elif kind == 'car':
        o.append(p.rect(x1, x2, y1, y2, rx=9, fill='#f4f3f1', stroke='#c9c4bb', stroke_width='0.8', stroke_dasharray='3,2'))
    elif kind == 'stair':
        o.append(p.rect(x1, x2, y1, y2, **st))
        for k in range(1, 6):
            yy = y1 + (y2 - y1) * k / 6
            o.append(p.line(x1, yy, x2, yy, stroke=st['stroke'], stroke_width='0.5'))
    elif kind == 'wh':
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        o.append(f'<circle cx="{r1(p.X(cx))}" cy="{r1(p.Y(cy))}" r="{r1(0.95 * p.s)}" fill="#fff" stroke="{st["stroke"]}" stroke-width="0.8"/>')
        o.append(p.text(cx, cy, 'WH', 6, fill='#9a9387'))
    elif kind == 'tv':
        o.append(p.rect(x1, x2 + 0.15, y1, y2, fill='#555', stroke='none'))
    elif kind == 'rods':
        o.append(p.rect(x1, x2, y1, y2, **st))
        if (x2 - x1) > (y2 - y1):
            o.append(p.line(x1, (y1 + y2) / 2, x2, (y1 + y2) / 2, stroke=st['stroke'], stroke_width='0.6', stroke_dasharray='4,2'))
        else:
            o.append(p.line((x1 + x2) / 2, y1, (x1 + x2) / 2, y2, stroke=st['stroke'], stroke_width='0.6', stroke_dasharray='4,2'))
    elif kind in ('washer', 'dryer'):
        o.append(p.rect(x1, x2, y1, y2, **st))
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        o.append(f'<circle cx="{r1(p.X(cx))}" cy="{r1(p.Y(cy))}" r="{r1(0.8 * p.s)}" fill="none" stroke="{st["stroke"]}" stroke-width="0.6"/>')
        o.append(p.text(cx, cy, 'W' if kind == 'washer' else 'D', 6, fill='#9a9387'))
    elif kind == 'fridge':
        o.append(p.rect(x1, x2, y1, y2, **st))
        o.append(p.text((x1 + x2) / 2, (y1 + y2) / 2, 'REF', 6, fill='#9a9387'))
    else:
        o.append(p.rect(x1, x2, y1, y2, **st))
        if kind in ('linen', 'shelves', 'counter', 'bench'):
            pass
    return '\n'.join(o)


def door_svg(p, d):
    tg, n, c, wdt, h, kind, room, hinge, swing, note = d
    w = P.wall(n)
    t = P.THICK[w[5]]
    ax = P.along_x(w)
    k = w[2] if ax else w[1]
    lo, hi = c - wdt / 2, c + wdt / 2
    ink = '#7d776d'
    o = []
    # the opening, drawn as a white gap with jamb lines
    if ax:
        o.append(p.rect(lo, hi, k - t / 2, k + t / 2, fill='#fff'))
        o.append(p.line(lo, k - t / 2, lo, k + t / 2, stroke=ink, stroke_width='0.8'))
        o.append(p.line(hi, k - t / 2, hi, k + t / 2, stroke=ink, stroke_width='0.8'))
    else:
        o.append(p.rect(k - t / 2, k + t / 2, lo, hi, fill='#fff'))
        o.append(p.line(k - t / 2, lo, k + t / 2, lo, stroke=ink, stroke_width='0.8'))
        o.append(p.line(k - t / 2, hi, k + t / 2, hi, stroke=ink, stroke_width='0.8'))
    sgn = 1 if swing == '+' else -1
    face = k + sgn * t / 2

    def leaf(hpos, length, toward):
        # hinge at hpos along the wall; the leaf stands open perpendicular to the wall, and the arc sweeps to the far jamb
        far = hpos + toward * length
        if ax:
            hx, hy, ex, ey, fx, fy = hpos, face, hpos, face + sgn * length, far, face
        else:
            hx, hy, ex, ey, fx, fy = face, hpos, face + sgn * length, hpos, face, far
        sweep = 1 if ((toward > 0) == (sgn > 0)) != ax else 0
        o.append(p.line(hx, hy, ex, ey, stroke=ink, stroke_width='1.1'))
        o.append(f'<path d="M{p.pt(ex, ey)} A{r1(length * p.s)},{r1(length * p.s)} 0 0 {sweep} {p.pt(fx, fy)}" fill="none" stroke="{ink}" stroke-width="0.5" stroke-dasharray="2,1.5"/>')

    if kind == 'swing':
        leaf(lo if hinge == 'lo' else hi, wdt, 1 if hinge == 'lo' else -1)
    elif kind == 'pair':
        leaf(lo, wdt / 2, 1)
        leaf(hi, wdt / 2, -1)
    elif kind == 'bifold':
        q = wdt / 4
        for a, dirn in ((lo, 1), (hi, -1)):
            pts = [(a, 0), (a + dirn * q, 0.8), (a + dirn * 2 * q, 0)]
            if ax:
                o.append(p.path([(u, face + sgn * v) for u, v in pts], stroke=ink, stroke_width='0.9'))
            else:
                o.append(p.path([(face + sgn * v, u) for u, v in pts], stroke=ink, stroke_width='0.9'))
    elif kind == 'overhead':
        if ax:
            o.append(p.rect(lo, hi, face, face + sgn * 0.15, fill='none', stroke=ink, stroke_width='0.6', stroke_dasharray='5,3'))
    return '\n'.join(o)


def window_svg(p, wn):
    tg, n, c, wdt, h, sill, room, typ = wn
    w = P.wall(n)
    t = P.THICK[w[5]]
    ax = P.along_x(w)
    k = w[2] if ax else w[1]
    lo, hi = c - wdt / 2, c + wdt / 2
    ink = '#6f8fa8'
    o = []
    if ax:
        o.append(p.rect(lo, hi, k - t / 2, k + t / 2, fill='#fff', stroke='#7d776d', stroke_width='0.7'))
        o.append(p.line(lo, k, hi, k, stroke=ink, stroke_width='1.2'))
    else:
        o.append(p.rect(k - t / 2, k + t / 2, lo, hi, fill='#fff', stroke='#7d776d', stroke_width='0.7'))
        o.append(p.line(k, lo, k, hi, stroke=ink, stroke_width='1.2'))
    return '\n'.join(o)


def grid(p, step=5):
    o = []
    for x in range(0, int(P.W) + 1, step):
        o.append(p.line(x, -6.5, x, 50.5, stroke='#d9e0e8', stroke_width='0.5', stroke_dasharray='2,3'))
        o.append(p.text(x, -7.3, str(x), 7, fill='#6b86a3'))
    for y in range(0, int(P.D) + 1, step):
        o.append(p.line(-2.5, y, 62.5, y, stroke='#d9e0e8', stroke_width='0.5', stroke_dasharray='2,3'))
        o.append(p.text(-3.4, y, str(y), 7, fill='#6b86a3'))
    o.append(p.text(-1.0, -1.0, '0,0', 6, fill='#4f6b8a', font_weight='600', text_anchor='end'))
    return '\n'.join(o)


def compass(p, x, y):
    X, Y = p.X(x), p.Y(y)
    return (f'<g transform="translate({r1(X)},{r1(Y)})"><circle r="13" fill="#fff" stroke="#999" stroke-width="0.8"/>'
            f'<path d="M0,-11 L4,3 L0,0.5 L-4,3 Z" fill="#b4462f"/><text y="-15" font-size="9" font-weight="700" text-anchor="middle" fill="#444">N</text>'
            f'<text y="25" font-size="6" text-anchor="middle" fill="#888">assumed</text></g>')


def title_block(p, sheet, title, line1, line2, y):
    x0, w = 30, p.w - 60
    return (f'<g font-family="IBM Plex Sans, Segoe UI, Helvetica, Arial, sans-serif"><rect x="{x0}" y="{y}" width="{w}" height="60" fill="#fff" stroke="#444" stroke-width="1"/>'
            f'<line x1="{x0 + w * 0.42}" y1="{y}" x2="{x0 + w * 0.42}" y2="{y + 60}" stroke="#444"/><line x1="{x0 + w * 0.8}" y1="{y}" x2="{x0 + w * 0.8}" y2="{y + 60}" stroke="#444"/>'
            f'<text x="{x0 + 12}" y="{y + 20}" font-size="12" font-weight="700" fill="#222">Waring Build</text>'
            f'<text x="{x0 + 12}" y="{y + 38}" font-size="9" fill="#555">BuildWise plan 3933 · 3 bed, 2 bath · 1,800 sq ft + 528 sq ft garage · 58\'-0" x 40\'-0" framing</text>'
            f'<text x="{x0 + 12}" y="{y + 52}" font-size="9" fill="#555">Slab on grade · 9\' ceilings · 6:12 gable · grid 5\', 0,0 at the south-west corner</text>'
            f'<text x="{x0 + w * 0.42 + 12}" y="{y + 20}" font-size="13" font-weight="700" fill="#222">{esc(title)}</text>'
            f'<text x="{x0 + w * 0.42 + 12}" y="{y + 38}" font-size="9" fill="#555">{esc(line1)}</text>'
            f'<text x="{x0 + w * 0.42 + 12}" y="{y + 52}" font-size="9" fill="#555">{esc(line2)}</text>'
            f'<text x="{x0 + w * 0.8 + 12}" y="{y + 24}" font-size="22" font-weight="700" fill="#b4462f">{esc(sheet)}</text>'
            f'<text class="rev" x="{x0 + w * 0.8 + 12}" y="{y + 40}" font-size="9" fill="#555">rev</text>'
            f'<text x="{x0 + w * 0.8 + 12}" y="{y + 53}" font-size="9" fill="#555">drawn for K. Christianson</text></g>')


# ------------------------------------------------------------------ room dimensions, placed clear of fixtures and names
def room_dims(p, ink='#4f6b8a', fs=6.5):
    taken = [(f[1], f[2], f[3], f[4]) for f in P.FIXTURES]
    for t, x, y, sz in P.LABELS:
        w = len(t) * 0.55 * sz / p.s
        h = sz * 1.2 / p.s
        taken.append((x - w / 2, x + w / 2, y - h / 2, y + h / 2))
    out, placed = [], []
    seen = set()

    def overlap(r, lst):
        return sum(max(0, min(r[1], b[1]) - max(r[0], b[0])) * max(0, min(r[3], b[3]) - max(r[2], b[2])) for b in lst)

    def place(along, a, b, lo, hi):
        L = b - a
        txt = ft_in(L)
        tw = len(txt) * 0.6 * fs / p.s + 0.3
        th = fs * 1.2 / p.s
        best = None
        k = lo
        while k <= hi + 1e-6:
            m = a + L / 2
            for dm in (0, -L / 4, L / 4):
                mm = m + dm
                if mm - tw / 2 < a + 0.3 or mm + tw / 2 > b - 0.3:
                    continue
                r = (mm - tw / 2, mm + tw / 2, k - th / 2, k + th / 2) if along == 'x' else (k - th / 2, k + th / 2, mm - tw / 2, mm + tw / 2)
                cost = overlap(r, taken) * 1000 + overlap(r, placed) * 1000 + abs(dm) * 0.2 + abs(k - lo) * 0.05
                if best is None or cost < best[0]:
                    best = (cost, k, mm, r)
            k += 0.25
        if not best:
            return
        _, k, mm, r = best
        placed.append(r)
        if along == 'x':
            ax, ay, bx, by = a, k, b, k
        else:
            ax, ay, bx, by = k, a, k, b
        X1, Y1, X2, Y2 = p.X(ax), p.Y(ay), p.X(bx), p.Y(by)
        MX, MY = p.X(mm if along == 'x' else k), p.Y(k if along == 'x' else mm)
        L2 = math.hypot(X2 - X1, Y2 - Y1)
        ux, uy = (X2 - X1) / L2, (Y2 - Y1) / L2
        nx, ny = -uy, ux
        gap = len(txt) * 0.6 * fs / 2 + fs * 0.35
        kk = 3
        o = [f'<path d="M{r1(X1)},{r1(Y1)}L{r1(MX - ux * gap)},{r1(MY - uy * gap)}M{r1(MX + ux * gap)},{r1(MY + uy * gap)}L{r1(X2)},{r1(Y2)}" stroke="{ink}" stroke-width="0.6" fill="none"/>']
        ticks = ''.join(f'M{r1(x - (ux + nx) * kk * 0.7)},{r1(y - (uy + ny) * kk * 0.7)}L{r1(x + (ux + nx) * kk * 0.7)},{r1(y + (uy + ny) * kk * 0.7)}M{r1(x - nx * kk)},{r1(y - ny * kk)}L{r1(x + nx * kk)},{r1(y + ny * kk)}' for x, y in ((X1, Y1), (X2, Y2)))
        o.append(f'<path d="{ticks}" stroke="{ink}" stroke-width="0.9" fill="none"/>')
        rot = math.degrees(math.atan2(uy, ux))
        if rot <= -90 or rot > 90:
            rot += 180
        o.append(f'<text x="0" y="0" transform="translate({r1(MX)},{r1(MY)}) rotate({r1(rot)})" font-size="{fs}" font-weight="600" fill="{ink}" text-anchor="middle" dominant-baseline="middle">{esc(txt)}</text>')
        out.append(''.join(o))

    for r in P.ROOMS:
        name, x1, x2, y1, y2, col, opn = r
        cx1, cx2, cy1, cy2 = P.clear(r)
        key = (round(cx1, 2), round(cx2, 2), round(cy1, 2), round(cy2, 2))
        if key in seen or (cx2 - cx1) < 1.5 or (cy2 - cy1) < 1.5:
            continue
        seen.add(key)
        if name == 'Back Hall':
            continue
        if 'W' not in opn and 'E' not in opn:
            place('x', cx1, cx2, cy1 + 0.7, cy2 - 0.7)
        if 'N' not in opn and 'S' not in opn:
            place('y', cy1, cy2, cx1 + 0.7, cx2 - 0.7)
    return '<g class="roomdims" pointer-events="none">' + '\n'.join(out) + '</g>'


# ------------------------------------------------------------------ where a thing is, in words a framer can tape
WALL_NAME = {1: 'front ext. wall', 2: 'east ext. wall', 3: 'rear ext. wall', 4: 'west ext. wall', 23: 'front ext. wall', 25: 'front ext. wall', 26: 'rear ext. wall', 28: 'rear ext. wall'}


def wname(n):
    return WALL_NAME.get(n, f'W{n}')


def faces():
    """every wall face: (n, axis, coordinate, lo, hi, side) where side is the direction the face looks"""
    out = []
    for w in P.WALLS:
        n, x1, y1, x2, y2, typ, _ = w
        t = P.THICK[typ]
        if P.along_x(w):
            lo, hi = min(x1, x2), max(x1, x2)
            if n != 1:
                out.append((n, 'y', y1 - t / 2, lo, hi, 'S'))
            if n != 3:
                out.append((n, 'y', y1 + t / 2, lo, hi, 'N'))
        else:
            lo, hi = min(y1, y2), max(y1, y2)
            if n != 4:
                out.append((n, 'x', x1 - t / 2, lo, hi, 'W'))
            if n != 2:
                out.append((n, 'x', x1 + t / 2, lo, hi, 'E'))
    return out


FACES = faces()
SIDE_WORD = {'N': 'north', 'S': 'south', 'E': 'east', 'W': 'west'}


def nearest(axis, v, at, direction):
    """nearest wall face perpendicular to travel along `axis` from v, crossing the line at `at`, going -1 or +1"""
    best = None
    for n, ax, c, lo, hi, side in FACES:
        if ax != axis or not (lo - 0.2 <= at <= hi + 0.2):
            continue
        d = (c - v) * direction
        if d >= -0.02 and (best is None or d < best[0]):
            best = (d, n)
    return best


def locate(x, y, side):
    """'on W12 north face, 2'-3" from W11' for a wall device; 'x from .., y from ..' for a ceiling one"""
    if side in ('N', 'S', 'E', 'W'):
        axis = 'y' if side in 'NS' else 'x'
        v = y if axis == 'y' else x
        hit = None
        for n, ax, c, lo, hi, s in FACES:
            if ax == axis and s == side and abs(c - v) < 0.12 and lo - 0.2 <= (x if axis == 'y' else y) <= hi + 0.2:
                hit = n
                break
        if hit is None:   # an exterior face from outside
            for n, ax, c, lo, hi, s in FACES:
                pass
            return f'outside, {ft_in(x)} E, {ft_in(y)} N of the datum'
        along = 'x' if axis == 'y' else 'y'
        u = x if along == 'x' else y
        a = nearest(along, u, v + (0.2 if side in 'NE' else -0.2), -1)
        b = nearest(along, u, v + (0.2 if side in 'NE' else -0.2), 1)
        pick = min([q for q in (a, b) if q], default=None)
        where = f'on {wname(hit)}, {SIDE_WORD[side]} face' if hit > 4 else f'on the {wname(hit)}'
        if pick:
            where += f', {ft_in(pick[0])} from {wname(pick[1])}'
        return where
    parts = []
    for axis, u, at in (('x', x, y), ('y', y, x)):
        a = nearest(axis, u, at, -1)
        b = nearest(axis, u, at, 1)
        pick = min([q for q in (a, b) if q], default=None)
        if pick:
            parts.append(f'{ft_in(pick[0])} from {wname(pick[1])}')
    return ', '.join(parts) if parts else f'{ft_in(x)} E, {ft_in(y)} N of the datum'
