# workbench — everything in this fork that is not upstream Dionysus

Upstream `pewdiepie-archdaemon/dionysus` is a Hyprland dotfiles repository
(`assets/`, `dotfiles/`). This fork adds its own work **only under this folder**
(plus `.github/workflows/skills-gate.yml`, which GitHub insists on reading from
the repository root). All paths in the documents below are relative to
`workbench/`.

| Directory | What it is | Start at |
|---|---|---|
| `skills/` | **Agent skills** — the process layer (`universal-agent-context`, wrapping `UNIVERSAL_AGENT_CONTEXT_v4.md`) and the first workload layer (`qt6-cmake-cpp`: references, drop-in templates, `qt_lint.py`). Gated by `skills/validate_skills.py` and `.github/workflows/skills-gate.yml`. | `skills/README.md` — includes the answer to "one skill, two, or three?" |
| `projects/` | **Pointers to project overlays** that live in their own repositories, plus dry-run evidence and the next-session runbook for each. Today: gifscythe (Qt 6 / CMake / C++), the proving ground for the Qt skill, and shotgun-king-anew (Lua mod), where the REA mod-safety experiment ran. | `projects/README.md`, then `projects/gifscythe/NEXT_SESSION.md` |
| `research/` | **Dated surveys** that back a decision: which repositories exist for a problem, verified against the GitHub API on the stated day, and what applies to the owner's projects. | `research/modding-engines-2026-10-14.md` |
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
