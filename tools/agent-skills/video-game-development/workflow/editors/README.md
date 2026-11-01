# Editors on request

The owner often wanted to change a small thing in a very specific way: a glow's softness, a vibration's rhythm,
where a button sits on one screen size, the wording of a tooltip. Rounds of "a bit more, a bit less" in chat are
slow; an editor is fast. When the owner asks for a tweak that will take more than one round, **build them an
editor for that one aspect** and let them tune it themselves.

## The pattern ("[x] Editor")

1. **One aspect per editor**: only its controls (sliders, pickers, a text box, a pad to tap a rhythm), named in the
   owner's words.
2. **A live preview drawn by the game's own code**: publish the game's modules the preview needs next to the editor
   (at their repo paths) and import them, so what the owner sees is exactly what the game will draw. Never imitate
   the game's look in the editor's own CSS.
3. **Saves as it goes** to the editor's db (one document per item, plus the owner's note); nothing is sent by hand.
4. **Claude applies** the saved values to the project (its config, the overrides file), with a test where it makes
   sense, then republishes the game and lists the editor on the board as a tool.
5. **"Back to the game's values"**: one button resets the controls to what the build has now.
6. **Done, notes and filters**: when the owner goes through many items, the standard below.

Dungeon Raid's editors, as examples:

| Editor | What it tuned | How |
|---|---|---|
| Text editor | every on-screen text: wording, bold, colours, the tile icons in a line | the kit in `text-editor/` (below) |
| Style tuner | the selected buttons' glow, the banners, the badges' shine | sliders over previews drawn by the game's views; values into the config |
| Buzz editor | the phone's vibration for each moment | hold a pad in rhythm with the moment's sound; drag the beats; the patterns go into the haptics table |
| Screen layout editor | each screen's groups at every phone size | drag or nudge a group on the real screen, recorded at thirteen sizes; offsets saved per screen |
| Tooltip preview | every skill's tooltip, the original's beside the new one | read-only: a picture to decide from |

## Every tool the owner tunes: Done, notes, filters, nothing lost (the standard)

Every tool where the owner goes through many items and tunes them (effects, sounds, vibrations, styles, texts) works
the same way, so the owner always knows what is finished and what is waiting on Claude (the owner, 2026-10-15/16: "add
a lock checkmark to each effect ... allow to filter by this tag ... a note per effect to tag you in it"; then "I lost
all my work" when a connection dropped, and a saved note that read "Not saved yet"). The reference build is Dungeon
Raid's Particle Playground (`tools/fx-playground/`: `index.html`, `playground.js`); Crawl's SFX tool follows it.

1. **A card per item**: its name in the owner's words, where it shows, **Play** (the item whole, in context: with what
   happens around it in the game, the real moment where it can be triggered), **Edit** (its settings, folded), a
   **Note to Claude** box with its own Save, and a "Note for Claude" badge on the card when it has one.
2. **Mark done**: a padlock button, "Mark done" / "Done" (`aria-pressed`). Done saves the item as it stands and locks
   its settings (a disabled fieldset) until it is tapped again. The owner's Done is their sign-off for that item.
3. **Two status lines**, never one for both: the settings' at the card's foot ("Settings not saved yet (kept on this
   device)", "Settings saved on this device; sent when the page reconnects", "Settings saved") and the note's in the
   note box (the same three for the note).
4. **A filter bar** at the top, sticky: All, To do, Done, With a note, each with its count; a group heading hides when
   none of its cards shows.
5. **The db**: one document per item, `{ recipe (or values), savedAt, locked, lockedAt, note, noteAt }`; a save writes
   the whole document (what is there plus the change).
6. **Nothing is ever lost**:
   - every change and every typed note is kept in the browser as it is made (localStorage, a quarter of a second after
     the last change, and on `pagehide`), and comes back on a reload, before the db answers;
   - a save shows at once and waits on the device until the db has it; if the connection is down it is sent when the
     page reconnects;
   - a dropped connection (the `onSnapshot` error) reconnects by itself, a little later each time (2, 5, 10, 20, 30 s:
     a fresh subscription is the db's only way back), and the status line says why it dropped (the error's `code`);
     `revoked` asks for a reload, which loses nothing;
   - on each snapshot a waiting save wins until it is sent, a change made here after the db's save stays a change,
     otherwise the db's version shows; rebuild only the cards whose saved content changed (redrawing every card on
     every snapshot loses a note being typed).
7. **Claude's loop**: read the collection (ArtifactData list to a folder), put the Done items' values into the project
   with a script that compares field by field and prints each change (treat a field missing from an older save as its
   default), answer every note in the reply naming its item (or do what it asks), add the tests, republish the game and
   the tool, update the board. Notes stay in the db as the record; a new note on an item is a new request.
8. **Test it before publishing** with a stand-in for the db (a mock `window.claude.use('db')` served with the page)
   that can drop the connection on demand: a change kept across a reload, a save made while dropped sent after the
   reconnect, the two status lines.

## The text editor kit (`text-editor/`)

A ready editor for a project's texts, project-independent: `kit/markup.js` (the markup and its model), `kit/editor.js`
and `kit/editor.css` (the page), `kit/apply-edits.mjs` (writes the saved edits into the project's overrides file).

- **The markup**: `[b]bold[/b]`, `[i]italic[/i]`, `[u]underline[/u]`, `[c=name]colour[/c]` or `[c=#rrggbb]`, `{icon}`,
  `\n` or `[br]` for a line break; `%name%` marks a word the program fills in (the editor warns when an edit drops
  one, and the apply step refuses it). The game's renderer reads the same grammar (port `toModel`, with a test).
- **Set up**: a registry of every text (`tools/text-editor/registry.json`, built by a script from the text tables:
  id, group, title, where it shows, kind, `live`, `base`, `text`, `params`); an overrides file the program reads
  through `textOf(id, fallback)`; an adapter (`tools/text-editor/adapter.js`: colour names, `iconUrl`, `surface`,
  `preview(entry, markup, host)` drawing with the project's own code); the page, which boots the kit:
  ```html
  <script type="module">
  import { boot } from './kit/editor.js';
  import adapter from './tools/text-editor/adapter.js';
  boot({ mount: document.getElementById('app'), registryUrl: 'tools/text-editor/registry.json', adapter,
    collection: 'edits', storageKey: '<project>-texts' });
  </script>
  ```
- **Publish** with `capabilities: {db: {}}` and `icon: "wrench"`; `files`: the kit's three page files, the adapter, the registry and every
  file the adapter imports, at their repo paths.
- **The loop**: the owner edits (each text saves itself to `edits/<id>`); before a build, read the edits
  (ArtifactData list), apply them (`node kit/apply-edits.mjs --registry … --out <overrides file> --edits <dir>`),
  rebuild the registry, run the tests, publish, then delete the applied edit documents in one batch (a text marked
  done keeps its lock and note: remove only its `markup` and `from`). A note on an edit is a request: answer it.
- **The standard** (above) is built in: Mark done per text (the padlock), the Show chips with counts (All, To do,
  Done, In the game, Edited, Waiting), saves that wait on the device until the db has them, and a dropped connection
  that reconnects by itself (Dungeon Raid's owner, 2026-10-16: "Add a "locked" function to this sheet, with the
  ability to filter out locked ones").
