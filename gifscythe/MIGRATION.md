# Gifscythe drop-in: dependencies, reproduction and skills

Prepared 2026-10-18. This folder is **supporting material**, not the application
source or a replacement project overlay. The historical dry run targets main
commit 97b075829cb0a2b52a9d34e45d275cd68bfba32a. Recheck the destination head
before treating its old counts or decisions as current.

## Install without overwriting the project

1. Open the existing freeforall1932-design/gifscythe checkout. Keep its root
   status, handoff, worklist, decisions and universal guide intact.
2. Copy this folder as a new subfolder named gifscythe at the checkout root.
   If that name already exists, stop and compare instead of overwriting it.
3. Copy the sibling downloadable skills folder as skills at the checkout root.
   Do not replace a pre-existing skills directory without reviewing its diff.
4. Append the loader from the skills INSTALL.md to the project's existing agent
   instructions, using paths relative to the checkout root. Load the universal
   and Qt lanes; skip the Lua lane.
5. Record source Dionysus commit, destination commit, copied paths and date in
   the project's handoff. Keep the universal v4 hash unchanged during relocation.

The old reports use testing-repository/workbench-relative paths. They are dated
historical evidence, not directly executable destination instructions. Use this
file for current copy paths and commands. NEXT_SESSION.md remains useful for
its decision checkpoints; consult current project records before acting.

## Dependency map

| Operation | Needs | Does not prove |
|---|---|---|
| Read skills / reports | Repository-reading agent, files installed | Actual agent compliance |
| Validate skill structure / run Qt lint | Python 3.10+, standard library only | C++ compilation or GUI correctness |
| Build existing Qt application | CMake, C++17 toolchain, Qt 6 Widgets and dependencies selected by the actual build | Deployment on another machine |
| Run C++ / offscreen tests | Built project test targets, Qt runtime/plugins; offscreen QPA for headless runs | Desktop appearance or user acceptance |
| Conversion integration | The project's gifsicle engine, fixture inputs and existing packaging rules | Output correctness without output verification |
| Build skill templates | C++ toolchain, Qt 6; supplied presets require CMake 3.25+ | That templates fit this existing project unchanged |
| Release | Platform compiler/SDK, Qt deployment tooling and required plugin/engine/license payloads | Clean-machine acceptance until tested there |

Ninja is needed if selecting a Ninja generator; do not assume it for all build
routes. Follow the project's existing CI for exact Qt/compiler/platform versions.
Its optional C# and other lanes have separate dependencies; the Qt skill does
not replace their build instructions. Do not install the entire testing repo as
an application runtime dependency.

## Reproduce the portable checks

Run from the **destination repository root** after copying both folders:

```sh
python3 skills/validate_skills.py --root . --layout portable --quiet
python3 skills/qt6-cmake-cpp/scripts/qt_lint.py --selftest
cd working_code/gifscythe
python3 ../../skills/qt6-cmake-cpp/scripts/qt_lint.py src tests CMakeLists.txt
python3 ../../skills/qt6-cmake-cpp/scripts/qt_lint.py src tests CMakeLists.txt --baseline ../../gifscythe/qt_lint.baseline.json
```

The unbaselined lint intentionally exits nonzero for findings. At the historical
revision the recorded result was nine findings; baseline keys depend on running
from working_code/gifscythe, **not the repository root**. Baseline exit zero is
acceptance of known warnings, not their elimination. Investigate any changed
findings against source and current owner decisions before refreshing it.

## Reproduce build/tests (existing project, not the templates)

From the destination repository root with dependencies installed:

```sh
working_code/gifscythe/scripts/check_docs.sh
working_code/gifscythe/scripts/sweep_stale.sh
cmake -S working_code/gifscythe -B build -DBUILD_GUI=ON
cmake --build build
QT_QPA_PLATFORM=offscreen ctest --test-dir build --output-on-failure
```

These shell examples target a POSIX shell. Use the existing Windows workflow
for its toolchain and environment syntax. Inspect configure output: the current
build uses optional Qt discovery, so BUILD_GUI=ON alone is **not proof the GUI
was built**. Confirm GUI and offscreen test targets were created and executed.
Do not bypass project document/hook gates if they reject the new files: update
project records through its supported workflow.

## Bonus uses and guardrails

- Qt subprocess reference: no shell-string argv, honest cancel and valid output
  checks before success; preserve previous good output.
- UI behavior contract: map controls, engine inputs, events, states and per-file
  results before redesign. Preserve test objectNames unless tests change too.
- Packaging reference: test the actual staged package in a clean environment.
- Optional future skill exercise: compile each supplied Qt template in an
  isolated sample project before treating it as production-ready.

Do not reopen accepted bounded waits merely because lint flags them. Do not
make GUI edits until current owner decision gates permit them.

## Evidence and limits

Historical evidence remains in the dry-run and defect logs. Migration-session
checks cover portable structure, lint self-test, template lint and archive
integrity, not a new application build. **Not verifiable here:** desktop
acceptance, clean-machine packaging, Qt template compilation and any controlled
measurement of agent-output improvement. Record new results against exact SHAs.
