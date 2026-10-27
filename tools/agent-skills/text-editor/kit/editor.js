// Text editor kit: the editor page. Generic: a project gives it its registry (every text, see SKILL.md) and an
// adapter (its colours' names, icons, the editing surface's look and a live preview drawn by the project's own code).
//
//   import { boot } from './kit/editor.js';
//   boot({ mount, registryUrl, adapter, collection: 'edits', storageKey });
//
// The owner picks a text, edits it as rich text (bold, italic, underline, a colour, an icon, a line break), sees the
// project's real preview, and can leave a note for Claude. Each edit is saved in the artifact's db (collection
// `edits`, one document per text id: { markup, note, from, title, updatedAt, locked, lockedAt }). Claude applies them
// before every build of the program (apply-edits.mjs, then the registry rebuilt); an edit equal to the text the
// program shows is done and disappears. Without a db (a local copy, signed out) the edits stay in this browser and a
// "Copy the edits" button (shown only then) hands them over.
// The standard for every tool the owner goes through item by item (Dungeon Raid's owner, 2026-10-16: "Add a "locked"
// function to this sheet, with the ability to filter out locked ones"; the Particle Playground the reference): Mark done
// per text (its padlock: the text locked until tapped again; a note can still be left), the Show chips with their
// counts (To do and Done among them), and nothing lost: every save waits on this device until the db has it, and a
// dropped connection reconnects by itself and sends what waited.
// Items (Dungeon Raid's owner, 2026-10-19: "instead of showing two different list entries, show as one list item with
// multiple text values (this is just for me, the user, not the structure of the DB)"): registry entries that share a
// `subject` (a skill's name and description …) are one item: one row in the list, one page with a tab per text (its
// `field`) over one preview that shows them together as they are now; `heading` marks the text that names the item.
// Mark done takes the whole item; under To do the next item opens in its place, and nothing on the page moves (the
// owner: "The view keeps jumping when I press on Mark Done ... I expect the next one in line to replace the view").
// The db keeps one document per text, as before; a registry without subjects works as it did.
// Claude's replies (Dungeon Raid's owner, 2026-10-21: "I added a bunch of notes to "marked as done" items ... the
// intention is for you to respond and send it back to me"): Claude answers a note in the text's own document (fields
// `reply`, the answer; `suggest`, a text Claude proposes, as markup; `imgs`, [{ src, caption }] pictures published with
// the page; `replyAt`), written with the db's merge (ArtifactData update), and sends the item back by clearing its
// `locked` / `lockedAt`. The page shows them under the preview ("Claude"), each suggestion drawn as the edit box draws
// it with Use this (it goes into the edit box like any edit), the badge Reply and the Show chip Replies (the items
// answered and not done yet); the owner's saves keep those fields. Words the program fills in (%name%) show highlighted
// in every box, so they read as what they are (the owner: "Variable?", "These are variables").
import * as M from './markup.js';

