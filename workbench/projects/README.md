> **Migration update:** ai-team-kit now lives in the real root folder named
> Odysseus API model team kit. The old project path below is a compatibility
> symlink. Read the root folder MIGRATION.md for portable installation.

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
| gifscythe — Qt 6 / CMake / C++ GUI over the `gifsicle` CLI; the proving ground for `skills/qt6-cmake-cpp` | https://github.com/freeforall1932-design/gifscythe · `main` @ `97b0758` (S40, v0.1.0) · read 2026-10-13; head + lint baseline rechecked 2026-10-18 · overlay files there: `STATUS.md`, `SESSION_HANDOFF.md`, `WORKLIST.md`, `IMPROVEMENT_LOG.md`, `OWNER_DECISIONS.md`, `docs/planning/` | `projects/gifscythe/SKILL_DRY_RUN_2026-10-13.md` (lint applied to the real tree, every finding dispositioned), `projects/gifscythe/NEXT_SESSION.md` (runbook for the retrospective + first real application) |
| shotgun-king-anew — Lua 5.1/LuaJIT mod (`sk-rework`) for Shotgun King's SUGAR engine; no Qt, no CMake; the universal layer applies, no workload lane exists yet | https://github.com/freeforall1932-design/shotgun-king-anew · default branch @ `4c4bf1b` · read 2026-10-14; head + evidence hashes rechecked 2026-10-18 · overlay files there: `HANDOFF.md`, `WORKLIST.md`, `<shotgun-king-anew>/notes/game-internals.md`, `<shotgun-king-anew>/tools/mod_smoketest.py` (the executable UI↔engine contract, 68 checks) | `projects/shotgun-king-anew/REA_MOD_SAFETY_EXPERIMENT_2026-10-14.md` (nine REA-captured harness runs: which UI/logic changes keep the contract, which break it, and what the live game alone can prove), the scripts that regenerate it, `projects/shotgun-king-anew/rea-experiment/` (evidence ids, hashes, ledger summary) |
| ai-team-kit — free-API AI team kit (quota-aware provider pool, adaptive council, model scout + harness); **lives in-repo** (owner-directed exception to the pointer convention), so the overlay files are the folder itself | in-repo · read 2026-10-18 · entry files: `projects/ai-team-kit/README.md`, then `projects/ai-team-kit/SESSION_HANDOFF.md` and `projects/ai-team-kit/WORKLIST.md` | everything under `projects/ai-team-kit/` (canonical kit source, audits, research reports) |
| kobold-cli — KoboldCpp on Google Colab as a pooled API endpoint for the AI team; **in-repo** (owner-directed exception), with a rebuilt adaptation of the official notebook (replacement not yet owner-run on Colab) | upstream https://github.com/LostRuins/koboldcpp · official notebook adapted at `concedo` @ `f41f621` (upstream loader/latest-binary download retained; coding/API presets/defaults changed) · entry: `projects/kobold-cli/README.md` | `projects/kobold-cli/kobold-cli.ipynb`, `projects/kobold-cli/COLAB_LINK.txt` (one-line direct Colab URL), `projects/kobold-cli/COLAB_NOTEBOOK_DISSECTION_2026-10-18.md` (notebook anatomy, flag verdicts, fine-tuned form spec, and upstream-based rebuild correction) |

Cross-project sweep: `projects/CODEBASE_SWEEP_AUDIT_2026-10-18.md` records the 2026-10-18 stale-file, missing-logic, upgrade, and bug sweep across the workbench projects (with upstream dotfiles scanned read-only).

## Adding a project

1. Add a row above with repo URL, branch, commit, date, and the overlay files that
   exist *there*.
2. Create `projects/<name>/NEXT_SESSION.md` using the gifscythe one as the shape:
   RECOVERY (commands) → STATE (one register, read from the project) → SKILLS IN
   PLAY → DECISIONS NEEDED → STANDING CONSTRAINTS. The block holds no state of its
   own.
3. Run `python3 skills/validate_skills.py`.
