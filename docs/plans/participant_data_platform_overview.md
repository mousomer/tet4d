# Tet4D Player Progress and Research Data — Plain-language Plan

Role: reference
Status: reference
Source of truth: none
Companion documents: `spatial_intuition_research_plan.md`, `participant_data_platform_implementation.md`
Supersedes: none
Date: 2026-11-18

## 1. What we want to do

Tet4D lets people play and explore in two, three and four dimensions. We want players to see how they improve over time. We also want to study a harder question: **can practice in Tet4D help people develop an understanding of four-dimensional space that they can use outside the game?**

To answer both needs, we plan to add optional user accounts, a secure central place to save progress, and a small set of carefully designed spatial reasoning assessments.

The project has three distinct outputs:

- **Player progress:** game results, practice history, and achievements.
- **Observations:** what happened during a session or assessment.
- **Research conclusions:** what those observations suggest about learning, after appropriate comparisons and statistical analysis.

A higher game score does not by itself prove that somebody has developed four-dimensional intuition.

This document explains the intended system for non-specialists. The detailed development order is in [Participant Data Platform Implementation Plan](participant_data_platform_implementation.md). Scientific study design remains governed by [Spatial Intuition Research Plan](spatial_intuition_research_plan.md).

## 2. What players will see

Players can continue playing without an account. Their progress can remain on their own computer.

A registered player will be able to save progress online, return on another supported installation, and view a simple history of sessions. We initially expect email one-time-code sign-in, with no need for Tet4D to maintain passwords.

The progress page should show:

- how often and how long someone played or explored;
- which dimensions, tasks, and topologies they used;
- scores or successes in comparable activities;
- results from short spatial reasoning assessments;
- changes over time, including where comparisons are uncertain.

Registration does **not** automatically make the player a research participant. Joining a study must be a separate, clearly explained decision.

## 3. What will be saved

### Ordinary play

Ordinary sessions will normally produce **one small summary**, not a recording of every keystroke. A summary can contain the activity and configuration, duration, score, completed tasks, and counts of useful actions or errors.

### Assessment tasks

Some tasks ask a specific spatial question, such as:

- Which cells are neighbors in a four-dimensional object?
- What happens to an object after a rotation in a particular plane?
- Is an object the same one when viewed from a different direction?
- Where will a cell be after a sequence of transformations?

For these tasks we need the exact question, the answer, whether it was correct, relevant timing and hints, and the version of the assessment. We need enough information to check the result later.

### Detailed research sessions

For a limited number of authorized research sessions, the system may keep a compact sequence of meaningful operations: object rotations, translations, camera/view changes, slice selection, answers, resets and failures.

It should **not** routinely record video, screenshots, cursor motion every frame, or other unnecessary details. Explorer allows topological behavior that differs from ordinary rigid-body movement; these sessions must be described correctly rather than treating exploratory behavior as an error.

## 4. How we will measure improvement

The first assessments will measure separate skills rather than giving everybody a single unvalidated "4D IQ" score:

| Skill | Example |
| --- | --- |
| Rotations | Predict an object's orientation after a 4D rotation |
| Neighbor relationships | Identify adjacent 4D cells |
| Different views | Recognize one object under another projection |
| Coordinates | Predict positions after transformations |
| Problem solving | Reach an unfamiliar target configuration |
| Transfer | Solve new tasks that do not reuse practiced patterns |

An initial assessment can be followed by practice, a second assessment using different but comparable questions, a test with unfamiliar problems, and a later retention test.

Researchers must also distinguish learning the controls from learning spatial ideas. Where feasible, a study will compare Tet4D practice with an appropriate comparison condition. The first reports will show observable results and uncertainty; more complex ability estimates can be added only after there is evidence that they are valid.

## 5. Where the data will live

We propose **Supabase**, a managed service providing accounts, a PostgreSQL database, secure APIs, and file storage. The initial hosted project would be created in the Ireland region (`eu-west-1`).

The intended journey is:

1. Tet4D records a permitted session locally.
2. The game saves its information on the computer first.
3. When a network connection is available, it sends the saved information securely.
4. The server checks ownership, permissions and record integrity.
5. Acknowledged records become part of the player's online history.

