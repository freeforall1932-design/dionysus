# gifscythe × skills — dry run, 2026-10-13

**Purpose.** Prove, with executed evidence, that the two skills in this repo
(`skills/universal-agent-context`, `skills/qt6-cmake-cpp`) say something *true and
useful* about the example project before the next session applies them to real work.
This is the "is this session heading the right direction?" check the owner asked for.

**Subject.** `freeforall1932-design/gifscythe`, `main` @ `97b0758` (S40 state, v0.1.0),
shallow clone in a sandbox. Nothing in gifscythe was modified or pushed.

**Tool under test.** `skills/qt6-cmake-cpp/scripts/qt_lint.py` (QL001–QL015) — the only
*executable* part of the Qt skill, so it is the only part that can be proven here. The
prose parts (references, templates) are checked for consistency by
`skills/validate_skills.py`, not for truth; their truth gets tested in the next session.

---

## 1. Commands (reproducible)

```bash
git clone --depth 1 https://github.com/freeforall1932-design/gifscythe /tmp/refs/gifscythe
cd /tmp/refs/gifscythe/working_code/gifscythe
LINT=<dionysus>/workbench/skills/qt6-cmake-cpp/scripts/qt_lint.py

python3 $LINT --selftest                                        # 24 checks → PASS
python3 $LINT src tests CMakeLists.txt                          # plain run
python3 $LINT src tests CMakeLists.txt --write-baseline /tmp/gs_baseline.json
python3 $LINT src tests CMakeLists.txt --baseline /tmp/gs_baseline.json
python3 $LINT src tests CMakeLists.txt --json --baseline /tmp/gs_baseline.json | jq .summary
```

## 2. Plain run — verbatim output (final lint version)

```
src/qtui/MainWindow.cpp:217: QL003 [warning] blocking wait on the GUI thread - keep only if bounded, measured and registered (then baseline it)
    process_->waitForFinished(2000);
src/qtui/MainWindow.cpp:1158: QL003 [warning] blocking wait on the GUI thread - keep only if bounded, measured and registered (then baseline it)
    if (!process_->waitForStarted(5000)) {
src/qtui/MainWindow.cpp:1234: QL003 [warning] blocking wait on the GUI thread - keep only if bounded, measured and registered (then baseline it)
    if (!process_->waitForStarted(5000)) {
src/qtui/MainWindow.cpp:1263: QL003 [warning] blocking wait on the GUI thread - keep only if bounded, measured and registered (then baseline it)
    process_->waitForFinished(3000);
src/qtui/MainWindow.cpp:1530: QL003 [warning] blocking wait on the GUI thread - keep only if bounded, measured and registered (then baseline it)
    previewProcess_->waitForFinished(1000);
src/qtui/PreviewPanel.cpp:42: QL006 [info] hard-coded hex colour in setStyleSheet() - breaks palette/dark mode
    frame->setStyleSheet(QStringLiteral("QFrame { background: #202020; }"));
src/qtui/PreviewPanel.cpp:53: QL006 [info] hard-coded hex colour in setStyleSheet() - breaks palette/dark mode
    label->setStyleSheet(QStringLiteral("background:#202020;color:#909090;"));
tests/test_gui_offscreen.cpp:443: QL002 [info] lambda connected without a context object - survives the receiver's death (test file: info only)
    QObject::connect(g_hb.timer, &QTimer::timeout, [] {
tests/test_gui_offscreen.cpp:1019: QL002 [info] lambda connected without a context object - survives the receiver's death (test file: info only)
    QObject::connect(&ticker, &QTimer::timeout, [&ticks]() { ++ticks; });
qt_lint: 9 finding(s) (info: 4, warning: 5); 9 not in baseline; 5 at or above --fail-on=warning -> exit 1
```

JSON summary with the baseline applied:
`{"total":9,"new":0,"baselined":9,"by_severity":{"info":4,"warning":5},"by_rule":{"QL002":2,"QL003":5,"QL006":2}}`

`CMakeLists.txt` alone: **no findings** — and that is a *true* negative, checked by hand:
`cmake_minimum_required(VERSION 3.16)`, `project(... VERSION ...)`, `qt_add_executable(gifscythe WIN32 ...)`,
`set_tests_properties(gui_offscreen PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen")` are all present.

## 3. Interpretation — every finding dispositioned

| # | Finding | Truth? | Disposition for the next session |
|---|---------|--------|----------------------------------|
| 1–5 | `QL003` MainWindow.cpp 217 / 1158 / 1234 / 1263 / 1530 | **True positive, already known.** These are exactly the five UI-thread waits of gifscythe **U-12**, which STATUS.md lists as DONE/dispositioned (bounded, measured in S37). | **Baseline them, do not re-fix.** The lint re-discovering U-12 independently — same five sites, no sixth — is the strongest evidence in this run that QL003 measures the right thing. |
| 6–7 | `QL006` PreviewPanel.cpp 42 / 53 (`#202020`, `#909090`) | **True positive, actionable.** Hard-coded dark colours inside a light-palette app; exactly what breaks when D-06 (dark mode) or any palette-driven redesign lands. | Input to the **UI-redesign route** (v4 §10 + `skills/qt6-cmake-cpp/references/ui-redesign.md`): replace with `palette()` roles. Info-level, so it never blocks CI. Note `SettingsPanel.cpp:51` uses `palette(mid)` correctly — the project already knows the right pattern. |
| 8–9 | `QL002` test_gui_offscreen.cpp 443 / 1019 (info, test file) | **Accurate but harmless.** Both receivers (`g_hb.timer`, stack `ticker`) outlive the test. | Baseline. Kept visible as info because a context-less lambda in a *product* file is a real UAF class (`skills/qt6-cmake-cpp/references/architecture.md`, connections section). |

