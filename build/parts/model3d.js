import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const SET = JSON.parse(document.getElementById('set-data').textContent);
const { walls, rooms, fixtures, devices, plumbing, hvac } = SET;
const $ = id => document.getElementById(id);
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const cssVar = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const ftIn = v => { let f = Math.floor(v + 1e-9), i = Math.round((v - f) * 12); if (i === 12) { f += 1; i = 0; } return `${f}'-${i}"`; };
const status = t => { const el = $('status'); el.textContent = t; el.hidden = !t; };
const W = SET.W, D = SET.D, CEIL = SET.ceil, PLATE = CEIL + 1.125 / 12, TEXT = SET.tExt;
// plan feet (x east from the west framing face, y north from the front framing face) -> model feet (x east, z south, y up)
const M = (px, py) => ({ x: px - W / 2, z: D / 2 - py });

// ---------------------------------------------------------------- renderer
const stage = $('stage');
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.localClippingEnabled = true;
stage.prepend(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(35, 1, 0.5, 2000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = !reduceMotion; controls.dampingFactor = 0.08; controls.maxPolarAngle = Math.PI / 2 + 0.35; controls.minDistance = 4; controls.maxDistance = 400;
// Orbit / Pan toggle: what a left-button or one-finger drag does. Right-drag and shift+drag pan in Orbit mode; two fingers always pan and pinch.
function setDragMode(mode) {
  const pan = mode === 'pan';
  controls.mouseButtons = { LEFT: pan ? THREE.MOUSE.PAN : THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: pan ? THREE.MOUSE.ROTATE : THREE.MOUSE.PAN };
  controls.touches = { ONE: pan ? THREE.TOUCH.PAN : THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
  for (const b of $('dragmode').querySelectorAll('button')) b.setAttribute('aria-pressed', String(b.dataset.mode === mode));
}
$('dragmode').addEventListener('click', e => { const b = e.target.closest('button[data-mode]'); if (b) setDragMode(b.dataset.mode); });
setDragMode('orbit');
scene.add(new THREE.HemisphereLight(0xf3f6ff, 0x8a7c62, 1.0));
const sun = new THREE.DirectionalLight(0xfff1da, 2.0); sun.position.set(-60, 120, 90); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -60, right: 60, top: 60, bottom: -60, near: 10, far: 400 }); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.05; scene.add(sun);
function applySky() { const sky = new THREE.Color(cssVar('--sky') || '#dfe5e9'); scene.background = sky; scene.fog = new THREE.Fog(sky, 300, 700); }
applySky(); matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applySky);
new MutationObserver(applySky).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
function resize() { const w = stage.clientWidth, h = stage.clientHeight; if (!w || !h) return; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
new ResizeObserver(resize).observe(stage); addEventListener('resize', resize); resize();

// ---------------------------------------------------------------- materials and the section cut
const cutPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 9.5);
const cutMats = [];
const mat = (c, o = {}) => { const m = new THREE.MeshStandardMaterial({ color: c, roughness: 0.9, metalness: 0, side: THREE.DoubleSide, clipShadows: true, ...o }); cutMats.push(m); return m; };
const MAT = {
  wall: mat(0xf1ede5), wallGhost: mat(0xf1ede5, { transparent: true, opacity: 0.12, depthWrite: false }), siding: mat(0xe9e7e2), sidingGhost: mat(0xe9e7e2, { transparent: true, opacity: 0.12, depthWrite: false }),
  trim: mat(0x2e2f31), garageDoor: mat(0xf4f3f0, { roughness: 0.6 }), frontDoor: mat(0x222326, { roughness: 0.5 }),
  wood: mat(0xc9a46a, { roughness: 0.8 }), woodExt: mat(0xb8915a, { roughness: 0.8 }), header: mat(0xa9824a), lvl: mat(0xd2a35a, { roughness: 0.7 }),
  glass: mat(0xa9cddd, { transparent: true, opacity: 0.3, roughness: 0.1, depthWrite: false }),
  slab: mat(0xcfcac2), conc: mat(0xd9d5ce), grass: mat(0x9fb08a, { roughness: 1 }), post: mat(0x8a6a44, { roughness: 0.8 }), roof: mat(0x4a4d52, { roughness: 0.85 }), roofGhost: mat(0x4a4d52, { transparent: true, opacity: 0.35, depthWrite: false }),
  rec: mat(0xc8650a), sw: mat(0x8a5a00), light: mat(0xfff2c4, { emissive: 0xd9a400, emissiveIntensity: 0.35 }), alarm: mat(0xb4462f), panel: mat(0x333333), tall: mat(0xd6d1c8), data: mat(0x2c6aa0),
  drain: mat(0x3c3a36, { roughness: 0.5 }), vent: mat(0x4c8c4a, { roughness: 0.5 }), cold: mat(0x2c6aa0, { roughness: 0.4 }), hot: mat(0xc8382b, { roughness: 0.4 }),
  sup: mat(0xe3a05a, { roughness: 0.6 }), ret: mat(0x7fa6c9, { roughness: 0.6 }), duct: mat(0xb0b0b0, { roughness: 0.5 }), unit: mat(0xe6e6e3, { roughness: 0.5 }), lineset: mat(0x7a4fa0), cond: mat(0x2a9d8f), gas: mat(0xd9b100, { roughness: 0.4 }), flue: mat(0xf2f2ee, { roughness: 0.5 }),
  hi: mat(0xe08a00, { emissive: 0x4a2a00 }),
};
function setCut(h) { const on = h < 9.5; cutPlane.constant = h; for (const m of cutMats) { m.clippingPlanes = on ? [cutPlane] : null; m.needsUpdate = true; } }

// ---------------------------------------------------------------- groups
const G = {}; for (const k of ['floor', 'shell', 'walls', 'framing', 'elec', 'plumb', 'furn', 'hvac', 'truss', 'roof']) { G[k] = new THREE.Group(); scene.add(G[k]); }
const pickables = [];
function box(x1, x2, y1, y2, bottom, top, material, data, group) {
  // a box over plan rectangle [x1,x2] × [y1,y2] from height bottom to top (feet)
  const a = M(Math.min(x1, x2), Math.min(y1, y2)), b = M(Math.max(x1, x2), Math.max(y1, y2));
  const w = Math.abs(b.x - a.x), d = Math.abs(b.z - a.z), h = top - bottom;
  if (w < 1e-4 || d < 1e-4 || h < 1e-4) return null;
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
  m.position.set((a.x + b.x) / 2, bottom + h / 2, (a.z + b.z) / 2);
  m.castShadow = true; m.receiveShadow = true;
  if (data) { m.userData = data; pickables.push(m); }
  group.add(m); return m;
}
function tube(p1, p2, r, material, data, group) {
  // a cylinder from plan point p1 {x,y,h} to p2 (feet)
  const a = M(p1.x, p1.y), b = M(p2.x, p2.y);
  const va = new THREE.Vector3(a.x, p1.h, a.z), vb = new THREE.Vector3(b.x, p2.h, b.z);
  const len = va.distanceTo(vb); if (len < 1e-4) return null;
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, 10), material);
  m.position.copy(va).add(vb).multiplyScalar(0.5);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), vb.clone().sub(va).normalize());
  m.castShadow = true;
  if (data) { m.userData = data; pickables.push(m); }
  group.add(m); return m;
}
function polyline(pts, h, r, material, data, group) { for (let i = 1; i < pts.length; i++) tube({ x: pts[i - 1][0], y: pts[i - 1][1], h }, { x: pts[i][0], y: pts[i][1], h }, r, material, data, group); }
function mergeBoxes(parts) {
  // parts: [w, h, d, x, y, z, rotX]; one geometry per truss keeps the mesh count down on phones
  const pos = [], nor = [];
  for (const [w, h, d, x, y, z, rx] of parts) {
    const g = new THREE.BoxGeometry(w, h, d); if (rx) g.rotateX(rx); g.translate(x, y, z);
    const ng = g.toNonIndexed(); pos.push(...ng.attributes.position.array); nor.push(...ng.attributes.normal.array); g.dispose(); ng.dispose();
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); out.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  return out;
}
const roomAt = (x, y) => { const r = rooms.filter(r => x > r.rect[0] - 0.05 && x < r.rect[1] + 0.05 && y > r.rect[2] - 0.05 && y < r.rect[3] + 0.05).sort((p, q) => (p.rect[1] - p.rect[0]) * (p.rect[3] - p.rect[2]) - (q.rect[1] - q.rect[0]) * (q.rect[3] - q.rect[2]))[0]; return r ? r.name : ''; };

// ---------------------------------------------------------------- ground, slabs and the plan drawing on the slab
function buildFloor() {
  const g = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), MAT.grass); g.rotation.x = -Math.PI / 2; g.position.y = -0.36; g.receiveShadow = true; G.floor.add(g);
  const fp = new THREE.Shape(SET.footprint.map(([x, y]) => new THREE.Vector2(x - W / 2, y - D / 2)));
  const sg = new THREE.ExtrudeGeometry(fp, { depth: 0.34, bevelEnabled: false }); sg.rotateX(-Math.PI / 2);
  const slab = new THREE.Mesh(sg, MAT.slab); slab.position.y = -0.34; slab.receiveShadow = true; slab.userData = { kind: 'slab', text: 'Slab on grade: 4" concrete on 10-mil vapour retarder, R-10 perimeter insulation, thickened edges; the garage slab steps down 4" and slopes 1/8"/ft to the door' }; pickables.push(slab); G.floor.add(slab);
  for (const [name, x1, x2, y1, y2, note] of SET.outdoor) box(x1, x2, y1, y2, -0.34, -0.06, MAT.conc, { kind: 'slab', text: `${name}: ${note}` }, G.floor);
  box(58.4, 61.6, 19.4, 22.6, -0.34, 0.1, MAT.conc, { kind: 'slab', text: 'AC-1 pad: concrete or composite, level, 3" above grade' }, G.floor);
  const b64 = document.getElementById('base-svg').textContent.trim();
  const img = new Image();
  const plateMat = new THREE.MeshLambertMaterial({ color: 0xffffff, side: THREE.DoubleSide, transparent: true, alphaTest: 0.05, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 });
  img.onload = () => {
    const s = SET.base.s, K = Math.max(1, Math.min(3, Math.floor(renderer.capabilities.maxTextureSize / (W * s))));
    const cv = document.createElement('canvas'); cv.width = Math.round(W * s * K); cv.height = Math.round(D * s * K);
    const ctx = cv.getContext('2d'); ctx.drawImage(img, 0, 0, cv.width, cv.height);
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
    plateMat.map = tex; plateMat.needsUpdate = true;
  };
  img.src = 'data:image/svg+xml;base64,' + b64;
  const pl = new THREE.Mesh(new THREE.PlaneGeometry(W, D), plateMat); pl.rotation.x = -Math.PI / 2; pl.position.y = 0.02; pl.receiveShadow = true; G.floor.add(pl);
}

