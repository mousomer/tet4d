---
name: video-game-development
description: Playbook for making video games with the owner, from the first decisions to release - an original game built from the owner's answers (Crawl, Starlane), or a 1:1 faithful browser rebuild of an old or abandoned game or app (Android APK, Flash SWF/FLA, Construct, GameMaker, legacy binaries) by reverse engineering into a locked recipe book, a discrepancy register the owner decides, an emulator oracle, a responsive-layout bench and a line-by-line rebuild with book-derived tests and screenshot comparisons. Every project - vertical slices the owner signs off through published test builds and test sheets, numbered decisions and worksheets, and a Kanban board of every artifact (builds, tools, worksheets, QA sheets) whose statuses the owner sets, updated at every release; the workflow kit in workflow/ holds them ready to use (worksheet and QA sheet templates, the editors-on-request pattern and a text editor kit, the board, the working rules). Use when starting, planning, resuming or reviewing any game project.
---

# Video game development playbook

How to make a game with the owner without drifting, guessing or redoing work. It began as the faithful
recreation playbook, distilled from the Dungeon Raid project (an abandoned 2012 Android game rebuilt in
the browser), including everything that went wrong in the first attempt; Crawl (an original phone dice
crawler) added the original game's side and the artifact board (§11.1). The owner renamed it on
2026-10-13.

**Which parts apply.** A recreation follows all of it. An original game skips the reverse engineering
(§3), the oracle (§5) and the register's fidelity default (§4): the owner's answers on decision
worksheets are its specification, recorded in the plan file (`PLAN.md`), and every departure from them
is still a numbered decision. Everything else (vertical slices, test builds and test sheets, QA states,
numbered decisions, the artifact board, continuity) applies as written.

**The workflow kit** (`workflow/`, beside this file; §15): the pages and rules of working with the owner, ready to
use: decision worksheets, QA sheets, editors on request (with a text editor kit), the project board and the
working rules. Start with `workflow/README.md`.

The recreation method has two halves:

1. **Understand the original completely before building anything.** Extract it, decompile every
   function, and write a *recipe book*: a precise specification of how to build the game. Lock it
   when every function and every constant is accounted for. Check it against the running original.
2. **Rebuild it line by line from the book, in vertical slices.** Each slice is a complete, playable
   part of the game with its visuals, motion and sound. It is verified by tests that encode the book
   and by screenshot comparisons with the original, then published as a test build. The owner plays
   it, fills in a test sheet and signs it off before the next slice starts.

Every deviation from the original is a decision the owner makes, recorded in one register and
flagged in the code.

---

## 1. Principles (the creed)

1. **Fidelity is the default.** Rules, numbers, layout, motion, timing and sound match the original
   1:1. "Close enough", "modernised" or "probably" are not acceptable defaults.
2. **The owner decides every deviation.** Bugs, platform limits, dead features and wishes all go to
   the owner as numbered decisions. Nothing deviates silently.
3. **Understand first, build second.** Do not build on guesses. A throwaway proof of concept may
   validate assumptions (rendering, RNG shape, input), but it is scrapped afterwards, never extended.
4. **One source of truth per kind of fact.** The recipe book says how the original behaves. The
   discrepancy register says where the rebuild differs. The plan file says what is being built now.
   Nothing else is authoritative.
5. **Never judge your own work as done.** Hold every screen, animation and number up against the
   original (screenshot, recording, emulator) element by element before calling it finished.
6. **Presentation ships with the feature.** Never build logic first and "the juice" later. Each
   slice includes its art, layout, animation and sound, so the owner can verify it as it lands.
7. **The owner tests every slice on real devices.** Publish a test build at the end of every slice,
   plus a test sheet, and wait for sign-off.
8. **Make decisions easy to answer.** Number every question hierarchically (1, 1.1, 1.2.1) so the
   owner can reply "1.2.1 yes". Flag every new discrepancy with an unmissable banner in chat.
9. **Leave a trail for the next session.** Plan file, register, project CLAUDE.md status, memory,
   git tags. A fresh session must be able to continue from the files alone.
10. **Work directly, in small steps, at the owner's pace.** Do the work yourself with the context already
   loaded: one change, checked, committed and published at a time. Multi-agent runs are the exception, for
   genuinely big parallel jobs, and only with the owner's OK (§10.1).

---

## 2. Phase 0: intake and setup

**Goal:** everything the original consists of, in one git repository, with tools that can read it.

1. **Create the repo and commit the untouched originals first** (the APK/SWF/project files), then
   the extracted forms. Every later finding can then be traced to an unchanged source.
2. **Extract every layer** of the original:
   - Android APK: unzip (`extracted/`, assets and native libraries), apktool (`decoded/`, smali and
     resources), jadx (`decompiled_java/`, readable Java), the JNI export list. Keep the *original*
     APK separate from any patched one and record exactly how they differ.
   - Flash: JPEXS FFDec (ActionScript, symbols, timelines, frame rate, sounds, fonts).
   - Construct / GameMaker / similar: the project's event sheets or scripts, object and layout data.
   - Native code: a disassembler/decompiler that can run headless (Ghidra `analyzeHeadless` with
     Java scripts), so the whole binary can be processed by script, not by clicking.
3. **Install the toolchain outside the repo** (JDK, Ghidra, Android SDK and emulator, Node, Python)
   and note where it lives in the project notes. Verify it with a smoke test before long sessions.
4. **Catalogue every external reference**: gameplay videos (with timestamps of the moments that
   matter), store screenshots, wiki pages, the developer's own descriptions. Write the catalogue to a
   file (`docs/reference/external-sources.md`). These are the visual ground truth later.
5. **Start a lab notebook** (`NOTES.md`): a dated, chronological log of findings, dead ends and
   corrections. It is the only place where history lives.

---

## 3. Phase 1: reverse engineering into a recipe book

### 3.1 Scope the original

- List every exported entry point, class and function (a scope report script). For a JNI game,
  categorise the exports: lifecycle, input, per-frame driver, accessors, save/load. The per-frame
  driver and the input handlers are where the game lives.
- Dump every string table and every static data table (names, descriptions, cooldowns, stat
  tables) with scripts. Official in-binary names and descriptions cross-check what the code says and
  resolve many mysteries at once.

### 3.2 Decompile exhaustively and read every function in full

