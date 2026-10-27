#!/usr/bin/env node
// Text editor kit: apply the owner's edits to the project's overrides file.
//
//   node apply-edits.mjs --registry <registry.json> --out <overrides.js|overrides.json>
//        [--edits <edits.json | a folder of <id>.json docs>] [--set <id>=<markup>]… [--dry]
//
// --edits takes { id: markup }, [{ id, markup }], or the folder ArtifactData `list … out_dir` writes (one
// <id>.json per edit, its `markup` field; docs without one, e.g. a note only, are skipped). An edit equal to the
// entry's `base` (the source table's text) removes the override; any other sets it. Unknown ids and texts that lose
// a %placeholder% are reported and skipped. The overrides are written in the registry's order.
//
// The overrides file: .json = the object itself; .js = a module whose object sits between the lines
// `// <text-overrides>` and `// </text-overrides>` (everything outside the object's braces is kept as it is).
import fs from 'node:fs';
import path from 'node:path';
import { normalise, missingPlaceholders } from './markup.js';

const args = process.argv.slice(2);
const opt = (name) => { const k = args.indexOf(name); return k >= 0 ? args[k + 1] : null; };
const sets = args.flatMap((a, k) => (a === '--set' ? [args[k + 1]] : []));
const registryPath = opt('--registry'), outPath = opt('--out'), editsPath = opt('--edits'), dry = args.includes('--dry');
if (!registryPath || !outPath) {
  console.error('usage: apply-edits.mjs --registry <registry.json> --out <overrides.js|.json> [--edits <file|dir>] [--set id=markup]… [--dry]');
  process.exit(2);
}

const registry = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
const entries = new Map(registry.entries.map((e) => [e.id, e]));
const mopts = registry.markup ?? {};

// ---------- The edits ----------
function readEdits(p) {
  if (!p) return [];
  if (fs.statSync(p).isDirectory()) {
    const out = [];
    const walk = (d) => {
      for (const f of fs.readdirSync(d)) {
        const q = path.join(d, f);
        if (fs.statSync(q).isDirectory()) walk(q);
        else if (f.endsWith('.json')) {
          const doc = JSON.parse(fs.readFileSync(q, 'utf8'));
          if (typeof doc.markup === 'string') out.push({ id: doc.id ?? f.slice(0, -5), markup: doc.markup });
        }
      }
    };
    walk(p);
    return out;
  }
  const j = JSON.parse(fs.readFileSync(p, 'utf8'));
  return Array.isArray(j) ? j : Object.entries(j).map(([id, markup]) => ({ id, markup }));
}
const edits = [...readEdits(editsPath), ...sets.map((s) => { const k = s.indexOf('='); return { id: s.slice(0, k), markup: s.slice(k + 1).replace(/\\n/g, '\n') }; })];

// ---------- The overrides file ----------
const START = '// <text-overrides>', END = '// </text-overrides>';
let before = '', after = '', overrides = {};
const isJs = outPath.endsWith('.js') || outPath.endsWith('.mjs');
if (fs.existsSync(outPath)) {
  const src = fs.readFileSync(outPath, 'utf8');
  let block = src;
  if (isJs) {
    const a = src.indexOf(START), b = src.indexOf(END);
    if (a < 0 || b < a) { console.error(`${outPath}: no ${START} … ${END} block`); process.exit(1); }
    block = src.slice(a, b);
    const o = block.indexOf('{'), c = block.lastIndexOf('}');
    before = src.slice(0, a) + block.slice(0, o);
    after = block.slice(c + 1) + src.slice(b);
    block = block.slice(o, c + 1);
  }
  overrides = JSON.parse(block);
} else if (isJs) {
  before = `${START}\nexport const TEXT_OVERRIDES = Object.freeze(`;
  after = `);\n${END}\n\nexport const textOf = (id, fallback) => (Object.hasOwn(TEXT_OVERRIDES, id) ? TEXT_OVERRIDES[id] : fallback);\n`;
}

// ---------- Apply ----------
const report = { set: [], removed: [], unchanged: [], skipped: [] };
for (const { id, markup } of edits) {
  const e = entries.get(id);
  if (!e) { report.skipped.push(`${id}: not in the registry`); continue; }
  const m = normalise(markup, mopts), base = normalise(e.base, mopts);
  const lost = missingPlaceholders(e.base, m);
  if (lost.length) { report.skipped.push(`${id}: loses ${lost.join(', ')}`); continue; }
  if (m === base) {
    if (Object.hasOwn(overrides, id)) { delete overrides[id]; report.removed.push(id); } else report.unchanged.push(id);
  } else if (overrides[id] === m) report.unchanged.push(id);
  else { overrides[id] = m; report.set.push(id); }
}
const order = [...entries.keys()];
const ids = Object.keys(overrides).sort((a, b) => (order.indexOf(a) >>> 0) - (order.indexOf(b) >>> 0));
const body = ids.length ? `{\n${ids.map((id) => `  ${JSON.stringify(id)}: ${JSON.stringify(overrides[id])}`).join(',\n')}\n}` : '{}';
const out = isJs ? before + body + after : `${body}\n`;
if (!dry) fs.writeFileSync(outPath, out);

for (const [k, v] of Object.entries(report)) if (v.length) console.log(`${k} (${v.length}): ${v.join('; ')}`);
console.log(`${dry ? 'would write' : 'wrote'} ${outPath}: ${ids.length} override(s)`);
if (report.skipped.length) process.exitCode = 1;