// ---------------------------------------------------------------- walls: finished, and framed
const STUD = 1.5 / 12, PL = 1.5 / 12, OC = 16 / 12;
function wallBoxes(w, ghost) {
  const data = { kind: 'wall', text: w.text };
  const [rx1, rx2, ry1, ry2] = w.rect, ext = w.type === 'E';
  const k1 = w.alongX ? ry1 : rx1, k2 = w.alongX ? ry2 : rx2;
  const lo = w.alongX ? rx1 : ry1, hi = w.alongX ? rx2 : ry2;
  // exterior walls carry the siding and sheathing outside the framing: 1" more on the outside face
  const out = ext ? 1 / 12 : 0, so = w.out < 0 ? [-1, 0] : w.out > 0 ? [0, 1] : [0, 0];
  const a1 = k1 + so[0] * out, a2 = k2 + so[1] * out;
  const place = (u1, u2, b, t, m, d = data) => w.alongX ? box(u1, u2, a1, a2, b, t, m, d, ext ? G.shell : G.walls) : box(a1, a2, u1, u2, b, t, m, d, ext ? G.shell : G.walls);
  const ops = w.ops.slice().sort((p, q) => p.lo - q.lo);
  let cur = lo - (ext ? out : 0); const end = hi + (ext ? out : 0);
  const top = ext ? PLATE : CEIL;
  for (const o of ops) {
    if (o.lo > cur) place(cur, o.lo, 0, top, ghost);
    if (o.sill > 0) place(o.lo, o.hi, 0, o.sill, ghost);
    place(o.lo, o.hi, o.head, top, ghost);
    const odata = { kind: 'opening', text: o.kind === 'window' ? `Window ${o.tag}: ${o.room}, ${ftIn(o.hi - o.lo)} x ${ftIn(o.head - o.sill)}, sill ${ftIn(o.sill)}` : `${o.kind === 'cased' ? 'Opening' : 'Door'} ${o.tag}: ${o.room}, ${ftIn(o.hi - o.lo)} x ${ftIn(o.head)}` };
    if (o.kind === 'window') {
      const g = place(o.lo, o.hi, o.sill, o.head, MAT.glass, odata); if (g) g.castShadow = false;
      // black frame, as the elevations
      for (const [u1, u2, b, t] of [[o.lo, o.hi, o.sill, o.sill + 0.12], [o.lo, o.hi, o.head - 0.12, o.head], [o.lo, o.lo + 0.12, o.sill, o.head], [o.hi - 0.12, o.hi, o.sill, o.head], [(o.lo + o.hi) / 2 - 0.04, (o.lo + o.hi) / 2 + 0.04, o.sill, o.head]]) {
        const c = w.alongX ? box(u1, u2, (a1 + a2) / 2 - 0.08, (a1 + a2) / 2 + 0.08, b, t, MAT.trim, odata, G.shell) : box((a1 + a2) / 2 - 0.08, (a1 + a2) / 2 + 0.08, u1, u2, b, t, MAT.trim, odata, G.shell);
      }
    } else if (ext && o.kind === 'overhead') {
      place(o.lo, o.hi, 0, o.head, MAT.garageDoor, { kind: 'opening', text: `Door ${o.tag}: 16'-0" x 8'-0" insulated overhead garage door, with opener` });
      for (let z = 2; z < o.head; z += 2) w.alongX && box(o.lo, o.hi, a1 - 0.03, a1, z - 0.03, z + 0.03, MAT.tall, null, G.shell);
    } else if (ext && o.tag === 'D1') {
      place(o.lo, o.hi, 0, o.head, MAT.frontDoor, odata);
    } else if (ext) {
      const g = place(o.lo, o.hi, 0, o.head, o.kind === 'pair' ? MAT.glass : MAT.frontDoor, odata); if (g && o.kind === 'pair') g.castShadow = false;
    }
    cur = o.hi;
  }
  if (end > cur) place(cur, end, 0, top, ghost);
}
function frameWall(w) {
  const data = { kind: 'framing', text: 'Framing, ' + w.text.replace(/^Wall (\d+):/, 'wall $1:') };
  const [rx1, rx2, ry1, ry2] = w.rect, k = w.alongX ? (ry1 + ry2) / 2 : (rx1 + rx2) / 2, d = w.t;
  const lo = w.alongX ? rx1 : ry1, hi = w.alongX ? rx2 : ry2, m = w.type === 'E' ? MAT.woodExt : MAT.wood;
  const place = (a, b, bottom, top, mm = m) => w.alongX ? box(a, b, k - d / 2, k + d / 2, bottom, top, mm, data, G.framing) : box(k - d / 2, k + d / 2, a, b, bottom, top, mm, data, G.framing);
  const TOP = PLATE;
  place(lo, hi, 0, PL); place(lo, hi, TOP - 2 * PL, TOP);
  const ops = w.ops.slice().sort((p, q) => p.lo - q.lo).map(o => ({ ...o, ro: o.kind === 'window' ? o.head : o.head + (o.kind === 'overhead' ? 0 : 0.2) }));
  const blocked = p => ops.some(o => p > o.lo - STUD && p < o.hi + STUD);
  for (let p = lo + STUD / 2; p < hi - STUD / 2; p += OC) if (!blocked(p)) place(p - STUD / 2, p + STUD / 2, PL, TOP - 2 * PL);
  place(hi - STUD, hi, PL, TOP - 2 * PL);
  for (const o of ops) {
    const a = o.lo, b = o.hi, hd = w.type === 'E' && w.alongX ? (b - a > 10 ? 14 / 12 : b - a > 3.6 ? 11.25 / 12 : 7.25 / 12) : w.type === 'E' ? 5.5 / 12 : 3.5 / 12;
    place(a - 2 * STUD, a - STUD, PL, TOP - 2 * PL); place(b + STUD, b + 2 * STUD, PL, TOP - 2 * PL);      // kings
    place(a - STUD, a, PL, o.ro); place(b, b + STUD, PL, o.ro);                                            // jacks
    place(a - STUD, b + STUD, o.ro, o.ro + hd, b - a > 10 ? MAT.lvl : MAT.header);                         // header
    if (o.sill > 0) { place(a, b, o.sill - PL, o.sill); for (let p = a + OC / 2; p < b; p += OC) place(p - STUD / 2, p + STUD / 2, PL, o.sill - PL); }
    for (let p = a + OC / 2; p < b; p += OC) if (o.ro + hd < TOP - 2 * PL - 0.05) place(p - STUD / 2, p + STUD / 2, o.ro + hd, TOP - 2 * PL);   // cripples
  }
}

