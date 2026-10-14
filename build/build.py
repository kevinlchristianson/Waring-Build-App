"""Builds index.html for the Waring Build contractor app.

    python3 build/build.py            # writes index.html next to build/
    python3 build/build.py --packets  # also prints each trade sheet to packets/*.pdf (needs Playwright + Chromium)

Edit the plan in plan.py, the trades in trades.py, then rebuild, bump VERSION below and in sw.js.
"""
import base64
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plan as P          # noqa: E402
import trades as T        # noqa: E402
import sheets as S        # noqa: E402
from draw import Paper, base_layers, room_dims, esc, ft_in, wall_rect, openings_on, locate  # noqa: E402

VERSION = 'v1'
DATE = '2026-10-14'
ROOT = os.path.dirname(HERE)
PARTS = os.path.join(HERE, 'parts')
read = lambda name: open(os.path.join(PARTS, name), encoding='utf-8').read()


def set_data():
    walls = []
    for w in P.WALLS:
        n, x1, y1, x2, y2, typ, note = w
        ops = []
        for d in P.DOORS:
            if d[1] == n:
                ops.append(dict(tag=d[0], kind=d[5], lo=d[2] - d[3] / 2, hi=d[2] + d[3] / 2, sill=0, head=d[4], hinge=d[7], swing=d[8], room=d[6]))
        for wn in P.WINDOWS:
            if wn[1] == n:
                ops.append(dict(tag=wn[0], kind='window', lo=wn[2] - wn[3] / 2, hi=wn[2] + wn[3] / 2, sill=wn[5], head=wn[5] + wn[4], room=wn[6]))
        ax = P.along_x(w)
        walls.append(dict(n=n, x1=x1, y1=y1, x2=x2, y2=y2, alongX=ax, type=typ, t=P.THICK[typ], rect=wall_rect(w), ops=ops,
                          text=f'Wall {n}: {ft_in(S.wall_len(w))}, {S.wall_runs(w)}. {S.WALL_TYPE[typ]}. {note[0].upper() + note[1:]}'))
    rooms = [dict(name=r[0], rect=P.clear(r), color=r[5]) for r in P.ROOMS]
    fixtures = [dict(kind=f[0], x1=f[1], x2=f[2], y1=f[3], y2=f[4], front=f[5], label=f[6], note=f[7]) for f in P.FIXTURES]
    devices = []
    for d in T.DEVICES:
        devices.append(dict(id=d['id'], type=d['type'], x=d['x'], y=d['y'], side=d['side'], h=d['h'], ckt=d['ckt'], text=S.dev_title(d)))
    plumbing = dict(fixtures=T.PFIX, drains=T.DRAINS, vents=T.VENTS, vtr=T.VTR, aav=T.AAV, trunks=T.TRUNKS, branches=T.BRANCHES,
                    manifold=T.MANIFOLD, service=T.SERVICE, cleanouts=T.CLEANOUTS)
    hvac = dict(ah=T.AH, sp=T.SUPPLY_PLENUM, rp=T.RETURN_PLENUM, trunks=T.DTRUNKS, registers=T.REGISTERS, returns=T.RETURNS, jumps=T.JUMPS,
                tstats=T.TSTATS, exhaust=T.EXHAUST, hp=T.HP, lineset=T.LINESET, condensate=T.CONDENSATE)
    return dict(date=DATE, W=P.W, D=P.D, ceil=P.CEIL, pitch=P.PITCH, overhang=P.OVERHANG, tExt=P.T_EXT, tInt=P.T_INT,
                walls=walls, rooms=rooms, fixtures=fixtures, outdoor=P.OUTDOOR, devices=devices, plumbing=plumbing, hvac=hvac,
                base=dict(s=20))


def base_svg():
    p = Paper(20, 0, P.W, 0, P.D, 0, 0)
    body = base_layers(p, outdoor=False, dims=room_dims(p, fs=8.5))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{p.w:.0f}" height="{p.h:.0f}" viewBox="0 0 {p.w:.0f} {p.h:.0f}" font-family="IBM Plex Sans, Segoe UI, Helvetica, Arial, sans-serif" role="img" aria-label="A-1 Base plan">'
           f'<rect width="100%" height="100%" fill="#fff"/>{body}</svg>')
    return base64.b64encode(svg.encode()).decode()


