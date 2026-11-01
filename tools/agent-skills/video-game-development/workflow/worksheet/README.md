# Worksheets (decisions)

The `decision-worksheet` skill, bundled here: `template.html` beside this guide is the page.

When a piece of work leaves **more than 5 decisions** for the user, don't list them in chat. Publish a
worksheet and reply with a short summary and the link. **5 or fewer** stay a numbered text message
(1, 1.1, 1.2.1) that the user can answer by number.

## Keep it small and quick (owner, 2026-10-06)

- **One screen (or one tab) per sheet**, about **8 questions at most**. More than that means the work is
  sliced too coarsely: split it per screen and send the first sheet now. (A 26-question sheet over four tabs,
  then 31 mockups, was slow to make and slow to answer.)
- **Build it yourself, directly**, from captures you take or already have: no agents, no proposal panels, no
  judges. A sheet redo should take minutes; the owner expected "10 min tops".
- **The user designs.** Questions are over today's screens (pictures of the build); offer concrete options and
  a recommendation, but don't design the answer for them first. Mock up only what the answers ask for, **one
  screen at a time** ("produce only one mockup ... to start with").
- **Options as pictures, not numbers**: render each option (a capture of the real build or a mockup) and label it
  in plain words; "18-px slots vs 53-px frames" alone was not understood (owner, 2026-10-06: "running simulations
  is a tremendous time saver").
- If the user changes direction while answering, stop, record the new direction, and redo the sheet briefly
  (only what changed).

## Build it

1. Copy `template.html` (next to this file) into the project, e.g. `tools/decision-sheets/<topic>/<topic>-decisions.html`,
   so it is versioned with the work it decides.
   **Then give it the project's look** (the owner, 2026-10-16: "I notice the Crawl worksheets and such look like Dungeon Raid's - but they should look like the style you chose for the project board"): the template's default is Dungeon Raid's. Restyle its
   `:root` tokens and fonts to the project board's colours, type and corners once, in a look file every sheet of the
   project passes through (Crawl: `tools/decision-sheets/crawl-look.cjs`), never sheet by sheet.
2. Fill in the `SHEET` object at the top of its script (everything else stays as is):
   - `title`: a two-to-four-word name ("WEB-11 Layout Decisions"); `storageKey`: a short unique key.
   - **Set the page's `<title>` to the same name** (the template's says SET ME): the artifact gallery shows the HTML
     `<title>`, not the heading the script sets, so sheets left on the template's title all look alike there (owner,
     2026-10-12: "You made 3 sheets with the same name - don't do that in the future"). Make the name unique: start it
     with the project ("Crawl: Puzzle Encounters") and give a second sheet on a topic its own words ("Signature Deeds 2").
   - `sections`: numbered `1`, `2`… Each question is numbered under its section (`1.1`) and each option under its
     question (`1.1.1`); a question that is the whole section is `2` with options `2.1`, `2.2`. Keep the numbers
     stable once the user has seen them.
   - **One decision per section** (owner, 2026-10-06: "too many decisions per section"): each section is one
     picture (or a few of the same thing) and one question; put `group: 'Race tab'` on the first section of a run
     to head the group.
   - Every section without a question gets a comment box of its own automatically (db id `c<section>`), so the
     user can comment on any part (owner, 2026-10-04); it is not counted as a question.
   - Every question gets 2–4 concrete options. Mark what the current build already does with `tag: 'built'`
     ("Built now", kept until the user answers) and a recommendation with `tag: 'rec'`. Add "Something else
     (say what in the comment)" when the options may not cover it. Every question has a comment box automatically.
   - Put choices the user can make themselves elsewhere (e.g. fine placement in an editor) as a pointer in the
     lede, not as questions.
   - Art tasks the user can do faster in their own tools (Photoshop: cut-outs, matting, repainting, exports) are
     offered as an option with an exact asset brief: file name and path, size, format and transparency.
   - Small defaults you are applying go in a final "Defaults I am applying" section: **one list with one
     question** ("All fine / Change some"), not one question each (owner, 2026-10-06).
3. Pictures: show the current build for every visual question. Capture the screens (headless or the browser pane)
   at the sizes the user really sees (the phone viewer, e.g. 390 × 705), combine them into labelled side-by-side
   JPEGs (about 300 px per phone screen, quality ~88), and save them next to the page. Reference them by relative
   path in `figure.src`; a section may take `figures: [...]`. Tapping a picture opens it full screen at full size,
   finger-scrollable, with − / + zoom (owner, 2026-10-06): keep that part of the template.

## Check before every publish

1. Every `figure.src` the page references is in this publish's `files` or already in the artifact (`action:
   "list"`, `scope: "files"`): a picture added later and left out shows as a broken image (owner, 2026-10-06).
2. Open it locally (any static server): click an option and see the counter change; tap a picture and see it full
   size; the page doesn't scroll sideways at phone width. Locally the db is absent, so answers fall back to this
   device.
3. One decision per section; the defaults are one list; about 8 questions at most.

## Publish

Publish with the Artifact tool: `file_path` = the page, `files` = the figures, `capabilities: {db: {}}`,
`icon: "checklist"`, and a one-sentence description. Republish to the same path after changes.

## Read the answers

The answers are documents in the artifact's db collection `answers`, one per question id:
`{ choice: '1.1.2', comment: '…', updatedAt }`. Read them with the ArtifactData tool (`action: "list"`,
`collection: "answers"`) when the user says they have answered. Treat comments as the user's answers, apply them,
and record each decision wherever the project records decisions.

## Reply

Say in one or two sentences what the sheet covers and how many questions it has, note any art tasks offered,
and end the reply with the sheet's link as the very last line.