// ---------------------------------------------------------------- furniture and fixtures, as low-poly models
// Each piece is built from boxes and cylinders in plan feet, then merged into one vertex-coloured mesh,
// so a piece costs one draw call and highlights as a whole when picked.
const FURN = mat(0xffffff, { vertexColors: true, roughness: 0.85 });
const FC = {
  wood: 0xa98257, woodDark: 0x6f5440, oak: 0xc9a77c, fabric: 0x8e9b8a, cushion: 0xa3ae9e, linen: 0xf3efe7, duvet: 0xdcd6ca, pillow: 0xfbfaf6,
  cab: 0xe6dfd2, stone: 0x8c8781, steel: 0xc3c7ca, dark: 0x2e2f31, chrome: 0xb7bcc1, porcelain: 0xf8f7f4, basin: 0xd9dde0, tile: 0xe4e1db,
  mirror: 0xbfd0d8, black: 0x3a3a3a, toe: 0x55504a, carA: 0xb8bcc2, carB: 0x24262b, tyre: 0x1b1b1b, glass: 0x6d8796,
};
const GARMENTS = [0x46566e, 0xb8a990, 0x7d4b3a, 0xe8e4dc, 0x5f6f52, 0x2f3a4a, 0x9c8f7a, 0x8a3f3f, 0xcfc6b4, 0x40464d];
function Piece() {
  const parts = [];
  const add = (g, c, px, py, z) => { const p = M(px, py); g.translate(p.x, z, p.z); parts.push([g, c]); };
  return {
    box(x1, x2, y1, y2, z1, z2, c) {
      const w = Math.abs(x2 - x1), d = Math.abs(y2 - y1), h = z2 - z1;
      if (w < 1e-4 || d < 1e-4 || h < 1e-4) return;
      add(new THREE.BoxGeometry(w, h, d), c, (x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2);
    },
    // a vertical cylinder at plan point (px, py); sx, sy stretch it along plan x and y
    cyl(px, py, z1, z2, r, c, seg = 14, sx = 1, sy = 1) {
      const g = new THREE.CylinderGeometry(r, r, z2 - z1, seg); g.scale(sx, 1, sy); add(g, c, px, py, (z1 + z2) / 2);
    },
    // a disc standing on a wall facing plan axis 'x' or 'y' (a washer door), centred at (px, py, z)
    disc(px, py, z, r, t, axis, c, seg = 18) {
      const g = new THREE.CylinderGeometry(r, r, t, seg); axis === 'y' ? g.rotateX(Math.PI / 2) : g.rotateZ(Math.PI / 2); add(g, c, px, py, z);
    },
    done(data) {
      if (!parts.length) return null;
      let n = 0; const gs = parts.map(([g, c]) => { const ng = g.index ? g.toNonIndexed() : g; n += ng.attributes.position.count; return [ng, c]; });
      const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), col = new Float32Array(n * 3), k = new THREE.Color(); let o = 0;
      for (const [g, c] of gs) {
        const cnt = g.attributes.position.count; pos.set(g.attributes.position.array, o * 3); nor.set(g.attributes.normal.array, o * 3); k.set(c);
        for (let i = 0; i < cnt; i++) { col[(o + i) * 3] = k.r; col[(o + i) * 3 + 1] = k.g; col[(o + i) * 3 + 2] = k.b; }
        o += cnt; g.dispose();
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
      geo.computeBoundingSphere();
      const m = new THREE.Mesh(geo, FURN); m.castShadow = true; m.receiveShadow = true; m.userData = data; pickables.push(m); G.furn.add(m);
      return m;
    },
  };
}
// A frame over a plan rectangle with its front facing N, S, E or W. u runs along the front (0..L),
// v from the back (0) to the front (D). r() gives the plan rectangle of a u-v rectangle, p() a plan point.
function frameOf(x1, x2, y1, y2, front) {
  const ns = front === 'N' || front === 'S';
  const L = ns ? x2 - x1 : y2 - y1, Dp = ns ? y2 - y1 : x2 - x1;
  const r = (u1, u2, v1, v2) => front === 'N' ? [x1 + u1, x1 + u2, y1 + v1, y1 + v2] : front === 'S' ? [x1 + u1, x1 + u2, y2 - v2, y2 - v1]
    : front === 'E' ? [x1 + v1, x1 + v2, y1 + u1, y1 + u2] : [x2 - v2, x2 - v1, y1 + u1, y1 + u2];
  const p = (u, v) => { const q = r(u, u, v, v); return [q[0], q[2]]; };
  return { L, D: Dp, r, p, faceAxis: ns ? 'y' : 'x' };
}
const legs = (P, F, z, s, inset, c) => { for (const [u, v] of [[inset, inset], [F.L - inset - s, inset], [inset, F.D - inset - s], [F.L - inset - s, F.D - inset - s]]) P.box(...F.r(u, u + s, v, v + s), 0, z, c); };
const handle = (P, F, u, z, len = 0.5) => P.box(...F.r(u - len / 2, u + len / 2, F.D, F.D + 0.06), z - 0.03, z + 0.03, FC.chrome);
const chair = (P, cx, cy, facing) => {   // a dining chair at plan point (cx, cy), its seat facing `facing`
  const s = 0.75, F = frameOf(cx - s, cx + s, cy - s, cy + s, facing);
  legs(P, F, 1.5, 0.12, 0.08, FC.woodDark);
  P.box(...F.r(0.05, F.L - 0.05, 0.05, F.D - 0.05), 1.5, 1.6, FC.oak);
  P.box(...F.r(0.1, F.L - 0.1, 0.05, 0.17), 1.6, 3.05, FC.oak);
};
function baseRun(P, F, u1, u2, top = 3.0, depth = F.D) {
  P.box(...F.r(u1, u2, 0, depth - 0.3), 0, 0.33, FC.toe);
  P.box(...F.r(u1, u2, 0, depth - 0.05), 0.33, top - 0.13, FC.cab);
  P.box(...F.r(u1, u2, 0, depth + 0.06), top - 0.13, top, FC.stone);
  for (let u = u1 + 0.75; u < u2 - 0.3; u += 1.5) handle(P, F, u, top - 0.45, 0.4);
}
function uppers(P, F, u1, u2) { P.box(...F.r(u1, u2, 0, 1.1), 4.5, 7.6, FC.cab); for (let u = u1 + 0.75; u < u2 - 0.3; u += 1.5) P.box(...F.r(u - 0.03, u + 0.03, 1.1, 1.16), 4.6, 5.1, FC.chrome); }

function buildFurniture() {
  fixtures.forEach((f, i) => {
    const { kind, x1, x2, y1, y2, front, label, note } = f;
    const w = x2 - x1, d = y2 - y1, cx = (x1 + x2) / 2, cy = (y1 + y2) / 2, R = roomAt(cx, cy) || (cy < 0 ? 'Front Porch' : '');
    const F = frameOf(x1, x2, y1, y2, front), P = Piece();
    let name = label.toLowerCase();
    if (kind === 'bed') {
      P.box(...F.r(0, F.L, 0, 0.18), 0, 3.6, FC.woodDark);                       // headboard
      P.box(...F.r(0.05, F.L - 0.05, 0.18, F.D), 0.25, 0.95, FC.wood);           // platform
      P.box(...F.r(0.12, F.L - 0.12, 0.2, F.D - 0.06), 0.95, 1.8, FC.linen);     // mattress
      P.box(...F.r(0.06, F.L - 0.06, F.D * 0.38, F.D), 1.25, 1.88, FC.duvet);
      P.box(...F.r(0.06, F.L - 0.06, F.D * 0.38, F.D * 0.46), 1.88, 1.93, FC.linen);
      for (const [a, b] of [[0.3, F.L / 2 - 0.15], [F.L / 2 + 0.15, F.L - 0.3]]) P.box(...F.r(a, b, 0.3, 1.2), 1.8, 2.2, FC.pillow);
    } else if (kind === 'nightstand') {
      P.box(...F.r(0, F.L, 0, F.D - 0.03), 0.5, 2.1, FC.wood); legs(P, F, 0.5, 0.12, 0.05, FC.woodDark);
      for (const z of [1.3, 2.05]) { P.box(...F.r(0.05, F.L - 0.05, F.D - 0.03, F.D - 0.01), z - 0.7, z, FC.oak); handle(P, F, F.L / 2, z - 0.35, 0.3); }
      P.cyl(...F.p(F.L / 2, F.D / 2), 2.1, 2.15, 0.3, FC.woodDark, 12); P.cyl(...F.p(F.L / 2, F.D / 2), 2.15, 2.9, 0.04, FC.chrome, 6); P.cyl(...F.p(F.L / 2, F.D / 2), 2.75, 3.25, 0.32, FC.linen, 14);
      name = 'nightstand with lamp';
    } else if (kind === 'dresser') {
      P.box(...F.r(0, F.L, 0, F.D - 0.03), 0.3, 2.8, FC.wood);
      for (const z of [0.95, 1.6, 2.25]) for (const [a, b] of [[0.05, F.L / 2 - 0.03], [F.L / 2 + 0.03, F.L - 0.05]]) { P.box(...F.r(a, b, F.D - 0.03, F.D - 0.01), z - 0.6, z, FC.oak); handle(P, F, (a + b) / 2, z - 0.3, 0.35); }
      legs(P, F, 0.3, 0.12, 0.05, FC.woodDark);
    } else if (kind === 'sofa') {
      const back = Math.min(0.75, F.D * 0.3), aw = 0.45;
      const others = fixtures.filter((g, j) => j !== i && g.kind === 'sofa');
      const butts = u => { const [px, py] = F.p(u, F.D / 2); return others.some(g => px > g.x1 - 0.2 && px < g.x2 + 0.2 && py > g.y1 - 0.2 && py < g.y2 + 0.2); };
      const e0 = butts(-0.1) ? 0 : aw, e1 = butts(F.L + 0.1) ? 0 : aw;
      P.box(...F.r(0, F.L, 0, F.D), 0.25, 1.15, FC.fabric);
      P.box(...F.r(0, F.L, 0, back), 1.15, 2.75, FC.fabric);
      if (e0) P.box(...F.r(0, e0, back, F.D), 1.15, 2.1, FC.fabric);
      if (e1) P.box(...F.r(F.L - e1, F.L, back, F.D), 1.15, 2.1, FC.fabric);
      const a0 = e0, a1 = F.L - e1, n = Math.max(1, Math.round((a1 - a0) / 2.6)), cw = (a1 - a0) / n;
      for (let k = 0; k < n; k++) { P.box(...F.r(a0 + k * cw + 0.03, a0 + (k + 1) * cw - 0.03, back, F.D - 0.02), 1.15, 1.6, FC.cushion); P.box(...F.r(a0 + k * cw + 0.03, a0 + (k + 1) * cw - 0.03, back, back + 0.35), 1.6, 2.6, FC.cushion); }
      legs(P, F, 0.25, 0.15, 0.08, FC.woodDark);
    } else if (kind === 'coffee') {
      P.box(x1, x2, y1, y2, 1.25, 1.35, FC.oak); legs(P, F, 1.25, 0.15, 0.08, FC.woodDark); P.box(...F.r(0.15, F.L - 0.15, 0.15, F.D - 0.15), 0.35, 0.42, FC.oak);
    } else if (kind === 'tv') {
      P.box(x1, x2, y1, y2, 3.3, 5.6, FC.black); P.box(...F.r(0.06, F.L - 0.06, F.D, F.D + 0.02), 3.36, 5.54, FC.dark);
    } else if (kind === 'table') {
      const T = frameOf(x1, x2, y1, y2, w > d ? 'N' : 'E');
      P.box(x1, x2, y1, y2, 2.38, 2.5, FC.oak); legs(P, T, 2.38, 0.25, 0.25, FC.woodDark);
      const n = 3;
      for (let k = 0; k < n; k++) { const u = T.L * (k + 0.5) / n; const [ax, ay] = T.p(u, -0.55), [bx, by] = T.p(u, T.D + 0.55); chair(P, ax, ay, w > d ? 'N' : 'E'); chair(P, bx, by, w > d ? 'S' : 'W'); }
      const [ax, ay] = T.p(-0.55, T.D / 2), [bx, by] = T.p(T.L + 0.55, T.D / 2);
      chair(P, ax, ay, w > d ? 'E' : 'N'); chair(P, bx, by, w > d ? 'W' : 'S');
      name = 'dining table, seats 8';
    } else if (kind === 'island') {
      // island: work side faces east (sink, dishwasher), 12" seating overhang on the dining side (west)
      const I = frameOf(x1, x2, y1, y2, 'E');
      P.box(...I.r(0, I.L, 1.0, I.D - 0.3), 0, 0.33, FC.toe); P.box(...I.r(0, I.L, 1.0, I.D - 0.05), 0.33, 2.87, FC.cab);
      P.box(...I.r(0, I.L, 0, I.D + 0.06), 2.87, 3.0, FC.stone);
      P.box(...I.r(1.2, 3.2, I.D - 0.02, I.D), 0.4, 2.8, FC.steel);                                   // dishwasher front
      P.box(...I.r(3.25, 5.75, I.D - 2.1, I.D - 0.4), 2.99, 3.01, FC.basin);                         // sink
      const [fx, fy] = I.p(4.5, I.D - 2.2); P.cyl(fx, fy, 3.0, 4.2, 0.05, FC.chrome, 8);
      for (let k = 0; k < 4; k++) { const [sx, sy] = I.p(0.9 + k * 1.6, -0.6); P.cyl(sx, sy, 0, 2.2, 0.06, FC.black, 8); P.cyl(sx, sy, 2.2, 2.3, 0.6, FC.woodDark, 16); }
      name = 'island: sink and dishwasher on the kitchen side, 12" seating overhang on the dining side, 4 stools';
    } else if (kind === 'counter') {
      const runs = front === 'W' ? [[0, 1.96], [4.45, F.L]] : [[0, F.L]];
      for (const [a, b] of runs) baseRun(P, F, a, b);
      if (front === 'W') { uppers(P, F, 0, 1.96); uppers(P, F, 4.45, F.L); P.box(...F.r(1.96, 4.45, 0, 1.6), 5.5, 6.2, FC.steel); }   // hood over the range
      else { uppers(P, F, 0, 1.2); }
      name = front === 'W' ? 'kitchen wall run: base cabinets, 36" top, uppers, hood over the range' : 'kitchen rear run under the window: base cabinets, uppers beside the window';
    } else if (kind === 'range') {
      P.box(...F.r(0.02, F.L - 0.02, 0, F.D), 0, 3.0, FC.steel); P.box(...F.r(0.05, F.L - 0.05, 0.1, F.D - 0.05), 3.0, 3.03, FC.dark);
      P.box(...F.r(0.1, F.L - 0.1, F.D, F.D + 0.04), 0.6, 2.4, FC.dark); P.box(...F.r(0, F.L, 0, 0.25), 3.0, 3.6, FC.steel);
    } else if (kind === 'fridge') {
      P.box(...F.r(0.03, F.L - 0.03, 0, F.D), 0, 6.0, FC.steel); P.box(...F.r(F.L / 2 - 0.02, F.L / 2 + 0.02, F.D, F.D + 0.02), 2.6, 6.0, FC.dark);
      for (const du of [-0.18, 0.18]) P.box(...F.r(F.L / 2 + du - 0.03, F.L / 2 + du + 0.03, F.D, F.D + 0.12), 3.2, 5.4, FC.chrome);
      P.box(...F.r(0, F.L, 0, F.D), 6.0, 8.0, FC.cab);
    } else if (kind === 'tub') {
      const rim = 1.6, b = 0.3;
      P.box(x1, x2, y1, y1 + b, 0, rim, FC.porcelain); P.box(x1, x2, y2 - b, y2, 0, rim, FC.porcelain); P.box(x1, x1 + b, y1, y2, 0, rim, FC.porcelain); P.box(x2 - b, x2, y1, y2, 0, rim, FC.porcelain);
      P.box(x1 + b, x2 - b, y1 + b, y2 - b, 0, 0.3, FC.basin);
      P.box(x2 - 0.04, x2, y1, y2, rim, 7.0, FC.tile); P.box(x1, x2, y1, y1 + 0.04, rim, 7.0, FC.tile); P.box(x1, x1 + 0.04, y1, y2, rim, 7.0, FC.tile);   // tile surround
      P.cyl(x2 - 0.15, cy, rim + 0.2, rim + 0.6, 0.05, FC.chrome, 8); P.cyl(x2 - 0.15, cy, 6.4, 6.6, 0.15, FC.chrome, 10);
    } else if (kind === 'toilet') {
      P.box(...F.r(0.1, F.L - 0.1, 0, 0.6), 1.3, 2.55, FC.porcelain); P.box(...F.r(0.05, F.L - 0.05, 0, 0.65), 2.55, 2.65, FC.porcelain);
      const [bx, by] = F.p(F.L / 2, 1.45), st = F.faceAxis === 'x' ? [1.3, 1] : [1, 1.3];
      P.cyl(bx, by, 0, 1.0, 0.38, FC.porcelain, 14, ...st); P.cyl(bx, by, 1.0, 1.32, 0.6, FC.porcelain, 18, ...st); P.cyl(bx, by, 1.32, 1.37, 0.6, FC.pillow, 18, ...st);
      P.box(...F.r(F.L / 2 - 0.3, F.L / 2 + 0.3, 0.6, 1.0), 0.6, 1.3, FC.porcelain);
    } else if (kind === 'vanity') {
      P.box(...F.r(0, F.L, 0, F.D - 0.3), 0, 0.33, FC.toe); P.box(...F.r(0, F.L, 0, F.D - 0.03), 0.33, 2.7, FC.oak); P.box(...F.r(0, F.L, 0, F.D), 2.7, 2.85, FC.porcelain);
      const sinks = F.L >= 5 ? [F.L * 0.25, F.L * 0.75] : [F.L / 2];
      for (const u of sinks) { const [px, py] = F.p(u, F.D * 0.55); P.cyl(px, py, 2.85, 2.86, 0.62, FC.basin, 18); const [qx, qy] = F.p(u, 0.25); P.cyl(qx, qy, 2.85, 3.35, 0.05, FC.chrome, 8); P.box(...F.r(u - 1.1, u + 1.1, 0, 0.04), 3.5, 6.4, FC.mirror); handle(P, F, u, 2.45, 0.6); }
    } else if (kind === 'shower') {
      P.box(x1, x2, y1, y2, 0, 0.05, FC.tile);
      for (const r of [[x1, x2, y2 - 0.04, y2], [x2 - 0.04, x2, y1, y2]]) P.box(...r, 0.05, 7.5, FC.tile);
      P.cyl(cx + 0.8, y2 - 0.15, 6.5, 6.7, 0.18, FC.chrome, 10);
      const g = box(x1, x1 + 0.04, y1, y2, 0, 7, MAT.glass, { kind: 'furn', text: 'Shower glass: fixed panel and door' }, G.furn); if (g) g.castShadow = false;
      const g2 = box(x1, x2, y1, y1 + 0.04, 0, 7, MAT.glass, { kind: 'furn', text: 'Shower glass: fixed panel and door' }, G.furn); if (g2) g2.castShadow = false;
    } else if (kind === 'washer' || kind === 'dryer') {
      P.box(...F.r(0.03, F.L - 0.03, 0.1, F.D - 0.05), 0, 3.1, FC.porcelain); P.box(...F.r(0.03, F.L - 0.03, F.D - 0.05, F.D - 0.02), 2.7, 3.05, FC.basin);
      const [px, py] = F.p(F.L / 2, F.D - 0.03); P.disc(px, py, 1.5, 0.8, 0.04, F.faceAxis, FC.chrome); P.disc(px, py, 1.5, 0.7, 0.07, F.faceAxis, FC.dark);
      if (kind === 'dryer') P.box(...F.r(0, F.L, 0, F.D), 4.5, 4.6, FC.cab);
    } else if (kind === 'linen') {
      P.box(...F.r(0, F.L, 0, F.D - 0.05), 0, 7.0, FC.cab); P.box(...F.r(F.L / 2 - 0.02, F.L / 2 + 0.02, F.D - 0.05, F.D - 0.03), 0.3, 6.9, FC.toe);
      for (const u of [F.L / 2 - 0.2, F.L / 2 + 0.2]) P.box(...F.r(u - 0.03, u + 0.03, F.D - 0.03, F.D + 0.04), 3.2, 4.0, FC.chrome);
    } else if (kind === 'shelves') {
      let k = i * 5;
      for (const z of [0.4, 1.6, 2.8, 4.0, 5.2, 6.4]) {
        P.box(...F.r(0, F.L, 0, F.D), z, z + 0.07, FC.oak);
        if (z > 6) continue;
        let u = 0.2;
        while (u < F.L - 0.6) { const bw = 0.3 + ((k * 7) % 5) / 10, bh = 0.4 + ((k * 3) % 6) / 10; if (k % 4) P.box(...F.r(u, Math.min(u + bw, F.L - 0.15), 0.1, F.D * 0.8), z + 0.07, z + 0.07 + bh, GARMENTS[k % GARMENTS.length]); u += bw + 0.1; k++; }
      }
    } else if (kind === 'rods') {
      const vm = F.D / 2, rz = 5.5;
      P.box(...F.r(0, F.L, vm - 0.06, vm + 0.06), rz, rz + 0.12, FC.chrome); P.box(...F.r(0, F.L, 0, F.D * 0.9), 5.85, 5.92, FC.cab);
      let u = 0.25, k = i * 7;
      while (u < F.L - 0.25) { const len = 2.4 + ((k * 37) % 13) / 10, c = GARMENTS[k % GARMENTS.length], t = 0.12 + ((k * 13) % 5) / 50; P.box(...F.r(u, u + t, vm - 0.8, vm + 0.8), Math.max(0.4, rz - len), rz - 0.05, c); u += t + 0.1 + ((k * 11) % 7) / 40; k++; }
      name = 'closet rod at 66" with shelf';
    } else if (kind === 'bench') {
      P.box(...F.r(0, F.L, 0, F.D), 1.4, 1.55, FC.oak); P.box(...F.r(0, F.L, 0, F.D - 0.1), 0, 1.4, FC.cab); P.box(...F.r(0, F.L, 0, 0.08), 4.5, 6.0, FC.oak);
      for (let u = 0.5; u < F.L; u += 1) P.box(...F.r(u - 0.05, u + 0.05, 0.08, 0.3), 5.3, 5.45, FC.black);
    } else if (kind === 'car') {
      const c = i % 2 ? FC.carB : FC.carA, C = frameOf(x1, x2, y1, y2, 'N');   // u across the car, v along it from the rear
      P.box(...C.r(0.1, C.L - 0.1, 0.4, C.D - 0.3), 1.1, 3.0, c);
      P.box(...C.r(0.35, C.L - 0.35, 3.5, C.D - 4.5), 3.0, 5.4, c);
      P.box(...C.r(0.4, C.L - 0.4, C.D - 4.6, C.D - 4.4), 3.1, 5.2, FC.glass); P.box(...C.r(0.4, C.L - 0.4, 3.4, 3.6), 3.1, 5.2, FC.glass);
      for (const [u, v] of [[0.05, 2.8], [C.L - 0.65, 2.8], [0.05, C.D - 3.0], [C.L - 0.65, C.D - 3.0]]) P.box(...C.r(u, u + 0.6, v - 1.1, v + 1.1), 0, 2.2, FC.tyre);
      name = 'parked car';
    } else if (kind === 'stair') {
      const m = box(x1, x2, y1, y2, CEIL - 0.05, CEIL + 0.05, MAT.wood, { kind: 'furn', text: `Attic access: ${note}` }, G.furn);
      P.box(x1 + 0.1, x2 - 0.1, y1 + 0.2, y2 - 0.2, CEIL - 0.12, CEIL - 0.05, FC.cab);
      name = 'attic access';
    } else if (kind === 'wh') {
      P.cyl(cx, cy, 0, 0.12, 1.05, FC.dark, 24); P.cyl(cx, cy, 0.12, 5.0, 0.95, FC.porcelain, 24); P.cyl(cx, cy, 5.0, 5.4, 0.1, FC.chrome, 8);
      P.cyl(cx - 0.6, cy, 5.4, 6.2, 0.25, FC.basin, 12);   // expansion tank
      name = 'water heater';
    } else {
      P.box(x1, x2, y1, y2, 0, 2.5, FC.cab);
    }
    const size = `${ftIn(w)} x ${ftIn(d)}`;
    P.done({ kind: 'furn', text: `${name[0].toUpperCase() + name.slice(1)}, ${size}${R ? ', ' + R : ''}${note ? ' — ' + note : ''}` });
  });
  // mechanical room and outdoor equipment
  const pn = devices.find(d => d.type === 'panel');
  if (pn) box(pn.x, pn.x + 0.35, pn.y - 1.2, pn.y + 1.2, 3.5, 6.5, MAT.panel, { kind: 'elec', text: pn.text }, G.elec);
  const h = hvac.hp; box(h.x1, h.x2, h.y1, h.y2, 0.6, 3.6, MAT.unit, { kind: 'hvac', text: h.note }, G.hvac);
  // porch and patio posts
  for (const [x, y, which] of SET.posts) box(x - 0.25, x + 0.25, y - 0.25, y + 0.25, 0, which === 'porch' ? PLATE - 0.95 : 8.6, MAT.post, { kind: 'roof', text: `6x6 cedar post on a post base and footing, as the elevations: ${which === 'porch' ? 'front porch, under the porch gable beam' : 'rear patio shed'}` }, G.roof);
  { const ps = SET.posts.filter(p => p[2] === 'porch'), y = ps[0][1]; box(ps[0][0] - 0.6, ps[ps.length - 1][0] + 0.6, y - 0.25, y + 0.25, PLATE - 0.95, PLATE, MAT.post, { kind: 'roof', text: 'Porch beam: 2-2x10 (or 6x10 cedar wrap) on the posts, carries the porch gable trusses' }, G.roof); }
}

// ---------------------------------------------------------------- electrical devices
function buildElectrical() {
  for (const d of devices) {
    if (d.type === 'panel') continue;
    const data = { kind: 'elec', text: d.text }, h = d.h / 12, t = d.type;
    const attic = d.h >= 120;
    if (d.side === 'c' && d.h === 0) { box(d.x - 0.25, d.x + 0.25, d.y - 0.25, d.y + 0.25, 0, 0.06, MAT.rec, data, G.elec); continue; }
    if (d.side === 'c') {
      const z = attic ? CEIL + 1.2 : t === 'pend' ? 6.4 : t === 'chand' ? 7.0 : t === 'opener' ? CEIL - 0.3 : CEIL - 0.04;
      const pm = ['smoke', 'combo'].includes(t) ? MAT.alarm : t === 'ef' ? MAT.tall : ['wap'].includes(t) ? MAT.data : ['gfci', 'ded', 'opener'].includes(t) ? MAT.rec : t === 'disc' ? MAT.panel : MAT.light;
      if (t === 'shop') { box(d.x - 2, d.x + 2, d.y - 0.25, d.y + 0.25, CEIL - 0.2, CEIL - 0.05, MAT.light, data, G.elec); continue; }
      if (t === 'fanbox') {
        const p = M(d.x, d.y); const m = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 0.3, 16), MAT.light); m.position.set(p.x, CEIL - 1.0, p.z); m.userData = data; pickables.push(m); G.elec.add(m);
        for (let k = 0; k < 5; k++) { const a = k * Math.PI * 2 / 5; box(d.x + Math.cos(a) * 0.4 - 0.12, d.x + Math.cos(a) * 2.2 + 0.12, d.y + Math.sin(a) * 0.4 - 0.12, d.y + Math.sin(a) * 2.2 + 0.12, CEIL - 0.85, CEIL - 0.8, MAT.tall, data, G.elec); }
        tube({ x: d.x, y: d.y, h: CEIL - 0.85 }, { x: d.x, y: d.y, h: CEIL }, 0.05, MAT.trim, null, G.elec); continue;
      }
      if (t === 'pend' || t === 'chand') { const p = M(d.x, d.y); const m = new THREE.Mesh(new THREE.SphereGeometry(t === 'chand' ? 0.7 : 0.35, 14, 10), MAT.light); m.position.set(p.x, z, p.z); m.userData = data; pickables.push(m); G.elec.add(m); tube({ x: d.x, y: d.y, h: z }, { x: d.x, y: d.y, h: CEIL }, 0.02, MAT.trim, null, G.elec); continue; }
      const r = t === 'ef' ? 0.5 : ['smoke', 'combo'].includes(t) ? 0.3 : t === 'soffit' ? 0.3 : 0.33;
      const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.08, 20), pm); const p = M(d.x, d.y); m.position.set(p.x, d.y < 0 || d.y > 40 ? 8.4 : z, p.z); m.userData = data; pickables.push(m); G.elec.add(m); continue;
    }
    if (t === 'strip') { const hl = 0.9; if (d.side === 'S' || d.side === 'N') box(d.x - hl, d.x + hl, d.y - 0.6, d.y - 0.4, 4.45, 4.5, MAT.light, data, G.elec); else box(d.x - 0.6, d.x - 0.4, d.y - hl, d.y + hl, 4.45, 4.5, MAT.light, data, G.elec); continue; }
    if (t === 'hood') continue;
    const m = ['ext', 'sconce'].includes(t) ? MAT.light : ['sw', 'sw3', 'dim', 'fansw', 'tmr'].includes(t) ? MAT.sw : ['data', 'bell', 'chime', 'media'].includes(t) ? MAT.data : ['disc', 'jbox'].includes(t) ? MAT.panel : MAT.rec;
    const sz = t === 'tv' || t === 'media' ? 0.5 : t === 'sconce' ? 0.6 : t === 'ext' ? 0.35 : t === 'disc' ? 0.45 : 0.2, dp = 0.12;
    const s = d.side, dir = { N: [0, 1], S: [0, -1], E: [1, 0], W: [-1, 0] }[s] || [0, 0];
    const x0 = d.x, y0 = d.y;
    if (s === 'N' || s === 'S') box(x0 - sz, x0 + sz, Math.min(y0, y0 + dir[1] * dp), Math.max(y0, y0 + dir[1] * dp), h - (t === 'sconce' ? 0.2 : sz), h + (t === 'sconce' ? 0.2 : sz), m, data, G.elec);
    else box(Math.min(x0, x0 + dir[0] * dp), Math.max(x0, x0 + dir[0] * dp), y0 - sz, y0 + sz, h - (t === 'sconce' ? 0.2 : sz), h + (t === 'sconce' ? 0.2 : sz), m, data, G.elec);
  }
}

