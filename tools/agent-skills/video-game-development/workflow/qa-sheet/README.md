# QA sheets (tests)

Every slice or phase the owner should check gets a QA sheet: one card per behaviour, each with a link that opens the
test build **in exactly the state the test needs**, what to do, what to expect, and Pass, Fail or Skip with a note.
The owner works through it on the phone; results save to the sheet's db and Claude reads them back. Sheets are
"great to provide per-item feedback without being lost and drowned in a sea of chat messages" (the owner).

## What the game needs first: links that build a state

A QA sheet is only as good as its links. Give the build dev links (a URL hash, or `?scenario=`) that set up any state
in one tap: a board, a class, a level, an enemy with given stats, a pop-up open, a moment just before game over.
Each link also carries **its own test storage** (a namespace token such as `-nsqa07`, and `-fresh` to start empty),
so tests never touch the owner's real progress or each other. When a phase needs unlocked content, the published
build opens with a test save that has it. (The main guide: QA states and the scenario loader.)

## Build a sheet

1. Copy `template.html` (beside this guide) into the project, e.g. `tools/qa-sheets/<phase>/<phase>-tests.html`.
   **Then give it the project's look** (the owner, 2026-10-16: "I notice the Crawl worksheets and such look like Dungeon Raid's - but they should look like the style you chose for the project board"): the template's default is Dungeon Raid's. Restyle its
   `:root` tokens and fonts to the project board's colours, type and corners once, in a look file every sheet of the
   project passes through (Crawl: `tools/decision-sheets/crawl-look.cjs`), never sheet by sheet.
2. Set the page's `<title>` to the sheet's name (the gallery shows it), then fill in the `SHEET` object:
   `title`, `storageKey`, `base` (the test build's URL ending in `#`), `lede`, `notes` (what this round is),
   `sections` with their `tests`.
3. Each test: `id` (stable; never reuse one the owner has marked), `link` (the state), `name`, `test`, `expect`.
   Write the expectation so a Fail is unambiguous ("the score reads 1,250, in white"), and say on the card when the
   test needs a computer, fullscreen or the phone held a certain way.
4. Pictures: a test that changes what the owner sees may carry `pic: { now, before, note }`: two captures of the same
   size (the new build and the previous one, at the phone's size); holding the picture shows the old one in place.
   Publish the pictures with the sheet (`files`).
5. **One sheet per phase**, its tests only. A later round of fixes is a new section on the same sheet with new ids
   ("Round 2"), so the history stays readable.
6. Prefer a small generator script per project (the data in one file per sheet, the template filled in by the
   script) once there are several sheets; validate the data with `node` before publishing: one stray quote in a
   test's text breaks the whole page.
7. Before publishing, open the page once (headless or in a browser) and check that it throws no error and that the
   line under the tally leaves "Connecting to saved results…": a page that stops after drawing its cards still
   takes taps but never connects, and the owner's marks stay on their device (a Dungeon Raid sheet, 2026-10-15).
   The template keeps every mark on the device too and sends the ones made before the db answered (or while it
   could not be reached) as soon as it does, and its status line names what it is waiting for.

## Publish and read back

Publish with `capabilities: {db: {}}` and `icon: "eyeframe"`; republish to the same URL for new rounds. When the
owner says the sheet is done, read the db collection `results` (ArtifactData list): one document per test id,
`{ status: 'pass' | 'fail' | 'skip' | '', comment, updatedAt }`. Treat every comment as the owner's word: fix the
fails and the notes, then add the next round's section. A test left unmarked may be one the owner judged
irrelevant: ask, don't assume.

## Test where the owner tests

Check the build at the owner's sizes before sending the sheet: the claude.ai viewer on a phone (about 390 x 705),
fullscreen with the system bars, and the smallest phone supported. The full regression waits for the release; per
phase it is the test suite, the phase's tests and these sizes.
