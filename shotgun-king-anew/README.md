> **Portable entry point:** read [MIGRATION.md](MIGRATION.md) for current
> dependencies, safe scratch-clone reproduction and installation. This folder
> is now a real root-level drop-in; older paths below are historical. The new
> Lua workload lane is available in the separate skills folder.

# shotgun-king-anew — project pointer

**Open this folder only if** the task is in the owner's `shotgun-king-anew`
repository, or you want the one executed example of REA process capture and
an obligation ledger wrapped around a mod test harness. For every other task,
skip it; nothing here is needed by the skills or by the other project.

| Field | Value |
|---|---|
| Repository | https://github.com/freeforall1932-design/shotgun-king-anew |
| Read at | default branch, commit `4c4bf1bcc9e21c4b274736363e88e3f99065f157`, 2026-10-14 |
| Stack | Lua 5.1 / LuaJIT mod (`sk-rework`) for Shotgun King's SUGAR engine; Python and PowerShell tools; no Qt, no CMake |
| Overlay files **there** (never copied here) | `HANDOFF.md`, `WORKLIST.md`, `notes/game-internals.md`, `shotgun-king-anew/tools/mod_smoketest.py` (the executable UI↔engine contract, 68 checks × 4 iterator variants) |
| Skills that apply | `skills/universal-agent-context` (fully); `skills/qt6-cmake-cpp` does **not** load (no Qt target); the experimental `skills/lua-game-modding` lane now applies |

## Files in this folder

| File | What it is |
|---|---|
| `REA_MOD_SAFETY_EXPERIMENT_2026-10-14.md` | The write-up: nine REA-captured harness runs (baseline + 8 single-edit mutations), which UI/logic changes keep the contract and which break it, the obligation ledger, and what only the live game can prove. |
| `rea_mod_safety_experiment.py` | Re-runs the nine captures on a scratch clone (restores the clone after every mutation). |
| `make-bundle.mjs`, `build_ledger_input.py` | Turn the captures into a canonical REA Evidence bundle and a ledger request. |
| `rea-experiment/results.json`, `rea-experiment/ledger-summary.json` | The kept outputs: evidence ids, file hashes, exit codes, failing rows, ledger statuses and diagnostics. Raw captures are regenerated, not committed. |

## Standing facts for the next session here

- The game binary and `data.sgr` are not in the repository and must not be
  fetched; every verdict here is integration authority (fake engine).
- Two findings for the owner's `WORKLIST.md`, not yet filed there: the `+3`
  ammo step is pinned in four harness rows (name it once); an `all()`
  semantics regression surfaces as a Python `KeyError` at
  `<shotgun-king-anew>/tools/mod_smoketest.py:1126` instead of a `FAILED` row.