// ---------------------------------------------------------------- plumbing: drains under the slab, vents up the walls into the attic, PEX home runs
const DRAIN_H = -1.0, COLD_H = -0.55, HOT_H = -0.7, ATTIC_H = PLATE + 0.6;
const rOf = s => ({ '4"': 0.2, '3"': 0.15, '2"': 0.1, '1-1/2"': 0.08, '1-1/4"': 0.07 })[s] || 0.075;
// underside of the roof sheathing over the wall line: truss bottom chord, heel and top chord depth
const RB = PLATE + 3.5 / 12 + 0.6 + 5.5 / 12 * (0.5 + 0.5 * Math.hypot(1, SET.pitch));
const roofAt = (y, x = W / 2) => RB + SET.pitch * Math.max(0, roofRun(x, y));
function buildPlumbing() {
  const pl = plumbing;
  for (const dr of pl.drains) polyline(dr.pts, DRAIN_H, rOf(dr.size), MAT.drain, { kind: 'plumb', text: `Drain ${dr.id}: ${dr.size} under the slab — ${dr.note}` }, G.plumb);
  for (const f of pl.fixtures) {
    if (!f.dfu) continue;
    const top = f.kind === 'wc' ? 0.05 : f.kind === 'shower' ? 0.05 : f.kind === 'tub' ? 0.3 : f.kind === 'washer' ? 3.0 : 1.6;
    tube({ x: f.x, y: f.y, h: DRAIN_H }, { x: f.x, y: f.y, h: top }, f.kind === 'wc' ? 0.15 : 0.08, MAT.drain, { kind: 'plumb', text: `${f.id} ${f.name}: drain, trap ${f.trap}, ${f.dfu} DFU — ${f.note}` }, G.plumb);
  }
  for (const v of pl.vents) {
    const [x0, y0] = v.base, d = { kind: 'plumb', text: `Vent ${v.id}: ${v.size}, rises in wall ${v.wall} to the attic — ${v.note}` };
    tube({ x: x0, y: y0, h: DRAIN_H }, { x: x0, y: y0, h: ATTIC_H }, rOf(v.size) * 0.9, MAT.vent, d, G.plumb);
    polyline(v.attic, ATTIC_H, rOf(v.size) * 0.9, MAT.vent, d, G.plumb);
  }
  tube({ x: pl.vtr.x, y: pl.vtr.y, h: ATTIC_H }, { x: pl.vtr.x, y: pl.vtr.y, h: roofAt(pl.vtr.y, pl.vtr.x) + 1.0 }, 0.15, MAT.vent, { kind: 'plumb', text: `VTR: ${pl.vtr.note}` }, G.plumb);
  box(pl.aav.x - 0.12, pl.aav.x + 0.12, pl.aav.y - 0.12, pl.aav.y + 0.12, 1.6, 2.1, MAT.vent, { kind: 'plumb', text: `AAV: ${pl.aav.note}` }, G.plumb);
  for (const t of pl.trunks) {
    polyline(t.pts.map(([x, y]) => [x - 0.15, y - 0.15]), COLD_H, 0.07, MAT.cold, { kind: 'plumb', text: `Supply bundle ${t.id}: PEX home runs, cold — ${t.note}` }, G.plumb);
    polyline(t.pts.map(([x, y]) => [x + 0.15, y + 0.15]), HOT_H, 0.07, MAT.hot, { kind: 'plumb', text: `Supply bundle ${t.id}: PEX home runs, hot — ${t.note}` }, G.plumb);
  }
  for (const b of pl.branches) {
    const f = pl.fixtures.find(q => q.id === b.fixture), [x, y] = b.pts[b.pts.length - 1], top = Math.max(0.4, f.h / 12);
    if (f.cold) { polyline(b.pts.map(([px, py]) => [px - 0.08, py - 0.08]), COLD_H, 0.04, MAT.cold, { kind: 'plumb', text: `1/2" PEX cold home run to ${f.id} ${f.name}` }, G.plumb); tube({ x: x - 0.08, y: y - 0.08, h: COLD_H }, { x: x - 0.08, y: y - 0.08, h: top }, 0.04, MAT.cold, { kind: 'plumb', text: `Cold riser to ${f.id} ${f.name}` }, G.plumb); }
    if (f.hot) { polyline(b.pts.map(([px, py]) => [px + 0.08, py + 0.08]), HOT_H, 0.04, MAT.hot, { kind: 'plumb', text: `1/2" PEX hot home run to ${f.id} ${f.name}` }, G.plumb); tube({ x: x + 0.08, y: y + 0.08, h: HOT_H }, { x: x + 0.08, y: y + 0.08, h: top }, 0.04, MAT.hot, { kind: 'plumb', text: `Hot riser to ${f.id} ${f.name}` }, G.plumb); }
  }
  const mf = pl.manifold; box(mf.x - 0.15, mf.x + 0.1, mf.y - 1.0, mf.y + 1.0, 2.5, 4.0, MAT.cold, { kind: 'plumb', text: `Manifold MF: ${mf.note}` }, G.plumb);
  tube({ x: mf.x, y: mf.y, h: COLD_H }, { x: mf.x, y: mf.y, h: 2.5 }, 0.09, MAT.cold, null, G.plumb);
  const ws = pl.service; tube({ x: 64, y: ws.y, h: -3 }, { x: ws.x, y: ws.y, h: -3 }, 0.1, MAT.cold, { kind: 'plumb', text: `Water service: ${ws.note}` }, G.plumb); tube({ x: ws.x, y: ws.y, h: -3 }, { x: ws.x - 0.3, y: ws.y, h: 2.0 }, 0.1, MAT.cold, { kind: 'plumb', text: `Water service: ${ws.note}` }, G.plumb);
  tube({ x: 32.5, y: -4, h: DRAIN_H }, { x: 32.5, y: -10, h: DRAIN_H - 0.6 }, 0.2, MAT.drain, { kind: 'plumb', text: 'Building drain on to the sewer / septic' }, G.plumb);
}

