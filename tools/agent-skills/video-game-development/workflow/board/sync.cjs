// The project board (workflow/board/README.md): items.json beside this script is the list of every artifact of the
// project; the board's cards live in its db, collection "items", one document per artifact id. The owner sets each
// card's status (and may add a note: userNote); Claude owns the rest. To update the board at a release:
//   1. edit items.json (a new artifact: a new entry, its "status" the column it starts in, usually "review"; a changed
//      one: its note, version and updated date);
//   2. list the board's cards: ArtifactData list, the board's url, collection "items", query.limit 1000, out_dir <dir>
//      (each card is saved as <dir>/items/<id>.json, its fields only; the listing prints each one's version);
//   3. node tools/artifact-board/sync.cjs <dir>/items > writes.json: new cards become sets; a changed card needs its
//      version from the listing, passed as --v <id>=<version>,<id>=<version> (the script names the ones it needs);
//      --batch <n> prints the n-th 50 (a batch takes at most 50 writes);
//   4. ArtifactData batch with those writes (new cards: set; existing ones: update pinned with if_version, Claude's
//      fields only, never status, statusAt or userNote).
//   5. The owner moves a card to Ready for Claude when they are done with it (owner, 2026-10-15): check that column at
//      the start of a session and whenever the owner says the board changed (ArtifactData query, where status ==
//      "ready"); move a card you pick up to "claude", and to "review" when its next round is published (an update of
//      status and statusAt, pinned with if_version). A card with nothing left (every test passed, or the owner
//      calls it finished) goes to "done" (owner, 2026-10-15). Never touch userNote.
const fs = require("fs"), path = require("path");
const dir = process.argv[2];
if(!dir){ console.error("usage: node sync.cjs <dir holding the listed cards (<id>.json)> [--v id=version,...] [--batch n]"); process.exit(1); }
const arg = (name) => { const i = process.argv.indexOf(name); return i > 0 ? process.argv[i + 1] : undefined; };
const versions = Object.fromEntries((arg("--v") || "").split(",").filter(Boolean).map((p) => p.split("=")));
const items = JSON.parse(fs.readFileSync(path.join(__dirname, "items.json"), "utf8"));
const docs = Object.fromEntries((fs.existsSync(dir) ? fs.readdirSync(dir) : []).filter((f) => f.endsWith(".json"))
  .map((f) => [path.basename(f, ".json"), JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"))]));
const MINE = ["title", "type", "topic", "note", "updated", "version", "order", "link"]; // Claude's fields; the owner's are status, statusAt, userNote
const writes = [], missing = [];
for(const { id, status, ...rest } of items){
  const cur = docs[id];
  if(!cur){ writes.push({ op: "set", collection: "items", doc_id: id, data: { ...rest, status: status || "review", addedAt: new Date().toISOString().slice(0, 10) } }); continue; }
  const change = {};
  for(const k of MINE) if(rest[k] !== undefined && JSON.stringify(rest[k]) !== JSON.stringify(cur[k])) change[k] = rest[k];
  if(!Object.keys(change).length) continue;
  const v = Number(versions[id]);
  if(!v) missing.push(id);
  writes.push({ op: "update", collection: "items", doc_id: id, data: change, if_version: v });
}
const gone = Object.keys(docs).filter((id) => !items.some((it) => it.id === id));
if(gone.length) console.error(`on the board but not in items.json (left alone): ${gone.join(", ")}`);
if(missing.length){ console.error(`these cards changed: pass their versions from the listing, --v ${missing.map((id) => `${id}=<version>`).join(",")}`); process.exit(2); }
const n = arg("--batch") !== undefined ? Number(arg("--batch")) : -1;
process.stdout.write(JSON.stringify(n >= 0 ? writes.slice(n * 50, n * 50 + 50) : writes));
console.error(`${writes.length} writes (${writes.filter((w) => w.op === "set").length} new cards)${writes.length > 50 ? `: ${Math.ceil(writes.length / 50)} batches, pass --batch 0, 1 ...` : ""}`);
