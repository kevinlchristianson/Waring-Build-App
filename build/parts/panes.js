<script>
// ---------------------------------------------------------------- schedules: one table at a time, search, back-to-list
(function () {
  const NAMES = [[/drywall/i, 'Drywall'], [/dimensional lumber/i, 'Lumber'], [/circuit/i, 'Circuits'], [/switch/i, 'Switches'], [/device/i, 'Devices'], [/bill of/i, 'Materials'], [/wall sched/i, 'Walls'], [/door/i, 'Doors'], [/blocking/i, 'Blocking'], [/fixture/i, 'Fixtures'], [/vent/i, 'Vents'], [/register/i, 'Registers'], [/trunk/i, 'Trunks'], [/note/i, 'Notes'], [/open/i, 'Open items']];
  const short = t => { for (const [re, n] of NAMES) if (re.test(t)) return n; return t.length > 18 ? t.slice(0, 17) + '…' : t; };

  for (const sheet of document.querySelectorAll('.sheet2d')) {
    const below = sheet.querySelector('.below'), tools = sheet.querySelector('.tools');
    if (!below) continue;
    const key = sheet.id;
    const panes = [];
    const mk = title => { const d = document.createElement('div'); d.className = 'pane'; d.dataset.title = title; panes.push(d); return d; };

    for (const sec of [...below.querySelectorAll(':scope > section')]) {
      const h3s = [...sec.querySelectorAll(':scope > h3')];
      const kids = [...sec.children];
      if (sec.classList.contains('wide') && h3s.length) {
        let cur = null;
        for (const k of kids) {
          if (k.tagName === 'H3') cur = mk(short(k.textContent));
          if (!cur) cur = mk(short(h3s[0].textContent));
          cur.appendChild(k);
        }
      } else {
        const h = h3s.length === 1 ? h3s[0] : sec.querySelector(':scope > h2');
        const cur = mk(short(h ? h.textContent : 'Info'));
        for (const k of kids) cur.appendChild(k);
      }
      sec.remove();
    }
    if (!panes.length) continue;

    // card labels + search
    for (const pane of panes) {
      for (const table of pane.querySelectorAll('table')) {
        const heads = [...table.querySelectorAll('thead th')].map(t => t.textContent.trim());
        for (const tr of table.querySelectorAll('tbody tr')) [...tr.children].forEach((td, i) => td.dataset.label = heads[i] || '');
      }
      const rows = [...pane.querySelectorAll('tbody tr')];
      pane.dataset.count = rows.length;
      if (rows.length > 6) {
        const box = document.createElement('div'); box.className = 'psearch';
        const inp = document.createElement('input'); inp.type = 'search'; inp.placeholder = 'Search ' + pane.dataset.title.toLowerCase() + '…';
        inp.setAttribute('aria-label', 'Search ' + pane.dataset.title); inp.autocomplete = 'off'; inp.autocapitalize = 'off'; inp.setAttribute('enterkeyhint', 'search');
        const cnt = document.createElement('span'); cnt.className = 'cnt'; cnt.textContent = rows.length + '';
        let pre = '';
        const apply = () => {
          const q = inp.value.toLowerCase().split(/\s+/).filter(Boolean); let n = 0;
          for (const r of rows) { const t = r.textContent.toLowerCase(); const ok = (!pre || r.dataset.pre === pre) && q.every(w => t.includes(w)); r.hidden = !ok; if (ok) n++; }
          cnt.textContent = (q.length || pre) ? n + ' of ' + rows.length : rows.length + '';
        };
        inp.addEventListener('input', apply);
        // big tables keyed by tag letters (R1, L7, S3...): add one-tap filters by type
        const m = rows.map(r => /^([A-Z]+)\d/.exec(r.children[0].textContent.trim()));
        if (rows.length > 40 && m.every(Boolean)) {
          const TYPES = { R: 'Receptacles', S: 'Switches', L: 'Lights', A: 'Alarms', X: 'Panels' };
          rows.forEach((r, i) => r.dataset.pre = m[i][1]);
          const letters = [...new Set(m.map(x => x[1]))].sort();
          const chips = document.createElement('div'); chips.className = 'panebar'; chips.style.position = 'static'; chips.style.margin = '0 0 8px'; chips.style.padding = '0'; chips.style.border = '0'; chips.style.background = 'none';
          const cb = [];
          for (const l of ['', ...letters]) {
            const b = document.createElement('button'); b.type = 'button'; b.textContent = l ? (TYPES[l] || l) : 'All'; b.setAttribute('aria-pressed', String(l === ''));
            b.addEventListener('click', () => { pre = l; cb.forEach(x => x.setAttribute('aria-pressed', String(x === b))); apply(); });
            cb.push(b); chips.appendChild(b);
          }
          pane.chips = chips;
        }
        box.append(inp, cnt);
        pane.querySelector('.tbl').before(box);
        if (pane.chips) box.before(pane.chips);
      }
    }

    // button bar
    const bar = document.createElement('div'); bar.className = 'panebar'; bar.setAttribute('role', 'group'); bar.setAttribute('aria-label', 'Sections');
    const wrap = document.createElement('div'); wrap.className = 'panes';
    const btns = panes.map((pane, i) => {
      const b = document.createElement('button'); b.type = 'button'; b.textContent = pane.dataset.title;
      if (+pane.dataset.count) { const n = document.createElement('span'); n.className = 'n'; n.textContent = pane.dataset.count; b.appendChild(n); }
      b.addEventListener('click', () => select(i, true));
      bar.appendChild(b); wrap.appendChild(pane); return b;
    });
    below.append(bar, wrap);

    const header = document.querySelector('header.bar');
    const tools_h = () => { const th = tools ? tools.offsetHeight : 0; sheet.style.setProperty('--tools-h', th + 'px'); sheet.style.setProperty('--chrome-h', (th + (header ? header.offsetHeight : 0)) + 'px'); };
    tools_h(); addEventListener('resize', tools_h);
    if (window.ResizeObserver) { const ro = new ResizeObserver(tools_h); if (tools) ro.observe(tools); if (header) ro.observe(header); }

    function select(i, scroll) {
      panes.forEach((p, j) => { p.hidden = j !== i; btns[j].setAttribute('aria-pressed', String(j === i)); });
      try { localStorage.setItem('wb-pane-' + key, panes[i].dataset.title); } catch (e) { /* per-viewer convenience */ }
      { const bl = btns[i].offsetLeft, bw = btns[i].offsetWidth; if (bl < bar.scrollLeft || bl + bw > bar.scrollLeft + bar.clientWidth) bar.scrollTo({ left: bl - (bar.clientWidth - bw) / 2, behavior: scroll ? 'smooth' : 'auto' }); }
      if (scroll) {
        const th = tools ? tools.offsetHeight : 0;
        const barTop = bar.getBoundingClientRect().top - sheet.getBoundingClientRect().top;
        if (barTop <= th + 2) sheet.scrollTo({ top: sheet.scrollTop + barTop - th, behavior: 'auto' });
      }
    }
    let first = panes.findIndex(p => +p.dataset.count > 0); if (first < 0) first = 0;
    try { const saved = localStorage.getItem('wb-pane-' + key); const j = panes.findIndex(p => p.dataset.title === saved); if (j >= 0) first = j; } catch (e) { /* ignore */ }
    select(first, false);

    // after tapping a row the drawing scrolls into view; give a one-tap way back to the list
    const back = document.createElement('button'); back.type = 'button'; back.className = 'backlist'; back.textContent = '↩ Back to list'; back.hidden = true;
    sheet.appendChild(back);
    let savedRow = null, savedTop = 0, away = false;
    sheet.addEventListener('click', e => { const tr = e.target.closest('tbody tr[data-id]'); if (tr) { savedRow = tr; savedTop = tr.getBoundingClientRect().top; away = false; } }, true);
    sheet.addEventListener('scroll', () => {
      if (!savedRow) { back.hidden = true; return; }
      const d = savedRow.getBoundingClientRect().top - savedTop; // how far the row has moved down the screen
      if (d > 150) away = true;
      if (away && d < 20) { savedRow = null; away = false; }
      back.hidden = !savedRow || !away;
    }, { passive: true });
    back.addEventListener('click', () => { if (savedRow) sheet.scrollTo({ top: sheet.scrollTop + savedRow.getBoundingClientRect().top - savedTop, behavior: 'smooth' }); back.hidden = true; savedRow = null; away = false; });
  }
})();
</script>
