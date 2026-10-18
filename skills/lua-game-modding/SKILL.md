---
name: lua-game-modding
description: Safety and verification guidance for Lua game mods with proprietary or unavailable engines. Use for hook changes, input consumption, engine API boundaries, iterator compatibility, save handling and fake-engine regression tests. Skip unrelated stacks. Does not require or redistribute game binaries.
metadata:
  layer: workload
  paste: loader
---

# Lua game-modding safety

Read `../universal-agent-context/SKILL.md` first. For UI changes also read
`../universal-agent-context/references/ui-behaviour-contract.md`.
This is an original, experimental workload lane; it needs evaluation on future
real tasks, not a claim of demonstrated output improvement.

## Before editing

- Inspect the actual entry script, engine notes, loader, runtime version and
  existing smoke-test harness. Lua 5.1, LuaJIT and later Lua versions are not
  interchangeable; use syntax supported by the shipped runtime.
- Read owner decisions and known incidents. Do not turn historical assumptions
  about a proprietary engine into confirmed API behavior.
- Map each hook and global write: who owns it, when it runs, what it returns,
  and whether the engine sandbox permits the write. Preserve the existing
  hook chain; replacing a global callback can silently remove other mods.
- Record test scope: modeled engine calls are integration evidence, not a
  recording of real-game behavior.

## Change and verification contract

| Change | Required regression evidence | Remaining live check |
|---|---|---|
| Move/resize controls | Tests locate controls from drawn geometry, hit bounds and modal state | Render/scale and real mouse handling |
| Rename visible controls | Intentional label contract updated with UI and tests together | Readability/localization |
| Input handling | Click consumed before board logic; outside clicks and close/reset paths tested | Engine event ordering, held buttons and click-through |
| Gameplay amount/limit | Every affected scenario, log and safety guard updated; negative case still fails | Interaction with real game state |
| Iterator compatibility | Test each plausible iterator convention until actual engine behavior is observed | Confirm shipped engine semantics |
| Hook/API call | Assert allowed calls and forbidden side effects, including failure paths | Interaction with other installed mods |
| Save/install tools | Backups, scratch fixtures, dry-run where supported; no user-save overwrite | Restore on a disposable profile |

Do not change expected values merely to make failing tests green: first decide
whether the requirement intentionally changed. Keep an independent invariant
or negative test so coordinated mistakes in code and tests remain detectable.

## Practical testing

Use the project's existing harness; a Python/Lua bridge such as lupa is a dev
option, not a new mandatory game dependency. Check which Lua runtimes the
installed bridge actually provides and report skipped variants explicitly.

Mutation tests are useful for input swallowing, forbidden engine calls and
iterator assumptions. Run them only in a **disposable clean clone**. Never
restore tracked files with destructive Git commands in an owner's active tree.
Capture exact source hashes, command, runtime, exit code and failing assertion.
An evidence wrapper is optional: a clear test log is preferable to an opaque
ledger that overstates its authority.

## Release boundary

Keep game binaries and proprietary data out of the skill and test bundles.
Audit asset/code permissions before redistribution. Smoke-test the actual
installed mod in a legitimately available game when possible; keep unobserved
input, rendering, engine and inter-mod behavior explicitly open otherwise.
