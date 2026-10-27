# The project board

A game makes many artifacts: test builds, tools (editors, tuners, benches, galleries), worksheets and QA sheets.
The owner keeps track of them on one Kanban board per project: "a simple Trello-like Kanban board with all the
artifacts that also lists their type" (the owner).

- **One card per artifact**: its name (a link to it), its type (game, tool, worksheet, QA sheet, report, page), a
  topic group, its version and date, and a short note from Claude on where it stands.
- **Every reply ends with the board's link** as its very last line (owner, 2026-10-17: "always finish your message [with] a link to the project board"), so the
  whole project is a tap away; a reply that released something puts the release's link on the line above it.
- **The status is the owner's**: five columns, To review, In review, Ready for Claude, With Claude, Done (tabs on a
  phone), a status picker on every card, drag and drop with a mouse, and a note field of the owner's own. Filters by
  type, topic and words.
- **Ready for Claude** is the owner's "I'm done with this sheet" (no chat message needed): check that column at the
  start of every session and whenever the owner says the board changed. A card you pick up goes to With Claude, and
  back to To review when its next round is published; a card with nothing left (every test passed, or the owner
  calls it finished) Claude moves to Done (owner, 2026-10-15). Claude never changes the owner's note.
- **In review** is the owner's own work in progress (owner, 2026-10-17: "If it's "In Review" it means I'm
  still working on it. Unless I explicitly say otherwise, I tend to work in piecemeal form so those things take me
  awhile"): the owner works piecemeal, so Claude never picks such a card up, applies what its tool has saved (a tuner's values, an
  editor's pieces, a sheet's half-given answers), or asks about it, unless the owner says so.
- **Ask Claude to check** (the owner, 2026-10-16): a button under the tally posts a comment on the board and sends it
  to the Claude sessions watching it (the `comments` capability's `sendToClaude`), listing the Ready for Claude cards.
  It is enabled only while a Claude session watches the board (one that published it, or watches it with
  ArtifactComments); otherwise it says why. The comment arrives in that session as a turn: check the Ready column
  then, and answer in the comment's thread. Only the project's own session watches its board: any other
  session that publishes it (a skill session, say) stops its watch afterwards (ArtifactComments watch, on: false), or
  the press reaches a session without the context (2026-10-16: the first press reached the skill session).
- **The cards live in the board's db** (collection `items`, one document per artifact id), never in the page, so an
  update needs no republish.
- **The work coming up** (the owner, 2026-10-15: "add all the future stuff as tickets, maybe in a SLICE category,
  so I'll see what's up next"): every planned slice or phase, every task Claude owes and the post-launch slices are
  cards of the type `slice` (id `slice-…`; no artifact, so no link unless the card sets `link`), With Claude, in plan
  order (`order`: the board sorts slices by it), post-launch ones in the topic `later`. A built slice's sheets get
  cards of their own; the slice card goes to Done when it is signed off. Add one the moment a slice is planned.
- **The owner's own work** (Dungeon Raid's owner, 2026-10-16: "Transform this into its own ticket"): anything only the
  owner can do (an art file in their own tools, a dashboard set-up such as connecting Cloudflare, a pass in an editor)
  is a card of the type `task` (id `task-…`, version "your task"), in To review, with the steps in its note (a line
  each: the board keeps a note's line breaks), the exact file names, sizes and addresses, and a link to where it is
  done. Its last line says what happens next ("move this card to Ready for Claude when it's done"). Crawl's
  `task-cloudflare` is the model (`site/` has its text).

## Files

| File | What it is |
|---|---|
| `board.html` | The page. Set its title, the lede and `TOPICS` (the project's groups) to suit the project. |
| `items.example.json` | The list the repository keeps (`tools/artifact-board/items.json`): one line per artifact. |
| `sync.cjs` | Turns the list into the db's writes: new cards are created in their starting column; existing ones get only Claude's fields (title, type, topic, note, version, date). Its header has the steps. |

## Set it up

1. Copy the three files to `tools/artifact-board/` (the list as `items.json`), adapt the page, publish it with
   `capabilities: {db: {}, comments: {}}` and `icon: "grid"`, and add a card for every artifact so far (`node sync.cjs <empty dir>` gives the writes;
   send them with one ArtifactData batch, at most 50 at a time).
2. Write the board's link into the project's CLAUDE.md with the rule below.
3. **The board's look is the project's look**: take it from the game, and give every sheet the same (SKILL.md §11.1, one
   look per project). The page here ships Dungeon Raid's colours and type: restyle them first.

## Keep it current

At every release and with every new sheet, tool or report: edit `items.json` (a new artifact: a card starting in "To
review"; a changed one: its note, version and date), list the board's cards (ArtifactData list, collection `items`,
`out_dir` in the scratchpad: each card's version is printed), run `node sync.cjs <dir>/items --v id=version,…` and
send its writes in one batch (pinned with `if_version`). Name the board in the reply.