// ---------------------------------------------------------------- HVAC in the attic
function buildHVAC() {
  const hv = hvac, TH = PLATE + 0.9;   // trunk centre height: on the ceiling joists, in the insulation
  const a = hv.ah; box(a.x1, a.x2, a.y1, a.y2, PLATE + 0.4, PLATE + 2.2, MAT.unit, { kind: 'hvac', text: a.note }, G.hvac);
  box(a.x1 - 0.5, a.x2 + 1.5, a.y1 - 1.5, a.y2 + 0.4, PLATE + 0.3, PLATE + 0.36, MAT.wood, { kind: 'hvac', text: 'FAU-1 service platform: 3/4" OSB on the truss bottom chords, 30" clear on the service side, catwalk from the pull-down stair in the garage' }, G.hvac);
  const [sx1, sx2, sy1, sy2] = hv.sp; box(sx1, sx2, sy1, sy2, PLATE + 0.4, PLATE + 2.0, MAT.sup, { kind: 'hvac', text: 'Supply plenum on FAU-1' }, G.hvac);
  const [rx1, rx2, ry1, ry2] = hv.rp; box(rx1, rx2, ry1, ry2, PLATE + 0.4, PLATE + 2.0, MAT.ret, { kind: 'hvac', text: 'Return plenum and filter rack on FAU-1' }, G.hvac);
  const rect = (pts, w, hgt, h0, m, text) => { for (let i = 1; i < pts.length; i++) { const [ax, ay] = pts[i - 1], [bx, by] = pts[i]; const along = Math.abs(ay - by) < 1e-6; box(Math.min(ax, bx) - (along ? 0 : w / 2), Math.max(ax, bx) + (along ? 0 : w / 2), Math.min(ay, by) - (along ? w / 2 : 0), Math.max(ay, by) + (along ? w / 2 : 0), h0 - hgt / 2, h0 + hgt / 2, m, { kind: 'hvac', text }, G.hvac); } };
  for (const t of hv.trunks) rect(t.pts, parseInt(t.size) / 12, 8 / 12, TH, MAT.sup, `Supply trunk ${t.id} ${t.size} in the attic — ${t.note}`);
  for (const [id, room, x, y, cfm, flex, frm] of hv.registers) {
    const d = { kind: 'hvac', text: `${id} ceiling diffuser, ${room}: ${cfm} CFM on ${flex} insulated flex` };
    tube({ x: frm[0], y: frm[1], h: TH }, { x, y, h: PLATE + 0.25 }, parseInt(flex) / 24, MAT.sup, d, G.hvac);
    box(x - 0.42, x + 0.42, y - 0.3, y + 0.3, CEIL - 0.04, CEIL, MAT.sup, d, G.hvac);
  }
  for (const r of hv.returns) {
    const d = { kind: 'hvac', text: `${r.id} return, ${r.room}: ${r.size}, ${r.cfm} CFM — ${r.note}` };
    box(r.x - r.w / 2, r.x + r.w / 2, r.y - r.l / 2, r.y + r.l / 2, CEIL - 0.04, CEIL, MAT.ret, d, G.hvac);
    if (r.route.length > 2) polyline(r.route, TH, 7 / 12, MAT.ret, d, G.hvac);
    tube({ x: r.x, y: r.y, h: CEIL }, { x: r.x, y: r.y, h: TH }, 0.5, MAT.ret, d, G.hvac);
  }
  for (const [id, room, p1, p2, size] of hv.jumps) {
    const d = { kind: 'hvac', text: `Jump duct ${id}: ${room} to the hall, ${size}` };
    tube({ x: p1[0], y: p1[1], h: CEIL }, { x: p1[0], y: p1[1], h: TH }, 0.4, MAT.ret, d, G.hvac); tube({ x: p1[0], y: p1[1], h: TH }, { x: p2[0], y: p2[1], h: TH }, 0.4, MAT.ret, d, G.hvac); tube({ x: p2[0], y: p2[1], h: TH }, { x: p2[0], y: p2[1], h: CEIL }, 0.4, MAT.ret, d, G.hvac);
  }
  for (const t of hv.tstats) box(t.x, t.x + 0.12, t.y - 0.25, t.y + 0.25, 4.25, 4.75, MAT.panel, { kind: 'hvac', text: `Thermostat ${t.id}: ${t.note}` }, G.hvac);
  for (const e of hv.exhaust) {
    const d = { kind: 'hvac', text: `${e.id} ${e.name}: ${e.size} duct to a ${e.cap}` }, r = parseInt(e.size) / 24;
    const [x0, y0] = e.pts[0], [x1, y1] = e.pts[e.pts.length - 1];
    const z0 = e.id === 'EF4' ? 3.0 : e.id === 'EF3' ? 6.2 : CEIL;
    tube({ x: x0, y: y0, h: z0 }, { x: x0, y: y0, h: TH }, r, MAT.duct, d, G.hvac);
    polyline(e.pts, TH, r, MAT.duct, d, G.hvac);
    tube({ x: x1, y: y1, h: TH }, { x: x1, y: y1, h: roofAt(y1, x1) + 0.5 }, r, MAT.duct, d, G.hvac);
  }
  const ls = hv.lineset; tube({ x: ls[0][0], y: ls[0][1], h: 2.0 }, { x: ls[1][0], y: ls[1][1], h: 2.0 }, 0.08, MAT.lineset, { kind: 'hvac', text: 'Refrigerant line set AC-1 to FAU-1' }, G.hvac);
  tube({ x: ls[2][0], y: ls[2][1], h: 2.0 }, { x: ls[2][0], y: ls[2][1], h: TH }, 0.08, MAT.lineset, { kind: 'hvac', text: 'Refrigerant line set AC-1 to FAU-1, up through the mech room ceiling' }, G.hvac);
  polyline(ls.slice(2), TH, 0.08, MAT.lineset, { kind: 'hvac', text: 'Refrigerant line set AC-1 to FAU-1, in the attic over the garage' }, G.hvac);
  const cd = hv.condensate; polyline(cd, PLATE + 0.45, 0.05, MAT.cond, { kind: 'hvac', text: 'Condensate from FAU-1: 3/4" PVC down wall 13 to the washer standpipe' }, G.hvac);
  tube({ x: cd[2][0], y: cd[2][1], h: PLATE + 0.45 }, { x: cd[2][0], y: cd[2][1], h: 3.3 }, 0.05, MAT.cond, { kind: 'hvac', text: 'Condensate drop in wall 13' }, G.hvac);
  // natural gas: meter on the garage east wall, up the wall into the mech room, up into the attic and over to FAU-1
  const gm = hv.meter; box(gm.x, gm.x + 0.9, gm.y - 0.6, gm.y + 0.6, 2.4, 4.0, MAT.gas, { kind: 'hvac', text: gm.note }, G.hvac);
  const GH = 3.0, GA = PLATE + 0.6;
  for (const g of hv.gas) {
    const d = { kind: 'hvac', text: `Gas ${g.id}, ${g.size}: ${g.note}` }, r = parseInt(g.size) === 3 ? 0.07 : 0.05;
    if (g.where === 'wall') { tube({ x: gm.x, y: gm.y, h: GH }, { x: g.pts[0][0], y: g.pts[0][1], h: GH }, r, MAT.gas, d, G.hvac); polyline(g.pts, GH, r, MAT.gas, d, G.hvac); }
    else if (g.where === 'riser') { const [x, y] = g.pts[0]; tube({ x, y, h: GH }, { x, y, h: GA }, r, MAT.gas, d, G.hvac); box(x - 0.2, x + 0.2, y - 0.2, y + 0.2, GH - 0.6, GH, MAT.gas, { kind: 'hvac', text: 'Main gas shutoff, drip leg and capped tee in the mech room' }, G.hvac); }
    else { const h = g.where === 'low' ? g.h : GA; polyline(g.pts, h, r, MAT.gas, d, G.hvac); const [x, y] = g.pts[g.pts.length - 1]; tube({ x, y, h }, { x, y, h: g.to ?? PLATE + 1.2 }, r, MAT.gas, d, G.hvac); }
  }
  for (const fl of hv.flues) {
    const [fx0, fy0] = fl.pts[0], [fx1, fy1] = fl.pts[fl.pts.length - 1], fd = { kind: 'hvac', text: `${fl.id} ${fl.name}: ${fl.note}` }, h0 = fl.id === 'V1' ? PLATE + 1.6 : 5.6, hr = PLATE + 2.6 + 0.02 * Math.abs(fy1 - fy0);
    tube({ x: fx0, y: fy0, h: h0 }, { x: fx0, y: fy0, h: PLATE + 2.6 }, 0.12, MAT.flue, fd, G.hvac);
    if (fx1 !== fx0 || fy1 !== fy0) tube({ x: fx0, y: fy0, h: PLATE + 2.6 }, { x: fx1, y: fy1, h: hr }, 0.12, MAT.flue, fd, G.hvac);
    tube({ x: fx1, y: fy1, h: hr }, { x: fx1, y: fy1, h: roofAt(fy1, fx1) + 1.6 }, 0.12, MAT.flue, fd, G.hvac);
  }
}

