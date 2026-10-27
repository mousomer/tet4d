# The workflow kit

The tools and habits that made the Dungeon Raid rebuild work between a designer and Claude, packed so any project
can use them. Each piece has its own folder with a guide and a template that is ready to fill in. Every page here is
a claude.ai artifact with the `db` capability: the owner answers on the phone, the page saves as they go, and Claude
reads the answers back with the ArtifactData tool. Nothing is ever retyped.

| Piece | Folder | Use it when |
|---|---|---|
| Worksheets | `worksheet/` | more than five decisions wait on the owner: one page, a picture per option, a recommendation, answers that save |
| QA sheets | `qa-sheet/` | a slice or phase is built: one test per behaviour, each link opening the build in that exact state; Pass, Fail or Skip with a note |
| Editors on request | `editors/` | the owner wants to change one aspect a very specific way (texts, a layout, vibrations, styles): build them an editor with a live preview; a tool with many items to tune has Done (a lock), a note per item, filters, and never loses work (the standard in its guide) |
| The project board | `board/` | from the first artifact on: a Kanban board of every artifact (builds, tools, worksheets, QA sheets) |
| Working rules | `working-rules.md` | always: how decisions, replies, docs and publishing work with the owner |
| The website | `site/` | the game goes public: a front page and the installable game on Cloudflare Pages, a coming-soon page until launch, the owner's set-up as a ticket |
| Post mortem | `post-mortem/` | at a project's end, before any tribute or launch page, or right after a slice that went badly: what worked, what didn't, and the rule changes the owner keeps |

## How the pieces fit

1. **Questions.** Five or fewer: a chat message, numbered (1, 1.1, 1.2.1) so the owner can answer "1.2 yes". More: a
   worksheet (`worksheet/`), one screen or topic per sheet, about eight questions at most.
2. **Build** the slice directly, one change at a time, and publish the test build.
3. **Test.** A QA sheet for the slice (`qa-sheet/`): every test's link opens the build in its state. The owner marks
   Pass, Fail or Skip; Claude reads the results, fixes what failed, and adds the next round as a new section.
4. **Tweaks.** A screenshot and one line from the owner; the change; the suite; a look at the phone size; commit,
   publish, a short reply with the link last (the tweak loop, `working-rules.md`).
5. **Fine-tuning.** When the owner wants to tune something themselves, an editor on request (`editors/`): a live
   preview drawn by the game's own code, values saved to the editor's db, Claude applies them.
6. **Track.** Every artifact is a card on the board (`board/`); at each release Claude updates the notes and versions.
   The statuses and the owner's notes are the owner's.
7. **Look back.** At the end, a post mortem (`post-mortem/`): its kept changes go into this skill.

## Before publishing any of them

Load the `artifact-design` skill (and `artifact-capabilities` for the `db` capability). Check every picture a page
references is published with it, open the page locally at phone width (nothing scrolls sideways, every control
reachable with a thumb), and validate the page's data (a stray quote in a test's text breaks the whole sheet).
