> **2026-10-23 cleanup update:** the three portable project drop-in folders
> (`gifscythe`, `shotgun-king-anew`, and `Odysseus API model team kit`) have been
> migrated to their own repositories and removed from Dionysus. Root `skills/`
> remains the live canonical skills catalog (including `skills/SKILL_DEFECT_LOG.md`),
> and `workbench/skills` remains its compatibility symlink.

# workbench — everything in this fork that is not upstream Dionysus

Upstream `pewdiepie-archdaemon/dionysus` is a Hyprland dotfiles repository
(`assets/`, `dotfiles/`). This fork keeps reusable skills in root `skills/` and
remaining experiments/tools under `workbench/` (gated by
`.github/workflows/skills-gate.yml`). All unit paths below are relative to
`workbench/`.

## Triage first — what to open, what to skip

Each unit below is self-contained: one skill, one project, one research page,
one tool. Nothing here needs another unit except the always-on process layer.
`index.json` holds the same table machine-readably (`read_when` / `skip_when`
per unit) and the gate fails if a unit is missing from it or from this page.

| Unit | Open it when | Skip it when |
|---|---|---|
| `skills/universal-agent-context` | every session in one of the owner's repos | never (always on) |
| `skills/lua-game-modding` | Lua mod hooks, engine boundaries, input safety or fake-engine tests | no Lua game mod involved |
| `skills/qt6-cmake-cpp` | the build entry point is CMake + `find_package(Qt6 …)` | no Qt 6 CMake target |
| `projects/kobold-cli` | the task is KoboldCpp-on-Colab as a pooled endpoint for the AI team, or its owner test notebook | any other project; relying on the endpoint until W-021 terms evidence exists |
| `research/modding-engines-2026-10-14.md` | choosing modding/RE tooling or a route | not about modding |
| `research/skills-repo-and-unified-2026-10-14.md` | deciding where skills live or how the process layer composes with a writing register | inside-project work |
| `research/harness-skill-support-2026-10-14.md` | installing the skills into a harness, or adding a harness profile — real skill dirs vs read-by-path vs paste-only, with sources | not about harness installation |
| `tools/magnet-excavator` | working on that tool | everything else |

## Directory map

| Directory | What it is | Start at |
|---|---|---|
| `skills/` | **Agent skills** (compatibility symlink to root `skills/`) — the process layer (`universal-agent-context`, wrapping `UNIVERSAL_AGENT_CONTEXT_v4.md`), workload skills (`qt6-cmake-cpp`, `lua-game-modding`), and the skills defect journal (`skills/SKILL_DEFECT_LOG.md`). Gated by `skills/validate_skills.py` and `.github/workflows/skills-gate.yml`. | `skills/README.md` |
| `projects/` | Remaining in-repo companion project (`projects/kobold-cli/`) and historical codebase sweep audit (`projects/CODEBASE_SWEEP_AUDIT_2026-10-18.md`). The three migrated projects (`gifscythe`, `shotgun-king-anew`, `Odysseus API model team kit`) live in their own repositories. | `projects/README.md` |
| `research/` | **Dated surveys and assessments** that back a decision, verified on the stated day; executed artefacts for one live in `research/skills-repo-compat/`. | `research/README.md` |
| `tools/magnet-excavator/` | Stdlib-only Python tool that pulls magnet links out of saved pages, with a local GUI and 142 tests (added by PR #1, moved here from the repo root). | `tools/magnet-excavator/README.md` |
| `AGENTS.md` = `CLAUDE.md` | The loader paragraph harnesses read when they work inside this folder. | — |

## Skills in one paragraph

The universal skill says *how to work* in any repo (evidence ranking, verification
ladder, truth maintenance, reporting). A workload skill says *what this kind of
work needs* (Qt 6 build/test/package facts, Lua mod safety, patterns, a lint that
can fail). The project's own repo says *where this project is* (status,
decisions, IDs). Load in that order; repository evidence outranks all three; the
owner's latest instruction outranks every document. Nothing in `skills/` names a
machine path — `validate_skills.py` fails if it does.

## Running the gate locally

```bash
python3 skills/validate_skills.py                       # frontmatter, links, machine paths, universal hash, pointers, lint self-test
python3 skills/qt6-cmake-cpp/scripts/qt_lint.py --selftest
python3 skills/qt6-cmake-cpp/scripts/qt_lint.py <path-to-a-qt-project>/src   # exit 1 on new warnings
```

No Qt, CMake or network is needed for the gate. The Qt *templates* are compiled
only inside a consuming project's CI.
