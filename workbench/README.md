> **2026-10-18 migration update:** Dionysus is the skills testing ground. Live
> reusable skills and the two portable project-support folders now live at the
> repository root. Old workbench paths below resolve through compatibility
> symlinks. See the root README and each root MIGRATION.md for download/drop-in
> instructions. The earlier "everything under workbench" convention below is
> historical and no longer applies to those three folders.

# workbench — everything in this fork that is not upstream Dionysus

Upstream `pewdiepie-archdaemon/dionysus` is a Hyprland dotfiles repository
(`assets/`, `dotfiles/`). This fork adds its own work **only under this folder**
(plus `.github/workflows/skills-gate.yml`, which GitHub insists on reading from
the repository root). All paths in the documents below are relative to
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
| `projects/gifscythe` | the task is in gifscythe (Qt 6 app) | any other repo |
| `projects/shotgun-king-anew` | the task is in shotgun-king-anew (Lua mod), or you want the REA capture/ledger example | any other repo or topic |
| `projects/ai-team-kit` | the task is the free-API AI team kit (provider pool, council direction, scout/harness) | any other project |
| `projects/kobold-cli` | the task is KoboldCpp-on-Colab as a pooled endpoint for the AI team, or its owner test notebook | any other project; relying on the endpoint until W-021 terms evidence exists |
| `research/modding-engines-2026-10-14.md` | choosing modding/RE tooling or a route | not about modding |
| `research/skills-repo-and-unified-2026-10-14.md` | deciding where skills live or how the process layer composes with a writing register | inside-project work |
| `research/harness-skill-support-2026-10-14.md` | installing the skills into a harness, or adding a harness profile — real skill dirs vs read-by-path vs paste-only, with sources | not about harness installation |
| `tools/magnet-excavator` | working on that tool | everything else |

Added per session: 2026-10-12 magnet-excavator (PR #1); 2026-10-13 both skills,
gifscythe pointer; 2026-10-14 shotgun-king-anew, three research pages, the skills-repo drop-in bundle under `research/skills-repo-compat/drop-in/`; 2026-10-18 the in-repo AI Team Kit and Kobold CLI project folders (the latter now with an owner test notebook), plus `projects/CODEBASE_SWEEP_AUDIT_2026-10-18.md`.

## Directory map

| Directory | What it is | Start at |
|---|---|---|
| `skills/` | **Agent skills** — the process layer (`universal-agent-context`, wrapping `UNIVERSAL_AGENT_CONTEXT_v4.md`) and the first workload layer (`qt6-cmake-cpp`: references, drop-in templates, `qt_lint.py`). Gated by `skills/validate_skills.py` and `.github/workflows/skills-gate.yml`. | `skills/README.md` — includes the answer to "one skill, two, or three?" |
| `projects/` | **Pointers to project overlays** that live in their own repositories, plus dry-run evidence and the next-session runbook for each. Today: gifscythe (Qt 6 / CMake / C++), the proving ground for the Qt skill, and shotgun-king-anew (Lua mod), where the REA mod-safety experiment ran. Two folders are owner-directed exceptions that keep their substance in-repo instead of pointing out: `projects/ai-team-kit/` (the free-API AI team project) and `projects/kobold-cli/` (its KoboldCpp-on-Colab arm). | `projects/README.md`, then `projects/gifscythe/NEXT_SESSION.md` |
| `research/` | **Dated surveys and assessments** that back a decision, verified on the stated day; executed artefacts for one live in a sibling folder (`research/skills-repo-compat/` holds the tested `compile.py` patch and the measurements). | `research/README.md` |
| `tools/magnet-excavator/` | Stdlib-only Python tool that pulls magnet links out of saved pages, with a local GUI and 142 tests (added by PR #1, moved here from the repo root). | `tools/magnet-excavator/README.md` |
| `AGENTS.md` = `CLAUDE.md` | The loader paragraph harnesses read when they work inside this folder. | — |

## Skills in one paragraph

The universal skill says *how to work* in any repo (evidence ranking, verification
ladder, truth maintenance, reporting). A workload skill says *what this kind of
work needs* (Qt 6 build/test/package facts, patterns, a lint that can fail). The
project's own repo says *where this project is* (status, decisions, IDs). Load in
that order; repository evidence outranks all three; the owner's latest instruction
outranks every document. Nothing in `skills/` names a project, a version, or a
machine path — `validate_skills.py` fails if it does.

## Running the gate locally

```bash
cd workbench
python3 skills/validate_skills.py                       # frontmatter, links, machine paths, universal hash, pointers, lint self-test
python3 skills/qt6-cmake-cpp/scripts/qt_lint.py --selftest
python3 skills/qt6-cmake-cpp/scripts/qt_lint.py <path-to-a-qt-project>/src   # exit 1 on new warnings
```

No Qt, CMake or network is needed for the gate. The Qt *templates* are compiled
only inside a consuming project's CI — see `projects/gifscythe/NEXT_SESSION.md`.
