# Skill defect log — gifscythe as the proving ground

The skills' own journal (session-protocol "Retrospective"). gifscythe's
`IMPROVEMENT_LOG.md` is the *project's* journal; the two are never merged.
One row per place a skill was **wrong, silent, or too noisy** against real code —
plus rows where the project already did better than the skill (those are
promotion candidates, not bugs).

Columns: `#` · `rule / section` · `what happened` · `evidence (command + output)` ·
`fix (commit)` · `promote to universal? (y/n, why)`. Status: `fixed` / `open` /
`wontfix (reason)`.

## Session 2026-10-13 (authoring session; dry run on gifscythe `97b0758`)

| # | rule / section | what happened | evidence | fix | promote? | status |
|---|---|---|---|---|---|---|
| 1 | `qt_lint.py` QL006 (and every `extract_calls` user) | Member-call forms never matched: lookbehind `(?<![\w:>.])` rejected `obj->setStyleSheet(` and `obj.connect(`. QL006 was silent on `PreviewPanel.cpp` l.42/53. | `--selftest`: `FAIL QL006 fires on the bad C++ fixture` (first run) | lookbehind → `(?<!\w)`; selftest case kept | n | fixed |
| 2 | QL008 | Fired on every `open(…WriteOnly)` including the correct `QSaveFile` pattern (gifscythe `MainWindow.cpp` l.1801 does it right). | `--selftest`: `FAIL clean C++ fixture is silent: [('QL008', 14)]` | skip when `QSaveFile` is on the line or ≤3 lines above | n | fixed |
| 3 | QL003/004/007/008/015 in test files | 27 noise findings in `tests/test_gui_offscreen.cpp`: a harness legitimately pumps events, sleeps, waits on fixture engines, writes scratch files. | first real run: `36 finding(s) (warning: 28, info: 8)` | `is_test_file()` policy: those rules off in tests, QL002 downgraded to info; selftest "test harness: only QL002/info fires" | **y** — "a harness may do what product code may not; lint policies need a test-file lane" is stack-agnostic (v4 §15 territory) | fixed |
| 4 | QL015 | Matched machine paths in *comments* (`core/ProcessRunner.h:8`) and `C:\Program Files\…` fixtures in an argv-splitter test. | first real run, 3 false positives | comments stripped (strings kept); `Program Files` removed from the pattern; tests exempt | n | fixed |
| 5 | baseline keys / `iter_files` | Key paths were relative to the *argument* directory (`qtui/MainWindow.cpp` for arg `src`), so the same baseline silently failed to match when the lint was invoked with a different argument spelling. | run from repo root with `working_code/gifscythe/src`: `7 not in baseline` against a baseline that should have matched | keys are now cwd-relative with forward slashes; doc says "always run from `working_code/gifscythe`"; a wrong cwd fails loudly, never passes silently; duplicate keys deduplicated (8 keys / 9 findings) | n | fixed |
| 6 | templates vs own lint | Dogfooding: `offscreen_test_main.cpp:66` QL004 and `thread_guard.h:61` QL005 fired on the skill's own templates (the harness template is not under `tests/`, so the test-file lane did not apply). | `qt_lint.py skills/qt6-cmake-cpp/templates` → `2 finding(s)`, exit 1 | inline `// ql-allow QLnnn: <reason>` in both templates — which also documents the suppression syntax at the point of use; CI step "qt_lint on its own templates" added | **y** — "a tool's own templates must pass the tool" belongs with v4 §13.2 (gates measure the artefact, not the sentence) | fixed |
| 7 | `skills/qt6-cmake-cpp/references/ui-redesign.md` §mockups vs gifscythe 2026-10-09 draft | The skill demands 2–3 *distinct* mockups; gifscythe already has one walkable draft that cost a session and was pushed back on once. Not a defect yet — flagged so the next session does not redo work: the draft counts as mockup 1. | `SESSION_HANDOFF.md` 2026-10-09 entry | none yet; `NEXT_SESSION.md` B2 says "the draft counts as one" | — | open |
| 8 | templates (all six) | Never compiled or run: no cmake/ninja/Qt6 in the authoring sandbox. Any of them may contain an error a compiler would catch in seconds. | header note in each file; `Not verifiable here` in the dry run | first compile in the next session (owner machine or gifscythe CI) | — | open |
| 9 | QL003 vs owner decision OD-19 | The lint's *warning* severity for the five U-12 waits contradicts a closed owner decision ("measured, T26 guards it"). Correct for a new project; for gifscythe the baseline is the right tool, but the message text ("acceptable only if bounded, measured and registered") should tell the reader that a baseline entry is the *expected* end state for a dispositioned wait. | dry run §3 rows 1–5 | message now ends "(then baseline it)"; baseline committed | n | fixed |

| 10 | `templates/github-workflow-qt.yml` + `.github/workflows/skills-gate.yml` | First CI run (ID 38464024793, green) carried the annotation "Node.js 20 is deprecated … actions/checkout@v4" — the template's own header says to check an action's declared runtime, and the author did not. | `gh run view 38464024793` → ANNOTATIONS | `checkout@v5`, `upload-artifact@v5`, `download-artifact@v6` (Node 24 majors); re-run quoted in the session summary | **y** — "an action tag is a runtime pin; read the runtime, not the tag" is harness-agnostic CI hygiene (v4 §3) | fixed |

## How to add a row

Run the thing, paste the command and the line of output that shows the defect,
then fix it with a self-test or fixture that fails without the fix. A row with no
evidence column is an opinion; move it to `NEXT_SESSION.md` §4 as a question.
