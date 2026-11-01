// Text editor kit: the rich-text markup and the editor's character model. Pure (no DOM): the editor page, the apply
// step (apply-edits.mjs) and a project's tests can all import it.
//
// The markup (one line of text, styles nest, an unclosed tag ends with the text):
//   [b]bold[/b]  [i]italic[/i]  [u]underline[/u]
//   [c=name]a palette colour[/c]  [c=#rrggbb]any colour[/c]
//   {name}       an icon from the project's icon set
//   \n or [br]   a line break
// Anything else is text: unknown tags, unknown icons, a closing tag with nothing open, a colour that is neither a
// palette name nor #rrggbb. A project's renderer reads the same grammar (Dungeon Raid: src/core/rich-text.js; its
// test keeps the two in step).
//
// `opts` everywhere: { icons: ['coin', …], palette: { name: [r, g, b] | { rgb: [r, g, b] }, … } }.

const TAG = /\[(\/?)(b|i|u|c|br)(?:=([^\]]+))?\]|\{(\w+)\}|\n/g;

export const rgbOf = (v) => (Array.isArray(v) ? v : v && v.rgb);

// A colour token (a palette name or #rrggbb, as written) when valid, else null.
export function colourToken(v, palette = {}) {
  if (!v) return null;
  const t = String(v).trim();
  if (Object.hasOwn(palette, t)) return t;
  return /^#[0-9a-f]{6}$/i.test(t) ? t.toLowerCase() : null;
}

// A token's [r, g, b] (null when unknown).
export function colourRgb(token, palette = {}) {
  if (!token) return null;
  if (Object.hasOwn(palette, token)) return rgbOf(palette[token]);
  const m = /^#([0-9a-f]{6})$/i.exec(token);
  return m ? [0, 2, 4].map((k) => parseInt(m[1].slice(k, k + 2), 16)) : null;
}

const plainStyle = () => ({ b: false, i: false, u: false, c: null });
export const sameStyle = (a, b) => a.b === b.b && a.i === b.i && a.u === b.u && a.c === b.c;

// The markup as a list of units, one per character, icon or break:
//   { k: 'ch', ch, s } | { k: 'icon', name, s } | { k: 'br' }, s = { b, i, u, c: token | null }.
export function toModel(markup, { icons = [], palette = {} } = {}) {
  const out = [], stack = [];
  const style = () => {
    const s = plainStyle();
    for (const e of stack) { if (e.tag === 'c') s.c = e.c; else s[e.tag] = true; }
    return s;
  };
  // One unit per UTF-16 code unit, as the DOM counts a selection's offsets.
  const text = (t) => { const s = style(); for (let k = 0; k < t.length; k++) out.push({ k: 'ch', ch: t[k], s }); };
  const src = String(markup ?? '');
  let last = 0;
  for (const m of src.matchAll(TAG)) {
    text(src.slice(last, m.index)); last = m.index + m[0].length;
    if (m[0] === '\n' || m[2] === 'br') { out.push({ k: 'br' }); continue; }
    if (m[4] !== undefined) { if (icons.includes(m[4])) out.push({ k: 'icon', name: m[4], s: style() }); else text(m[0]); continue; }
    const tag = m[2];
    if (m[1]) {
      const k = stack.map((e) => e.tag).lastIndexOf(tag);
      if (k >= 0) stack.splice(k, 1); else text(m[0]);
    } else if (tag === 'c') {
      const c = colourToken(m[3], palette);
      if (c) stack.push({ tag, c }); else text(m[0]);
    } else stack.push({ tag });
  }
  text(src.slice(last));
  return out;
}