// A padlock, open or shut (it pictures what it does: the text is done and locked).
const LOCK_SVG = (shut) => `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="${shut ? 'M4.5 7V5a3.5 3.5 0 0 1 7 0v2' : 'M4.5 7V5a3.5 3.5 0 0 1 6.6-1.6'}" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="3" y="7" width="10" height="7.5" rx="1.5" fill="currentColor"/></svg>`;

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
  const subjects = [], subjectOf = new Map(), bySubject = new Map();   // the items (an entry without a subject is its own)
  for (const e of reg.entries) {
    const sid = e.subject ?? e.id;
    let it = bySubject.get(sid);
    if (!it) { it = { id: sid, group: e.group, entries: [] }; bySubject.set(sid, it); subjects.push(it); }
    it.entries.push(e); subjectOf.set(e.id, it);
  }
  const S = { edits: {}, wrote: {}, localAt: 0, cur: null, curS: null, model: [], hist: [], fut: [], lastSel: null, q: '', group: '', show: 'all', mode: 'connecting', tray: null, composing: false, navAt: 0,
    locked: {}, pend: store.get(`${storageKey}:pending`) ?? {} };   // locked: id → lockedAt; pend: id → { data } (a save not in the db yet)
  const prefs = store.get(`${storageKey}:prefs`) ?? {};
  Object.assign(S, { group: prefs.group ?? '', show: prefs.show ?? 'all' });
  const keepPend = () => store.set(`${storageKey}:pending`, S.pend);
  // Claude's fields in a text's document: kept as they are by every save of the page (only Claude writes them).
  const CLAUDE_FIELDS = ['reply', 'replyAt', 'suggest', 'imgs'];
  const claudeOf = (d) => Object.fromEntries(CLAUDE_FIELDS.filter((k) => d?.[k] !== undefined && d[k] !== null && d[k] !== '').map((k) => [k, d[k]]));
  const answered = (id) => { const d = S.edits[id]; return !!(d && (d.reply || d.suggest || d.imgs?.length)); };
  const locksOf = (edits) => Object.fromEntries(Object.entries(edits).filter(([, d]) => d?.locked).map(([id, d]) => [id, d.lockedAt ?? d.updatedAt ?? '']));
  // What waits on this device goes over what the db (or the browser) holds.
  const withPending = (edits) => { const out = { ...edits }; for (const [id, p] of Object.entries(S.pend)) { if (p.data) out[id] = p.data; else delete out[id]; } return out; };

  // The adapter's art (icons, preview); a failure leaves the editor working without them.
  let artReady = false;
  try { await adapter.init?.(); artReady = true; } catch (err) { console.warn('preview unavailable:', err); }
  const iconUrl = (n) => (artReady ? adapter.iconUrl?.(n) : null) ?? null;
  const colourName = (k) => adapter.colourNames?.[k] ?? k;
  const varTitle = (k) => { const v = adapter.sampleOf?.(k); return `Filled in by the program${v ? ` (e.g. ${v})` : ''}`; };

  // ---------- Entry state ----------
  const editOf = (id) => S.edits[id];
  const pending = (e) => { const d = editOf(e.id); return !!d && typeof d.markup === 'string' && norm(d.markup) !== norm(e.text); };
  const shown = (e) => (pending(e) ? editOf(e.id).markup : e.text);
  const isLocked = (e) => !!e && Object.hasOwn(S.locked, e.id);
  const badges = (e) => {
    const out = [];
    if (isLocked(e)) out.push(['lockb', '✓ Done']);
    if (pending(e)) out.push(['wait', 'Next build']);
    else if (e.text !== e.base) out.push(['done', 'Edited']);
    if (editOf(e.id)?.note) out.push(['noteb', 'Note']);                // 'noteb': the note box is .tx-note
    if (answered(e.id)) out.push(['replyb', 'Reply']);
    out.push(e.live ? ['live', 'In the game'] : ['later', 'Not live yet']);
    return out;
  };
  // An item: its texts' states together. Done when every text of it is.
  const nowOf = (e) => (e === S.cur ? M.toMarkup(S.model) : shown(e));
  const headingOf = (it) => it.entries.find((e) => e.heading) ?? null;
  const itemTitle = (it) => {
    const hd = headingOf(it), t = hd ? M.plainText(nowOf(hd), mopts).trim() : '';
    return t || it.entries[0].subjectTitle || it.entries[0].title;
  };
  const itemLocked = (it) => it.entries.every(isLocked);
  const itemBadges = (it) => {
    if (it.entries.length === 1) return badges(it.entries[0]);
    const out = [];
    if (itemLocked(it)) out.push(['lockb', '✓ Done']);
    if (it.entries.some(pending)) out.push(['wait', 'Next build']);
    else if (it.entries.some((e) => e.text !== e.base)) out.push(['done', 'Edited']);
    if (it.entries.some((e) => editOf(e.id)?.note)) out.push(['noteb', 'Note']);
    if (it.entries.some((e) => answered(e.id))) out.push(['replyb', 'Reply']);
    out.push(it.entries.some((e) => e.live) ? ['live', 'In the game'] : ['later', 'Not live yet']);
    return out;
  };
  const itemText = (it) => (it.entries.length === 1 ? M.plainText(shown(it.entries[0]), mopts)
    : it.entries.filter((e) => !e.heading).map((e) => M.plainText(shown(e), mopts)).filter(Boolean).join(' · '));

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
  // The Show chips, each with its count of items; To do hides the items marked done, Done shows only them; Replies,
  // the items Claude answered that are not done yet.
  const SHOW = [['all', 'All'], ['todo', 'To do'], ['replies', 'Replies'], ['locked', 'Done'], ['live', 'In the game'], ['edited', 'Edited'], ['wait', 'Waiting']];
  const SHOWS = {
    all: () => true, todo: (it) => !itemLocked(it), locked: (it) => itemLocked(it), live: (it) => it.entries.some((e) => e.live),
    replies: (it) => !itemLocked(it) && it.entries.some((e) => answered(e.id)),
    edited: (it) => it.entries.some((e) => e.text !== e.base || pending(e)), wait: (it) => it.entries.some(pending),
  };
  for (const [k, label] of SHOW) showChips.append(h('button', { type: 'button', class: 'tx-chip', 'data-k': k, onclick: () => { S.show = k; savePrefs(); renderList(); } },
    label, ' ', h('small', { class: 'tx-chip-n' })));
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
    const wait = reg.entries.filter(pending).length, done = reg.entries.filter((e) => e.text !== e.base).length, locked = reg.entries.filter(isLocked).length;
    counts.textContent = `${reg.entries.length} texts · ${locked} done · ${done} edited in the game · ${wait} for the next build`;
    for (const c of showChips.children) { const n = c.querySelector('.tx-chip-n'); if (n) n.textContent = String(subjects.filter((it) => (!S.group || it.group === S.group) && SHOWS[c.dataset.k](it)).length); }
    copyBtn.hidden = S.mode !== 'local' || (!wait && !reg.entries.some((e) => editOf(e.id)?.note));
    if (S.cur && headBadges) headBadges.replaceChildren(...itemBadges(S.curS).map(([k, t]) => h('span', { class: `tx-badge tx-${k}`, text: t })), h('code', { class: 'tx-id', text: S.cur.id }));
  }
  // The items the list shows (the group, the Show chips, the search over all their texts): the list and the pager's order.
  function rowsOf() {
    const q = S.q.trim().toLowerCase();
    return subjects.filter((it) => (!S.group || it.group === S.group) && (SHOWS[S.show] ?? SHOWS.all)(it)
      && (!q || it.entries.some((e) => `${e.title} ${e.id} ${M.plainText(shown(e), mopts)} ${e.where ?? ''}`.toLowerCase().includes(q))));
  }
  function renderList() {
    for (const c of showChips.children) c.setAttribute('aria-pressed', String(c.dataset.k === S.show));
    const rows = rowsOf(), top = list.scrollTop;
    list.replaceChildren(...rows.map((it) => h('li', {}, h('button', { type: 'button', class: 'tx-row', 'aria-current': S.curS === it ? 'true' : null, onclick: () => select(it.entries[0].id) },
      h('span', { class: 'tx-row-top' }, h('span', { class: 'tx-row-title', text: itemTitle(it) }), h('span', { class: 'tx-badges' }, ...itemBadges(it).filter(([k]) => k !== 'later' && k !== 'live').map(([k, t]) => h('span', { class: `tx-badge tx-${k}`, text: t })))),
      h('span', { class: 'tx-row-text', text: itemText(it) || '(empty)' })))));
    if (!rows.length) list.append(h('li', { class: 'tx-empty', text: 'No text matches. Clear the search or pick another group.' }));
    list.scrollTop = top;                                        // the list stays where it was (no shifting)
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
    const k = S.curS ? rows.indexOf(S.curS) : -1;
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
    if (to >= 0 && to < rows.length) select(rows[to].entries[0].id);
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
    // A word the program fills in (%name%) in a mark of its own; the text reads back unchanged (parseNodes).
    const vars = (t) => esc(t).replace(/%([A-Za-z]\w*)%/g, (m, k) => `<span class="tx-var" title="${esc(varTitle(k))}">${m}</span>`);
    const flush = () => { if (run) out.push(wrap(run.s, vars(run.t))); run = null; };
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
    const lk = isLocked(S.cur);                                   // a text marked done: its tools off until it is unlocked
    for (const b of [bBtn, iBtn, uBtn, cBtn, icBtn, brBtn, clrBtn]) b.disabled = lk;
    undoBtn.disabled = lk || !S.hist.length; redoBtn.disabled = lk || !S.fut.length;
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
      // The item's preview: every text of it as it is now (the open one as typed), so its parts always agree.
      const textOf = (id) => (byId.has(id) ? nowOf(byId.get(id)) : '');
      const res = adapter.preview(S.cur, M.toMarkup(S.model), preview, { registry: reg, byId, subject: S.curS, textOf });
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
    if (titleEl && S.curS) titleEl.textContent = itemTitle(S.curS);
    renderTabs(); reflectSuggestions();
    S.localAt = Date.now();
    reflectTools(); drawPreview(); queueSave();
  }

  // ---------- Saving ----------
  // A save shows at once and waits on this device (S.pend, kept in the browser) until the db has it; with the
  // connection down it is sent when the page reconnects.
  let db = null, live = null;                                    // live: the db's collection while connected
  const writing = new Map();                                     // id → the write in flight (one at a time per text)
  function record(id) {
    const e = byId.get(id), markup = id === S.cur?.id ? M.toMarkup(S.model) : editOf(id)?.markup ?? e.text;
    const note = (id === S.cur?.id ? noteBox.value : editOf(id)?.note ?? '').trim();
    const same = norm(markup) === norm(e.text), lockedAt = Object.hasOwn(S.locked, id) ? S.locked[id] : null, kept = claudeOf(editOf(id));
    return same && !note && lockedAt === null && !Object.keys(kept).length ? null : { ...(same ? {} : { markup }), ...(note ? { note } : {}),
      ...(lockedAt !== null ? { locked: true, lockedAt } : {}), ...kept, from: e.text, title: e.title, updatedAt: new Date().toISOString() };
  }
  const queueSave = debounce(() => { if (S.cur) save(S.cur.id); }, 700);
  const said = (id, text) => { if (id === S.cur?.id) saveState.textContent = text; };
  async function save(id, { quiet = false } = {}) {
    const data = record(id);
    const key = (d) => JSON.stringify(d ? [d.markup ?? null, d.note ?? '', !!d.locked] : null);
    const same = key(editOf(id)) === key(data);
    if (data) S.edits[id] = data; else delete S.edits[id];
    if (same && S.mode !== 'local') { if (!quiet) renderList(); return; }
    S.wrote[id] = data?.markup ?? null;
    if (!quiet) renderList();
    if (S.mode === 'local') { store.set(`${storageKey}:edits`, S.edits); said(id, 'Kept on this device'); return; }
    S.pend[id] = { data }; keepPend();
    return send(id);
  }
  async function send(id) {
    const p = S.pend[id];
    if (!p) return true;
    if (!live) { said(id, 'Saved on this device; sent when the page reconnects'); return false; }
    said(id, 'Saving…');
    const target = live, run = (writing.get(id) ?? Promise.resolve()).then(() => (p.data ? target.doc(id).set(p.data) : target.doc(id).delete()));
    writing.set(id, run.catch(() => {}));
    try {
      await run;
      if (S.pend[id] === p) { delete S.pend[id]; keepPend(); }
      said(id, p.data ? (p.data.markup !== undefined ? 'Saved · in the next build' : 'Saved') : 'No change from the game');
      return true;
    } catch (err) {
      said(id, `Saved on this device; the db did not take it yet (${err?.code ?? err?.message ?? 'error'}). It is sent when the page reconnects.`);
      return false;
    }
  }
  window.addEventListener('pagehide', () => { queueSave.flush(); keepPend(); });

  // Mark done (the padlock): the item's texts saved as they stand and locked until tapped again. Under To do (the items
  // not marked done yet) the next one in line opens in its place, so the work goes on without a jump.
  function toggleLock(it) {
    if (!it) return;
    queueSave.flush();
    const on = !itemLocked(it), at = new Date().toISOString(), k = rowsOf().indexOf(it);
    for (const e of it.entries) {
      if (on) { if (!Object.hasOwn(S.locked, e.id)) S.locked[e.id] = at; } else delete S.locked[e.id];
      save(e.id, { quiet: true });
    }
    if (on && S.show === 'todo' && S.curS === it) {
      const after = rowsOf(), next = after[Math.min(Math.max(k, 0), after.length - 1)];
      if (next && next !== it) { select(next.entries[0].id, { scroll: false }); flash(`Marked done: ${itemTitle(it)}. The next one is open.`); return; }
    }
    reflectLock(); renderList();
  }

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
  let headBadges = null;                                         // the open item's badges (kept current by renderList)
  let titleEl = null, whereEl = null, tabsEl = null, fieldHost = null, editLabel = null;   // the open item's page
  let origBox = null, origState = null, origUse = null;          // the open text's Original box
  let lockBtn = null, resetBtn = null;                           // the item's padlock; the open text's Reset changes
  let repliesEl = null, repliesSig = '';                          // the open item's replies from Claude
  // The open text locked (done) or not: the edit box, its tools, the markup and the resets follow; the note stays open.
  // The padlock shows the item (Done when every text of it is). The state is said in the Edit label's own line, so
  // nothing on the page moves when it changes.
  function reflectLock() {
    if (!S.cur || !lockBtn) return;
    const on = isLocked(S.cur), all = itemLocked(S.curS);
    surface.contentEditable = on ? 'false' : 'true';
    surface.setAttribute('aria-readonly', String(on));
    surface.classList.toggle('tx-locked', on);
    markupBox.readOnly = on;
    if (resetBtn) resetBtn.disabled = on;
    if (origUse) origUse.disabled = on;
    lockBtn.setAttribute('aria-pressed', String(all));
    lockBtn.innerHTML = `${LOCK_SVG(all)}<span>${all ? 'Done' : 'Mark done'}</span>`;
    if (editLabel) { editLabel.textContent = on ? 'Edit · done, locked (tap Done to change it)' : 'Edit'; editLabel.classList.toggle('tx-label-done', on); }
    if (on) S.tray = null;
    renderTray(); reflectTools(); renderTabs(); reflectSuggestions();
  }
  // The item's texts as tabs (when it has more than one): each its name and its text as it is now.
  function renderTabs() {
    if (!tabsEl || !S.curS) return;
    const it = S.curS;
    tabsEl.hidden = it.entries.length < 2;
    if (tabsEl.hidden) return;
    tabsEl.replaceChildren(...it.entries.map((e) => {
      const on = e === S.cur;
      return h('button', { type: 'button', class: 'tx-tab', role: 'tab', 'aria-selected': String(on), onclick: () => { if (!on) select(e.id, { scroll: false }); } },
        h('span', { class: 'tx-tab-name' }, e.field ?? e.title, pending(e) ? h('span', { class: 'tx-tab-dot', title: 'Changed: in the next build' }) : null, isLocked(e) ? ' ✓' : null),
        h('span', { class: 'tx-tab-text', text: M.plainText(nowOf(e), mopts) || '(empty)' }));
    }));
  }
  function reflectOriginal(markup) {
    if (!origBox || !S.cur) return;
    const same = norm(markup) === norm(S.cur.base);
    origState.textContent = same ? 'Unchanged' : 'Edited below';
    origState.dataset.state = same ? 'same' : 'changed';
    origUse.hidden = same;
  }
  // Opens a text: its item's page (built once per item: the head, the preview, the tabs), then the text itself.
  function select(id, { scroll = true } = {}) {
    const e = byId.get(id);
    if (!e) return;
    if (S.cur && S.cur.id !== id) queueSave.flush();
    const it = subjectOf.get(id), same = S.curS === it && !!fieldHost && editPane.contains(fieldHost);
    S.cur = e; S.curS = it; S.hist = []; S.fut = []; S.lastSel = null; S.tray = null;
    S.model = M.toModel(shown(e), mopts);
    try { history.replaceState(null, '', `#${id}`); } catch { /* sandboxed: fine */ }
    mount.dataset.view = 'edit';
    if (!same) buildItem(it);
    showText(e);
    renderList();
    renderReplies(!same);
    if (!same) {
      list.querySelector('[aria-current="true"]')?.scrollIntoView?.({ block: 'nearest' });
      if (scroll) editPane.scrollIntoView?.({ block: 'start' });
    }
  }
  // Claude's replies to the open item, each text's in turn (its name above it when the item has several): the answer,
  // its pictures, and a suggested text drawn as the edit box draws it, with Use this. Rebuilt only when they change.
  const when = (iso) => { try { return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short' }); } catch { return ''; } };
  function renderReplies(force = false) {
    if (!repliesEl || !S.curS) return;
    const it = S.curS, many = it.entries.length > 1, mine = it.entries.filter((e) => answered(e.id));
    const sig = JSON.stringify(mine.map((e) => [e.id, claudeOf(editOf(e.id))]));
    if (!force && sig === repliesSig) { reflectSuggestions(); return; }
    repliesSig = sig;
    repliesEl.hidden = !mine.length;
    if (!mine.length) { repliesEl.replaceChildren(); return; }
    const boxes = [];
    repliesEl.replaceChildren(h('p', { class: 'tx-label', text: 'Claude' }), ...mine.map((e) => {
      const d = editOf(e.id), parts = [];
      if (many) parts.push(h('p', { class: 'tx-reply-field', text: e.field ?? e.title }));
      for (const t of String(d.reply ?? '').split(/\n{2,}/).map((x) => x.trim()).filter(Boolean)) parts.push(h('p', { class: 'tx-reply-text', text: t }));
      for (const im of d.imgs ?? []) parts.push(h('figure', { class: 'tx-reply-fig' }, h('img', { src: im.src, alt: im.caption ?? 'A picture from Claude', loading: 'lazy' }), im.caption ? h('figcaption', { text: im.caption }) : null));
      if (d.suggest) {
        const surf = adapter.surface?.(e) ?? {}, box = h('div', { class: 'tx-surface tx-suggest', role: 'note', 'aria-label': `Suggested text for ${e.field ?? e.title}` });
        box.style.background = surf.bg ?? ''; box.style.color = surf.fg ?? '';
        boxes.push([box, d.suggest]);
        const use = tool('Use this', 'Put the suggested text in the edit box', () => useSuggestion(e.id), { class: 'tx-tool tx-use', 'data-id': e.id });
        parts.push(h('div', { class: 'tx-reply-sub' }, h('span', { class: 'tx-ref-label', text: 'Suggested text' }), h('span', { class: 'tx-use-state', 'data-id': e.id })), box, use);
      }
      if (d.replyAt) parts.push(h('p', { class: 'tx-reply-at', text: when(d.replyAt) }));
      return h('div', { class: 'tx-reply' }, ...parts);
    }));
    for (const [box, m] of boxes) box.innerHTML = modelHtml(M.toModel(m, mopts), parseCssColour(getComputedStyle(box).backgroundColor) ?? [255, 255, 255]);
    reflectSuggestions();
  }
  // Each suggestion's Use this: off while its text is done (locked) or already says it.
  function reflectSuggestions() {
    if (!repliesEl) return;
    for (const b of repliesEl.querySelectorAll('.tx-use')) {
      const e = byId.get(b.dataset.id), d = editOf(b.dataset.id);
      if (!e || !d?.suggest) continue;
      const inUse = norm(nowOf(e)) === norm(d.suggest), lk = isLocked(e);
      b.disabled = inUse || lk;
      b.title = lk ? 'Done: tap Done to change this text first' : inUse ? 'The edit box already says this' : 'Put the suggested text in the edit box';
      const st = repliesEl.querySelector(`.tx-use-state[data-id="${CSS.escape(b.dataset.id)}"]`);
      if (st) st.textContent = inUse ? 'In the edit box' : lk ? 'Tap Done to change it' : '';
    }
  }
  function useSuggestion(id) {
    const d = editOf(id), e = byId.get(id);
    if (!d?.suggest || !e || isLocked(e)) return;
    if (S.cur?.id !== id) select(id, { scroll: false });
    remember();
    apply(M.toModel(d.suggest, mopts), null);
    flash('The suggestion is in the edit box: it saves like any edit.');
  }
  function buildItem(it) {
    const g = groupOf.get(it.group);
    pagers.length = 0;
    repliesSig = '';
    lockBtn = h('button', { type: 'button', class: 'tx-tool tx-lock', title: 'Done: this item is finished and locked (tap again to change it). Under To do the next one opens.', onclick: () => toggleLock(S.curS) });
    titleEl = h('h2', { text: itemTitle(it) });
    whereEl = h('p', { class: 'tx-where' });
    tabsEl = h('div', { class: 'tx-tabs', role: 'tablist', 'aria-label': 'Its texts' });
    fieldHost = h('div', { class: 'tx-field' });
    editPane.replaceChildren(
      h('div', { class: 'tx-nav' },
        h('button', { type: 'button', class: 'tx-back', onclick: () => { mount.dataset.view = 'list'; renderList(); list.querySelector('[aria-current="true"]')?.focus(); } }, '‹ All texts'),
        pager()),
      h('div', { class: 'tx-entry-head' },
        h('p', { class: 'tx-eyebrow', text: g?.title ?? it.group }),
        h('div', { class: 'tx-title-row' }, titleEl, lockBtn),
        whereEl,
        headBadges = h('p', { class: 'tx-badges' })),
      h('div', { class: 'tx-block' }, h('p', { class: 'tx-label', text: 'Preview' }), preview, previewNote),
      repliesEl = h('div', { class: 'tx-block tx-replies', 'aria-label': 'Replies from Claude', hidden: true }),
      tabsEl, fieldHost,
      h('div', { class: 'tx-nav tx-nav-end' }, pager()));
  }
  function showText(e) {
    const id = e.id, surf = adapter.surface?.(e) ?? {};
    surface.style.background = surf.bg ?? ''; surface.style.color = surf.fg ?? '';
    noteBox.value = editOf(id)?.note ?? '';
    whereEl.textContent = e.where ?? '';
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
    resetBtn = tool('Reset changes', 'Reset changes', () => { remember(); apply(M.toModel(e.text, mopts), null); });
    editLabel = h('p', { class: 'tx-label', text: 'Edit' });
    const many = S.curS.entries.length > 1;
    fieldHost.replaceChildren(
      origin,
      h('div', { class: 'tx-block tx-editor' }, editLabel, toolbar, tray, surface, warn,
        h('div', { class: 'tx-actions' }, saveState, resetBtn)),
      h('div', { class: 'tx-block' }, h('label', { class: 'tx-label', for: 'tx-note', text: many ? `Note for Claude (${e.field ?? e.title})` : 'Note for Claude' }), noteBox),
      h('details', { class: 'tx-block tx-details' }, h('summary', { text: 'Markup' }),
        h('p', { class: 'tx-help', text: '[b]bold[/b] · [i]italic[/i] · [u]underline[/u] · [c=name]colour[/c] or [c=#rrggbb] · {icon} · a new line = a line break' }), markupBox));
    renderTray(); renderSurface();
    origBox.innerHTML = modelHtml(M.toModel(e.base, mopts), parseCssColour(getComputedStyle(origBox).backgroundColor) ?? surfaceBg());
    changed();
    reflectLock();
    saveState.textContent = Object.hasOwn(S.pend, id) && !live ? 'Saved on this device; sent when the page reconnects' : pending(e) ? 'Saved · in the next build' : '';
  }
  markupBox.addEventListener('input', () => { if (Date.now() - typingMark > 1200) remember(); typingMark = Date.now(); S.model = M.toModel(markupBox.value, mopts); renderSurface(); changed(); });
  noteBox.addEventListener('input', () => queueSave());

  // ---------- The store ----------
  function setMode(mode, text) {
    S.mode = mode;
    status.textContent = text ?? { connecting: 'Connecting…', db: 'Edits save automatically and reach the game with the next build.', local: 'Edits are kept on this device only: use Copy the edits.' }[mode];
    status.dataset.mode = mode;
  }
  setMode('connecting');
  // Saves that waited on this device show at once, before the db answers.
  S.edits = withPending({}); S.locked = locksOf(S.edits);
  renderGroups(); renderList();
  const start = location.hash.slice(1);
  if (byId.has(start)) select(start, { scroll: false }); else mount.dataset.view = 'list';
  if (!S.cur && matchMedia('(min-width: 900px)').matches) select(reg.entries[0].id, { scroll: false });

  try { db = window.claude?.use ? await window.claude.use('db') : null; } catch { db = null; }
  if (!db) {
    S.edits = withPending(store.get(`${storageKey}:edits`) ?? {}); S.locked = locksOf(S.edits);
    setMode('local'); renderList(); if (S.cur) select(S.cur.id, { scroll: false });
    return;
  }
  // Connected: the db's documents come and every save waiting here is sent. Dropped: it reconnects by itself, a little
  // later each time (a fresh subscription is the db's only way back); a page whose access was withdrawn says so.
  let unsub = null, tries = 0, retryT = 0, slowT = 0;
  const why = (e) => e?.code ?? e?.message ?? 'no answer';
  function connect() {
    if (unsub) { try { unsub(); } catch { /* gone already */ } unsub = null; }
    live = null;
    const col = db.collection(collection);
    let first = true;
    const lost = (e) => {
      clearTimeout(slowT); live = null;
      if (why(e) === 'revoked') { setMode('retry', `This page lost its access to the saved edits (revoked). Your edits are kept on this device: reload the page to carry on.`); return; }
      tries += 1;
      const wait = [2, 5, 10, 20, 30][Math.min(tries, 5) - 1];
      setMode('retry', `The connection to the saved edits dropped (${why(e)}); reconnecting in ${wait} s. Your edits are kept on this device.`);
      clearTimeout(retryT); retryT = setTimeout(connect, wait * 1000);
    };
    clearTimeout(slowT);
    slowT = setTimeout(() => { if (!live) setMode('retry', 'Still connecting to the saved edits. Your edits are kept on this device.'); }, 8000);
    try {
      unsub = col.onSnapshot((snap) => {
        clearTimeout(slowT); live = col;
        const next = {};
        for (const d of snap.docs) next[d.id] = d.data();
        const merged = withPending(next);                      // a save waiting here wins until it is sent
        const curId = S.cur?.id;
        const theirs = curId ? merged[curId]?.markup ?? null : null, mine = curId ? record(curId)?.markup ?? null : null;
        const lockChanged = curId && Object.hasOwn(S.locked, curId) !== !!merged[curId]?.locked;
        S.edits = merged; S.locked = locksOf(merged);
        if (first) {
          first = false;
          setMode('db', tries ? 'Connected again: edits save automatically and reach the game with the next build.' : undefined);
          tries = 0;
          for (const id of Object.keys(S.pend)) send(id);
          if (curId) select(curId, { scroll: false }); else renderList();
          return;
        }
        // Another device changed the open text: take it, unless it is this view's own write coming back or this view
        // changed the text in the last few seconds (its own save follows).
        const echo = curId && Object.hasOwn(S.wrote, curId) && S.wrote[curId] === theirs;
        if (curId && ((!echo && theirs !== mine && Date.now() - S.localAt > 4000) || lockChanged)) select(curId, { scroll: false });
        else { renderList(); renderReplies(); }
      }, lost);
    } catch (e) { lost(e); }
  }
  connect();
}