// ---------------------------------------------------------------- roof: 6:12 gable, ridge east–west, with a front gable over the porch and one over the garage
const TR = { heel: 0.6, top: 5.5 / 12, bot: 3.5 / 12, web: 3.5 / 12, w: 1.5 / 12 };
const OV = SET.overhang, PIT = SET.pitch, GAB = SET.roof.gables, RIDGE = D / 2;
// "run": horizontal distance up the slope from the wall line; the roof is RB + pitch × run, the highest of the main roof and the front gables
const mainRun = (x, y) => Math.min(y, D - y);
const inMain = (x, y) => x >= -OV - 1e-6 && x <= W + OV + 1e-6 && y >= -OV - 1e-6 && y <= D + OV + 1e-6;
const gabRun = (g, x) => Math.min(x - g.a, g.b - x);
const inGab = (g, x, y) => x >= g.a - OV - 1e-6 && x <= g.b + OV + 1e-6 && y >= g.front - OV - 1e-6 && y <= (g.b - g.a) / 2 + 1e-6;
function roofRun(x, y) { let r = inMain(x, y) ? mainRun(x, y) : -Infinity; for (const g of GAB) if (inGab(g, x, y)) r = Math.max(r, gabRun(g, x)); return r; }

// sticks: [[x, y, h], [x, y, h], width, depth, plan normal of the member's plane [nx, ny]] merged into one geometry
function sticks(list) {
  const pos = [], nor = [];
  for (const [a, b, wd, dp, n] of list) {
    const A = M(a[0], a[1]), B = M(b[0], b[1]), va = new THREE.Vector3(A.x, a[2], A.z), vb = new THREE.Vector3(B.x, b[2], B.z);
    const dir = vb.clone().sub(va), len = dir.length(); if (len < 0.05) continue; dir.normalize();
    let xa = new THREE.Vector3(n[0], 0, -n[1]).normalize();
    const za = new THREE.Vector3().crossVectors(xa, dir).normalize(); xa = new THREE.Vector3().crossVectors(dir, za).normalize();
    const g = new THREE.BoxGeometry(wd, len, dp), mt = new THREE.Matrix4().makeBasis(xa, dir, za); mt.setPosition(va.clone().add(vb).multiplyScalar(0.5));
    g.applyMatrix4(mt); const ng = g.toNonIndexed(); pos.push(...ng.attributes.position.array); nor.push(...ng.attributes.normal.array); g.dispose(); ng.dispose();
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); out.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  return out;
}
function addTruss(list, text) {
  const m = new THREE.Mesh(sticks(list), MAT.woodExt); m.castShadow = true; m.receiveShadow = true; m.userData = { kind: 'roof', text }; pickables.push(m); G.truss.add(m);
}
// one truss in a vertical plane. P(s, h) gives the plan point at station s; top(s) the underside of the top chord; s0..s1 the bearing span
function truss(P, n, top, s0, s1, e0, e1, bottomAt, breaks, text) {
  const L = [], seg = (sa, ha, sb, hb, d, wd = TR.w) => L.push([P(sa, ha), P(sb, hb), wd, d, n]);
  const st = [e0, ...breaks.filter(b => b > e0 && b < e1), e1];
  for (let k = 1; k < st.length; k++) seg(st[k - 1], top(st[k - 1]) + TR.top / 2, st[k], top(st[k]) + TR.top / 2, TR.top);   // top chord
  seg(s0, bottomAt - TR.bot / 2, s1, bottomAt - TR.bot / 2, TR.bot);                                                           // bottom chord
  for (const s of [s0, s1]) seg(s, bottomAt, s, top(s), TR.web);                                                               // heels
  const np = 8;
  for (let k = 1; k <= np; k++) {
    const a = s0 + (k - 1) * (s1 - s0) / np, b = s0 + k * (s1 - s0) / np, ha = (k - 1) % 2 ? top(a) : bottomAt, hb = k % 2 ? top(b) : bottomAt;
    if (Math.min(top(a), top(b)) - bottomAt > 0.3) seg(a, ha, b, hb, TR.web);
  }
  const mid = (s0 + s1) / 2; if (top(mid) - bottomAt > 0.3) seg(mid, bottomAt, mid, top(mid), TR.web);
  addTruss(L, text);
}
function buildRoofTrusses() {
  const y0 = PLATE + TR.bot, T0 = y0 + TR.heel;
  // main trusses north–south at 24" o.c.; the end trusses are sheathed gable ends
  for (let px = 0; px <= W + 1e-6; px += 2) {
    const x = px === 0 ? 0.0625 : px >= W ? W - 0.0625 : px, top = s => T0 + PIT * Math.min(s, D - s), end = px === 0 || px >= W;
    truss((s, h) => [x, s, h], [1, 0], top, 0, D, -OV, D + OV, y0, [RIDGE],
      `Roof truss ${px / 2 + 1} of ${W / 2 + 1}${end ? ` (${px ? 'east' : 'west'} gable end, sheathed, verticals at 16")` : ''}: 6:12 common, ${ftIn(px)} from the west wall, 40'-0" clear span from the front wall to the rear wall, 12" overhang; interior walls stay non-bearing`);
  }
  // the front gables: framed trusses where they stand clear of the main roof, valley trusses where they sit on it
  const lift = RB - T0 + 0.29;
  for (const g of GAB) {
    const mid = (g.a + g.b) / 2, top = x => T0 + PIT * Math.min(x - g.a, g.b - x);
    for (let y = g.front; y < (g.b - g.a) / 2 - 1e-6; y += 2) {
      if (y <= 1e-6) {
        truss((s, h) => [s, y, h], [0, 1], top, g.a, g.b, g.a - OV, g.b + OV, y0, [mid], `${g.name}: ${y === g.front ? 'gable end truss, sheathed and sided' : 'common truss'}, 6:12, ${ftIn(g.b - g.a)} span${g.id === 'CG1' ? ', bearing on the porch beam and the trusses behind' : ''}`);
      } else {
        const d = y + lift / PIT, xl = g.a + d, xr = g.b - d, base = RB + PIT * y + 0.04;
        if (xr - xl < 1) continue;
        truss((s, h) => [s, y, h], [0, 1], top, xl, xr, xl, xr, base, [mid], `${g.name}: valley truss on the main roof sheathing, ${ftIn(xr - xl)} wide; valley sets at 24" o.c. up to where the gable ridge meets the main roof`);
      }
    }
  }
}
function buildRoof() {
  // one surface for the whole roof: the main gable and the two front gables, with valleys where the planes meet.
  // Every valley here runs at 45° in plan, so a 6" grid, split on the right diagonal, follows them exactly.
  const step = 0.5, x0 = -OV, x1 = W + OV, y0 = Math.min(-OV, ...GAB.map(g => g.front - OV)), y1 = D + OV;
  const H = (x, y) => RB + 0.04 + PIT * roofRun(x, y), pos = [];
  const v = (x, y) => { const m = M(x, y); pos.push(m.x, H(x, y), m.z); };
  for (let x = x0; x < x1 - 1e-6; x += step) for (let y = y0; y < y1 - 1e-6; y += step) {
    const cx = x + step / 2, cy = y + step / 2; if (roofRun(cx, cy) === -Infinity) continue;
    const xb = x + step, yb = y + step, hc = H(cx, cy);
    if (Math.abs((H(x, y) + H(xb, yb)) / 2 - hc) <= Math.abs((H(xb, y) + H(x, yb)) / 2 - hc)) { v(x, y); v(xb, y); v(xb, yb); v(x, y); v(xb, yb); v(x, yb); }
    else { v(x, y); v(xb, y); v(x, yb); v(xb, y); v(xb, yb); v(x, yb); }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.computeVertexNormals();
  const rm = MAT.roof.clone(); rm.side = THREE.DoubleSide;
  const roof = new THREE.Mesh(g, rm); roof.castShadow = true; roof.receiveShadow = true;
  roof.userData = { kind: 'roof', text: 'Roof: 6:12 gable, ridge east–west, with two front gables (porch and garage), architectural asphalt shingles on 7/16" OSB, synthetic underlayment, ice barrier 24" inside the wall line and in the valleys, ridge vent; 12" overhangs' };
  pickables.push(roof); G.roof.add(roof);
  // main gable ends over walls 4 and 2
  { const k = RB - PLATE, sh = new THREE.Shape(); sh.moveTo(-D / 2, 0); sh.lineTo(D / 2, 0); sh.lineTo(D / 2, k); sh.lineTo(0, k + PIT * D / 2); sh.lineTo(-D / 2, k); sh.closePath();
    for (const px of [0, W]) {
      const g = new THREE.ExtrudeGeometry(sh, { depth: TEXT, bevelEnabled: false }); g.rotateY(Math.PI / 2);
      const m = new THREE.Mesh(g, MAT.siding); m.position.set(px - W / 2 - (px ? TEXT : 0), PLATE, 0); m.userData = { kind: 'roof', text: `Gable end over the ${px ? 'east' : 'west'} wall: sheathed gable truss, siding to match` }; pickables.push(m); G.roof.add(m);
    } }
  // front gable faces: sided triangles over the porch beam and over the garage door wall
  for (const gb of GAB) {
    const sh = new THREE.Shape(), xa = gb.a - W / 2, xb = gb.b - W / 2, k = RB - PLATE;
    sh.moveTo(xa, 0); sh.lineTo(xb, 0); sh.lineTo(xb, k); sh.lineTo((xa + xb) / 2, k + PIT * (gb.b - gb.a) / 2); sh.lineTo(xa, k); sh.closePath();
    const m = new THREE.Mesh(new THREE.ShapeGeometry(sh), MAT.siding.clone()); m.material.side = THREE.DoubleSide;
    m.position.set(0, PLATE, M(0, gb.front).z + 0.1); m.userData = { kind: 'roof', text: `${gb.name}: sheathed gable end truss, board-and-batten siding as the front elevation` }; pickables.push(m); G.roof.add(m);
  }
  const shed = (x1, x2, ya, yb, ha, hb, text) => {
    const L = Math.hypot(yb - ya, hb - ha), g = new THREE.BoxGeometry(x2 - x1, 0.08, L), m = new THREE.Mesh(g, MAT.roof);
    const a = M((x1 + x2) / 2, (ya + yb) / 2); m.position.set(a.x, (ha + hb) / 2, a.z); m.rotation.x = Math.atan2(hb - ha, yb - ya); m.castShadow = true; m.userData = { kind: 'roof', text }; pickables.push(m); G.roof.add(m);
  };
  const pat = SET.outdoor.find(o => o[0] === 'Rear Patio');
  shed(pat[1] - 0.3, pat[2] + 0.3, D + 0.4, pat[4] + 0.5, RB - PIT * 0.4, 8.7, 'Rear patio cover beyond the main eave: shed on 2x6 rafters from a ledger under the eave, 2-2x10 beam on 6x6 posts; the first 4\' of the patio is under the house roof');
}

// ---------------------------------------------------------------- build everything
buildFloor();
for (const w of walls) { wallBoxes(w, w.type === 'E' ? MAT.siding : MAT.wall); frameWall(w); }
buildFurniture(); buildElectrical(); buildPlumbing(); buildHVAC(); buildRoofTrusses(); buildRoof();

// ---------------------------------------------------------------- picking
const raycaster = new THREE.Raycaster(); let picked = null, downAt = null;
function clearPick() { if (!picked) return; picked.mesh.material = picked.mat; picked = null; $('sel').hidden = true; $('selpop').hidden = true; $('selcomment').setAttribute('aria-expanded', 'false'); }
// a picked item's comments are open items on its trade's sheet; electrical devices use the same tag as the E-1 card, so both show the same comments
const SHEET_OF = { elec: 'e1', plumb: 'p1', hvac: 'm1' };
function refOf3d({ kind, text }) {
  const sheet = SHEET_OF[kind] || (kind === 'furn' && /toilet|tub|vanity|shower|washer|sink|water heater/i.test(text) ? 'p1' : 's1');
  const ref = kind === 'elec' ? text.split(' ')[0] : text.split(/:| — /)[0].trim();
  return { sheet, ref: ref.slice(0, 60) };
}
function pick(mesh) {
  clearPick(); picked = { mesh, mat: mesh.material }; mesh.material = MAT.hi; $('seltext').textContent = mesh.userData.text; $('sel').hidden = false;
  const { sheet, ref } = refOf3d(mesh.userData); $('sel').dataset.sheet = sheet; $('selref').textContent = ref;
}
$('selclear').addEventListener('click', clearPick);
renderer.domElement.addEventListener('pointerdown', e => { downAt = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', e => {
  const far = !downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 5; downAt = null; if (far) return;
  const r = renderer.domElement.getBoundingClientRect();
  raycaster.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), camera);
  const targets = pickables.filter(m => m.parent && m.parent.visible && m.material !== MAT.wallGhost && m.material !== MAT.sidingGhost);
  const hit = raycaster.intersectObjects(targets, false).find(h => h.point.y <= cutPlane.constant + 0.02 || [G.plumb, G.hvac, G.truss, G.roof, G.elec].includes(h.object.parent));
  if (hit) pick(hit.object); else clearPick();
});

// ---------------------------------------------------------------- start view, layers, loop
camera.position.set(-48, 58, 70); controls.target.set(0, 2, 0); controls.update();   // bird's eye from the south-west, over the front porch
function applyLayers() {
  const fr = $('ly-framing').checked;
  G.framing.visible = fr;
  G.walls.visible = $('ly-walls').checked; G.shell.visible = $('ly-shell').checked;
  for (const m of G.walls.children) if (m.material === MAT.wall || m.material === MAT.wallGhost) m.material = fr ? MAT.wallGhost : MAT.wall;
  for (const m of G.shell.children) if (m.material === MAT.siding || m.material === MAT.sidingGhost) m.material = fr ? MAT.sidingGhost : MAT.siding;
  G.elec.visible = $('ly-elec').checked; G.plumb.visible = $('ly-plumb').checked; G.hvac.visible = $('ly-hvac').checked; G.truss.visible = $('ly-truss').checked; G.roof.visible = $('ly-roof').checked;
  G.furn.visible = $('ly-furn').checked; G.floor.visible = true; G.floor.children.forEach((m, i) => { if (m.material && m.material.map !== undefined && m.geometry.type === 'PlaneGeometry' && i > 0) m.visible = $('ly-floor').checked; });
  const h = parseFloat($('cut').value); $('cutval').value = h >= 9.5 ? 'no cut' : ftIn(h); setCut(h);
  if (picked && fr) clearPick();
}
for (const id of ['ly-walls', 'ly-framing', 'ly-elec', 'ly-plumb', 'ly-hvac', 'ly-truss', 'ly-roof', 'ly-furn', 'ly-shell', 'ly-floor', 'cut']) $(id).addEventListener('input', applyLayers);
applyLayers(); status('');
const needle = $('needle');
function frame() {
  requestAnimationFrame(frame);
  if (document.hidden || $('sheet-3d').hidden) return;
  controls.update();
  needle.style.transform = `rotate(${THREE.MathUtils.radToDeg(controls.getAzimuthalAngle()).toFixed(1)}deg)`;
  renderer.render(scene, camera);
}
requestAnimationFrame(frame);