// The model as markup, canonical: tags open in the order colour, bold, italic, underline and close as late as they
// can; breaks as \n (tags stay open across a break).
export function toMarkup(model) {
  let out = '';
  const open = [];                                             // [{ tag, v }]
  const want = (s) => [...(s.c ? [{ tag: 'c', v: s.c }] : []), ...['b', 'i', 'u'].filter((t) => s[t]).map((tag) => ({ tag }))];
  const sync = (list) => {
    let k = 0;
    while (k < open.length && k < list.length && open[k].tag === list[k].tag && open[k].v === list[k].v) k++;
    while (open.length > k) out += `[/${open.pop().tag}]`;
    for (const t of list.slice(k)) { out += t.tag === 'c' ? `[c=${t.v}]` : `[${t.tag}]`; open.push(t); }
  };
  model.forEach((u, k) => {
    if (u.k === 'br') {                                        // close what the next line does not carry on
      const next = model.slice(k + 1).find((v) => v.k !== 'br');
      const w = next ? want(next.s) : [];
      let n = 0;
      while (n < open.length && n < w.length && open[n].tag === w[n].tag && open[n].v === w[n].v) n++;
      sync(open.slice(0, n));
      out += '\n';
      return;
    }
    sync(want(u.s));
    out += u.k === 'icon' ? `{${u.name}}` : u.ch;
  });
  sync([]);
  return out;
}

// Normalised markup (parsed and written back): what the editor stores, so equal texts compare equal.
export const normalise = (markup, opts) => toMarkup(toModel(markup, opts));

// The plain text (icons dropped, breaks as spaces).
export const plainText = (markup, opts) => toModel(markup, opts).map((u) => (u.k === 'ch' ? u.ch : u.k === 'br' ? ' ' : '')).join('').replace(/ +/g, ' ').trim();

// ---------- Edits on the model (all return a new model) ----------

const restyle = (u, f) => (u.k === 'br' ? u : { ...u, s: f({ ...u.s }) });

// Bold / italic / underline over [from, to): off when every unit there has it, else on.
export function toggle(model, from, to, key) {
  const span = model.slice(from, to).filter((u) => u.k !== 'br');
  const on = !span.length || !span.every((u) => u.s[key]);
  return model.map((u, k) => (k >= from && k < to ? restyle(u, (s) => ({ ...s, [key]: on })) : u));
}
export const isOn = (model, from, to, key) => {
  const span = model.slice(from, to).filter((u) => u.k !== 'br');
  return span.length > 0 && span.every((u) => u.s[key]);
};
export const setColour = (model, from, to, c) => model.map((u, k) => (k >= from && k < to ? restyle(u, (s) => ({ ...s, c })) : u));
export const clearStyle = (model, from, to) => model.map((u, k) => (k >= from && k < to ? restyle(u, () => plainStyle()) : u));

// The style typed text takes at `at`: the unit before it (a break or the start: the one after it, else plain).
export function styleAt(model, at) {
  for (const k of [at - 1, at]) { const u = model[k]; if (u && u.k !== 'br') return { ...u.s }; }
  return plainStyle();
}

// Replace [from, to) with `units` (text: a string, styled as at `from`; or ready units).
export function insert(model, from, to, units) {
  const s = styleAt(model, from);
  const list = typeof units === 'string'
    ? units.replace(/\r\n?/g, '\n').split('').map((ch) => (ch === '\n' ? { k: 'br' } : { k: 'ch', ch, s }))
    : units.map((u) => (u.k === 'br' || u.s ? u : { ...u, s }));
  return [...model.slice(0, from), ...list, ...model.slice(to)];
}

// The word around `at` (letters, digits, apostrophes and the icons glued to them), as [from, to); null outside one.
export function wordAt(model, at) {
  const inWord = (u) => u && (u.k === 'icon' || (u.k === 'ch' && /[\p{L}\p{N}'’%-]/u.test(u.ch)));
  if (!inWord(model[at]) && !inWord(model[at - 1])) return null;
  let a = at, b = at;
  while (inWord(model[a - 1])) a--;
  while (inWord(model[b])) b++;
  return a < b ? [a, b] : null;
}

// Placeholders (%name%) a text must keep: those of `base` missing from `markup`.
export const placeholders = (s) => [...new Set(String(s ?? '').match(/%\w+%/g) ?? [])];
export const missingPlaceholders = (base, markup) => placeholders(base).filter((p) => !String(markup).includes(p));