- **Decompile every non-library function** into per-class files with an index (address, class,
  name, callers, callees) and resolved literal pools. Do not decompile "what seems relevant": in
  Dungeon Raid only 39 % of the code had ever been read before the exhaustive pass, and big
  "already covered" functions turned out to hide major missed mechanics and outright errors.
- **Read every function completely**, including the big ones you think you know. Old summaries are
  where the errors hide.
- **Where the decompiler loses information** (floating-point arguments in VFP registers, register
  arguments, inlined constants), read the raw disassembly and keep it as evidence.
- **Beware of look-alike enums.** Small enums (race, enemy type, perk) can make a direct comparison
  look like a lookup of another table. Confirm which function is actually called before trusting a
  claim.
- Keep every raw dump in the repo (`tools/ghidra_scripts/...`). It is the evidence behind the book.

### 3.3 Write the recipe book

The book (`docs/01-…NN-*.md`) states **how to build the game**, precisely. It is not a story of how
facts were found.

- **Normative only.** Each mechanic is stated once, as the rule to implement: pseudocode for
  algorithms, exact constants, full tables, layouts in reference pixels, atlas rectangles, colours,
  timings, sound events, RNG streams and the order of every random draw.
- **No discovery narrative**: no "previously thought", no "corrected on", no dated tags. History
  goes to the notebook and git. Binary addresses appear only as terse citations for verification.
- **One fact, one place.** Other chapters link to it.
- **Chapters that worked** (adapt to the project):

  | # | Chapter | Contents |
  |---|---|---|
  | 01 | Architecture | coordinate system and viewport, frame loop and timestep, input plumbing, the RNG (bit-exact), math helpers, atlases, the rendering primitives, fonts and text layout, sound system, saves, host-layer duties |
  | 02 | Data tables | every enum and static table verbatim, all official names and descriptions |
  | 03 | Board / world | the core entities, their records, spawning, stats, movement, appearance |
  | 04 | The turn / game loop | the full state machine: frame order, input handling, resolution, end of turn, game end |
  | 05 | Combat and resources | damage, kills, rewards, resources, the enemy attack, status effects |
  | 06 | Enemies | every enemy type and ability, passives, special variants |
  | 07 | Player abilities | skills, requirements, cooldowns, combos, racial/perk/flaw effects |
  | 08 | Progression | starting state, items, level-up, shop, upgrades, unlocks |
  | 09 | Modes, scoring, achievements | |
  | 10 | Screens | every screen and menu: flow graph, exact layout, atlas rects, colours, fonts, all UI text, input, transitions |
  | 11 | Animation and sound | every effect's motion, timing and colour; the event → sound table |

- **A reference appendix** (`docs/reference/*.md`) holds per-function specs and struct-offset
  tables: the evidence the chapters cite.

### 3.4 Lock the book

The book is locked when coverage is measured, not felt:

- **Traceability matrix** (`TRACEABILITY.tsv`): every function → the book section that specifies
  it, or `NOBEHAVIOUR` (accessors, destructors, container plumbing, runtime). Target: 0 partial,
  0 missing. Dungeon Raid: 978 native functions (727 specified, 251 no-behaviour) and 116 Java host
  methods.
- **Constant coverage** (`constant_coverage.py`): extract every literal the code uses (integers,
  floats, strings, field offsets) and check that the specifying section accounts for it. Record
  compiler/addressing artefacts with reasons. Target: 0 unexplained (Dungeon Raid: 7,480 of 7,480).
- **Independent re-verification**: fresh agents re-check each chapter against the decompile without
  seeing the original author's reasoning. Run them in batches of about five (ten in parallel hit
  the rate limit).
- **Whole-book audit**, then zero "Unresolved" items.
- **After the lock**, a change needs binary evidence, an in-place edit and an updated matrix row.
  Re-run constant coverage after any edit.

---

## 4. Phase 2: the discrepancy register

The book says what the original does. `DISCREPANCIES.md` lists every point where copying it
literally would be odd, buggy, dead, platform-bound or impossible in a browser, and records the
owner's decision.

**Categories, each with an ID prefix:**

| Prefix | Category | Example |
|---|---|---|
| BUG | Bugs a player can notice | rewards take their delivery mode from an unrelated tile |
| QRK | Quirks kept as they are (table) | an off-by-one percentage that only matters for RNG parity |
| DEAD | Dead and unreachable features | two skills that can never be unlocked |
| PLAT | Platform and host behaviour | the timestep uses CPU time; achievements lived on a dead service |
| VID | Differences between source variants | the iPhone video differs from the Android build |
| WEB | Browser presentation | a fixed 320 × 480 screen on today's phones; touch on a mouse |
| TXT | Text that does not match the rules | a description says "all enemies" but only normal ones are affected |
| UX / GAME | Owner-requested changes | hover tooltips; a skill made stronger post-launch |

**Entry template:**

```
### BUG-01 — <one-line title>
- **Original**: what the original does, with book citations.
- **Why questionable**: the harm to the player.
- **Options**: faithful; or …
- **Recommendation**: FAITHFUL | FIX | OMIT | ADAPT | OWNER — and how.
- **Decision (owner, YYYY-MM-DD)**: …
- **Impact**: visible / invisible (RNG only) / rare.
```

- **Default rule:** FAITHFUL, unless the point harms the player, is dead code, or cannot exist in a
  browser.
- **Review in small batches** (about three at a time), concise, numbered.
- **Keep a summary table** at the top and a **post-launch backlog** at the bottom.
- **Implementation rule:** every place the code departs from the book carries
  `// DISCREPANCY <ID>: what the original did / what we do instead`. A search for `DISCREPANCY`
  finds every deviation, and every one traces to an entry.
- **In chat**, a newly found discrepancy is announced with an asterisk banner and its ID, never
  buried in a table.
- **Book errors are not discrepancies.** When the original disagrees with the book, the book is
  fixed (with evidence) and the fix is logged as ED-n (see §5).

---

## 5. Phase 3: the oracle (running the original)

Run the original and check the book against it. It catches what reading code cannot: rendering
behaviour, platform effects and timing.

- **Android:** an emulator AVD with ARM translation for 32-bit native code, `adb exec-out screencap`
  for frames, `adb screenrecord` for motion (decoded frame by frame with PyAV, using timestamps),
  and `adb shell input swipe x y x y 300` as a press.
