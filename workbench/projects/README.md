# projects/ — pointers to project overlays (layer 3)

A project overlay — status register, handoff, task board, decision log, IDs,
versions, machine facts — **lives in the project's own repository**. This
directory holds nothing but *pointers* to those overlays plus the records that
belong to this repo: dry runs of the skills against the project, and the runbook
for the next session on it.

Rules (from `skills/universal-agent-context/SKILL.md`, "What goes where"):

- A pointer names the repository, the branch, the commit it was last read at, and
  the date. State is never copied here; a copied register goes stale the moment
  the project moves (v4 §13).
- Dry-run and retrospective documents here quote **executed** evidence and carry a
  `Not verifiable here` section (v4 §19).
- `skills/validate_skills.py` checks that every local path mentioned in these
  files exists. It cannot check the remote repository — the date on the pointer
  is the honesty mechanism.

| Project | Pointer | Files here |
|---|---|---|
| gifscythe — Qt 6 / CMake / C++ GUI over the `gifsicle` CLI; the proving ground for `skills/qt6-cmake-cpp` | https://github.com/freeforall1932-design/gifscythe · `main` @ `97b0758` (S40, v0.1.0) · read 2026-10-13 · overlay files there: `STATUS.md`, `SESSION_HANDOFF.md`, `WORKLIST.md`, `IMPROVEMENT_LOG.md`, `OWNER_DECISIONS.md`, `docs/planning/` | `projects/gifscythe/SKILL_DRY_RUN_2026-10-13.md` (lint applied to the real tree, every finding dispositioned), `projects/gifscythe/NEXT_SESSION.md` (runbook for the retrospective + first real application) |

## Adding a project

1. Add a row above with repo URL, branch, commit, date, and the overlay files that
   exist *there*.
2. Create `projects/<name>/NEXT_SESSION.md` using the gifscythe one as the shape:
   RECOVERY (commands) → STATE (one register, read from the project) → SKILLS IN
   PLAY → DECISIONS NEEDED → STANDING CONSTRAINTS. The block holds no state of its
   own.
3. Run `python3 skills/validate_skills.py`.