**Verified-clean areas** (0 findings, consistent with the independent grep audit in the
session log): QL001 string-based `SIGNAL()/SLOT()` — 0 in 80 connects; QL005 `deleteLater`
in destructors; QL007 every product `QProcess` user connects `errorOccurred`; QL009 `#include
<QtWidgets>` umbrella; QL011–QL014 CMake hygiene.

## 4. Baseline round trip (the CI story)

```
--write-baseline   → wrote baseline with 8 key(s) for 9 finding(s)        exit 0
--baseline         → 9 finding(s); 0 not in baseline                       exit 0
inject `process_->waitForFinished(9000);` into MainWindow::MainWindow
--baseline         → 10 finding(s); 1 not in baseline (MainWindow.cpp:101) exit 1
```

The injection shifted every existing finding by two lines (217→219, …) and the baseline
**still matched** — keys are `rule|path|normalised line text`, not line numbers (the two
identical `waitForStarted(5000)` lines share one key, hence 8 keys for 9 findings). So the
owner can refactor around the U-12 sites without the baseline rotting, while any *new*
blocking wait fails the gate. Paths in keys are relative to the working directory, so the
lint is always run from `working_code/gifscythe`; from any other directory it fails loudly
(checked: 7 "not in baseline" from the repo root) rather than passing silently. Injection
reverted; `git status` clean. The baseline is committed as
`projects/gifscythe/qt_lint.baseline.json`.

## 5. What the dry run fixed in the skill (retrospective log, entries 1–4)

This is the first content of the "skill-defect log" the next session must continue.
Each item was found by running the lint on the real project, not by reading it.

| # | Defect in `qt_lint.py` | Symptom on gifscythe | Fix | Guarded by |
|---|------------------------|----------------------|-----|------------|
| 1 | `extract_calls` lookbehind `(?<![\w:>.])` rejected member-call forms | `label->setStyleSheet(...)` never matched → QL006 silent | lookbehind is now `(?<!\w)` (still keeps `disconnect(` from matching `connect(`) | selftest "QL006 fires on the bad C++ fixture" |
| 2 | QL008 flagged *every* `open(WriteOnly)` | would have flagged the correct `QSaveFile` at MainWindow.cpp:1801 | skip when `QSaveFile` appears on the line or ≤3 lines above | selftest "clean C++ fixture is silent" |
| 3 | No test-file policy | **27 noise findings** in `test_gui_offscreen.cpp` (processEvents/msleep/waitFor* on fixture engines, scratch `QFile` writes, QProcess without errorOccurred) | `is_test_file()`: QL003/004/007/008/015 off, QL002 downgraded to info | selftest "test harness: only QL002/info fires" |
| 4 | QL015 matched machine paths in comments and `Program Files` | `core/ProcessRunner.h:8` (comment: `C:\Users\John Smith\in.gif`), `test_gifsicle_command.cpp:1238/1241` (argv-splitter fixtures) | comments stripped (strings kept); `Program Files` removed from the pattern (standard location ≠ machine-specific) | selftest "QL015 ignores paths that appear only in comments" |

Net effect: **36 → 9 findings, 0 false positives remaining** on this project. Every fix
added a self-test that fails without it (the guard-can-fail rule from v4 §15).

## 6. Not verifiable here

- Templates (`CMakeLists.txt`, `CMakePresets.json`, `thread_guard.h`, `logging.h`,
  `offscreen_test_main.cpp`, `github-workflow-qt.yml`) were **not compiled or run** — the
  sandbox has no cmake/ninja/Qt6 and no package network. First compile happens in the
  next session on the owner's machine or in gifscythe CI.
- The lint's rules were calibrated against **one** project. Precision on a second Qt
  code base is unknown; `skills/qt6-cmake-cpp/references/ui-redesign.md` and `crash-diagnosis.md` claims
  are untested in anger.
- Whether the owner *agrees* with the dispositions above (especially baselining U-12
  rather than removing the waits) is an owner decision — see `NEXT_SESSION.md`.

## 7. Verdict for "right direction?"

Yes, on the evidence available: the workload skill's only executable component found
exactly the project's known, registered debt (U-12), one genuinely new and relevant
item for the planned UI work (QL006 ×2), and nothing false — after four fixes that the
dry run itself forced. That is the loop the owner asked for (apply → see what goes
wrong → improve), already running once before the next session starts.
