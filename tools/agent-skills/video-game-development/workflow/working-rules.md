# Working rules

How the owner (a UX designer) and Claude worked, written as rules. Each one came from a real moment in the
Dungeon Raid project; the dates are when the owner said it.

## Decisions and replies

1. **Number everything that needs the owner** hierarchically (1, 1.1, 1.2.1) so a reply can be "1.2.1 yes". More than
   five decisions go on a worksheet (`worksheet/`), never a long chat message.
2. **A question lives in one place**: on a sheet, or in chat, never both. When a sheet carries the questions or the
   tests, the reply says in a line what changed and links it. A sheet's result (a Pass on a "keep it?" test) is the
   answer.
3. **Link everything**: every item in a status update or a list of pending work links to where it lives (the
   artifact's URL, or the file as `path:line`), so it opens with a tap.
4. **Every reply ends with the project board's link** as its very last line (owner, 2026-10-17: "always finish your message [with] a link to the project board"). A reply
   that released something puts the release's link on the line just above it; a project without a board ends with the
   release's link.
5. **Document as you go**: every plan, proposal or question sent to the owner is written into the project's docs in
   the same turn (the decision register, the plan file, the status), with the questions numbered as sent. The owner
   should never have to ask whether something was recorded.

## Designing and building

6. **The owner designs, Claude executes.** A redesign starts with a worksheet over today's screens: the options as
   rendered pictures (captures of the real build, or mockups), never as pixel numbers, and never design proposals or
   design agents first.
7. **Piecemeal**: multi-screen work is an overall ticket plus one phase per screen, each built, published and tested
   on its own QA sheet before (or while) the next is built.
8. **Work directly**: one change at a time, checked, committed and published. Rounds of parallel AI agents only for
   genuinely big jobs and only with the owner's OK (on Dungeon Raid they bloated two slices, hit the weekly usage
   limit and stopped work for 38 hours).
9. **Vertical slices**: each feature complete with its art, motion and sound; never leave "the juice" for the end.
10. **The tweak loop** (what worked best): the owner sends a screenshot and a line; Claude makes the change, runs the
    suite, looks at the changed screen at the phone's size, commits, pushes, republishes only the changed files, and
    answers in two or three lines, the release's link and then the board's last.
11. **Test where the owner looks**: the claude.ai viewer on a phone (about 390 x 705), fullscreen with the system bars,
    and the smallest supported phone; never only a full desktop window.
12. **Editors on request**: when the owner wants something "just so", give them an editor with a live preview
    (`editors/`) instead of a round of guesses.
13. **Image editing is the owner's**: cut-outs, matting and repainting go to the owner as a numbered item with an
    asset brief (file name, size, format, transparency), not a round of pixel fiddling.

## Words and pictures

14. **Icons picture their subject**: an icon goes beside something only when it shows that thing (the game's coin
    beside the rule about coins); otherwise a plain line icon, or none. No decorative sprites, no initials as logos.
15. **Text in the owner's name is written as the owner**: first person, the AI in the third person, their tone (on
    Dungeon Raid: a diehard fan, direct and candid, short sentences, the odd exclamation mark, never schmaltzy); quote
    their real words where they exist.
16. **Never quote durations from feel**: measure them (commit times, logs) or say nothing.

## Keeping track

17. **Publish anything testable** as an artifact and republish to the same URL after every change. **The tab icon
    (`icon` on the first publish) is fixed per kind of artifact, on every project, so the owner tells tabs apart by
    kind** (the owner's picks, 2026-10-16): board `grid`, worksheet `checklist`, test sheet (QA) `eyeframe`, editor /
    tool `wrench`, playable build `play`. Never invent another word: claude.ai maps the word onto a fixed set of 155
    glyphs (`https://claude.ai/images/artifact-icons/glyphs.svg`), loosely (`board` gives Clipboard, `kanban` Tasks,
    `game` Interactive) and some words give none (`gamepad`, `dice`); a glyph's own name, lowercased, gives exactly it.
    An older artifact with another icon gets its kind's `icon` passed on its next republish; never sweep old ones
    just for the icon (the owner, 2026-10-16: a republish needs the live page read in full first, too many tokens).
18. **The board** (`board/`) holds every artifact; update it with every release, every new sheet and every tool. The
    statuses and the owner's notes belong to the owner, except that a card the owner moves to Ready for Claude is
    Claude's to pick up (With Claude while working, To review with the next round); check that column at the start of
    every session.
19. **Push after every commit** when the repository has a remote: the owner may continue from a phone in a cloud
    session on the repository.
20. **Keep the project's own instructions current** (its CLAUDE.md status and notes) whenever work lands, a decision
    is made or something is learned.
21. **Questions in a report are answered in place**: a report that asks the owner anything (a speed check, an audit)
    lets each question be answered on the page, worksheet-style, or its questions move to a decisions sheet
    (`worksheet/`); never leave them as plain text (the owner's board notes on Dungeon Raid's Speed Check and
    Accessibility Audit, 2026-10-17).
