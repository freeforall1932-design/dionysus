# Qt 6 · CMake · C++ (layer 2 workload skill)

Read the process layer first — `../universal-agent-context/SKILL.md`, installed
beside this skill — this skill assumes it.
Everything below is *what this stack needs*; nothing below is a project fact.
When a project's register says a finding here is accepted (for example a
bounded blocking wait that was measured and dispositioned), the register wins
and the lint baseline records it (v4 §13.4).

## Reference index — open only what the task needs

| Topic | File | Read when |
|---|---|---|
| Build: modern Qt6 CMake, presets, Linux/Windows/macOS, sanitizers, warnings, resources, version single-source | `references/cmake.md` | touching any `CMakeLists.txt`, presets, or CI build steps |
| Architecture: ownership, lifetimes, signal/slot rules, startup/shutdown, error reporting, logging categories | `references/architecture.md` | new modules, refactors, crash classes |
| GUI over a CLI engine: QProcess lifecycle, cancel, timeouts, exit codes, stale output, atomic promotion, settings snapshot | `references/subprocess-engine.md` | the app shells an executable (converter, encoder, packer…) |
| Testing: offscreen QPA, house-style harness vs QTest, objectName contract, dialog auto-close, fixtures, CI wiring | `references/testing.md` | adding or changing tests; any UI change (the harness contract) |
| UI redesign of an existing Qt Widgets app: method, state inventory, mockups, theming/palette, high-DPI, results tables, screenshot capture | `references/ui-redesign.md` | the task says redesign, new layout, dark mode, "looks like X" |
| Crash/hang diagnosis on Linux and Windows: sanitizers, cores, minidump concept, QPointer, thread guards, readable crash record | `references/crash-diagnosis.md` | a crash, a freeze, a use-after-free, "works on my machine" |
| Packaging and deployment: plugins that must ship, windeployqt/linuxdeploy/macdeployqt, LGPL notices, portable zips, clean-machine smoke | `references/packaging.md` | releases, artifacts, "missing platform plugin" |
| Platform notes: Wayland/X11, MinGW vs MSVC, console subsystem, DPI, paths/Unicode, Defender, fonts | `references/platform-notes.md` | a platform-specific symptom |

## Drop-in templates (`templates/`)

Written fresh for this skill (the reference repository that inspired the
pattern carries no license, so none of its files were copied). **Not compiled
in the session that wrote them — the sandbox had no Qt 6 or CMake.** First use
must build them in CI or on a Qt machine and record the result in
`projects/<name>/`.

| File | Purpose |
|---|---|
| `templates/CMakeLists.txt` | Cross-platform skeleton: core INTERFACE/STATIC lib, `qt_add_executable(… WIN32 MACOSX_BUNDLE)`, offscreen test target with `QT_QPA_PLATFORM`, optional ASan/UBSan, warnings, deploy script hook |
| `templates/VERSION` + `templates/cmake/version.h.in` | The single version source the skeleton reads (`MAJOR.MINOR.PATCH`) and the header it generates **into the build tree only** (`app::version::string`) |
| `templates/CMakePresets.json` | `linux-gcc`, `linux-clang-asan`, `windows-mingw`, `windows-msvc`, `macos` configure presets + build/test presets; Qt location via `CMAKE_PREFIX_PATH` from an env var, never a literal path |
| `templates/thread_guard.h` | `ASSERT_THREAD(obj)` — thread-affinity assertion that logs class/method/threads before `Q_ASSERT_X` |
| `templates/logging.h` | Per-module `QLoggingCategory` declarations, a one-line structured message handler, a bounded ring buffer for crash records |
| `templates/offscreen_test_main.cpp` | House-style offscreen harness skeleton: CHECK counter, non-zero exit, modal-dialog auto-closer, objectName lookup helper, fixture directory from env |
| `templates/github-workflow-qt.yml` | Linux (apt `qt6-base-dev`) + Windows (aqt, MinGW) jobs that build, run unit + offscreen tests, package, and assert the package manifest |

## Mechanical check (`scripts/qt_lint.py`)

Standard-library Python. Scans C++ and CMake for the anti-patterns the
references explain, with an ID per rule, a `--baseline` so an existing project
can accept dispositioned findings and fail only on new ones, `--json`, and a
`--selftest` that proves every rule fires on a bad fixture and stays silent on
a clean one.

```bash
python3 skills/qt6-cmake-cpp/scripts/qt_lint.py <dir-or-files>            # report, exit 1 on warning+
python3 skills/qt6-cmake-cpp/scripts/qt_lint.py src --write-baseline qt_lint.baseline.json
python3 skills/qt6-cmake-cpp/scripts/qt_lint.py src --baseline qt_lint.baseline.json
python3 skills/qt6-cmake-cpp/scripts/qt_lint.py --selftest
```

It is a grep with a parser for `connect(` arguments, not a compiler: it finds
*candidates*, the human reads the site. A rule's finding is never a status flip
on its own (v4 §6).