def sheet(key, no, label, packet, name, svg, below, extra=''):
    return (f'    <!-- ================================================================ {no} -->\n'
            f'    <div class="sheet sheet2d" id="sheet-{key}" role="tabpanel" aria-labelledby="tab-{key}" hidden>\n'
            f'      {S.tools(key, packet, name)}\n'
            + (f'      {extra}\n' if extra else '') +
            f'      <div class="drawing"><div class="scroller"><div class="paper">{svg}\n</div></div></div>\n'
            f'      {below}\n'
            '    </div>\n')


PRINT_CSS = """<style>
@page { size: letter landscape; margin: 0.4in; }
body { margin: 0; font-family: 'IBM Plex Sans', 'Segoe UI', Helvetica, Arial, sans-serif; color: #1e1b16; font-size: 9pt; }
.cover { height: 7.6in; display: flex; align-items: center; justify-content: center; page-break-after: always; }
.cover svg { max-width: 100%; max-height: 100%; width: auto; height: auto; }
h2 { font-size: 13pt; margin: 0 0 4pt; } h3 { font-size: 10.5pt; margin: 10pt 0 3pt; page-break-after: avoid; }
p.lede { margin: 0 0 6pt; color: #5b554b; }
table { border-collapse: collapse; width: 100%; margin-bottom: 8pt; } tr { page-break-inside: avoid; }
th, td { border: 0.5pt solid #c9c2b4; padding: 2pt 4pt; text-align: left; vertical-align: top; font-size: 8pt; }
th { background: #ebe7df; } section { margin-bottom: 10pt; }
ul.legend { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: 4pt 14pt; }
ul.legend .sw { display: inline-block; width: 10pt; height: 10pt; margin-right: 4pt; vertical-align: -1pt; border-radius: 2pt; }
button, .tools, nav { display: none !important; }
</style>"""

PRINT_JS = """const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  for (const [src, out] of JSON.parse(process.argv[2])) {
    const p = await b.newPage();
    await p.goto('file://' + src);
    await p.pdf({ path: out, format: 'Letter', landscape: true, printBackground: true });
    await p.close();
  }
  await b.close();
})();
"""


def packets(sheets):
    """Prints each trade sheet to packets/*.pdf: the drawing on page 1, then its tables and notes."""
    os.makedirs(os.path.join(ROOT, 'packets'), exist_ok=True)
    tmp = tempfile.mkdtemp()
    jobs = []
    for no, name, fname, svg, below in sheets:
        title = f'{no} {name} contractor packet — Waring Build'
        html = (f'<!doctype html><html><head><meta charset="utf-8"><title>{esc(title)}</title>{PRINT_CSS}</head><body>'
                f'<div class="cover">{svg}</div>{below}</body></html>')
        src = os.path.join(tmp, fname.replace('.pdf', '.html'))
        open(src, 'w', encoding='utf-8').write(html)
        jobs.append([src, os.path.join(ROOT, 'packets', fname)])
    js = os.path.join(tmp, 'print.js')
    open(js, 'w').write(PRINT_JS)
    env = dict(os.environ)
    env.setdefault('NODE_PATH', subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip())
    subprocess.run(['node', js, json.dumps(jobs)], check=True, env=env)
    for _, out in jobs:
        print(f'{os.path.relpath(out, ROOT)}: {os.path.getsize(out) // 1024} KB')


