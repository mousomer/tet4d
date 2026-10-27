---
name: text-editor
description: Set up, publish and run a rich-text editor artifact for a project's user-facing texts (a registry of every text, a live preview drawn by the project's own code, bold / italic / underline / colours / icons / line breaks, edits saved to the artifact's db), then apply the user's edits to the project. Use when the user wants to edit or review an app's texts, tooltips or copy themselves, or asks where a text lives.
---

# Text editor

The user edits the project's texts on a page instead of chasing them through the code. Claude builds a
**registry** (every text, where it shows), gives the editor an **adapter** (the project's preview), publishes, and
later **applies** the saved edits to an **overrides** file the project reads. The kit is project-independent:

| File (kit/) | What it is |
|---|---|
| `markup.js` | The markup grammar and the editor's character model (pure; Node and browser). |
| `editor.js`, `editor.css` | The page: list (search, groups, the Show chips with their counts: All, To do, Replies, Done, In the game, Edited, Waiting; one row per item, see Items), Previous / Next through the filtered list (above and under the open text), an item's texts as tabs over one preview, Mark done per item (a padlock: its texts locked until tapped again; a note can still be left; under To do the next item opens in its place, and nothing on the page moves), preview, the Original box (the text before any edit, read-only, with "Use the original"), toolbar and the edit box (the modified text, if any), Reset changes, note to Claude, Claude's replies (under the preview: the answer, pictures, a suggested text with Use this), raw markup; words the program fills in (`%name%`) highlighted in every box. Nothing is lost: every save waits on the device until the db has it, and a dropped connection reconnects by itself (2, 5, 10, 20, 30 s) and sends what waited (the video-game-development skill's standard for tuning tools). |
| `apply-edits.mjs` | Writes the edits into the overrides file (`.js` module with markers, or `.json`). |

## The markup

`[b]bold[/b]` · `[i]italic[/i]` · `[u]underline[/u]` · `[c=name]palette colour[/c]` or `[c=#rrggbb]` · `{icon}` ·
`\n` (or `[br]`) a line break. Tags nest; unknown tags, icons and colours stay text. `%name%` marks a word the
program fills in: the editor warns when an edit drops one and the apply step refuses it. The project's renderer
must read the same grammar: port `toModel` (or the project's own parser) and add a test that parses the same
samples with both (Dungeon Raid: `tests/text-editor.test.js`).

## Set it up in a project

1. **Registry** (`tools/text-editor/registry.json`, built by a script in the project that imports the text
   tables, never hand-written):
   ```json
   { "project": "Name", "format": 1,
     "markup": { "icons": ["coin"], "palette": { "health": [255, 70, 60] } },
     "groups": [{ "id": "tips", "title": "Help tips", "note": "…" }],
     "entries": [{ "id": "tip.8", "group": "tips", "title": "Tip 8 · Chain damage", "where": "When it shows",
       "kind": "bubble", "live": true, "original": "the first version (optional)", "base": "the source text",
       "text": "what the program shows now (override, else base)", "params": ["%class%"], "preview": {} }] }
   ```
   Ids are stable and use letters, digits, `.`, `_`, `-` (they are db doc ids and `#` links). `live`: the program
   reads the override today. Function texts: call them with `%name%` arguments.
   **Items** (Dungeon Raid's owner, 2026-10-19: "instead of showing two different list entries, show as one list item
   with multiple text values ... just for me, the user, not the structure of the DB"): the texts of one thing (a
   skill's name and description, a race's four) share a `subject` (any id: `"skill.4"`) and each has a `field` (its
   tab's name: "Name", "Description"); `heading: true` marks the text that names the item in the list (its current
   text), `subjectTitle` names it when none does. The list shows one row per item, the page a tab per text over one
   preview, Mark done takes the whole item, and under To do the next item opens in its place. The db still keeps one
   document per text. Group by the builder's id patterns; a registry without subjects works as before.
2. **Overrides** the program reads: `textOf(id, fallback)` over an object between `// <text-overrides>` and
   `// </text-overrides>` (apply-edits creates the file when missing). Wire it where each live text is used.
3. **Adapter** (`tools/text-editor/adapter.js`, default export, every member optional):
   `colourNames {name: label}`, `labels {earlier}` (the caption of an entry's `original` under the Original box;
   default "Earlier version"), `async init()` (load art; a throw only turns previews off), `iconUrl(name)` (an
   image URL for the icon picker and the edit box), `surface(entry) → {bg, fg}` (the edit box looks like where the
   text shows), `preview(entry, markup, host, {registry, byId, subject, textOf}) → {note}` (draw into `host` with the
   project's own rendering code; return a note such as the line count). `subject` is the open item (`{id, entries}`),
   `textOf(id)` any of its texts as it is now (the open one as typed): draw the whole item from them, so its parts
   always agree (a tooltip's title and body; Dungeon Raid's previews had shown a stale copy of the other half).
4. **Page** (`tools/text-editor/index.html`, no doctype): `<title>`, fonts, a `<style>` redefining the kit's
   `--tx-*` tokens on `:root` (the kit's defaults have no specificity; give a single-look page `color-scheme`), a
   `<div id="app">` and
   ```html
   <script type="module">
   import { boot } from './kit/editor.js';
   import adapter from './tools/text-editor/adapter.js';
   boot({ mount: document.getElementById('app'), registryUrl: 'tools/text-editor/registry.json', adapter,
     collection: 'edits', storageKey: '<project>-texts' });
   </script>
   ```

## Publish

Load the `artifact-design` and `artifact-capabilities` skills first (the page declares `db`). Publish the page as
the artifact's root with `capabilities: {db: {}}`, and in `files`: `kit/markup.js`, `kit/editor.js`,
`kit/editor.css` (from this skill's folder), `tools/text-editor/adapter.js`, `tools/text-editor/registry.json`
and every file the adapter imports or fetches, **at its repo path** (the adapter resolves the project's root as
`new URL('../../', import.meta.url)`). List the adapter's import graph with a small script rather than guessing.
On later publishes send only the changed files. After the first publish: one `ArtifactData list` of `edits`.
Without a browser in the session (cloud), smoke-test the page's DOM logic with jsdom in the scratchpad (a fake
adapter and a fake `db`) instead of a capture, and say so.

## The loop

The user does not hand edits over: **every build of the program carries them**. Before each build or publish, run
steps 2–4 (write that rule into the project's CLAUDE.md when you set the editor up). There is no "send to Claude"
button, by design.

1. The user edits; each text saves itself (`edits/<id>`: `markup`, `note`, `from` = the text it started from,
   `title`, `updatedAt`, and `locked` / `lockedAt` once the user marks it done); its badge reads "Next build". Without the db (signed out, local file) edits stay in the
   browser and a **Copy the edits** button (shown only then) gives a JSON to paste.
2. Read them: `ArtifactData list` (collection `edits`, `out_dir` in the scratchpad). Notes are requests: answer
   each **in the editor** (the user, 2026-10-21: "I added a bunch of notes to "marked as done" items ... the intention
   is for you to respond and send it back to me"; marking an item done only clears it from their To do list). Write
   the answer into the text's own doc with `ArtifactData update` (merge, pinned to the version you read): `reply`
   (plain text; a blank line between paragraphs), `replyAt`, optionally `suggest` (a proposed text as markup: the page
   draws it as the edit box does, with **Use this**) and `imgs` (`[{ src, caption }]`, pictures published with the
   page, e.g. under `notes/`), and send the item back by removing `locked` and `lockedAt` (`{"__delete__": true}`).
   The answer can sit on another text of the same item (a note on a name, the fix on the description): the page shows
   every reply of the open item, each under its text's name. The user finds them under **Replies** (answered, not done
   yet). Publish the page **before** the first reply of a session if its kit changed: an older page writes whole docs
   and would drop the reply fields. Cross-cutting questions (a style rule over many texts) go to the chat or a
   worksheet, not into each text's reply.
3. Apply: `node <kit>/apply-edits.mjs --registry tools/text-editor/registry.json --out <overrides file> --edits
   <out_dir>/edits` (or a pasted JSON file). It reports set / removed / skipped (unknown id, a lost
   placeholder). An edit equal to `base` removes the override.
4. Rebuild the registry, run the tests, commit, push, republish the program (its overrides file) and the editor
   (`registry.json`). Then delete the applied `edits` docs with one `ArtifactData batch` (keep the ones skipped,
   and tell the user why), so the list shows them as done. A doc marked done (`locked`) keeps its lock and its note:
   update it instead, removing only `markup` and `from` (`{"__delete__": true}`), so the text stays Done; its
   `reply`, `suggest` and `imgs` go with it once the user has seen them (delete them in the same update).

## Notes

- **A suggestion must stay usable on a done item** (the owner, 2026-10-23: "I missed that in the sheet, didn't see an
  active button"): Use this (and Use the original) stay active on an item marked done; pressing one opens the item
  again (unlocks it) with the text in the edit box. A reply that carries a `suggest` always sends its item back
  unlocked, and the reply says in words what the suggestion changes, so it can't be missed when the item was done.
- `from` lets you see when the program's text changed under an edit: if `from` ≠ the registry's `text`, show the
  user both before applying.
- A text that is not `live` is still edited and stored; say in the reply that it reaches the program when its
  screen reads the overrides.
- Keep the kit generic: project facts belong in the adapter, the registry builder and the page's tokens. Improve
  the kit here and copy it to `~/.claude/skills/text-editor/` on the PC so every project gets the change.