- **Flash:** the standalone projector or Ruffle; Construct / GameMaker: the original runtime.
- **Patch what makes the oracle lie.** Dungeon Raid's timestep used `clock()` (CPU time), so it ran
  12× slow or fast in the emulator. A one-function binary patch (wall-clock time, no other byte
  changed), re-signed with a throwaway debug key, made timing measurable.
- **Write a check log** (`docs/reference/emulator-original-apk.md`) in which each row is: id, screen,
  what was observed (with numbers), the book section, and the result. Dungeon Raid: 45 checks.
- **Record the oracle's limits** (rendering it gets wrong, timing it distorts) so nobody trusts it
  where it can't be trusted.
- **Book fixes found this way** are logged as ED-n with the measured evidence, then the book is
  corrected in place. ED-1 (a wrong inset) was found in the emulator. ED-2 (Android uploads
  textures premultiplied, so soft edges render darker) was found later, by measuring a glow ring
  pixel by pixel against a screenshot.
- **The owner can drive the oracle.** Long states (a nearly full upgrade bar, a rare enemy, a
  trophy) are cheaper for the owner to play to than to script. Agree on who captures when, and
  capture on the owner's cue.
- **Emulator gotchas that cost time:** taps shorter than one game frame are missed (use 200+ ms
  presses); `monkey` injects a random event (launch with `am start`); a killed script can leave
  `screenrecord` or a half-sent touch running, which blocks all injection; in one `input motionevent`
  script, MOVE events sent after a `sleep` are dropped.

---

## 6. Phase 4: the plan file

One file, `BUILD_PLAN.md`, read first in every session. It contains:

1. **Where things stand**: a table of areas (RE, book, register, layout, implementation, oracle)
   with their state.
2. **Sources of truth, in order**: book → register → layout spec → evidence. Everything else is
   history.
3. **Anti-drift rules:**
   - Build only what the current slice lists. No "while I'm here".
   - Every behaviour cites a book section or a `DISCREPANCY` comment. Code with neither is not
     allowed.
   - Tests take reference values from the book, never from what the code happens to do.
   - No new decisions in code: a question the book and register don't answer goes to the owner
     first, then into the register, then into code.
   - The book stays locked (see §3.4).
   - One plan file. Status lives here; decisions live in the register.
   - Every slice ends with the owner's sign-off, a commit, a git tag and a push.
4. **The fresh-start decision**: code written against an earlier, wrong understanding is archived,
   not patched. List exactly what may be carried over (exact pieces only: the RNG core, enums,
   parsers, loaders), each with the fixes it needs.
5. **Architecture** (see §8.1).
6. **Milestones as vertical slices**, each with acceptance criteria tied to reference moments (§9).
7. **How every slice is verified**, a per-slice verification record, and the **polish list** (small
   fidelity points the owner saw and deferred to a final pass).

Tag a save point when the plan is approved (`savepoint-YYYY-MM-DD`).

---

## 7. Phase 5: the responsive layout (the layout bench)

The original had one fixed screen (e.g. 320 × 480). Phones today are taller, so the layout must
adapt. Do it in two steps.

### 7.1 Version 1 matches the original exactly

At the original aspect ratio or wider, the rebuild shows the original layout exactly as the book
specifies (fit-to-screen as the original did). "At 320 × 480 the screen is identical to the
original" is a permanent check.

### 7.2 A bench tool so the owner can decide the taller layout

Build an **interactive layout bench** (a published artifact) that draws the screen's elements as
labelled boxes at real reference sizes and lets the owner try arrangements live. Dungeon Raid's
bench (`design/raid-layout-bench.html`) had these parameters:

| Parameter | Values | Meaning |
|---|---|---|
| Viewport `w × h` + presets | Original 320×480, small phone 360×640, modern 390×844, tall 360×800, large 430×932, tablet 820×1180; drag to resize | the screen being designed for |
| `origAt23` | on/off | use the exact original layout on screens 2:3 or wider |
| `topMode` | decorative bar / nothing / original skill bar | what sits above the board (new tiles fall in from under it) |
| `pAnchor` | screen bottom / right under the board | where the bottom group sits |
| `pArr` | original / rows | HUD as in the original, or re-flowed into rows |
| `rows` | order + per-row alignment (around, between, stacked, centre …) | which HUD rows exist, in what order, and how each row spreads its items |
| `valPoke` | on/off | the value badges straddle the HUD's top edge (half poke out); the layout reserves the poking half so they never cover the board |
| `valStrip` | on/off | values as a slim full-width strip instead |
| `goldFill` | on/off | the gold stack fills the free width beside the health jar |
| `skillPos` | under the HUD / above the HUD | where the skill bar goes (under = within thumb reach) |
| `equal` + `gap` | on/off, 2–16 px (baseline 8) | one spacing value for every gap in the bottom group: panel edges, rows, items, bottom edge |
| `balance` | on/off | the gap above the board equals the gap between the board and the HUD |
| `spare` | decorative / empty | what fills leftover height |
| Size multipliers | spells 1–1.6, buttons 1–2.2, values 1–2.5, gold 1–2.5, jar 1–2.5, bar thickness 1–3, bar width 30–100 % | element sizes relative to the original (Dungeon Raid baseline: values 1.3, gold 1.3, jar 1.3, bars 1.6, buttons 1.4, bar width 100 %) |
| Overlays | flight paths, falling-tile zone, thumb reach (hard-to-reach top third, stretch zone up to 55 %), level-up panel, labels | the consequences each arrangement must keep working |
| Readout + flags | live numbers and warnings (e.g. a control in the hard-to-reach zone) | checks the owner sees while deciding |
| Copy settings | JSON | the exact decided configuration |

The owner tunes it, approves defaults, and those defaults become the baseline. A spec file
(`design/responsive-layout-spec.md`) states the rules in words plus **checks every layout change
must pass** (identical at the original size; falling tiles covered except a stated gap; every flight
path lands on its target; all tappable controls outside the top third of a phone).

### 7.3 Why re-implementing the bench is open to interpretation, and how to close it

The bench was right, but it decides **boxes**. The game must also decide **how the original's art
fills a box that is bigger or a different shape**, and the bench said nothing about that. In Dungeon
Raid every one of these became a review round:

