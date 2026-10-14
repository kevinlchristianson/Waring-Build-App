<script src="chat-config.js"></script>
<script>
// ---------------------------------------------------------------- one Firebase connection (anonymous sign-in) shared by the chat and the open items
(function () {
  const cfg = window.ZR_CHAT || {};
  if (!cfg.firebase || !cfg.firebase.projectId) return;
  const V = cfg.sdk || '12.18.0', base = `https://www.gstatic.com/firebasejs/${V}/`;
  window.zrFirebase = Promise.all([import(base + 'firebase-app.js'), import(base + 'firebase-auth.js'), import(base + 'firebase-firestore.js')])
    .then(async ([A, U, F]) => {
      const app = A.initializeApp(cfg.firebase, 'zr-chat');
      const auth = U.getAuth(app), db = F.getFirestore(app);
      const cred = await U.signInAnonymously(auth);
      return { F, db, uid: cred.user.uid, room: cfg.room || 'waring-crew' };
    });
})();
</script>
<script>
// ---------------------------------------------------------------- crew chat: one room for everyone on the job, kept in Firebase (see CHAT-SETUP.md)
(function () {
  const cfg = window.ZR_CHAT || {};
  const root = document.getElementById('chat'), panel = document.getElementById('sheet-chat'), tab = document.getElementById('tab-chat');
  if (!root) return;
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  const store = { get: k => { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* per-viewer convenience */ } } };
  const visible = () => !panel.hidden && document.visibilityState === 'visible';

  if (!cfg.firebase || !cfg.firebase.projectId) {
    const n = el('div', 'chat-note');
    n.append(el('h2', null, 'Crew chat'), el('p', null, 'Chat isn’t switched on yet. Once the owner connects it, questions posted here go to everyone on the job.'));
    root.append(n);
    return;
  }

  // the thing last picked on a sheet, so a question can say what it's about
  let lastPick = null;
  const sheetNo = node => { const s = node.closest('.sheet'); const t = s && document.getElementById('tab-' + s.id.slice(6)); return t ? t.querySelector('.no').textContent : ''; };
  const watchPick = (node, isOn) => new MutationObserver(() => {
    if (isOn()) lastPick = (sheetNo(node) + ' · ' + node.textContent.trim()).slice(0, 120);
    else if (lastPick && lastPick.startsWith(sheetNo(node) + ' ')) lastPick = null;
  }).observe(node, { childList: true, characterData: true, subtree: true, attributes: true });
  for (const s of document.querySelectorAll('.tools .sel')) watchPick(s, () => s.classList.contains('on'));
  { const t = document.getElementById('seltext'), box = document.getElementById('sel'); if (t && box) watchPick(t, () => !box.hidden && t.textContent.trim() !== ''); }

  // who's talking
  let me = { name: store.get('zr-chat-name') || '', trade: store.get('zr-chat-trade') || '' };
  const who = el('div', 'chat-who'), log = el('div', 'chat-log'), form = el('form', 'chat-form');
  log.setAttribute('aria-live', 'polite'); log.setAttribute('aria-label', 'Messages');
  const status = el('span', 'st', 'connecting…');
  root.append(who, log, form);

  function drawWho() {
    who.replaceChildren();
    if (!me.name) { who.append(el('span', null, 'Everyone on the job sees this room.'), status); return; }
    const b = el('b', null, me.name + (me.trade ? ' · ' + me.trade : ''));
    const ch = el('button', 'chat-btn', 'Change'); ch.type = 'button'; ch.addEventListener('click', () => { me.name = ''; drawWho(); drawForm(); });
    who.append(el('span', null, 'You’re '), b, ch, status);
  }

  let send = null; // set once signed in
  function drawForm() {
    form.replaceChildren();
    if (!me.name) {
      const n = el('input'); n.placeholder = 'Your name'; n.required = true; n.maxLength = 40; n.autocomplete = 'name'; n.value = store.get('zr-chat-name') || ''; n.setAttribute('aria-label', 'Your name');
      const t = el('input'); t.placeholder = 'Trade (optional)'; t.maxLength = 40; t.value = store.get('zr-chat-trade') || ''; t.setAttribute('aria-label', 'Trade or company');
      const go = el('button', 'chat-btn go', 'Join'); go.type = 'submit';
      const line = el('div', 'line'); line.append(n, t);
      form.append(el('label', null, 'Tell the crew who you are'), line, go);
      form.onsubmit = e => { e.preventDefault(); me = { name: n.value.trim().slice(0, 40), trade: t.value.trim().slice(0, 40) }; if (!me.name) return; store.set('zr-chat-name', me.name); store.set('zr-chat-trade', me.trade); drawWho(); drawForm(); };
      return;
    }
    const re = el('label', 'chat-re'); const reBox = el('input'); reBox.type = 'checkbox'; reBox.checked = true; const reTxt = el('span');
    re.append(reBox, reTxt); re.hidden = true;
    const refreshRe = () => { re.hidden = !lastPick; reTxt.textContent = lastPick ? 'About ' + lastPick : ''; reBox.checked = true; };
    form.refreshRe = refreshRe; refreshRe();
    const ta = el('textarea'); ta.rows = 1; ta.maxLength = 2000; ta.placeholder = 'Ask the crew a question…'; ta.setAttribute('aria-label', 'Message'); ta.setAttribute('enterkeyhint', 'send');
    const fit = () => { ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight + 2, 140) + 'px'; };
    ta.addEventListener('input', fit);
    // Enter sends on a keyboard; Shift+Enter (or the phone's return key with enterkeyhint) makes a new line
    ta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey && !e.isComposing && matchMedia('(pointer: fine)').matches) { e.preventDefault(); form.requestSubmit(); } });
    const go = el('button', 'chat-btn go', 'Send'); go.type = 'submit'; go.disabled = !send;
    form.goBtn = go;
    const line = el('div', 'line'); line.append(ta, go);
    form.append(re, line);
    form.onsubmit = async e => {
      e.preventDefault();
      const text = ta.value.trim(); if (!text || !send) return;
      const msg = { name: me.name, text: text.slice(0, 2000) };
      if (me.trade) msg.trade = me.trade;
      if (!re.hidden && reBox.checked && lastPick) msg.sheet = lastPick;
      ta.value = ''; fit(); lastPick = null; refreshRe();
      try { await send(msg); } catch (err) { ta.value = text; fit(); status.textContent = 'not sent: ' + (err.code || err.message || 'error'); }
    };
  }
  drawWho(); drawForm();
  new MutationObserver(() => { if (!panel.hidden) { if (form.refreshRe) form.refreshRe(); seen(); scrollEnd(); } }).observe(panel, { attributes: true, attributeFilter: ['hidden'] });

  // unread count on the tab, from the last message seen on this device
  const badge = el('span', 'badge'); badge.hidden = true; tab.appendChild(badge);
  let msgs = [], myUid = null;
  const lastAt = () => msgs.length ? msgs[msgs.length - 1].at : 0;
  // a new message from someone else covers the app until this phone opens the chat; after that every tab works again
  const alertBox = el('div', 'chat-alert'); alertBox.hidden = true;
  alertBox.setAttribute('role', 'alertdialog'); alertBox.setAttribute('aria-modal', 'true'); alertBox.setAttribute('aria-labelledby', 'chat-alert-h');
  const alertCard = el('div', 'box'), alertH = el('h2', null, 'New message'), alertFrom = el('div', 'from'), alertTxt = el('div', 'txt');
  const alertGo = el('button', null, 'Open chat'); alertGo.type = 'button'; alertH.id = 'chat-alert-h';
  alertGo.addEventListener('click', () => tab.click());
  alertCard.append(alertH, alertFrom, alertTxt, alertGo); alertBox.append(alertCard); document.body.append(alertBox);
  function seen() { if (visible() && msgs.length) { store.set('zr-chat-seen-' + cfg.room, String(lastAt())); badge.hidden = true; } if (!panel.hidden) alertBox.hidden = true; }
  function countUnread() {
    const since = +(store.get('zr-chat-seen-' + cfg.room) || 0);
    const unread = msgs.filter(m => m.at > since && m.uid !== myUid && !m.pending), n = unread.length;
    badge.textContent = n > 99 ? '99+' : String(n); badge.hidden = !n || visible();
    tab.setAttribute('aria-label', 'Chat' + (n ? `, ${n} unread` : ''));
    if (n && panel.hidden) {
      const last = unread[n - 1], wasHidden = alertBox.hidden;
      alertH.textContent = n > 1 ? `${n} new messages` : 'New message';
      alertFrom.textContent = (n > 1 ? 'Latest from ' : 'From ') + (last.name || '?') + (last.trade ? ' · ' + last.trade : '');
      alertTxt.textContent = last.text.length > 280 ? last.text.slice(0, 280) + '…' : last.text;
      alertBox.hidden = false;
      if (wasHidden) alertGo.focus();
    } else alertBox.hidden = true;
  }
  document.addEventListener('visibilitychange', () => { seen(); countUnread(); });

  const nearEnd = () => log.scrollHeight - log.scrollTop - log.clientHeight < 80;
  const scrollEnd = () => { log.scrollTop = log.scrollHeight; };
  const dayFmt = new Intl.DateTimeFormat(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  const timeFmt = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' });
  let remove = null;
  function draw() {
    const stick = nearEnd() || !log.childElementCount;
    log.replaceChildren();
    if (!msgs.length) log.append(el('p', 'chat-empty', 'No messages yet. Ask the first question: everyone on the job will see it here.'));
    let day = '';
    for (const m of msgs) {
      const d = new Date(m.at || Date.now()), ds = dayFmt.format(d);
      if (ds !== day) { day = ds; log.append(el('div', 'chat-day', ds)); }
      const box = el('div', 'msg' + (m.uid === myUid ? ' mine' : '') + (m.pending ? ' pending' : ''));
      const meta = el('div', 'meta'); meta.append(el('b', null, m.name || '?'));
      if (m.trade) meta.append(el('span', null, m.trade));
      const t = el('time', null, m.pending ? 'sending…' : timeFmt.format(d)); t.dateTime = d.toISOString(); meta.append(t);
      box.append(meta);
      if (m.sheet) box.append(el('div', 're', m.sheet));
      box.append(el('div', 'txt', m.text));
      if (m.uid === myUid && remove && !m.pending) { const x = el('button', 'del', 'Delete'); x.type = 'button'; x.addEventListener('click', () => { if (confirm('Delete this message for everyone?')) remove(m.id).catch(() => {}); }); box.append(x); }
      log.append(box);
    }
    if (stick) scrollEnd();
    seen(); countUnread();
  }

  window.zrFirebase
    .then(({ F, db, uid, room }) => {
      myUid = uid;
      const col = F.collection(db, 'rooms', room, 'messages');
      send = msg => F.addDoc(col, { ...msg, uid: myUid, at: F.serverTimestamp() });
      remove = id => F.deleteDoc(F.doc(col, id));
      if (form.goBtn) form.goBtn.disabled = false;
      status.textContent = '';
      F.onSnapshot(F.query(col, F.orderBy('at', 'desc'), F.limit(300)), { includeMetadataChanges: true }, snap => {
        msgs = snap.docs.map(d => { const x = d.data({ serverTimestamps: 'estimate' }); return { id: d.id, name: x.name, trade: x.trade, text: x.text, sheet: x.sheet, uid: x.uid, at: x.at ? x.at.toMillis() : Date.now(), pending: d.metadata.hasPendingWrites }; }).reverse();
        status.textContent = snap.metadata.fromCache ? 'offline' : '';
        draw();
      }, err => { status.textContent = 'can’t load: ' + (err.code || 'error'); });
    })
    .catch(err => { status.textContent = navigator.onLine ? 'can’t connect: ' + (err.code || err.message || 'error') : 'offline'; });
})();
</script>

