# projects/ — project pointers and companion experiments (layer 3)

A project overlay — status register, handoff, task board, decision log, IDs,
versions, machine facts — **lives in the project's own repository**.

The three earlier portable project drop-in folders have been migrated out of
Dionysus into their destination repositories and removed here on 2026-10-23
(with the skills' own retrospective journal preserved at
`skills/SKILL_DEFECT_LOG.md`):

| Project | Repository | Status in Dionysus |
|---|---|---|
| gifscythe — Qt 6 / CMake / C++ GUI over the `gifsicle` CLI; proving ground for `skills/qt6-cmake-cpp` | https://github.com/freeforall1932-design/gifscythe | Migrated; local drop-in removed (`skills/SKILL_DEFECT_LOG.md` kept in `skills/`) |
| shotgun-king-anew — Lua 5.1/LuaJIT mod (`sk-rework`) for Shotgun King's SUGAR engine | https://github.com/freeforall1932-design/shotgun-king-anew | Migrated; local drop-in removed |
| Odysseus API model team kit — free-API AI team kit (provider pool, adaptive council, model scout + harness) | https://github.com/freeforall1932-design/odysseus-fork-but-api-dev | Migrated; local drop-in removed |
| kobold-cli — KoboldCpp on Google Colab as a pooled API endpoint for the AI team | in-repo companion under `projects/kobold-cli/` (adapted from https://github.com/LostRuins/koboldcpp `concedo` @ `f41f621`) | Active here: `projects/kobold-cli/README.md`, `projects/kobold-cli/kobold-cli.ipynb`, `projects/kobold-cli/COLAB_LINK.txt`, `projects/kobold-cli/COLAB_NOTEBOOK_DISSECTION_2026-10-18.md` |

Cross-project historical sweep: `projects/CODEBASE_SWEEP_AUDIT_2026-10-18.md`
records the 2026-10-18 stale-file, missing-logic, upgrade, and bug sweep before
the three migrated project folders were removed.