- A bar trough art stretched wider smeared its arrow/plus texture. *Decision:* keep the end caps,
  repeat one 9-px period of the pattern instead of stretching it.
- Pieces stretched side by side showed hairline seams. *Decision:* snap every seam to whole device
  pixels.
- "Bar height" was ambiguous: the fill or the whole trough? *Decision:* the rect is the trough, so
  the spacing shows between troughs.
- The gold stack had 5 columns in the art; a wider stack needed more. *Decision:* 6 columns, with
  the amount shown scaled so the same gold reads the same.
- Icons cut from the panel art were clipped at their top (the original hid the cut behind a band).
  *Deferred* to the art-upscaling polish pass.

**To make the port faithful to the bench:**

1. **Port the bench's layout function verbatim** into the game's layout engine (same algorithm,
   same defaults), and drive it with the bench's exported settings as the config. Do not re-derive
   the rules from the prose spec.
2. **List every "how art fills a box" decision explicitly** (stretch, repeat, 9-slice, cap sizes,
   pixel snapping, counts that scale, text scale) and get each one decided before or during the
   first slice. Better still, render the real art in the bench so these are seen when the boxes are
   decided.
3. **Keep the layout as configuration.** One config module of independent groups (top cap, board,
   HUD, skill bar). Every number is a parameter, and no coordinate is hard-coded in rendering or
   game code.
4. **Game code asks the layout, every frame,** for every position that depends on it: token flight
   targets, damage-number legs, tooltip anchors, help-bubble anchors, panel positions, hit tests.
   Moving an element moves everything that refers to it.
5. **Re-layout on resize** without restarting the game. In a browser, also request fullscreen on the
   first touch, because a page does not own the whole screen.
6. **Run the layout tests** (identical at the original size; flight targets on their elements) at
   several phone sizes.

Every code path of the new layout carries `// DISCREPANCY WEB-01`.

---

## 8. Phase 6: the rebuild, line by line

### 8.1 Architecture that keeps fidelity possible

- **Plain JavaScript ES modules, Canvas2D, no framework, no bundler.** Nothing between the book
  and the code.
- **`core/` is pure game logic** (no DOM, no canvas). It mirrors the original's classes, fields and
  state machines one to one, with field names from the book. `view/` draws it; `layout/` places it;
  `platform/` loads assets and plays sound; `dev/` holds scenarios.
- **Resolution-independent assets:** sprite rects in reference pixels from manifests, so upscaled
  art drops in later.
- **Time:** wall clock, `dt` capped (0.1 s), paused while hidden. Every per-frame effect of the
  original (alpha steps of `(int)(k·dt)`, per-frame multipliers) becomes time-based **calibrated to
  match the original frame for frame at its native rate** (60 fps). This is a decided discrepancy,
  because browsers run at 90–360 Hz.
- **A dev server that disables caching**: plain static servers serve stale ES modules after edits.

### 8.2 Port, don't paraphrase

- **Translate the book's pseudocode function by function**, in the original's order, with a comment
  citing the book section (and the function name/address) above each one.
- **Preserve every RNG draw**: same stream, same order, same count, including draws whose result is
  thrown away and the "count idiom" that draws even when there is nothing to pick. Implement the RNG
  bit-exact (float32 rounding included) and test it against a sequence generated independently.
- **Emulate the machine's arithmetic**: `Math.fround` where the original used 32-bit floats,
  truncation toward zero for float→int, saturating casts where ARM saturates, integer division where
  the original divided integers.
- **Emulate the rendering model**: texel × vertex colour, the blend function, premultiplied texture
  upload if the platform did it, the exact font metrics and wrap algorithm, 9-slice panels.
- **Never invent.** When the book doesn't say, stop and ask; do not fill gaps with something
  plausible.
- **Mark what belongs to a later slice** with a comment naming that slice, so nothing is forgotten
  and nothing is half-built.

### 8.3 Tests that encode the book