<script>
// ---------------------------------------------------------------- open items: tick off to resolve (struck through for everyone), add new ones per trade,
// or comment on a picked item from its card (the comment is an open item tied to that item); kept in Firebase next to the chat
(function () {
  const TRADES = { s1: 'Framing', e1: 'Electrical', p1: 'Plumbing', m1: 'HVAC' };
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  const store = { get: k => { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* per-viewer convenience */ } } };
  // a drawn item is keyed by its sheet and its wording, so it stays resolved until the wording changes
  const hash = t => { let h = 5381; for (let i = 0; i < t.length; i++) h = (h * 33 ^ t.charCodeAt(i)) >>> 0; return h.toString(36); };
  const dateFmt = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' });
  const when = ms => ms ? dateFmt.format(new Date(ms)) : '';

  const me = () => store.get('zr-chat-name') || '';
  let fb = null, items = [], done = new Map(), hidden = new Set(), state = 'connecting…';
  // owners (chat-config.js) can delete anyone's item, and hide the items drawn on the sheets
  const owner = () => !!fb && ((window.ZR_CHAT || {}).owners || []).includes(fb.uid);
  const lists = [];
  let L3 = null;   // the 3D view's comment popup, set up below

  for (const sheet of document.querySelectorAll('.sheet2d')) {
    const ul = sheet.querySelector('.open ul'); if (!ul) continue;
    const key = sheet.id.slice(6), trade = TRADES[key] || '';
    const pane = ul.closest('.pane'), wrap = pane && pane.parentElement, bar = wrap && wrap.previousElementSibling;
    const btn = bar && bar.children[[...wrap.children].indexOf(pane)];
    const drawn = [...ul.children].map(li => { const span = el('span', 'oi-txt'); span.append(...li.childNodes); return { id: 'b-' + key + '-' + hash(span.textContent.trim()), body: span }; });
    ul.classList.add('oi-list');
    const st = el('p', 'oi-st');
    const form = el('form', 'oi-add');
    ul.after(st, form);
    const L = { key, trade, ul, drawn, st, form, btn };
    // the picked item's card gets its own open items and a comment box
    const pk = sheet.querySelector('.picked .pk-card'), tag = pk && pk.querySelector('.pk-tag');
    if (tag) {
      L.card = { box: el('div', 'pk-oi'), h: el('div', 'pk-oi-h'), ul: el('ul', 'oi-list'), st: el('p', 'oi-st'), form: el('form', 'oi-add'), tag };
      L.card.box.append(L.card.h, L.card.ul, L.card.st, L.card.form); pk.append(L.card.box);
      new MutationObserver(() => drawCard(L)).observe(tag, { childList: true, characterData: true, subtree: true });
    }
    lists.push(L); drawForms(L);
  }
  if (!lists.length) return;
  // the 3D view: the item ribbon's Comment button pops up the picked item's open items and a comment box
  { const sel = document.getElementById('sel'), ref = document.getElementById('selref'), pop = document.getElementById('selpop'), btn = document.getElementById('selcomment');
    if (sel && ref && pop && btn) {
      L3 = { get key() { return sel.dataset.sheet || 's1'; }, get trade() { return TRADES[this.key] || ''; }, btn, st: el('p', 'oi-st'),
        card: { box: el('div', 'pk-oi'), h: el('div', 'pk-oi-h'), ul: el('ul', 'oi-list'), st: el('p', 'oi-st'), form: el('form', 'oi-add'), tag: ref } };
      const head = el('div', 'pop-h'), x = el('button', 'pop-x', 'Close'); x.type = 'button';
      head.append(L3.card.h, x); L3.card.box.append(head, L3.card.ul, L3.card.st, L3.card.form); pop.append(L3.card.box);
      const show = on => { pop.hidden = !on; btn.setAttribute('aria-expanded', String(on)); if (on) { drawForms(L3); const ta = pop.querySelector('textarea, input'); if (ta && matchMedia('(hover: hover)').matches) ta.focus(); } };
      btn.addEventListener('click', () => show(pop.hidden)); x.addEventListener('click', () => show(false));
      new MutationObserver(() => { drawCard(L3); if (!pop.hidden) drawForms(L3); }).observe(ref, { childList: true, characterData: true, subtree: true });
      drawForms(L3);
    }
  }
  const all = () => L3 ? [...lists, L3] : lists;

  function row(L, id, body, meta, mine, itemId) {
    const d = done.get(id);
    const li = el('li', 'oi' + (d ? ' done' : ''));
    const box = el('input'); box.type = 'checkbox'; box.checked = !!d; box.disabled = !fb;
    box.setAttribute('aria-label', d ? 'Resolved; untick to reopen' : 'Mark resolved');
    box.addEventListener('change', () => toggle(L, id, box));
    const main = el('div', 'oi-main'); main.append(body);
    const m = el('div', 'oi-meta');
    if (meta) m.append(el('span', null, meta));
    if (d) m.append(el('span', 'oi-res', 'Resolved by ' + (d.name || '?') + (d.at ? ' · ' + when(d.at) : '')));
    if (mine) { const x = el('button', 'oi-del', 'Delete'); x.type = 'button'; x.addEventListener('click', () => { if (!confirm('Delete this open item for everyone?')) return; const { F, db, room } = fb; (itemId ? F.deleteDoc(F.doc(db, 'rooms', room, 'items', itemId)) : F.setDoc(F.doc(db, 'rooms', room, 'hidden', id), { uid: fb.uid, at: F.serverTimestamp() })).then(() => d && F.deleteDoc(F.doc(db, 'rooms', room, 'done', id))).catch(err => say(L, 'not deleted: ' + (err.code || 'error'))); }); m.append(x); }
    if (m.childElementCount) main.append(m);
    li.append(box, main);
    return li;
  }

  function draw() {
    for (const L of lists) {
      L.ul.replaceChildren();
      let open = 0;
      for (const b of L.drawn) { if (hidden.has(b.id)) continue; L.ul.append(row(L, b.id, b.body.cloneNode(true), '', owner())); if (!done.has(b.id)) open++; }
      for (const it of items) {
        if (it.sheet !== L.key) continue;
        const id = 'i-' + it.id;
        L.ul.append(row(L, id, el('span', 'oi-txt', it.text), (it.ref ? 'On ' + it.ref + ' · ' : '') + 'Added by ' + (it.name || '?') + (it.trade ? ' (' + it.trade + ')' : '') + ' · ' + when(it.at), fb && (it.uid === fb.uid || owner()), it.id));
        if (!done.has(id)) open++;
      }
      if (L.btn) { let n = L.btn.querySelector('.n'); if (!n) { n = el('span', 'n'); L.btn.appendChild(n); } n.textContent = open; L.btn.title = open + ' open'; }
      if (!L.err) L.st.textContent = state;
      drawCard(L);
    }
    if (L3) drawCard(L3);
  }
  function refOf(L) { return L.card.tag.textContent.trim().slice(0, 60); }
  function drawCard(L) {
    if (!L.card) return;
    const ref = refOf(L), mine = items.filter(it => it.sheet === L.key && it.ref === ref);
    L.card.ul.replaceChildren();
    for (const it of mine) L.card.ul.append(row(L, 'i-' + it.id, el('span', 'oi-txt', it.text), 'Added by ' + (it.name || '?') + (it.trade ? ' (' + it.trade + ')' : '') + ' · ' + when(it.at), fb && (it.uid === fb.uid || owner()), it.id));
    const open = mine.filter(it => !done.has('i-' + it.id)).length;
    L.card.h.textContent = mine.length ? `Open items on ${ref}: ${open} open` : `Comments on ${ref} become open items for ${L.trade || 'this sheet'} until resolved.`;
    if (L === L3) L.btn.textContent = open ? `Comments (${open})` : 'Comment';
    const ta = L.card.form.querySelector('textarea'); if (ta && L !== L3) ta.placeholder = 'Comment on ' + ref + '…';
    if (!L.err) L.card.st.textContent = state;
  }
  function sts(L) { return L.card ? [L.st, L.card.st] : [L.st]; }
  function say(L, msg) { L.err = true; sts(L).forEach(x => x.textContent = msg); setTimeout(() => { L.err = false; sts(L).forEach(x => x.textContent = state); }, 6000); }

  function needName(L) {
    if (me()) return false;
    const forms = [L.card && !L.card.box.closest('[hidden]') && L.card.form, L.form].filter(Boolean);
    const n = forms.map(f => f.querySelector('input[name=who]')).find(Boolean);
    if (n) { n.focus(); say(L, 'Put your name in first, so the crew knows who resolved it.'); }
    return true;
  }

  async function toggle(L, id, box) {
    if (!fb || needName(L)) { box.checked = !box.checked; return; }
    const { F, db, room, uid } = fb, ref = F.doc(db, 'rooms', room, 'done', id);
    try {
      if (box.checked) await F.setDoc(ref, { name: me(), uid, at: F.serverTimestamp() });
      else await F.deleteDoc(ref);
    } catch (err) { box.checked = !box.checked; say(L, 'not saved: ' + (err.code || err.message || 'error')); }
  }

  function drawForms(L) { if (L.form) drawForm(L, L.form, false); if (L.card) drawForm(L, L.card.form, true); }
  function drawForm(L, f, onCard) {
    f.replaceChildren();
    if (!me()) {
      const n = el('input'); n.name = 'who'; n.placeholder = 'Your name'; n.maxLength = 40; n.autocomplete = 'name'; n.setAttribute('aria-label', 'Your name');
      const ok = el('button', 'chat-btn', 'Save'); ok.type = 'button';
      ok.addEventListener('click', () => { const v = n.value.trim().slice(0, 40); if (!v) return n.focus(); store.set('zr-chat-name', v); if (!store.get('zr-chat-trade') && L.trade) store.set('zr-chat-trade', L.trade); all().forEach(x => { x.err = false; drawForms(x); }); draw(); });
      const line = el('div', 'line'); line.append(n, ok);
      f.append(el('label', null, 'Your name, to resolve or add items (the chat uses it too)'), line);
      return;
    }
    const ta = el('textarea'); ta.rows = 1; ta.maxLength = 1000; ta.placeholder = onCard ? (L === L3 ? 'Add a comment…' : 'Comment on ' + refOf(L) + '…') : 'Add an open item for ' + (L.trade || 'this sheet') + '…'; ta.setAttribute('aria-label', onCard ? 'Comment on this item (adds an open item)' : 'New open item');
    const fit = () => { ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight + 2, 140) + 'px'; };
    ta.addEventListener('input', fit);
    const go = el('button', 'chat-btn go', onCard ? 'Post' : 'Add'); go.type = 'submit';
    const line = el('div', 'line'); line.append(ta, go);
    f.append(line);
    f.onsubmit = async e => {
      e.preventDefault();
      const text = ta.value.trim(); if (!text) return;
      if (!fb) return say(L, 'not connected yet; try again in a moment');
      const { F, db, room, uid } = fb, it = { sheet: L.key, text: text.slice(0, 1000), name: me(), uid, at: F.serverTimestamp() };
      const t = store.get('zr-chat-trade'); if (t) it.trade = t.slice(0, 40);
      if (onCard && refOf(L)) it.ref = refOf(L);
      ta.value = ''; fit();
      try { await F.addDoc(F.collection(db, 'rooms', room, 'items'), it); } catch (err) { ta.value = text; fit(); say(L, 'not added: ' + (err.code || err.message || 'error')); }
    };
  }

  draw();
  if (!window.zrFirebase) { state = 'Resolving and adding items needs the crew chat switched on (CHAT-SETUP.md).'; draw(); return; }
  window.zrFirebase.then(conn => {
    fb = conn; state = ''; draw();
    const { F, db, room } = conn;
    const onErr = err => { state = 'can’t load: ' + (err.code || 'error'); draw(); };
    F.onSnapshot(F.query(F.collection(db, 'rooms', room, 'items'), F.orderBy('at'), F.limit(500)), snap => {
      items = snap.docs.map(d => { const x = d.data({ serverTimestamps: 'estimate' }); return { id: d.id, sheet: x.sheet, ref: x.ref, text: x.text, name: x.name, trade: x.trade, uid: x.uid, at: x.at ? x.at.toMillis() : Date.now() }; });
      state = snap.metadata.fromCache ? 'offline: showing the last copy' : ''; draw();
    }, onErr);
    F.onSnapshot(F.query(F.collection(db, 'rooms', room, 'done'), F.limit(2000)), snap => {
      done = new Map(snap.docs.map(d => { const x = d.data({ serverTimestamps: 'estimate' }); return [d.id, { name: x.name, at: x.at ? x.at.toMillis() : Date.now() }]; }));
      draw();
    }, onErr);
    F.onSnapshot(F.query(F.collection(db, 'rooms', room, 'hidden'), F.limit(2000)), snap => { hidden = new Set(snap.docs.map(d => d.id)); draw(); }, () => {});   // quiet until the rules with `hidden` are published
  }).catch(err => { state = navigator.onLine ? 'can’t connect: ' + (err.code || err.message || 'error') : 'offline'; draw(); });
})();
</script>

<script>
if ('serviceWorker' in navigator) {
  // A home-screen app on a phone resumes without reloading, so check for a new version
  // whenever it comes back to the foreground, and reload once the new copy takes over.
  const hadController = !!navigator.serviceWorker.controller;
  let reloaded = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!hadController || reloaded) return;
    reloaded = true;
    location.reload();
  });
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js', { updateViaCache: 'none' }).then(reg => {
      document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') reg.update().catch(() => {}); });
    }).catch(() => {});
  });
}
</script>
