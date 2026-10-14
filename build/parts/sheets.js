<script>
// ---------------------------------------------------------------- tabs and 2D sheets (plain script, runs first)
(function () {
  // Sheet title blocks show the app version as their revision.
  const ver = document.querySelector('meta[name="app-version"]').content;
  for (const t of document.querySelectorAll('text.rev')) t.textContent = 'rev ' + ver;
  const $ = id => document.getElementById(id);
  const tabs = [...document.querySelectorAll('.tabs [role="tab"]')];
  function show(key, setHash = true) {
    for (const t of tabs) {
      const on = t.dataset.sheet === key;
      t.setAttribute('aria-selected', String(on));
      $('sheet-' + t.dataset.sheet).hidden = !on;
    }
    if (setHash) history.replaceState(null, '', '#' + key);
    try { localStorage.setItem('wb-sheet', key); } catch (e) { /* per-viewer convenience */ }
    dispatchEvent(new Event('resize'));
  }
  for (const t of tabs) t.addEventListener('click', () => show(t.dataset.sheet));
  addEventListener('hashchange', () => { const k = location.hash.slice(1); if (tabs.some(t => t.dataset.sheet === k)) show(k, false); });
  let start = location.hash.slice(1);
  if (!tabs.some(t => t.dataset.sheet === start)) { try { start = localStorage.getItem('wb-sheet') || '3d'; } catch (e) { start = '3d'; } }
  if (!tabs.some(t => t.dataset.sheet === start)) start = '3d';
  show(start, location.hash.slice(1) === start);

  // each 2D sheet: zoom, pick on the drawing, pick from the schedule
  for (const sheet of document.querySelectorAll('.sheet2d')) {
    const paper = sheet.querySelector('.paper'), svg = sheet.querySelector('.paper svg'), sel = sheet.querySelector('.sel'), scroller = sheet.querySelector('.scroller');
    // zoom. Fit / 2× / 4× buttons; pinch and double-tap on touch; ctrl+wheel (a trackpad pinch) on desktop.
    // The paper is sized in px (fit width × zoom). A pinch previews with a CSS transform and commits the width when the fingers lift.
    const tools = sheet.querySelector('.tools'), header = document.querySelector('header.bar');
    const MAXZ = 8;
    // the sticky section bar sits under the toolbar and the zoomed frame fills the rest of the screen: publish both heights
    const measure = () => { const th = tools ? tools.offsetHeight : 0; sheet.style.setProperty('--tools-h', th + 'px'); sheet.style.setProperty('--chrome-h', (th + (header ? header.offsetHeight : 0)) + 'px'); };
    let zoom = 1;
    const fitW = () => Math.min(scroller.clientWidth, 1400);
    const phone = () => scroller.clientWidth < 700;
    const framed = () => matchMedia('(max-width: 760px), (pointer: coarse)').matches;
    function layout() {
      if (!scroller.clientWidth) return; // hidden sheet: laid out when shown (show() fires resize)
      measure();
      paper.style.maxWidth = 'none'; paper.style.width = Math.round(fitW() * zoom) + 'px';
      scroller.classList.toggle('zoomed', zoom > 1.02);
      for (const o of sheet.querySelectorAll('[data-zoom]')) o.setAttribute('aria-pressed', String(Math.abs(zoom - +o.dataset.zoom) < 0.02));
    }
    // zoom to z keeping the paper point (px, py), in paper px at the current zoom, under the client point (cx, cy)
    function zoomTo(z, px, py, cx, cy) {
      z = Math.min(MAXZ, Math.max(1, z)); const k = z / zoom;
      zoom = z; layout();
      const pr = paper.getBoundingClientRect();
      const dx = pr.left + px * k - cx, dy = pr.top + py * k - cy;
      scroller.scrollLeft += dx;
      const was = scroller.scrollTop; scroller.scrollTop += dy;
      const rest = dy - (scroller.scrollTop - was); if (Math.abs(rest) > 0.5) sheet.scrollTop += rest;
    }
    function zoomAt(z, cx, cy) { const pr = paper.getBoundingClientRect(); zoomTo(z, cx - pr.left, cy - pr.top, cx, cy); }
    const toolsBottom = () => tools ? tools.getBoundingClientRect().bottom : sheet.getBoundingClientRect().top;
    function visibleCenter() {
      const r = scroller.getBoundingClientRect(), s = sheet.getBoundingClientRect();
      const top = Math.max(r.top, toolsBottom()), bottom = Math.min(r.bottom, s.bottom);
      return [r.left + r.width / 2, bottom > top ? (top + bottom) / 2 : r.top + r.height / 2];
    }
    // on a phone the zoomed frame fills the screen below the toolbar: put it there
    function alignFrame() { measure(); if (framed() && scroller.classList.contains('zoomed')) { const d = scroller.getBoundingClientRect().top - toolsBottom() - 8; if (Math.abs(d) > 2) sheet.scrollTop += d; } }
    // bring a picked element into view: zoomed enough to read on a phone, centred in the frame, the frame under the toolbar
    function reveal(el) {
      measure();
      if (phone() && zoom < 3.9) { const c = el.getBoundingClientRect(); zoomAt(4, c.left + c.width / 2, c.top + c.height / 2); }
      const r = el.getBoundingClientRect(), p = scroller.getBoundingClientRect();
      scroller.scrollLeft += r.left + r.width / 2 - (p.left + p.width / 2);
      if (scroller.scrollHeight > scroller.clientHeight + 1) scroller.scrollTop += r.top + r.height / 2 - (p.top + p.height / 2);
      const r2 = el.getBoundingClientRect(), s = sheet.getBoundingClientRect(), tb = toolsBottom();
      const frameTop = scroller.getBoundingClientRect().top - tb - 8, centred = r2.top + r2.height / 2 - (tb + s.bottom) / 2;
      const by = framed() && scroller.classList.contains('zoomed') ? frameTop : Math.max(frameTop, centred);
      sheet.scrollTo({ top: sheet.scrollTop + by, behavior: 'smooth' });
    }
    for (const b of sheet.querySelectorAll('[data-zoom]')) b.addEventListener('click', () => { zoomAt(+b.dataset.zoom, ...visibleCenter()); alignFrame(); });
    addEventListener('resize', () => {
      if (sheet.hidden) return;
      const w = paper.offsetWidth || 1, h = paper.offsetHeight || 1;
      const fx = (scroller.scrollLeft + scroller.clientWidth / 2 - paper.offsetLeft) / w, fy = (scroller.scrollTop + scroller.clientHeight / 2 - paper.offsetTop) / h;
      layout();
      scroller.scrollLeft = fx * paper.offsetWidth + paper.offsetLeft - scroller.clientWidth / 2;
      scroller.scrollTop = fy * paper.offsetHeight + paper.offsetTop - scroller.clientHeight / 2;
    });
    layout();
    // pinch (two fingers) previews with a transform; double-tap zooms in on the spot, or back to fit
    let pinch = null, lastTap = { t: 0, x: 0, y: 0 };
    const mid = t => [(t[0].clientX + t[1].clientX) / 2, (t[0].clientY + t[1].clientY) / 2];
    const dist = t => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
    scroller.addEventListener('touchstart', e => {
      if (e.touches.length !== 2) return;
      const pr = paper.getBoundingClientRect(), [mx, my] = mid(e.touches);
      pinch = { d0: dist(e.touches), px: mx - pr.left, py: my - pr.top, k: 1, mx, my };
      paper.style.willChange = 'transform';
    }, { passive: true });
    scroller.addEventListener('touchmove', e => {
      if (!pinch || e.touches.length < 2) return;
      e.preventDefault();
      const [mx, my] = mid(e.touches);
      pinch.k = Math.min(MAXZ, Math.max(1, zoom * dist(e.touches) / pinch.d0)) / zoom; pinch.mx = mx; pinch.my = my;
      const sr = scroller.getBoundingClientRect();
      const left = sr.left + paper.offsetLeft - scroller.scrollLeft, top = sr.top + paper.offsetTop - scroller.scrollTop;
      paper.style.transform = `translate(${mx - left - pinch.px * pinch.k}px, ${my - top - pinch.py * pinch.k}px) scale(${pinch.k})`;
    }, { passive: false });
    function endPinch() {
      if (!pinch) return;
      const p = pinch; pinch = null;
      paper.style.transform = ''; paper.style.willChange = '';
      zoomTo(zoom * p.k, p.px, p.py, p.mx, p.my);
      alignFrame();
    }
    scroller.addEventListener('touchend', e => {
      if (pinch) { if (e.touches.length < 2) endPinch(); lastTap.t = 0; return; }
      if (e.touches.length || e.changedTouches.length !== 1) return;
      const t = e.changedTouches[0], now = e.timeStamp;
      if (now - lastTap.t < 350 && Math.hypot(t.clientX - lastTap.x, t.clientY - lastTap.y) < 30) {
        lastTap.t = 0; e.preventDefault();
        const big = phone() ? 4 : 2;
        zoomAt(zoom < big - 0.1 ? big : 1, t.clientX, t.clientY); alignFrame();
      } else lastTap = { t: now, x: t.clientX, y: t.clientY };
    }, { passive: false });
    scroller.addEventListener('touchcancel', endPinch);
    scroller.addEventListener('gesturestart', e => e.preventDefault());
    scroller.addEventListener('wheel', e => { if (!e.ctrlKey) return; e.preventDefault(); zoomAt(zoom * Math.exp(-Math.max(-40, Math.min(40, e.deltaY)) * 0.01), e.clientX, e.clientY); }, { passive: false });
    // thin pipes and ducts get a wide invisible stroke to catch the tap
    for (const g of svg.querySelectorAll('.sym')) {
      if (g.querySelector('circle.hit')) continue;
      for (const ln of [...g.querySelectorAll('path, line')]) {
        const h = ln.cloneNode(false); h.removeAttribute('stroke-dasharray');
        h.setAttribute('class', 'hitline'); h.setAttribute('stroke', '#000'); h.setAttribute('stroke-opacity', '0'); h.setAttribute('stroke-width', '12'); h.setAttribute('fill', 'none'); h.setAttribute('pointer-events', 'stroke');
        const tt = g.querySelector('title'); g.insertBefore(h, tt ? tt.nextSibling : g.firstChild);
      }
    }
    // the picked item's card, pinned directly below the drawing
    const card = document.createElement('div'); card.className = 'picked'; card.hidden = true;
    card.innerHTML = '<div class="pk-card" role="region" aria-live="polite" aria-label="Selected item"><div class="pk-head"><span class="pk-tag"></span><span class="pk-sub"></span><button type="button" class="pk-x">Clear</button></div><div class="pk-body"></div></div>';
    sheet.querySelector('.drawing').after(card);
    card.querySelector('.pk-x').addEventListener('click', () => clear());
    function showCard(tag, sub, lead, row) {
      card.querySelector('.pk-tag').textContent = tag; card.querySelector('.pk-sub').textContent = sub || '';
      const body = card.querySelector('.pk-body'); body.textContent = '';
      if (lead) { const p = document.createElement('p'); p.className = 'pk-lead'; p.textContent = lead; body.appendChild(p); }
      if (row) {
        const heads = [...row.closest('table').querySelectorAll('thead th')].map(t => t.textContent.trim());
        const dl = document.createElement('dl'); dl.className = 'pk-dl';
        [...row.children].forEach((td, i) => { if (i < 2 || !td.textContent.trim()) return; const dt = document.createElement('dt'); dt.textContent = heads[i] || ''; const dd = document.createElement('dd'); dd.textContent = td.textContent.trim(); dl.append(dt, dd); });
        if (dl.children.length) body.appendChild(dl);
      }
      card.hidden = false;
      sel.textContent = `Selected: ${tag}`; sel.classList.add('on');
      const btn = document.createElement('button'); btn.type = 'button'; btn.textContent = 'Clear'; btn.addEventListener('click', clear); sel.appendChild(btn);
    }
    let on = null;
    function legs(el) { return (el && el.dataset.leg) ? el.dataset.leg.split(' ') : []; }
    function lightLegs(ids) {
      for (const el of svg.querySelectorAll('.sym[data-leg]')) el.classList.toggle('on-leg', legs(el).some(l => ids.includes(l)));
      for (const r of sheet.querySelectorAll('tr[data-id^="LEG:"]')) r.classList.toggle('on', ids.includes(r.dataset.id.slice(4)));
    }
    function clear() {
      if (on) { on.classList.remove('on'); on = null; }
      lightLegs([]);
      for (const r of sheet.querySelectorAll('tr.on')) r.classList.remove('on');
      sel.textContent = sel.dataset.hint; sel.classList.remove('on');
      card.hidden = true;
    }
    function pick(el, fromTable) {
      clear();
      if (!el) return;
      on = el; el.classList.add('on');
      const t = el.querySelector('title'), text = t ? t.textContent : el.dataset.id;
      const row = sheet.querySelector(`tr[data-id="${CSS.escape(el.dataset.id)}"]`);
      if (row) row.classList.add('on');
      // the card: the schedule row when there is one (its first two cells as the heading), else the drawing's note
      let tag = el.dataset.id, sub = '', lead = text;
      if (row) { tag = row.children[0].textContent.trim(); sub = row.children[1] ? row.children[1].textContent.trim() : ''; lead = ''; }
      else { const m = /^([^:—]{1,60}?)\s*[:—]\s*(.*)$/s.exec(text); if (m) { tag = m[1]; lead = m[2]; } }
      const lg = legs(el);
      if (lg.length) { lightLegs(lg); const n = svg.querySelectorAll('.sym.on-leg').length; lead = (lead ? lead + ' ' : '') + `Switch leg${lg.length > 1 ? 's' : ''} ${lg.join(', ')}: ${n} devices lit in blue.`; }
      showCard(tag, sub, lead, row);
      if (fromTable) reveal(el);
    }
    svg.addEventListener('click', e => { const g = e.target.closest('.sym, .tag'); if (g) pick(g, false); else clear(); });
    const subtabs = sheet.querySelector('.subtabs');
    if (subtabs) {
      subtabs.style.setProperty('--half', Math.ceil(subtabs.children.length / 2));   // phones: two rows, read left to right
      const names = {}; for (const r of sheet.querySelectorAll('tbody tr[data-id^="C"]')) names[r.dataset.id.slice(1)] = r.children[1].textContent + ' · ' + r.children[2].textContent;
      subtabs.addEventListener('click', e => {
        const b = e.target.closest('button[data-ckt]'); if (!b) return;
        const k = b.dataset.ckt;
        for (const o of subtabs.querySelectorAll('button')) o.setAttribute('aria-pressed', String(o === b));
        clear();
        if (k === 'all') { svg.removeAttribute('data-ckt-mode'); for (const el of svg.querySelectorAll('.show')) el.classList.remove('show'); $('ckt-name').textContent = 'All circuits. Pick a circuit sheet to see just its devices and the cable run from MP.'; return; }
        svg.setAttribute('data-ckt-mode', k);
        for (const el of svg.querySelectorAll('.sym, .wire')) {
          const on = k === 'data' ? (el.dataset.net === '1' || el.dataset.ckt === 'data' || el.dataset.ckt === 'panel') : (el.dataset.ckt === k || (el.classList.contains('sym') && el.dataset.ckt === 'panel'));
          el.classList.toggle('show', on);
        }
        $('ckt-name').textContent = k === 'data' ? 'E-1.D — Cat6 home runs to the media panel' : `${b.textContent.trim()} — ${names[k] || ''}`;
      });
    }
    for (const row of sheet.querySelectorAll('tbody tr[data-id]')) {
      const go = () => {
        if (row.dataset.id.startsWith('LEG:')) { clear(); const l = row.dataset.id.slice(4); lightLegs([l]); row.classList.add('on'); showCard(`Switch leg ${l}`, row.children[1].textContent.trim(), '', row); const first = svg.querySelector(`.sym[data-leg~="${CSS.escape(l)}"]`); if (first) reveal(first); return; }
        const el = svg.querySelector(`[data-id="${CSS.escape(row.dataset.id)}"]`); if (el) pick(el, true); else { clear(); row.classList.add('on'); showCard(row.children[0].textContent.trim(), row.children[1] ? row.children[1].textContent.trim() : '', 'Not drawn on the sheet; see the schedule.', row); } };
      row.addEventListener('click', go);
      row.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } });
    }
  }
})();
</script>