The game must remain fully usable offline. Interrupted connections must not erase progress or create duplicate results.

Supabase is the **leading candidate**, not a claim that hosting already exists. The final provider is chosen in a separate decision once the measurement and storage contract is agreed. An account, contract, region choice, privacy review and deployment authorization are still needed.

## 6. How we will keep storage small

The guiding rule is **save what is needed to answer a defined question, not everything the computer does**.

- Routine gameplay: small session summaries, with an initial target of no more than about 10 KiB (roughly ten thousand bytes) of logical summary data per session.
- Assessments: individual responses and task information, because they are needed for later comparison.
- Detailed research: only selected sessions; compressed sequences of meaningful actions rather than full boards after every move.
- Temporary records: remove or archive them under an approved retention policy.
- Monitoring: watch growth, unexpected event rates, and monthly cost.

These sizes are planning targets to test, not measurements from existing users. A detailed research session that exceeds its target must be split into trace segments or explicitly marked incomplete; it must not be quietly truncated.

## 7. Privacy and personal control

The system must separate:

1. **Account identity**, needed for login and recovery.
2. **Player history**, needed to show progress.
3. **Research identity**, a separate identifier used for studies.

A player can save personal progress without joining a study. Any research collection must have a documented purpose and suitable legal and ethics arrangements. Research exports should normally exclude names and email addresses.

Players must be able to understand what is collected, which activities are recorded in detail, and how to request an export or deletion. Rules for withdrawal, research retention, backups and any legal exceptions must be reviewed before collecting real participant data.

The first study pilot should recruit adults only. Studies involving children need additional review and safeguards. Hosting data in Ireland alone does not establish GDPR compliance.

## 8. The development sequence

| Stage | What we will build | Evidence of success |
| --- | --- | --- |
| 1. Define measurements | Decide what to measure and how to interpret it | Clear tasks, data fields, privacy and storage rules |
| 2. Record locally | Session summaries and safe storage on the player's device | No lost completed records on restart; no gameplay impact |
| 3. Accounts and server | Optional registration and secure online synchronization | Progress returns on another installation; no cross-user access |
| 4. Assessments | Repeatable questions and a simple progress page | Results can be compared and independently checked |
| 5. Research recordings | Limited, detailed studies with explicit permission | Meaningful session sequences can be reconstructed |
| 6. Pilot | Test the entire system with authorized adults | Data completeness, task usability and costs are established |

A research study must not begin simply because the software appears to work. It also needs a suitable protocol, permission and ethics review where applicable, reliable assessments and an independently checked dataset.

## 9. What could go wrong

| Risk | Main safeguard |
| --- | --- |
| Collecting far too much data | Record summaries by default and detailed traces selectively |
| Losing records offline | Local durable storage and acknowledged retries |
| Saving the same session twice | Stable session IDs and duplicate detection |
| Exposing private data | Secure account checks and restricted research access |
| Apparent improvement is only keyboard familiarity | Independent, unfamiliar spatial reasoning tasks |
| An updated game changes the meaning of results | Store game, task, topology and scoring versions |
| Data can no longer be reproduced | Preserve exact assessment questions, answers and configurations |
| A hosting incident destroys records | Back up both the database and stored trace files |
| Uncontrolled hosting cost | Data budgets, retention and usage alerts |

## 10. What success means

A **product success** means a person can play, save progress, reconnect later, and see a clear, accurate history.

A **data-platform success** means researchers can reconstruct authorized observations, distinguish reliable from incomplete records, and repeat the same analysis.

A **scientific success** means the project can conduct a fair test and report what the results show, including negative or inconclusive findings. It is not defined as proving that Tet4D works.

**The purpose of the platform is to collect enough reliable information to understand learning—not to collect as much information as possible.**

## 11. Status and next step

This is a planning document. No backend, public account service, participant recording authorization, or new scientific result is asserted by its publication.

The next engineering step is to agree on the assessment and event contract, then build local recording before relying on cloud hosting.
