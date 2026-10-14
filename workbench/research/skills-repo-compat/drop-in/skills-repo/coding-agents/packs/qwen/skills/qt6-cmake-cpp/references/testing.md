# Testing Qt 6 desktop apps — headless, honest, and tied to the UI contract

## 1. The levels, and what each proves (v4 §6 applied to Qt)

| Level | Tool | Proves | Does not prove |
|---|---|---|---|
| Core unit | plain C++ test executable, no Qt | argv builder, validation, planner, verifiers | anything about widgets |
| Qt-core unit | `Qt6::Test` or house harness, `QCoreApplication` | settings I/O, models, process runner | rendering, focus, dialogs |
| Offscreen GUI | real `QApplication` + `QT_QPA_PLATFORM=offscreen` | widget wiring, state machine, honest statuses, run/cancel paths against fake engines | visible rendering, physical input, native dialogs, DPI |
| Real desktop probe | a person, a checklist, a date | the three or four behaviours offscreen cannot reach | other machines |
| Packaged smoke | fresh runner, downloaded artifact | the staged package launches and runs one job | a clean consumer machine |

Report at the level reached. "GUI tests green" means offscreen; say so.

## 2. Offscreen harness — house style

Framework or not is a per-project choice. Qt Test gives `QVERIFY/QCOMPARE`,
data-driven tests and `QSignalSpy`; a house-style harness (a `CHECK` macro
that counts, prints `FAIL file:line expr`, and exits non-zero) has no extra
dependency and lets the test read like a scenario script. The skeleton is
`templates/offscreen_test_main.cpp`. Either way:

- `QT_QPA_PLATFORM=offscreen` set by the CTest property **and** defaulted in
  `main()` with `qputenv` if unset, so a developer running the binary by hand
  gets the same behaviour.
- `QApplication::processEvents()` and `QTest::qWait()` only inside the
  harness's own wait helper, with a deadline, never an unbounded spin.
- Every block prints its ID and a one-line purpose; the summary line prints
  `N blocks, M checks, F failures` from counters **in this run**.
- A crash prints no FAIL line — the CI step must check the exit status and say
  "exited N (a crash prints no FAIL lines)".

## 3. The objectName contract

Widgets the harness touches are found by `findChild<T*>("name")`. Therefore:

- Every interactive widget gets a stable `setObjectName("…")` at construction.
- **Object names are a public test API.** A redesign may move, restyle, regroup
  or re-parent a widget freely, but renaming it breaks the harness; rename only
  together with the harness, in the same commit, and list the renames in the PR.
- The lint has no rule for this (it cannot know which names the harness uses);
  the review checklist does.

## 4. Modal dialogs

A `QMessageBox::exec()` blocks the harness. Use a *dialog killer*: a repeating
`QTimer` that scans `QApplication::topLevelWidgets()` for visible `QDialog`s,
records title + text, and closes/rejects them. The recorded list is itself an
assertion surface ("exactly one dialog, titled X, mentioning the colliding
path"). Better still, route all user-facing errors through one reporter
(`architecture.md` §5) so the harness can subscribe instead of chasing windows.

## 5. Fixtures

- Binary fixtures (images, sample inputs) as **text** (base64) with a checksum
  file, decoded on demand into an ignored build directory. Keeps the repo
  binary-free, survives an owner deleting "all images", and lets both shell and
  Node/Python tooling decode the same bytes. Pin line endings with
  `.gitattributes` (`*.b64 text eol=lf`) — a CRLF checkout breaks `base64 -d`.
- Fake engines as tiny C++ programs built by the same CMake (see
  `subprocess-engine.md` §10) and declared as `add_dependencies` of the harness.
- A real engine for E2E in CI, located through the same locator the app uses.

## 6. Red → green, and guards that can fail

- A fixed defect keeps a test that fails on the pre-fix code; keep the red run
  ID in the register.
- For a source sentinel (a grep that pins an invariant such as "the batch loop
  reads the snapshot, not the live settings"), prove it bites: apply the
  reverse patch, watch it fail, restore. Strip comments before grepping so a
  comment cannot satisfy the guard.
- Environment assertions **measure**: a "UI thread did not freeze" check times
  an event-loop heartbeat around the operation and asserts a bound, instead
  of asserting the premise that a wait is absent.

## 7. CI wiring (Linux + Windows)

Linux: `apt-get install -y qt6-base-dev` on `ubuntu-24.04`, build with CMake,
`ctest --output-on-failure`, then run the offscreen harness as its own step
with `tee` to a log and an explicit exit-status check. Windows: `aqtinstall`
(`aqt install-qt windows desktop <ver> win64_mingw` + `aqt install-tool … tools_mingw*`,
or `win64_msvc2022_64` with the VS toolchain already on the runner), then the
same steps. Pin runner labels deliberately; a `-latest` migration can change
the Qt or compiler you get. Record the compiler actually used in a
diagnostic-only step so a toolchain-chain fallback is visible in the log.

A 4-byte-`long` lane (zig/MinGW cross or `-m32`) for the core suite catches
the Windows integer-width class without a Windows runner. See
`templates/github-workflow-qt.yml`.

## 8. What the offscreen harness should cover for a converter-style app

defaults · live command pane sync · queue ops (add/drop/dedupe/remove/clear/
reorder) · N-in N-out batch · merge/explode modes · empty-output refusals ·
lying-engine refusal · failed engine → honest status + previous output intact ·
async start/busy indicators/cancel mid-run · close while running kills child ·
each control maps to the right flag · preview debounce/invalidation/temp
hygiene · output tab honesty · settings persistence round-trip + corrupt file →
defaults + warning · destination lock during run · batch planning refusals ·
cancel-latch honesty · non-ASCII engine path · mid-batch settings snapshot.

## 9. What offscreen cannot prove — write it down

Physical drag-and-drop from a file manager, native file dialogs, killing the
engine from outside, screen rendering/DPI, system theme. Keep a dated runsheet
for the owner with one command block per probe and record the observations as
`desktop:` evidence in the register.