def main():
    s1_svg, s1_below = S.s1()
    e1_svg, e1_sub, e1_below = S.e1()
    p1_svg, p1_below = S.p1()
    m1_svg, m1_below = S.m1()
    counts = f'{len(P.WALLS)} walls · {len([d for d in P.DOORS if d[5] != "cased"])} doors · {len(P.WINDOWS)} windows · {len(T.DEVICES)} electrical devices · {len(T.PFIX)} plumbing fixtures · {len(T.REGISTERS)} registers'
    head = read('head.html').replace('{{VERSION}}', VERSION).replace('{{STYLE}}', read('style.css'))
    side = read('side3d.html')
    body = [head,
            '<div id="app">',
            '  <header class="bar">',
            f'    <div class="brand"><span class="eyebrow">Waring Build · single story</span><h1>Contractor App <span class="ver" id="appver" title="App version">{VERSION}</span></h1></div>',
            '    <nav class="tabs" role="tablist" aria-label="Sheets">',
            '      <button type="button" role="tab" id="tab-3d" aria-selected="true" aria-controls="sheet-3d" data-sheet="3d"><span class="no">3D</span>Model</button>',
            '      <button type="button" role="tab" id="tab-s1" aria-selected="false" aria-controls="sheet-s1" data-sheet="s1"><span class="no">S-1</span>Framing</button>',
            '      <button type="button" role="tab" id="tab-e1" aria-selected="false" aria-controls="sheet-e1" data-sheet="e1"><span class="no">E-1</span>Electrical</button>',
            '      <button type="button" role="tab" id="tab-p1" aria-selected="false" aria-controls="sheet-p1" data-sheet="p1"><span class="no">P-1</span>Plumbing</button>',
            '      <button type="button" role="tab" id="tab-m1" aria-selected="false" aria-controls="sheet-m1" data-sheet="m1"><span class="no">M-1</span>HVAC</button>',
            '      <button type="button" role="tab" id="tab-chat" aria-selected="false" aria-controls="sheet-chat" data-sheet="chat"><span class="no">✉</span>Chat</button>',
            '    </nav>',
            f'    <span class="counts">{counts}</span>',
            '  </header>',
            '  <main>',
            side,
            sheet('s1', 'S-1', 'Framing', 'S-1-framing-packet.pdf', 'Framing', s1_svg, s1_below),
            sheet('e1', 'E-1', 'Electrical', 'E-1-electrical-packet.pdf', 'Electrical', e1_svg, e1_below, e1_sub),
            sheet('p1', 'P-1', 'Plumbing', 'P-1-plumbing-packet.pdf', 'Plumbing', p1_svg, p1_below),
            sheet('m1', 'M-1', 'HVAC', 'M-1-hvac-packet.pdf', 'HVAC', m1_svg, m1_below),
            '    <!-- ================================================================ crew chat -->',
            '    <div class="sheet" id="sheet-chat" role="tabpanel" aria-labelledby="tab-chat" hidden>',
            '      <div class="chat-wrap" id="chat"></div>',
            '    </div>',
            '  </main>',
            '</div>',
            '',
            '<!-- Embedded data for the 3D view. "set-data" is the model: walls, openings, rooms, fixtures and every',
            '     device on the trade sheets. "base-svg" is the A-1 base plan drawing, base64-encoded, which the 3D view',
            '     lays on the floor as its texture. Both are written by build/build.py from build/plan.py and build/trades.py. -->',
            '<script type="application/json" id="set-data">' + json.dumps(set_data(), separators=(',', ':')) + '</script>',
            '<script type="text/plain" id="base-svg">' + base_svg() + '</script>',
            read('sheets.js'),
            read('panes.js'),
            '<script type="importmap">\n{ "imports": { "three": "./vendor/three/build/three.module.min.js", "three/addons/": "./vendor/three/examples/jsm/" } }\n</script>',
            '<script type="module">\n' + read('model3d.js') + '\n</script>',
            '',
            read('chat.js'),
            '</body>\n</html>\n']
    out = '\n'.join(body)
    with open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(out)
    print(f'index.html: {len(out) // 1024} KB · {counts}')
    if '--packets' in sys.argv:
        packets([('S-1', 'Framing', 'S-1-framing-packet.pdf', s1_svg, s1_below),
                 ('E-1', 'Electrical', 'E-1-electrical-packet.pdf', e1_svg, e1_below),
                 ('P-1', 'Plumbing', 'P-1-plumbing-packet.pdf', p1_svg, p1_below),
                 ('M-1', 'HVAC', 'M-1-hvac-packet.pdf', m1_svg, m1_below)])


if __name__ == '__main__':
    main()
