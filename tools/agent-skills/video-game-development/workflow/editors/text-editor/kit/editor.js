// Text editor kit: the editor page. Generic: a project gives it its registry (every text, see SKILL.md) and an
// adapter (its colours' names, icons, the editing surface's look and a live preview drawn by the project's own code).
//
//   import { boot } from './kit/editor.js';
//   boot({ mount, registryUrl, adapter, collection: 'edits', storageKey });
//
// The owner picks a text, edits it as rich text (bold, italic, underline, a colour, an icon, a line break), sees the
// project's real preview, and can leave a note for Claude. Each edit is saved in the artifact's db (collection
// `edits`, one document per text id: { markup, note, from, title, updatedAt }). Claude applies them before every
// build of the program (apply-edits.mjs, then the registry rebuilt); an edit equal to the text the program shows is
// done and disappears. Without a db (a local copy, signed out) the edits stay in this browser and a "Copy the edits"
// button (shown only then) hands them over.
import * as M from './markup.js';

const CSS_URL = new URL('./editor.css', import.meta.url);

// ---------- Small DOM helpers ----------
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs ?? {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else if (k === 'text') el.textContent = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat()) if (c !== null && c !== undefined && c !== false) el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return el;
}
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const debounce = (fn, ms) => { let t = 0; const d = (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; d.flush = () => { clearTimeout(t); fn(); }; return d; };
const lum = ([r, g, b]) => (0.299 * r + 0.587 * g + 0.114 * b) / 255;
const cssRgb = (c) => `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
const parseCssColour = (s) => {
  const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)/.exec(s || '');
  if (m) return [+m[1], +m[2], +m[3]];
  const x = /^#([0-9a-f]{6})$/i.exec(s || '');
  return x ? [0, 2, 4].map((k) => parseInt(x[1].slice(k, k + 2), 16)) : null;
};
const hex = (c) => '#' + c.map((v) => v.toString(16).padStart(2, '0')).join('');
const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private window: nothing kept */ } },
};

export async function boot({ mount, registryUrl, adapter = {}, collection = 'edits', storageKey = 'text-editor' }) {
  try { const css = await (await fetch(CSS_URL)).text(); document.head.append(h('style', { text: css })); } catch { /* unstyled */ }
  mount.classList.add('tx');
  mount.replaceChildren(h('p', { class: 'tx-loading', text: 'Loading the texts…' }));
  let reg;
  try { const r = await fetch(registryUrl); if (!r.ok) throw new Error(`${r.status}`); reg = await r.json(); } catch (err) {
    mount.replaceChildren(h('p', { class: 'tx-error', text: `The list of texts did not load (${err.message}). Reload the page.` }));
    return;
  }
  const palette = reg.markup?.palette ?? {}, icons = reg.markup?.icons ?? [];
  const mopts = { icons, palette };
  const norm = (s) => M.normalise(s, mopts);
  const byId = new Map(reg.entries.map((e) => [e.id, e]));
  const groupOf = new Map(reg.groups.map((g) => [g.id, g]));
  const S = { edits: {}, wrote: {}, localAt: 0, cur: null, model: [], hist: [], fut: [], lastSel: null, q: '', group: '', show: 'all', mode: 'connecting', tray: null, composing: false, navAt: 0 };
  const prefs = store.get(`${storageKey}:prefs`) ?? {};
  Object.assign(S, { group: prefs.group ?? '', show: prefs.show ?? 'all' });

  // The adapter's art (icons, preview); a failure leaves the editor working without them.
  let artReady = false;
  try { await adapter.init?.(); artReady = true; } catch (err) { console.warn('preview unavailable:', err); }
  const iconUrl = (n) => (artReady ? adapter.iconUrl?.(n) : null) ?? null;
  const colourName = (k) => adapter.colourNames?.[k] ?? k;

  // ---------- Entry state ----------
  const editOf = (id) => S.edits[id];
  const pending = (e) => { const d = editOf(e.id); return !!d && typeof d.markup === 'string' && norm(d.markup) !== norm(e.text); };
  const shown = (e) => (pending(e) ? editOf(e.id).markup : e.text);
  const badges = (e) => {
    const out = [];
    if (pending(e)) out.push(['wait', 'Next build']);
    else if (e.text !== e.base) out.push(['done', 'Edited']);
    if (editOf(e.id)?.note) out.push(['note', 'Note']);
    out.push(e.live ? ['live', 'In the game'] : ['later', 'Not live yet']);
    return out;
  };

  // ---------- Layout ----------
  const status = h('span', { class: 'tx-status', role: 'status', 'aria-live': 'polite' });
  const counts = h('span', { class: 'tx-counts' });
  const copyBtn = h('button', { type: 'button', class: 'tx-tool', hidden: true, onclick: () => copyForClaude() }, 'Copy the edits');
  const header = h('header', { class: 'tx-head' },
    h('div', { class: 'tx-titles' }, h('h1', { text: `${reg.project} Texts` }), h('p', { class: 'tx-sub' }, counts), h('p', { class: 'tx-sub' }, status)),
    h('div', { class: 'tx-head-actions' }, copyBtn));
  const search = h('input', { id: 'tx-search', type: 'search', placeholder: 'Search the texts', 'aria-label': 'Search the texts', autocomplete: 'off',
    oninput: (e) => { S.q = e.target.value; renderList(); } });
  const groupSel = h('select', { id: 'tx-group', 'aria-label': 'Group', onchange: (e) => { S.group = e.target.value; savePrefs(); renderList(); } });
  const showChips = h('div', { class: 'tx-chips', role: 'group', 'aria-label': 'Show' });
  const SHOW = [['all', 'All'], ['live', 'In the game'], ['edited', 'Edited'], ['wait', 'Waiting']];
  for (const [k, label] of SHOW) showChips.append(h('button', { type: 'button', class: 'tx-chip', 'data-k': k, onclick: () => { S.show = k; savePrefs(); renderList(); } }, label));
  const list = h('ul', { class: 'tx-list', id: 'tx-list' });
  const listPane = h('nav', { class: 'tx-listpane', 'aria-label': 'Texts' }, h('div', { class: 'tx-filters' }, search, groupSel, showChips), list);
  const editPane = h('section', { class: 'tx-editpane', 'aria-label': 'Edit' });
  mount.replaceChildren(header, h('div', { class: 'tx-main' }, listPane, editPane));
  const savePrefs = () => store.set(`${storageKey}:prefs`, { group: S.group, show: S.show });

  function renderGroups() {
    const n = (g) => reg.entries.filter((e) => !g || e.group === g).length;
    groupSel.replaceChildren(h('option', { value: '' }, `All groups (${n('')})`), ...reg.groups.map((g) => h('option', { value: g.id, selected: S.group === g.id }, `${g.title} (${n(g.id)})`)));
    groupSel.value = S.group;
  }
  function renderCounts() {
    const wait = reg.entries.filter(pending).length, done = reg.entries.filter((e) => e.text !== e.base).length;
    counts.textContent = `${reg.entries.length} texts · ${done} edited in the game · ${wait} for the next build`;
    copyBtn.hidden = S.mode !== 'local' || (!wait && !reg.entries.some((e) => editOf(e.id)?.note));
    if (S.cur && headBadges) headBadges.replaceChildren(...badges(S.cur).map(([k, t]) => h('span', { class: `tx-badge tx-${k}`, text: t })), h('code', { class: 'tx-id', text: S.cur.id }));
  }
  // The texts the list shows (the group, the Show chips, the search): the list and the pager's order.
  function rowsOf() {
    const q = S.q.trim().toLowerCase();
    return reg.entries.filter((e) => (!S.group || e.group === S.group)
      && (S.show === 'all' || (S.show === 'live' && e.live) || (S.show === 'edited' && (e.text !== e.base || pending(e))) || (S.show === 'wait' && pending(e)))
      && (!q || `${e.title} ${e.id} ${M.plainText(shown(e), mopts)} ${e.where ?? ''}`.toLowerCase().includes(q)));
  }
  function renderList() {
    for (const c of showChips.children) c.setAttribute('aria-pressed', String(c.dataset.k === S.show));
    const rows = rowsOf();
    list.replaceChildren(...rows.map((e) => h('li', {}, h('button', { type: 'button', class: 'tx-row', 'aria-current': S.cur?.id === e.id ? 'true' : null, onclick: () => select(e.id) },
      h('span', { class: 'tx-row-top' }, h('span', { class: 'tx-row-title', text: e.title }), h('span', { class: 'tx-badges' }, ...badges(e).filter(([k]) => k !== 'later' && k !== 'live').map(([k, t]) => h('span', { class: `tx-badge tx-${k}`, text: t })))),
      h('span', { class: 'tx-row-text', text: M.plainText(shown(e), mopts) || '(empty)' })))));
    if (!rows.length) list.append(h('li', { class: 'tx-empty', text: 'No text matches. Clear the search or pick another group.' }));
    renderCounts(); renderPager(rows);
  }

  // ---------- Previous / Next (owner, 2026-10-09: "so I can get through them quickly") ----------
  // Through the list as filtered (e.g. Show: Edited), above and under the open text. A text that leaves the filter
  // while open (an edit undone under Edited) keeps its place: Next opens the one that took it.
  const pagers = [];
  const pager = () => {
    const prev = h('button', { type: 'button', class: 'tx-tool tx-step', onclick: () => step(-1) }, '‹ Previous');
    const next = h('button', { type: 'button', class: 'tx-tool tx-step', onclick: () => step(1) }, 'Next ›');
    const at = h('span', { class: 'tx-pos', 'aria-live': 'polite' });
    const el = h('div', { class: 'tx-pager', role: 'navigation', 'aria-label': 'Previous and next text' }, prev, at, next);
    pagers.push({ prev, next, at });
    return el;
  };
  function place(rows) {
    const k = S.cur ? rows.indexOf(S.cur) : -1;
    if (k >= 0) S.navAt = k;
    return k;
  }
  function renderPager(rows = rowsOf()) {
    const k = place(rows), n = rows.length, at = k >= 0 ? k : Math.min(S.navAt ?? 0, n);
    for (const P of pagers) {
      P.at.textContent = n ? (k >= 0 ? `${k + 1} / ${n}` : `– / ${n}`) : '0 / 0';
      P.prev.disabled = !n || at <= 0;
      P.next.disabled = !n || (k >= 0 ? k >= n - 1 : at >= n);
    }
  }
  function step(d) {
    const rows = rowsOf(), k = place(rows);
    const to = k >= 0 ? k + d : d > 0 ? Math.min(S.navAt ?? 0, rows.length - 1) : (S.navAt ?? 0) - 1;
    if (to >= 0 && to < rows.length) select(rows[to].id);
  }

  // ---------- The editor pane ----------
  const surface = h('div', { class: 'tx-surface', id: 'tx-surface', contenteditable: 'true', role: 'textbox', 'aria-multiline': 'true', 'aria-label': 'The text', spellcheck: 'true' });
  const preview = h('div', { class: 'tx-preview', 'aria-label': 'Preview' });
  const previewNote = h('p', { class: 'tx-preview-note' });
  const warn = h('p', { class: 'tx-warn', role: 'alert' });
  const saveState = h('span', { class: 'tx-save', role: 'status', 'aria-live': 'polite' });
  const markupBox = h('textarea', { id: 'tx-markup', class: 'tx-markup', rows: 4, spellcheck: 'false', 'aria-label': 'Markup' });
  const noteBox = h('textarea', { id: 'tx-note', class: 'tx-note', rows: 2, placeholder: 'A note for Claude about this text (optional)', 'aria-label': 'Note for Claude' });
  const tray = h('div', { class: 'tx-tray' });
  const tool = (label, title, fn, extra = {}) => h('button', { type: 'button', class: 'tx-tool', title, 'aria-label': title,
    onpointerdown: (e) => e.preventDefault(), onmousedown: (e) => e.preventDefault(), onclick: fn, ...extra }, label);
  const bBtn = tool(h('b', { text: 'B' }), 'Bold', () => styleOp('b'));
  const iBtn = tool(h('i', { text: 'I' }), 'Italic', () => styleOp('i'));
  const uBtn = tool(h('u', { text: 'U' }), 'Underline', () => styleOp('u'));
  const cBtn = tool(h('span', { class: 'tx-colour-dot' }), 'Colour', () => toggleTray('colour'), { 'aria-expanded': 'false' });
  const icBtn = tool('Icon', 'Insert an icon', () => toggleTray('icon'), { 'aria-expanded': 'false' });
  const brBtn = tool('↵', 'Line break', () => insertUnits([{ k: 'br' }]));
  const clrBtn = tool('Plain', 'Remove the styles', () => rangeOp((m, a, b) => M.clearStyle(m, a, b)));
  const undoBtn = tool('↶', 'Undo', () => undo());
  const redoBtn = tool('↷', 'Redo', () => redo());
  const toolbar = h('div', { class: 'tx-toolbar', role: 'toolbar', 'aria-label': 'Text style' }, bBtn, iBtn, uBtn, cBtn, icBtn, brBtn, clrBtn, h('span', { class: 'tx-sep' }), undoBtn, redoBtn);

  function renderTray() {
    cBtn.setAttribute('aria-expanded', String(S.tray === 'colour')); icBtn.setAttribute('aria-expanded', String(S.tray === 'icon'));
    tray.hidden = !S.tray;
    if (S.tray === 'colour') {
      const custom = h('input', { type: 'color', id: 'tx-custom-colour', 'aria-label': 'Any colour', value: '#c81818',
        onchange: (e) => rangeOp((m, a, b) => M.setColour(m, a, b, e.target.value.toLowerCase())) });
      // The palette's swatches with their names, any other colour, no colour.
      tray.replaceChildren(
        ...Object.entries(palette).map(([k, v]) => tool([h('span', { class: 'tx-swatch', style: `background:${cssRgb(M.rgbOf(v))}` }), h('span', { class: 'tx-pick-name', text: colourName(k) })],
          colourName(k), () => rangeOp((m, a, b) => M.setColour(m, a, b, k)), { class: 'tx-tool tx-pick' })),
        h('label', { class: 'tx-tool tx-pick tx-custom', for: 'tx-custom-colour' }, custom, h('span', { class: 'tx-pick-name', text: 'Other' })),
        tool([h('span', { class: 'tx-swatch tx-swatch-none' }), h('span', { class: 'tx-pick-name', text: 'None' })], 'No colour',
          () => rangeOp((m, a, b) => M.setColour(m, a, b, null)), { class: 'tx-tool tx-pick' }));
    } else if (S.tray === 'icon') {
      tray.replaceChildren(...icons.map((n) => tool([iconUrl(n) ? h('img', { src: iconUrl(n), alt: '', class: 'tx-icon-pick' }) : h('span', { class: 'tx-swatch', text: '?' }),
        h('span', { class: 'tx-pick-name', text: n })], `Insert ${n}`, () => insertUnits([{ k: 'icon', name: n }]), { class: 'tx-tool tx-pick' })));
    }
  }
  function toggleTray(k) { S.tray = S.tray === k ? null : k; renderTray(); }

  // ---------- Model ↔ the editing surface ----------
  const surfaceBg = () => parseCssColour(getComputedStyle(surface).backgroundColor) ?? [255, 255, 255];
  function renderSurface() { surface.innerHTML = modelHtml(S.model, surfaceBg(), true); }
  // A model as the edit box's HTML on a background `bg` (the Original box draws its text the same way); `pad` adds
  // the trailing break the editable box needs to show an empty last line.
  function modelHtml(model, bg, pad = false) {
    const bgL = lum(bg), out = [];
    let run = null;
    const wrap = (s, inner) => {
      let x = inner;
      if (s.u) x = `<u>${x}</u>`;
      if (s.i) x = `<i>${x}</i>`;
      if (s.b) x = `<b>${x}</b>`;
      if (s.c) {
        const c = M.colourRgb(s.c, palette) ?? [0, 0, 0], ring = Math.abs(lum(c) - bgL) < 0.35;
        const shade = bgL > 0.5 ? '0,0,0' : '255,255,255';
        x = `<span data-c="${esc(s.c)}" style="color:${cssRgb(c)}${ring ? `;text-shadow:0 0 1px rgb(${shade}),0 0 1px rgb(${shade}),0 0 1px rgb(${shade})` : ''}">${x}</span>`;
      }
      return x;
    };
    const flush = () => { if (run) out.push(wrap(run.s, esc(run.t))); run = null; };
    for (const u of model) {
      if (u.k === 'br') { flush(); out.push('<br>'); continue; }
      if (u.k === 'icon') {
        flush();
        const src = iconUrl(u.name);
        out.push(wrap(u.s, src ? `<img data-icon="${esc(u.name)}" src="${esc(src)}" alt="${esc(u.name)}" class="tx-icon" draggable="false">`
          : `<img data-icon="${esc(u.name)}" alt="{${esc(u.name)}}" class="tx-icon tx-icon-missing" draggable="false">`));
        continue;
      }
      if (run && M.sameStyle(run.s, u.s)) run.t += u.ch; else { flush(); run = { s: u.s, t: u.ch }; }
    }
    flush();
    if (pad && (!model.length || model[model.length - 1].k === 'br')) out.push('<br data-pad="">');
    return out.join('');
  }

  // The surface's DOM as model units (whatever the browser left there: our spans, its own tags, blocks).
  function parseNodes(rootNode, fragment) {
    const out = [];
    const tokenOf = (el) => {
      if (el.dataset?.c) return M.colourToken(el.dataset.c, palette);
      const c = parseCssColour(el.style?.color) ?? (el.tagName === 'FONT' ? parseCssColour(el.getAttribute('color')) : null);
      if (!c) return undefined;
      const name = Object.keys(palette).find((k) => M.rgbOf(palette[k]).join() === c.join());
      return name ?? hex(c);
    };
    const walk = (node, s) => {
      for (const n of node.childNodes) {
        if (n.nodeType === 3) { for (const ch of n.data.replace(/\u200b/g, '').replace(/\u00a0/g, ' ').split('')) out.push({ k: 'ch', ch, s }); continue; }
        if (n.nodeType !== 1) continue;
        const tag = n.tagName;
        if (tag === 'BR') {
          if (n.hasAttribute('data-pad')) continue;
          const block = n.parentNode !== rootNode && /^(DIV|P|LI)$/.test(n.parentNode.tagName) && n === n.parentNode.lastChild;
          if (block) continue;                                   // a block's placeholder line
          out.push({ k: 'br' }); continue;
        }
        if (tag === 'IMG') { const name = n.dataset.icon; if (name && icons.includes(name)) out.push({ k: 'icon', name, s }); continue; }
        if (/^(DIV|P|LI)$/.test(tag) && out.length && out[out.length - 1].k !== 'br') out.push({ k: 'br' });
        const t = { ...s };
        if (/^(B|STRONG)$/.test(tag) || +n.style?.fontWeight >= 600 || n.style?.fontWeight === 'bold') t.b = true;
        if (/^(I|EM)$/.test(tag) || n.style?.fontStyle === 'italic') t.i = true;
        if (tag === 'U' || /underline/.test(n.style?.textDecoration ?? '') || /underline/.test(n.style?.textDecorationLine ?? '')) t.u = true;
        const c = tokenOf(n);
        if (c !== undefined) t.c = c;
        walk(n, t);
      }
    };
    walk(rootNode, { b: false, i: false, u: false, c: null });
    if (!fragment) {                                             // the browser's trailing placeholder <br>
      let last = rootNode.lastChild;
      while (last && last.nodeType === 1 && last.tagName !== 'BR' && last.lastChild) last = last.lastChild;
      if (last && last.nodeType === 1 && last.tagName === 'BR' && !last.hasAttribute('data-pad') && out[out.length - 1]?.k === 'br') out.pop();
    }
    return out;
  }
  const inSurface = (n) => n && (n === surface || surface.contains(n));
  function getSel() {
    const sel = window.getSelection();
    if (!sel || !sel.rangeCount) return null;
    const r = sel.getRangeAt(0);
    if (!inSurface(r.startContainer) || !inSurface(r.endContainer)) return null;
    const at = (node, off) => { const q = document.createRange(); q.setStart(surface, 0); q.setEnd(node, off); return parseNodes(q.cloneContents(), true).length; };
    const a = at(r.startContainer, r.startOffset), b = at(r.endContainer, r.endOffset);
    return [Math.min(a, b), Math.max(a, b)];
  }
  // Model index → a DOM position in the surface we rendered.
  function locate(idx) {
    let left = idx, found = null;
    const visit = (node) => {
      for (const n of node.childNodes) {
        if (found) return;
        if (n.nodeType === 3) { if (left <= n.data.length) { found = [n, left]; return; } left -= n.data.length; continue; }
        if (n.nodeType !== 1) continue;
        if (n.tagName === 'BR' || n.tagName === 'IMG') {
          if (n.hasAttribute('data-pad')) continue;
          if (left === 0) { found = [n.parentNode, [...n.parentNode.childNodes].indexOf(n)]; return; }
          left -= 1; continue;
        }
        visit(n);
      }
    };
    visit(surface);
    if (found) return found;
    const pad = surface.querySelector('br[data-pad]');
    return pad ? [surface, [...surface.childNodes].indexOf(pad)] : [surface, surface.childNodes.length];
  }
  function setSel(a, b = a) {
    const sel = window.getSelection(), r = document.createRange();
    try { r.setStart(...locate(a)); r.setEnd(...locate(b)); sel.removeAllRanges(); sel.addRange(r); } catch { /* the surface changed under us */ }
    S.lastSel = [a, b];
  }
  document.addEventListener('selectionchange', () => { const s = getSel(); if (s) { S.lastSel = s; reflectTools(); } });

  // ---------- Operations ----------
  const snapshot = () => ({ markup: M.toMarkup(S.model), sel: S.lastSel });
  function remember() { S.hist.push(snapshot()); if (S.hist.length > 200) S.hist.shift(); S.fut = []; reflectTools(); }
  function apply(model, sel) {
    S.model = model; renderSurface();
    if (sel) { surface.focus({ preventScroll: true }); setSel(...sel); }
    changed();
  }
  function range() {
    let [a, b] = S.lastSel ?? [S.model.length, S.model.length];
    a = Math.min(a, S.model.length); b = Math.min(b, S.model.length);
    if (a === b) { const w = M.wordAt(S.model, a); if (w) return { a: w[0], b: w[1], word: true, caret: a }; }
    return { a, b };
  }
  function rangeOp(fn) {
    const r = range();
    if (r.a === r.b) { flash('Select some text (or put the cursor in a word) first.'); return; }
    remember();
    apply(fn(S.model, r.a, r.b), r.word ? [r.caret, r.caret] : [r.a, r.b]);
  }
  const styleOp = (key) => rangeOp((m, a, b) => M.toggle(m, a, b, key));
  function insertUnits(units) {
    const [a, b] = S.lastSel ?? [S.model.length, S.model.length];
    remember();
    const m = M.insert(S.model, a, b, units);
    apply(m, [a + units.length, a + units.length]);
  }
  function undo() { if (!S.hist.length) return; S.fut.push(snapshot()); const s = S.hist.pop(); S.model = M.toModel(s.markup, mopts); apply(S.model, s.sel); }
  function redo() { if (!S.fut.length) return; S.hist.push(snapshot()); const s = S.fut.pop(); S.model = M.toModel(s.markup, mopts); apply(S.model, s.sel); }
  function reflectTools() {
    undoBtn.disabled = !S.hist.length; redoBtn.disabled = !S.fut.length;
    const r = S.cur ? range() : { a: 0, b: 0 };
    for (const [btn, k] of [[bBtn, 'b'], [iBtn, 'i'], [uBtn, 'u']]) btn.setAttribute('aria-pressed', String(r.a < r.b && M.isOn(S.model, r.a, r.b, k)));
  }

  // Typing: read the surface back (no re-render: the browser keeps its caret and the keyboard its word).
  let typingMark = 0;
  surface.addEventListener('beforeinput', (e) => {
    const t = e.inputType;
    if (t === 'insertParagraph' || t === 'insertLineBreak') { e.preventDefault(); S.lastSel = getSel() ?? S.lastSel; insertUnits([{ k: 'br' }]); return; }
    if (t === 'historyUndo') { e.preventDefault(); undo(); return; }
    if (t === 'historyRedo') { e.preventDefault(); redo(); return; }
    if (t === 'formatBold' || t === 'formatItalic' || t === 'formatUnderline') { e.preventDefault(); styleOp({ formatBold: 'b', formatItalic: 'i', formatUnderline: 'u' }[t]); return; }
    if (t === 'insertFromDrop' || t.startsWith('format')) { e.preventDefault(); return; }
    if (Date.now() - typingMark > 1200) remember();
    typingMark = Date.now();
  });
  surface.addEventListener('paste', (e) => {
    e.preventDefault();
    const text = e.clipboardData?.getData('text/plain') ?? '';
    if (!text) return;
    S.lastSel = getSel() ?? S.lastSel;
    const [a, b] = S.lastSel ?? [S.model.length, S.model.length];
    remember();
    const m = M.insert(S.model, a, b, text);
    apply(m, [a + text.replace(/\r\n?/g, '\n').length, a + text.replace(/\r\n?/g, '\n').length]);
  });
  surface.addEventListener('drop', (e) => e.preventDefault());
  surface.addEventListener('compositionstart', () => { S.composing = true; });
  surface.addEventListener('compositionend', () => { S.composing = false; readSurface(); });
  surface.addEventListener('input', (e) => { if (!S.composing && !e.isComposing) readSurface(); });
  surface.addEventListener('keydown', (e) => {
    if (!(e.ctrlKey || e.metaKey)) return;
    const k = e.key.toLowerCase();
    if (k === 'b' || k === 'i' || k === 'u') { e.preventDefault(); styleOp(k); }
    else if (k === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); }
    else if (k === 'y') { e.preventDefault(); redo(); }
  });
  function readSurface() { S.model = parseNodes(surface, false); S.lastSel = getSel() ?? S.lastSel; changed(); }

  // ---------- After every change: markup, warnings, preview, save ----------
  const drawPreview = debounce(() => {
    if (!S.cur) return;
    previewNote.textContent = '';
    if (!artReady || !adapter.preview) { preview.hidden = true; return; }
    preview.hidden = false;
    try {
      const res = adapter.preview(S.cur, M.toMarkup(S.model), preview, { registry: reg, byId });
      if (res?.note) previewNote.textContent = res.note;
    } catch (err) { previewNote.textContent = `The preview failed: ${err.message}`; }
  }, 90);
  function changed() {
    const markup = M.toMarkup(S.model);
    if (document.activeElement !== markupBox) markupBox.value = markup;
    const lost = S.cur ? M.missingPlaceholders(S.cur.base, markup) : [];
    warn.textContent = lost.length ? `Keep ${lost.join(', ')}: the game fills ${lost.length > 1 ? 'these words' : 'this word'} in.` : '';
    warn.hidden = !lost.length;
    reflectOriginal(markup);
    S.localAt = Date.now();
    reflectTools(); drawPreview(); queueSave();
  }

  // ---------- Saving ----------
  let db = null, col = null;
  const writing = new Map();                                     // id → the write in flight (one at a time per text)
  function record(id) {
    const e = byId.get(id), markup = id === S.cur?.id ? M.toMarkup(S.model) : editOf(id)?.markup ?? e.text;
    const note = (id === S.cur?.id ? noteBox.value : editOf(id)?.note ?? '').trim();
    const same = norm(markup) === norm(e.text);
    return same && !note ? null : { ...(same ? {} : { markup }), ...(note ? { note } : {}), from: e.text, title: e.title, updatedAt: new Date().toISOString() };
  }
  const queueSave = debounce(() => { if (S.cur) save(S.cur.id); }, 700);
  async function save(id) {
    const data = record(id);
    const key = (d) => JSON.stringify(d ? [d.markup ?? null, d.note ?? ''] : null);
    const same = key(editOf(id)) === key(data);
    if (data) S.edits[id] = data; else delete S.edits[id];
    if (same && S.mode !== 'local') { renderList(); return; }
    S.wrote[id] = data?.markup ?? null;
    renderList();
    if (S.mode === 'local') { store.set(`${storageKey}:edits`, S.edits); saveState.textContent = 'Kept on this device'; return; }
    if (!col) return;
    saveState.textContent = 'Saving…';
    const run = (writing.get(id) ?? Promise.resolve()).then(() => (data ? col.doc(id).set(data) : col.doc(id).delete()));
    writing.set(id, run.catch(() => {}));
    try { await run; saveState.textContent = data ? (data.markup !== undefined ? 'Saved · in the next build' : 'Saved') : 'No change from the game'; }
    catch (err) { saveState.textContent = `Not saved (${err?.code ?? err?.message ?? 'error'}). Your edit is still here; try again.`; }
  }
  window.addEventListener('pagehide', () => queueSave.flush());

  async function copyForClaude() {
    const out = {};
    for (const e of reg.entries) {
      const d = editOf(e.id);
      if (!d) continue;
      out[e.id] = { ...(pending(e) ? { markup: d.markup } : {}), ...(d.note ? { note: d.note } : {}) };
    }
    const text = JSON.stringify(out, null, 1);
    try { await navigator.clipboard.writeText(text); flash('Copied. Paste it to Claude.'); }
    catch { const t = h('textarea', { class: 'tx-copy', readonly: true }); t.value = text; editPane.prepend(t); t.select(); flash('Select all and copy this text for Claude.'); }
  }
  let flashT = 0;
  function flash(msg) { status.textContent = msg; clearTimeout(flashT); flashT = setTimeout(() => setMode(S.mode), 4000); }

  // ---------- Choosing a text ----------
  let headBadges = null;                                         // the open text's badges (kept current by renderList)
  let origBox = null, origState = null, origUse = null;          // the open text's Original box
  function reflectOriginal(markup) {
    if (!origBox || !S.cur) return;
    const same = norm(markup) === norm(S.cur.base);
    origState.textContent = same ? 'Unchanged' : 'Edited below';
    origState.dataset.state = same ? 'same' : 'changed';
    origUse.hidden = same;
  }
  function select(id, { scroll = true } = {}) {
    const e = byId.get(id);
    if (!e) return;
    if (S.cur && S.cur.id !== id) queueSave.flush();
    S.cur = e; S.hist = []; S.fut = []; S.lastSel = null; S.tray = null;
    S.model = M.toModel(shown(e), mopts);
    try { history.replaceState(null, '', `#${id}`); } catch { /* sandboxed: fine */ }
    mount.dataset.view = 'edit';
    const g = groupOf.get(e.group);
    const surf = adapter.surface?.(e) ?? {};
    surface.style.background = surf.bg ?? ''; surface.style.color = surf.fg ?? '';
    noteBox.value = editOf(id)?.note ?? '';
    // The Original box (owner, 2026-10-08): the text before any edit, always shown, drawn as the edit box draws it
    // (read-only); the edit box below holds the modified text when there is one. `original` (an earlier version,
    // e.g. the original game's) is a line under it when it differs.
    origBox = h('div', { class: 'tx-surface tx-original', 'aria-readonly': 'true', 'aria-label': 'Original text' });
    origBox.style.background = surf.bg ?? ''; origBox.style.color = surf.fg ?? '';
    origState = h('span', { class: 'tx-orig-state' });
    origUse = tool('Use the original', 'Put the original text back in the edit box', () => { remember(); apply(M.toModel(e.base, mopts), null); });
    const origin = h('div', { class: 'tx-block tx-orig' },
      h('div', { class: 'tx-orig-head' }, h('p', { class: 'tx-label', text: 'Original' }), origState), origBox,
      ...(e.original && e.original !== e.base ? [h('p', { class: 'tx-orig-earlier' }, h('span', { class: 'tx-ref-label', text: `${adapter.labels?.earlier ?? 'Earlier version'} ` }), M.plainText(e.original, mopts))] : []),
      origUse);
    pagers.length = 0;
    editPane.replaceChildren(
      h('div', { class: 'tx-nav' },
        h('button', { type: 'button', class: 'tx-back', onclick: () => { mount.dataset.view = 'list'; renderList(); list.querySelector('[aria-current="true"]')?.focus(); } }, '‹ All texts'),
        pager()),
      h('div', { class: 'tx-entry-head' },
        h('p', { class: 'tx-eyebrow', text: g?.title ?? e.group }),
        h('h2', { text: e.title }),
        h('p', { class: 'tx-where', text: e.where ?? '' }),
        headBadges = h('p', { class: 'tx-badges' })),
      h('div', { class: 'tx-block' }, h('p', { class: 'tx-label', text: 'Preview' }), preview, previewNote),
      origin,
      h('div', { class: 'tx-block tx-editor' }, h('p', { class: 'tx-label', text: 'Edit' }), toolbar, tray, surface, warn,
        h('div', { class: 'tx-actions' }, saveState,
          tool('Reset changes', 'Reset changes', () => { remember(); apply(M.toModel(e.text, mopts), null); }))),
      h('div', { class: 'tx-block' }, h('label', { class: 'tx-label', for: 'tx-note', text: 'Note for Claude' }), noteBox),
      h('details', { class: 'tx-block tx-details' }, h('summary', { text: 'Markup' }),
        h('p', { class: 'tx-help', text: '[b]bold[/b] · [i]italic[/i] · [u]underline[/u] · [c=name]colour[/c] or [c=#rrggbb] · {icon} · a new line = a line break' }), markupBox),
      h('div', { class: 'tx-nav tx-nav-end' }, pager()));
    renderTray(); renderSurface();
    origBox.innerHTML = modelHtml(M.toModel(e.base, mopts), parseCssColour(getComputedStyle(origBox).backgroundColor) ?? surfaceBg());
    changed();
    saveState.textContent = pending(e) ? 'Saved · in the next build' : '';
    renderList();
    if (scroll) editPane.scrollIntoView?.({ block: 'start' });
  }
  markupBox.addEventListener('input', () => { if (Date.now() - typingMark > 1200) remember(); typingMark = Date.now(); S.model = M.toModel(markupBox.value, mopts); renderSurface(); changed(); });
  noteBox.addEventListener('input', () => queueSave());

  // ---------- The store ----------
  function setMode(mode) {
    S.mode = mode;
    status.textContent = { connecting: 'Connecting…', db: 'Edits save automatically and reach the game with the next build.', local: 'Edits are kept on this device only: use Copy the edits.' }[mode];
    status.dataset.mode = mode;
  }
  setMode('connecting');
  renderGroups(); renderList();
  const start = location.hash.slice(1);
  if (byId.has(start)) select(start, { scroll: false }); else mount.dataset.view = 'list';
  if (!S.cur && matchMedia('(min-width: 900px)').matches) select(reg.entries[0].id, { scroll: false });

  try { db = window.claude?.use ? await window.claude.use('db') : null; } catch { db = null; }
  if (!db) {
    S.edits = store.get(`${storageKey}:edits`) ?? {};
    setMode('local'); renderList(); if (S.cur) select(S.cur.id, { scroll: false });
    return;
  }
  col = db.collection(collection);
  let first = true;
  col.onSnapshot((snap) => {
    const next = {};
    for (const d of snap.docs) next[d.id] = d.data();
    const curId = S.cur?.id;
    const theirs = curId ? next[curId]?.markup ?? null : null, mine = curId ? record(curId)?.markup ?? null : null;
    S.edits = { ...next };
    if (first) { first = false; setMode('db'); if (curId) select(curId, { scroll: false }); else renderList(); return; }
    // Another device changed the open text: take it, unless it is this view's own write coming back or this view
    // changed the text in the last few seconds (its own save follows).
    const echo = curId && Object.hasOwn(S.wrote, curId) && S.wrote[curId] === theirs;
    if (curId && !echo && theirs !== mine && Date.now() - S.localAt > 4000) select(curId, { scroll: false });
    else renderList();
  }, () => { setMode('local'); flash('Lost the connection to the saved edits. Reload the page.'); });
}