- **Expected values come from the book**, generated independently (e.g. a Python fixture script
  re-implements a formula or RNG sequence from the book's text), never copied from the code's output.
- **One test per rule**: the timeline of an animation at 60 fps (frame counts), a state machine's
  transitions, each ability, each decided fix.
- **Mutation-check the important ones.** Remove a fix and confirm its test fails. A test that passes
  either way proves nothing.
- **When a test fails, decide who is wrong against the book**: the code or the test's expectation.
  Several Dungeon Raid failures were wrong expectations (e.g. counting one frame too many); the code
  was right.
- Run headless (`node tests/run.mjs`) before every commit, plus a browser runner for anything that
  needs the browser (audio decoding).

### 8.4 Visual verification against the original

- **Scenario loader:** dev-only URL parameters set up exact states: `?scenario=<name>` (boards read
  from original screenshots by a script that matches each cell against the atlas), `?seed=`, `?size=WxH`,
  `?dpr=`, and config/HUD overrides. Published builds keep only the `#hash`, so also accept scenarios
  by hash (`#skills-11-30`, `#enemy-13-race3`).
- **Frame stepping:** `?manual` stops the clock; `window.__step(n, dt)` advances exact frames. A
  recorded drag from the original can be replayed frame by frame and captured at the same offsets
  after release.
- **Capture:** a dev-server endpoint that saves canvas PNGs, or a headless-Chrome driver (DevTools
  protocol) that loads a page, runs steps and saves canvas or full-page screenshots. Keep the driver,
  because the interactive browser is not always available (sign-in popups, hidden panes that throttle
  `requestAnimationFrame`).
- **Compare, don't eyeball:**
  - pixel-diff against the reference, reporting mean difference per region and the best alignment
    offset, which should be zero;
  - montage the rebuild's frames against the recording's frames at equal timestamps;
  - when something looks off, measure the pixel ramp (e.g. a glow's edge values) on both. This is how
    the premultiplied-texture rule was found and proven.
- **Look at the result yourself** before showing it, every time.

---

## 9. Phase 7: vertical slices and sign-off

### 9.1 Slices that make sense

Each slice builds one part of the game **completely** (logic, layout, art, animation, sound) so it
can be played and compared the moment it exists. Dungeon Raid's slices (a template for games):

| Slice | Content | Accepted when |
|---|---|---|
| S0 The screen | skeleton, carried-over exact pieces, RNG, asset loaders (atlases, fonts, sounds), layout engine (original + responsive), the main screen drawn with real art and fonts, a static board | screenshot matches the original at the native size; layout matches the bench on phone sizes |
| S1 One action, fully felt | input, the core action (drag a chain), every visual and sound of it, rewards flying to the HUD, gravity and refill | matches recorded moments side by side |
| S2 The opponent's turn | the turn machine, the enemy attack sequence, status ticks, end of turn, death | matches the attack sequences frame by frame |
| S3 Player abilities | the skill bar, charge and glow, every skill effect with its visuals | each skill scenario plays correctly; tooltip matches |
| S4 Enemies | promotion, every enemy ability with visuals | each enemy scenario plays correctly |
| S5 Progression | trophies, level-up, shop and upgrade panels, items and stats | matches the panels in the recordings |
| S6 A whole game | every screen and menu, modes, scoring, achievements, saves | every screen reachable; a full game plays through |
| S7 Release readiness | remaining decided discrepancies, device tuning, final comparisons | every decided register entry implemented and flagged |

Order slices so each one can be played: the screen first, then the core action, then what reacts
to it, then what extends it, then everything around it.

(Dungeon Raid's own list grew from this: S6 starting a game, S7 the layout infrastructure, S7b the Class Editor
redesign, S8 playing, S9 ending, S10 polish, S11 release readiness, S12 the post mortem, S13 a tribute page: the post mortem first, so its conclusions go into
the page. How to run one: `workflow/post-mortem/`.)

**Size phases by screen.** A slice that touches several screens or tabs (a redesign, a set of menus) is split
into an **overall ticket** (what the screens share: common look, shared controls, cross-screen rules) plus **one
phase per screen**, each with its own short sheet, one mockup and its own sign-off. Never fold new work into a
slice already in test: Dungeon Raid's S6 took in a tall-phone redesign of every menu before its first round was
tested and became "a mess" (scaled down); S7b ran four tabs as one phase, so every round carried 26 questions or
31 mockups at once.

### 9.2 What "done" means for a slice

1. Built completely: logic, art, motion and sound.
2. Book-derived tests pass, including the new ones.
3. Frames captured and compared with the original wherever references exist, at the sizes the owner really
   uses (the phone's artifact viewer, about 390 × 705; fullscreen with late safe-area insets; the original size).
   Dungeon Raid's first phone test found a build "unplayable" that had passed every check at 390 × 844.
4. **An independent book audit of the slice's code** before hand-over: one auditor per area reads
   the book chapter and the code in full and lists every difference that no discrepancy entry covers;
   each suspected difference must survive an attempt to refute it (book text plus binary evidence).
   Self-review and screenshot comparison both missed a book rule once (double-width spaces in every
   screen label: the tooltips drew them single), and the owner found it. A full audit run then found
   28 more unflagged differences across already signed-off slices: missing labels, skipped RNG draws,
   a tint formula that undid a verified texture fix. Agree the cadence with the owner: the audit is
   expensive (Dungeon Raid's S5 run: 80 agents, 8.7M tokens) but it finds real differences. From S6 on, Dungeon
   Raid's owner moved the full audit and full regression to release readiness; each slice gets the suite, its
   own tests and a phone-conditions check of what it changed.
5. Committed and pushed; the plan file's verification section updated.
6. **The test build is republished** (the same artifact URL every time) so the owner can play it on
   the phone. Forgetting this left the owner with nothing to test once; it is now a hard rule.
7. **A test sheet artifact** is published (see 9.3).
8. The owner reports back; every result is answered (see 9.4).
9. The owner signs off: tag `slice-N`, push, update status, start the next slice.

### 9.3 User-facing test sheets

A published page with one card per test:

- the item's icon (cut from the game's own atlas);
- an **Open test** link straight into the build with the right setup (`…#enemy-13-race3`);
- **what to do** and **what should happen**, in the player's words;
- **Pass / Fail** buttons (tap again to clear) and a comment box that saves as you type (Fail moves
  the cursor into the comment);
- a tally bar with progress, and filters for **Untested** and **Failed**;
- a "not testable yet" list naming the slice each item waits for.

A test sheet holds tests only (Dungeon Raid's owner, 2026-10-21: "Why did u start adding these open question notes? No
need"): every card a thing to do and what should happen, passed or failed. No "your pick" cards, no questions or asides
inside a test ("if you still see it, send a screenshot"); a choice goes to a decisions worksheet (more than five) or
to the chat (five or fewer, numbered), a set of takes to compare goes in as tests of each take.

Results are stored in the artifact's database (the `db` capability, collection `results`), so
they survive across devices and Claude reads them back directly. The template and its guide:
`workflow/qa-sheet/` (with Skip for a test that no longer applies, and hold-to-compare pictures).

### 9.4 Answering the owner's audit

Read every result and classify each failure and comment:

| Finding | Response |
|---|---|
| The original behaves that way | explain it with the book citation (and what the player misread); no change |
| The test setup can't show it | fix the scenario or the test text and republish the sheet |
| A real bug | fix it, add a test, republish |
| A wish or a deviation from the original | a numbered decision: new register entry, recommendation, the owner's choice (now, later stage, post-launch) |

Most "fails" in Dungeon Raid's S3 audit were the original's own behaviour. Explaining them with the
rule and the arithmetic (e.g. "31 = 20 magic sword + 4 sword + 7 base damage") is part of the
deliverable.

**For broad visual decisions, publish a preview artifact** that shows every case side by side
(e.g. all 150 tooltips, original wrap vs balanced wrap, drawn with the game's real renderer and
font), so one decision is checked against every instance.

### 9.5 Redesigns the owner directs

When the owner wants a screen redesigned (not restored), the owner designs it:

1. The first deliverable is a **decisions sheet over today's screens** (the decision-worksheet skill): one screen
   per sheet, one decision per section, pictures of the build. No proposal panels or design agents first.
2. Mock up **one screen at a time**, only what the answers say. The owner's own mockup (e.g. a Photoshop layout)
   is the best spec: measure it and build it 1:1.
3. Build it directly, then take the owner's **tweak stream** in chat: a screenshot and one line each; change,
   check at the phone size, commit, publish, reply in a few lines with the link. Minutes per tweak. Every phase
   still gets its own short **test sheet**: per-item feedback that doesn't drown in chat (the owner is not always
   free to mark up screenshots).
4. When a choice is the owner's, **show each option as a rendered picture** (a capture of the real build), not as
   pixel numbers: running simulations saves the owner the most time ("what are you talking about?" was the
   answer to "18-px slots vs 53-px frames").
5. Publish the test build with a **test save** where everything is reachable (e.g. every class unlocked), so the
   owner can test every case, not only the first class.
6. "Signed off for now" is a normal outcome: further tweaks become a polish ticket.
7. Before any change to the look of everything (texture sampling, scaling, a palette), show a **before / after**
   of a few screens and let the owner decide; Dungeon Raid built crisp enlarging for all the art, then scoped it
   back once the comparison showed shaded art getting jaggier.

### 9.6 Polish list and post-launch backlog

- **Polish list** (in the plan file): small fidelity points the owner saw and deferred to a final
  pass (a font difference, clipped art, edge artefacts). Each has an id, the point and when it was
  raised.
- **Post-launch backlog** (in the register): owner ideas and deferred deviations. Launch ships the
  faithful or decided behaviour; the backlog is reviewed after launch.

### 9.7 Accessibility, keyboard control and speed (before the lock)

Learned on Dungeon Raid (2026-10-10 to 10-17); do these while additions are still allowed, since their fixes are
additions.

- **Measure accessibility, don't guess.** Draw every screen in the real page and record each text the renderer draws
  (its size and colour); hide it alone to sample what is behind it. Report texts under a minimum size (set one, e.g. the
  smallest text of the newest pages), under WCAG contrast (4.5 : 1, large text 3 : 1), and tap targets in CSS px (24 the
  least, 44 recommended). Offer the fixes as a build to compare (hold to compare on a sheet): the owner may keep them for
  everyone (Dungeon Raid's "Larger text" ended always on, its switch removed).
- **Colour-only and sound-only cues.** List every sound and what the screen shows with it. Find meaning carried by colour
  alone (better / worse, the newest entry, a rank) and show it as red-green colour blindness sees it: the real screen
  through a deuteranopia simulation (Machado 2009, in linear light). Mock each fix in the game's own font, both views.
- **Reduced motion.** Decorative motion honours `prefers-reduced-motion`; optional effects start off under it; a page
  says when its motion is off (a badge), so "nothing moves" can be explained.
- **Keyboard control (enhanced only; the original was touch only).** One focus layer over every screen: each screen
  lists its targets (the rects its own taps already test) in reading order. Tab and Shift+Tab go round, the arrows to the
  nearest target that way, Enter and Space press as a tap (a touch down one frame, up the next, so the screen's own
  code runs: its sound, its vibration), Esc is Back, ? lists the keys. The ring shows after a key and hides on a touch
  or click; each screen remembers its focus. Whatever needs a user gesture (a share sheet, a file picker, a new tab, a
  download) runs inside the key's own event, as a tap's release does. A key no phone sends (Tab, an arrow, Esc, the
  numpad) marks a physical keyboard: stop asking for full screen (Esc would leave it), but never for a key typed into a
  text field. On a board: a cursor on the grid, moved by the numpad, the letters round S or the arrows; Enter starts and
  ends the drag, which runs through the game's own chain rules. Build it as a decisions sheet, then one phase per
  screen group, then **the sweep**: every screen driven by real key presses at computer sizes, each Tab stop recorded
  (on screen, ring visible, reading order). The sweep finds what the sheets miss.
- **Speed check on the built site.** Headless Chromium as a mid-range phone (390 × 844 at 3×, touch, the CPU slowed 4×
  and 8×, no GPU for a canvas game), the network shaped by the test's own server (each response waits the latency, then
  every byte queues at the bandwidth: Chrome's own emulation let files through unthrottled on Windows). Measure the first
  paint, a tappable menu, the bytes by then, a repeat visit, and the frames while dragging and through a cascade. Typical
  wins: textures as lossless WebP; what the menu doesn't need loaded after it; optional HD art only once switched on; a
  service worker registered only after the game has loaded (else it downloads the whole game during the first visit).
- **Tools the owner works in for long** (editors, tuners, sheets) keep each change on the device until the database
  confirms it, and reconnect by themselves: a dropped connection once lost an evening of the owner's tuning.
- **Checks that lie: look at a result before trusting it.** A full-page capture wraps round past 16,384 px (capture in
  chunks); a page's smooth scrolling makes `scrollTo` land later (use `behavior: 'instant'`); a one-call tap presses and
  releases between two game frames (hold it across frames, as a finger does); repeat a real-input check a few times (a
  race passes once and fails the next).
- **Seams in drawn art** (Dungeon Raid v187 to v188, 2026-10-17). Put a rounded or nine-slice box's edges, and every
  straight edge, on whole device pixels; a band and its middle that meet at a fraction leave a thin line. Draw a shape
  made of two fills (an arrow's shaft and head) as one path, or a see-through line shows where they meet inside a pixel
  row. A piece drawn smaller with smoothing on blends in its neighbours on the atlas, so give it a padded copy of its
  own. An AI upscale isn't flat where the original was, and it saw a piece's atlas neighbours, not the pieces it meets
  on screen: if any piece of an image is a one-texel stretch strip, draw every piece of that image from the 1x art,
  smoothly enlarged (the help bubble's upscaled corners sat at alpha 224 to 248 against the 1x strip's 255). Images
  with no stretch piece keep the upscale; the rule is per image, since all-1x softened art that had no line. Check
  drawn art at the owner's real device scale: their Pixel 8 is 2.625 device px per CSS px, and both seams were
  invisible at 3x and 1.25x and plain at 2.625 (Playwright: `deviceScaleFactor: 2.625`, viewport 412 x 780).
- **Keys inside the claude.ai viewer** (v189). A game that cancels its pointerdown (`preventDefault`) also cancels the
  browser's focus-on-click, so inside the viewer's iframe a click never gives the game the keys: Tab goes to the viewer,
  and once the keys leave, a click can't bring them back. On a primary pointerdown, focus the canvas (`tabIndex = -1`,
  no outline). Run headless key checks inside a frame with the viewer's sandbox (`allow-scripts allow-same-origin
  allow-forms allow-pointer-lock`) and allow list, not only in a plain page.

---

## 10. Working with the owner

- **Numbered decisions, always** (1, 1.1, 1.2.1), stable across follow-ups.
- **Recommend, don't survey.** Give options, a recommendation and the consequence, then ask.
- **Flag discrepancies loudly**: an asterisk banner with the ID and a one-line summary.
- **Report outcomes faithfully**: tests that failed, checks that couldn't be done (and why), limits
  of the evidence (e.g. "no footage of the original exists for these enemies").
- **Explain in the player's words**, not internal ids alone.
- **End every reply with the project board's link** as the very last line (owner, 2026-10-17: "always finish your message [with] a link to the project board"), a build
  report's published link on the line just above it.
- **Keep the owner able to follow remotely:** keep Remote Control on, and publish everything testable as an
  artifact.

### 10.1 Pace and agents

The second Dungeon Raid attempt's worst stretch (S6–S7) came from how the work was run, not from the method:

- **Work directly by default.** With the context loaded, a tweak takes minutes (Dungeon Raid's last S7b
  stretch: about 30 requests in 75 minutes, each committed 1–5 minutes after it was asked). Multi-agent
  workflows start cold (re-reading the book and the code), ran 16–126 minutes each, often outlived a change of
  direction, and needed a re-check on top. Use them only for genuinely big parallel jobs (the exhaustive
  decompile, book audits, an independent pre-launch review, long mechanical runs), and only after asking.
- **Mind the usage limit.** 33.6M subagent tokens in 2.3 days hit the weekly limit in the middle of S7 and
  stopped the project for 38 hours.
- **Do what was asked, at the scope asked.** A "sweep" for a kind of bug covers the screens in play at the phone
  sizes, not every state at every pixel density ("Do you remember not to over do each task?").
- **Confirm a change of direction** in one or two points before starting anything big; three runs were stopped
  and restarted in one day.
- **Never quote durations from feel** (the model has no clock): measure from commit times or say nothing.
- **One commit per change; publish only the changed files;** keep replies short, questions numbered and few
  (more than 5 go in a worksheet), the release's link, then the board's link last.
- **Image editing goes to the owner** (cut-outs, matting, repainting): flag it with an asset brief; an agent took
  33 minutes on a logo cut-out the owner did quickly in Photoshop.

---

## 11. Continuity between sessions

- **Start every session by reading the plan file**, then the project `CLAUDE.md` (Status and Notes).
- **Project `CLAUDE.md`** carries Status (slice, artifacts and their URLs) and Notes (tools,
  gotchas, dev hashes). Update it whenever work lands.
- **Memory** holds the owner's standing feedback (fidelity creed, docs style, vertical slices,
  publish every slice, numbering, discrepancy flags) and pointers, never facts the repo already
  records.
- **Git:** commit each coherent change with the *why*; tag save points and slices; push after
  commits (the remote is the backup).
- **Artifacts:** republish to the same URLs. Read a published file before overwriting it if this
  session didn't publish it.

### 11.1 The artifact board

A game makes many artifacts: test builds, tools (editors, tuners, benches, galleries), decision
worksheets and test sheets. The owner keeps track of them on a Kanban board, one per project (the
owner, 2026-10-13: "Create an ever constantly updating, every time you make a release, update this
file ... a simple Trello-like Kanban board with all the artifacts that also lists their type").

- **One card per artifact**: its name (a link to it), its type (game, tool, worksheet, QA sheet), a
  topic group (a map, a system, the heroes, the sound ...), its version and date, and a short note from
  Claude on where it stands.
- **The status is the owner's**: five columns, To review, In review, Ready for Claude, With Claude,
  Done (tabs on a phone), a status picker on every card, drag and drop with a mouse, and a note field
  of the owner's own. Filters by type, topic and words. **Ready for Claude** is the owner's "I'm done
  with this sheet": check that column at the start of every session and whenever the owner says the
  board changed; move a card you pick up to With Claude, and back to To review with its next round.
  A card with nothing left (every test passed, or the owner calls it finished) Claude moves to Done
  (owner, 2026-10-15); Claude never changes the owner's note.
- **The cards live in the board's database** (the artifact's `db`, collection `items`, one document per
  artifact id), never in the page source, so an update needs no republish. The repository keeps the
  list (`tools/artifact-board/items.json`) and a sync script that turns it into the database's writes:
  a new card is created with its starting column; an existing one gets only Claude's fields (title,
  type, topic, note, version, date).
- **Update it at every release** and whenever an artifact is published or changes: a new artifact
  starts in To review, a changed one gets its note, version and date; name the board in the reply.
- **The work coming up is on it too** (the owner, 2026-10-15: "add all the future stuff as tickets, maybe
  in a SLICE category, so I'll see what's up next"): every planned slice or phase, every task Claude owes and
  the post-launch slices are cards of the type `slice` (id `slice-…`, no artifact: no link unless the card
  sets `link`), With Claude, in plan order (`order`; the board sorts slices by it), post-launch ones in the
  topic `later`. When a slice is built its sheets get cards of their own; the slice card moves to Done when
  it is signed off. Add a slice card the moment a slice is planned, and keep the order current.
- One board per project, never one across projects. The template: `workflow/board/` (board.html,
  sync.cjs, items.example.json; its README has the steps).
- **One look per project** (the owner, 2026-10-16: "I notice the Crawl worksheets and such look like Dungeon Raid's - but they should look like the
  style you chose for the project board"): the board sets the project's look (its colours, type and corners, taken from the
  game), and every page made for the project wears it: worksheets, QA sheets, tuners and editors. Keep the look in one
  file laid over the templates' tokens and pass every sheet through it, the builders' output too (Crawl:
  `tools/decision-sheets/crawl-look.cjs`). The templates' default look is Dungeon Raid's: never ship it in another
  project.

---

## 12. Lessons from the first attempt (avoid these)

| Mistake | Consequence | Rule now |
|---|---|---|
| Building on the proof of concept | wrong architecture and hard-coded numbers carried forward | the POC is scrapped; start fresh from the book |
| Code written against early, partly wrong docs | the backbone was wrong and its tests locked the errors in | fresh start after the book was locked; carry over only exact pieces |
| Selective decompiling | 61 % of the code never read; "known" functions summarised wrongly | decompile everything, read everything, measure coverage |
| Docs written as a discovery log | the spec was unreadable as a spec; correction tags everywhere | recipe-book style; history only in notes and git |
| Logic first, "the juice" last | the owner could verify nothing until the end | vertical slices with presentation included |
| Calling UI done without comparing | repeated rounds of owner frustration | compare with the reference element by element before reporting |
| Re-implementing the layout bench from prose | each "how does art fill a bigger box" became a review round | port the bench's function verbatim; decide art-fill rules explicitly |
| Not publishing at slice end | the owner had nothing to test | republish every slice, same URL |
| Unnumbered decision lists | slow, ambiguous answers | hierarchical numbering |

**Lessons from the second attempt (S6–S7b) — avoid these too:**

| Mistake | Consequence | Rule now |
|---|---|---|
| Multi-agent workflows as the default way to work | cold starts, 16–126 min runs, restarts; the weekly usage limit hit, a 38 h stall | work directly; agents by exception, with the owner's OK (§10.1) |
| Designing a redesign for the owner (proposal panels, judges) | stopped rounds | the owner designs; a sheet over today's screens first (§9.5) |
| One phase spanning four tabs; new work folded into a slice in test | 26-question sheets, 31 mockups at once; S6 "a mess" | an overall ticket plus one phase per screen (§9.1) |
| Checking in window sizes the owner never sees | "unplayable" on the first phone test | the phone viewer size and fullscreen with late insets (§9.2) |
| A global look change without a before / after | built, then scoped back | before / after first (§9.5) |
| Durations quoted from feel | wrong by an order of magnitude | measure from commits or say nothing |
| Sheets with missing pictures, no zoom, several decisions per section | the owner caught them | the decision-worksheet skill's check list |
| A bug sweep far bigger than asked | a heavy run; "don't overdo each task" | the scope asked, at the phone sizes |

**Tooling gotchas:**
- Python on Windows opens files as cp1252 by default: always pass `encoding='utf-8'`.
- Bash heredocs mangle quotes and backslashes: write patch scripts to files and run them.
- Plain static servers cache ES modules: use a no-cache dev server.
- Hidden browser panes throttle `requestAnimationFrame`: use manual frame stepping for tests.
- A sign-in popup can block the in-app browser: keep the headless capture driver.
- Plus the emulator gotchas in §5.

---

## 13. Templates and checklists

**Repository layout**

```
BUILD_PLAN.md            the only plan (read first)
DISCREPANCIES.md         every deviation and its decision; post-launch backlog
NOTES.md                 lab notebook (history)
CLAUDE.md                project status and notes
docs/01…NN-*.md          the recipe book (locked)
docs/reference/          evidence: per-function specs, oracle check log, external sources
design/                  layout bench, layout spec, reference shots (+ README of what each shows)
extracted/ decoded/ …    the original, untouched and extracted
src/core|view|layout|render|platform|dev/
tests/                   *.test.js, headless runner, browser runner, fixtures
tools/                   decompile scripts, coverage tools, scenario-from-shot, compare-shot,
                         capture driver, dev server, emulator scripts
archive/                 superseded code (read-only)
```

**Slice checklist**

- [ ] Plan file lists the slice; every item cites the book or a register entry
- [ ] Logic ported line by line, RNG order preserved, deviations flagged `// DISCREPANCY <ID>`
- [ ] Art, layout, motion, sound included
- [ ] Book-derived tests added; key fixes mutation-checked; all tests pass
- [ ] Frames captured and compared with the original at the owner's real sizes; differences explained or fixed
- [ ] Committed, pushed, plan file verification section updated
- [ ] Test build republished (same URL), with a test save where every case is reachable; test sheet published
- [ ] The artifact board updated: new artifacts in To review, changed ones' notes, versions and dates (§11.1)
- [ ] Owner audit answered item by item; decisions recorded and numbered
- [ ] Sign-off → tag `slice-N`, push, status updated

**Register entry**: see §4. **Test sheet card**: icon, Open-test link, Test, Expect, Pass/Fail,
comment.

---

## 14. Adapting to other sources

- **Flash (SWF/FLA):** decompile ActionScript and the timeline with JPEXS. The book also needs the
  frame rate (timeline animations are per-frame, so apply the same calibrated time-based rule), the
  symbol library with registration points, and the sound sync modes. The oracle is the Flash
  projector or Ruffle.
- **Construct / GameMaker:** the "code" is event sheets or GML plus object, room and layout data.
  Export them to text and trace every event the same way (traceability per event or script).
  Engine behaviours (physics, platform movement) belong in the book as specified behaviour, measured
  in the original runtime.
- **Web or desktop apps:** the same method applies: book (behaviour and screens), register, oracle
  (the original running), bench for any layout change, slices, test sheets.

## 15. The workflow kit

`workflow/` (beside this file) packs the way the owner and Claude worked, ready to use in any project:

| Piece | Folder | What it gives |
|---|---|---|
| Worksheets | `workflow/worksheet/` | the decisions page: a picture per option, a recommendation, a comment box, answers saved for Claude to read (more than five decisions) |
| QA sheets | `workflow/qa-sheet/` | the test page: each test a link into the build's exact state; Pass, Fail or Skip with a note; hold-to-compare pictures |
| Editors on request | `workflow/editors/` | the "[x] Editor" pattern for tuning one aspect with a live preview drawn by the game's own code; the standard for every tool the owner tunes (Done with a lock, a note per item, filters, nothing lost); a complete text editor kit |
| The project board | `workflow/board/` | the Kanban board of every artifact and the sync script that keeps it current |
| Working rules | `workflow/working-rules.md` | numbered decisions, one place per question, link everything, document as you go, the tweak loop, the owner designs |
| The website | `workflow/site/` | the site on Cloudflare Pages: the build script (a front page, the game installable and offline at /play/), the coming-soon gate, the owner's set-up ticket (the dashboard's steps), launch |
| Post mortem | `workflow/post-mortem/` | the look back at a project's end (or after a slice that went badly): the record, the findings with evidence, the owner keeps or drops each proposed rule, the kept ones go into the skill |

Read `workflow/README.md` for how the pieces fit, then each folder's README before using its template. Every template
ships Dungeon Raid's look: give it the project's own (§11.1, one look per project) before the first page goes out.
