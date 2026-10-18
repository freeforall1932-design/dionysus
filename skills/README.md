# Skills — reusable source and testing catalog

Dionysus is the owner's **skills testing ground**. All live reusable skills are
consolidated in this root folder. Keep them here after copying them to the
skills-repo distribution repository. Promote tested fixes with an explicit
source revision; do not silently let the copies drift.

## Load selectively

| Skill | Read when | Skip when |
|---|---|---|
| `universal-agent-context` | Coding sessions: evidence, verification and handoff discipline | Do not reread the full guide for every trivial edit; use its session minimum |
| `qt6-cmake-cpp` | Real Qt 6 / CMake / C++ targets | Lua, Python, web, .NET or unrelated work |
| `lua-game-modding` | Lua mod hooks, engine boundaries, input safety and fake-engine tests | No Lua game mod involved |

Read the universal wrapper first, the project’s current authoritative records
second, and only task-relevant workload references. Repository facts outrank
skills; the owner's latest instructions govern intent. Skills guide an agent;
only executable tests/gates enforce behavior. Do not infer compliance from an
agent reciting a filename or hash.

## Download and drop in

Copy this **whole folder** into the destination checkout as `skills/`; retain
scripts, templates, references and provenance, not just SKILL.md files. Run:

```sh
python3 skills/validate_skills.py --root . --layout portable --quiet
python3 skills/qt6-cmake-cpp/scripts/qt_lint.py --selftest
```

Python 3.10+ is the portable gate prerequisite; no pip packages, Qt or network
are needed for these commands. They do not build the Qt templates. To compile
those, install a C++ toolchain, Qt 6 and CMake (the supplied presets require
CMake 3.25+), then follow the selected template/reference in a consuming project.
Templates are starting points, not replacements for an existing build.

See [INSTALL.md](INSTALL.md) for harness loading and skills-repo integration.
The destination's existing project state must never be replaced by these files.
Record the Dionysus commit and folder digest in the destination's migration log.

## Rules this directory enforces mechanically

The validator checks skill frontmatter, local reference links, machine paths,
the pinned universal guide hash, Python syntax and the Qt lint self-test.
Portable mode does not require workbench projects, loaders or its index.
The legacy workbench gate additionally checks its index/loaders and historical
research bundle mirrors. Catalog mode supports a variants-based catalog.
None of these checks certify live GUI/game behavior or agent output quality.

## Repository layout and historical copies

The root skills folder is canonical in this testing repository. The old
workbench skills path is a compatibility symlink, not a second source.
The research drop-in is a **dated integration artifact**, not the current skill
catalog. Its old two-skill snapshots are retained for historical reproduction;
refresh deliberately before distribution. Never run its wholesale replacement
instructions against a newer skills-repo without reviewing the diff.

## Provenance and promotion

The universal v4 bytes remain pinned by its PROVENANCE.md. Do not edit them
silently. New generalized guidance belongs in a versioned successor. The Lua
lane is original guidance generalized from the recorded mutation experiment;
it has not yet been evaluated in a new real-game development session.
Qt references and scripts retain their existing source/provenance notes.
Keep upstream and third-party license notices when distributing derived code;
this migration does not grant a new license to game binaries or assets.