## Quick patterns (the ten things to get right on this stack)

1. **Build entry:** `cmake_minimum_required(VERSION 3.21)` (Qt 6 CMake API floor;
   older minimums work for simple trees but presets v6 and `qt_standard_project_setup`
   want 3.21+), `find_package(Qt6 REQUIRED COMPONENTS …)`,
   `qt_standard_project_setup()`, `qt_add_executable(app WIN32 MACOSX_BUNDLE …)`,
   `target_link_libraries(app PRIVATE Qt6::Widgets)`. Never `add_executable` +
   manual AUTOMOC for a Qt target when the Qt API is available.
2. **One version source.** Read it in CMake with `file(READ)`, generate a header
   **into the build tree only**; configure must never write into the source tree.
3. **Connections:** pointer-to-member only; every lambda gets a context object
   (4-argument form) or a `QPointer` guard; `Qt::UniqueConnection` in re-init paths;
   explicit `Qt::QueuedConnection` across threads.
4. **Ownership:** parent-child for widgets; `QPointer<T>` for any `QObject*`
   member you do not own; `std::unique_ptr` for non-QObject state; no raw
   `new` without a parent or an owner.
5. **Never block the GUI thread for the *duration* of work.** Bounded waits at
   start/cancel may be acceptable when *measured* and recorded; unbounded
   `waitForFinished()`, nested `QEventLoop::exec()`, `processEvents()` loops are
   defects until proven otherwise.
6. **Engine subprocesses:** build argv as a list (never a shell string), connect
   `finished` *and* `errorOccurred`, drain stdout/stderr continuously, write to
   a temp path and promote atomically only after exit 0 **and** output
   verification; cancel = kill + reap + keep the previous good output.
7. **Tests run headless:** `QT_QPA_PLATFORM=offscreen` on the test property or
   in the harness; widgets are found by `objectName` — treat object names as a
   public test API and keep them across redesigns.
8. **Deployment is part of the build:** the `platforms/` plugin, `imageformats/`
   the app actually loads, `styles/` if used, LGPL notices for Qt, the engine
   binary; verify the staged package in a fresh job, not only the build tree.
9. **Diagnosability by default:** logging categories per module, one-line log
   format, a thread-affinity assert in thread-sensitive methods, sanitizer
   preset in CI, a crash record a reader can grep.
10. **Linux is Wayland and X11; Windows is MinGW *and* MSVC.** Do not assume one.
    `long` is 4 bytes on Windows; paths are UTF-16 there; the console subsystem
    opens a window unless `WIN32` is set.

## Review checklist (paste into a PR review)

- [ ] `qt_lint.py` clean or every finding baselined with a reason in the project register
- [ ] every new `connect` has a context object or `QPointer` guard; no string-based `SIGNAL/SLOT`
- [ ] no new unbounded wait / nested event loop on the GUI thread
- [ ] QProcess sites: argv list, both `finished` and `errorOccurred`, continuous draining, timeout, cancel path, output verified before success
- [ ] file writes that replace user data use `QSaveFile` or temp+rename
- [ ] object names of widgets the harness touches unchanged (or the harness updated in the same change)
- [ ] offscreen harness and unit suites run locally where Qt exists; otherwise CI run ID quoted
- [ ] packaging manifest still asserts every required plugin/notice/binary
- [ ] no hard-coded machine path or Qt location in CMake, presets, scripts, or docs

---

## Files of the `qt6-cmake-cpp` skill — not inlined

Relative paths above resolve inside `.github/skills/qt6-cmake-cpp/` (install the skill directory from `packs/<agent>/skills/qt6-cmake-cpp/` there; nothing below is reproduced in this file).

- `.github/skills/qt6-cmake-cpp/references/architecture.md`
- `.github/skills/qt6-cmake-cpp/references/cmake.md`
- `.github/skills/qt6-cmake-cpp/references/crash-diagnosis.md`
- `.github/skills/qt6-cmake-cpp/references/packaging.md`
- `.github/skills/qt6-cmake-cpp/references/platform-notes.md`
- `.github/skills/qt6-cmake-cpp/references/subprocess-engine.md`
- `.github/skills/qt6-cmake-cpp/references/testing.md`
- `.github/skills/qt6-cmake-cpp/references/ui-redesign.md`
- `.github/skills/qt6-cmake-cpp/scripts/qt_lint.py`
- `.github/skills/qt6-cmake-cpp/templates/CMakeLists.txt`
- `.github/skills/qt6-cmake-cpp/templates/CMakePresets.json`
- `.github/skills/qt6-cmake-cpp/templates/VERSION`
- `.github/skills/qt6-cmake-cpp/templates/cmake/version.h.in`
- `.github/skills/qt6-cmake-cpp/templates/github-workflow-qt.yml`
- `.github/skills/qt6-cmake-cpp/templates/logging.h`
- `.github/skills/qt6-cmake-cpp/templates/offscreen_test_main.cpp`
- `.github/skills/qt6-cmake-cpp/templates/thread_guard.h`
