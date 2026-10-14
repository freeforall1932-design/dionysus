# gifscythe — next session runbook (retrospective + first real application of the skills)

Written 2026-10-13 against gifscythe `main` @ `97b0758` (S40). **This block holds
no state.** Everything below that describes gifscythe is a pointer with a date;
the project's own `STATUS.md` wins the moment it disagrees.

Purpose of the next session, in the owner's words: *improvement or debugging of
what went wrong after applying the skills to gifscythe* — with the UI redesign
route (Qt 6 / CMake / C++) as the primary candidate and the audit's open rows as
the alternates. The order below is deliberate: **retrospective first, one real
task second, skill fixes third, promotion to universal last** (session-protocol
"Retrospective").

---

## 0. Load order (5 minutes)

1. `skills/universal-agent-context/SKILL.md` → v4 → `skills/universal-agent-context/references/session-protocol.md`.
2. Inspect gifscythe's real build entry point (`working_code/gifscythe/CMakeLists.txt`,
   `find_package(Qt6 …)`, `qt_add_executable`) → `skills/qt6-cmake-cpp/SKILL.md` applies.
3. Open the overlay **in gifscythe**: `STATUS.md` (single register), `SESSION_HANDOFF.md`
   (S40 top), `WORKLIST.md`, `docs/planning/OWNER_DECISIONS.md`, `docs/planning/PLANNING.md` §3–§5.
4. Read `projects/gifscythe/SKILL_DRY_RUN_2026-10-13.md` — the lint evidence and the first
   four skill-defect entries.

## 1. RECOVERY — gifscythe's own commands, in its order (from its repo root)

```
working_code/gifscythe/scripts/bootstrap_hooks.sh     # only if check_docs G15 says core.hooksPath != .githooks
working_code/gifscythe/scripts/check_docs.sh          # must be 0 failed; G18 FAIL = commit NOW
working_code/gifscythe/scripts/sweep_stale.sh         # must be 0 failed
./working_code/gifscythe/build.sh --gui               # or: cmake -S working_code/gifscythe -B build -DBUILD_GUI=ON && cmake --build build
QT_QPA_PLATFORM=offscreen ctest --test-dir build --output-on-failure
```

Then the skill's own gate, run from **this** repo's checkout, never installed into gifscythe
(OD-15 is open — see §4):

```
python3 <dionysus>/workbench/skills/validate_skills.py
cd working_code/gifscythe        # baseline keys are cwd-relative - always lint from here
python3 <dionysus>/workbench/skills/qt6-cmake-cpp/scripts/qt_lint.py src tests CMakeLists.txt \
    --baseline <dionysus>/workbench/projects/gifscythe/qt_lint.baseline.json
```

Expected on `97b0758`: 9 findings (5× QL003 = U-12 sites, 2× QL006 PreviewPanel, 2× QL002-info
in tests), exit 1 without a baseline, exit 0 with the baseline from the dry run. **If the
numbers differ, the tree moved or the lint is wrong — find out which before anything else**
(v4 §13.3: "verified previously on revision X" is not "verified now").

## 2. STATE — read it there, do not trust it here

Pointers dated 2026-10-13 (`97b0758`): v0.1.0; STATUS 179 DONE / 7 PARTIAL / 14 OPEN; last
session S40 added `UNIVERSAL_AGENT_CONTEXT_v4.md`. The rows this session can touch:

| Row | Where it stands (dated) | Which skill section applies |
|---|---|---|
| **UI redesign** (owner ask 2026-10-08, specified 2026-10-09) | Four-tab XnConvert shape Input → Actions → Output → **Status**; a walkable draft exists *outside* the repo; **standing rule: no GUI edit before the owner confirms `OD-21`**; W-29 (1.0.0) waits on the UI/UX gates | v4 §10 (visual evidence, 2–3 distinct mockups, all states) + `skills/qt6-cmake-cpp/references/ui-redesign.md` (state inventory, objectName contract, palette roles) + `skills/qt6-cmake-cpp/references/testing.md` (harness T1–T24 must stay green) |
| **W-32** Status tab / per-file results | OPEN, not started; contract + 14 test cases proposed in `docs/planning/W32_RESULT_CONTRACT.md` (unconfirmed) | `ui-redesign.md` results-table section; `subprocess-engine.md` (exit codes → named failure reasons) |
| **GS-203 / P1-25** core `OutputVerify.h` into the Qt run lifecycle | PARTIAL; single/queue/Merge paths; test no-write, stale-valid, text-as-PNG, short, cancel | `subprocess-engine.md` (capture before launch, verify only after exit 0, atomic promotion) |
| **U-12** five UI-thread waits | DONE by measurement (S37, T26 guard); OD-19 declined the rewrite | QL003 → **baseline, do not re-open** (owner decision already taken) |
| **F-02** data loss on Cancel; **GS-210** CMake-first dispatch / `.pro` drift; **GS-204** clean-machine smoke | OPEN / PARTIAL | `subprocess-engine.md` cancel section; `cmake.md`; `packaging.md` clean-machine smoke |
| **D-06** dark mode | OPEN, optional, "after 1.0.0" | QL006 findings are its evidence; **owner approval only** |
| **OD-21**, **OD-22**, **OD-15** | open owner decisions | breakpoints — §4 |

## 3. THE SESSION, in phases (each phase ends with a gate and a commit)

### Phase A — Retrospective (do this before writing any product code)

A1. Re-run every proof the dry run claimed (§1 commands). Record actual vs expected.
A2. Continue `projects/gifscythe/SKILL_DEFECT_LOG.md` **in this repo** (the skills' journal;
    gifscythe's `IMPROVEMENT_LOG.md` stays the project's journal — never merge the two).
    It is seeded with entries 1–4 from the dry run §5. Row format:
    `# · rule/section · what happened · evidence (command + output) · fix · promote to universal? (y/n, why)`.
A3. Read `skills/qt6-cmake-cpp/references/*.md` **against** gifscythe's code with one question
    per file: *where is this wrong, silent, or too noisy for this project?* Log each as a
    defect — including "the skill says X and gifscythe already does X better" (that is a
    promotion candidate, not a bug).
A4. Gate: `python3 skills/validate_skills.py` (run from `workbench/`) green → commit in this repo.

### Phase B — One real task (owner picks; recommended order)

**B1 — Adopt the lint without violating OD-15 (≈30 min, lowest risk).**
The baseline from the dry run is already committed **here** as
`projects/gifscythe/qt_lint.baseline.json` (9 keys, `97b0758`). Re-generate with
`--write-baseline`, diff against it, and keep it here until OD-15 says how external
tooling may enter gifscythe. Nothing is installed in gifscythe; its CI is untouched. Evidence =
the three exit codes (plain 1 / baseline 0 / injected wait 1).

**B2 — UI redesign, planning half (no GUI edit; allowed before OD-21).**
0. Fill the four tables of
   `skills/universal-agent-context/references/ui-behaviour-contract.md` for the
   current app first: engine = gifsicle via `QProcess` (exit codes, no progress
   signal, outputs, cancel semantics — read them from `core/` and the engine, not
   from memory); states; control→argument (the Actions/Output controls, with the
   engine argument that must stay visible — OD-21 (b)); engine-event→UI. gifscythe's
   `docs/planning/W32_RESULT_CONTRACT.md` already *is* §5 of that contract (per-item
   rows, six states, named reasons, honest Cancel) — reference it, do not rewrite it.
   The XnConvert/ScreenToGif behaviours from the 2026-10-09 draft become §6
   obligations with verifiers (harness `T*` cases), each `open` until a test runs.
1. State inventory of the current Qt surface (`src/qtui/MainWindow.cpp`, `PreviewPanel.cpp`,
   `SettingsPanel.cpp`): every widget with an objectName (103), every state (idle /
   running / cancelled / failed / done / preview-stale), every signal the harness
   T1–T24 relies on. Output: a table in gifscythe `docs/planning/` (text only — OD-22 (a)).
2. **Three distinct mockups** (v4 §10 — the 2026-10-09 draft counts as one). Each must
   show all states, name which objectNames survive, and which harness tests change.
   Distinct = different layout decisions (dock vs tabs for preview; Status as tab vs
   bottom pane; chain cards vs form), not three colour schemes.
3. Harness-contract diff per mockup: which `T*` cases break, which new ones W-32's 14
   cases add. The mockup whose contract diff is smallest *and* satisfies the four-tab
   requirement is the recommendation.
4. **Breakpoint:** owner picks a mockup and answers OD-21. Stop here if no answer.

**B3 — UI redesign, implementation half (only after the breakpoint).**
Rules from `ui-redesign.md`: keep every objectName the harness names unless its test is
rewritten in the same commit; palette roles, no hex (clears QL006 ×2); one commit per
tab; `QT_QPA_PLATFORM=offscreen ctest` green after each; screenshot evidence from the
offscreen harness (`QWidget::grab()`), committed under gifscythe's own evidence path, not
here. W-32 is implemented as the result **model** first (`W32_RESULT_CONTRACT.md`,
14 cases red → green) and rendered second.

**B4 — Alternate if the owner would rather not touch the UI yet: GS-203 / P1-25.**
`subprocess-engine.md` lifecycle: snapshot expected outputs before `start()`, run the core
verifier only after `exitCode()==0 && exitStatus()==NormalExit`, surface named failures;
five tests from PLANNING §4. No UI change needed beyond the existing log pane.

### Phase C — Skill fixes and promotion

C1. For each defect in `SKILL_DEFECT_LOG.md` with a fix: change the skill, add a self-test
    or fixture that fails without the fix, re-run `validate_skills.py` and `qt_lint.py --selftest`.
C2. Promotion: anything that held **without project details attached** goes into a
    proposal list for a v4 → v5 bump (v4 §17.6) — proposal only; the universal file is not
    edited in place (its hash is pinned in `PROVENANCE.md`).
C3. Make gifscythe's own copy of `UNIVERSAL_AGENT_CONTEXT_v4.md` a **pinned pointer**: keep
    the file (its gates read it) and add a top note naming this repo, the commit, and the
    sha256 `51f21f331b0b708ed65824253e15ca73259e8fcc80dbf1d0439c60c207eda0d5`. That is a
    gifscythe change → its own PR, its own `check_docs.sh` run.

### Phase D — Close

Session log entry in gifscythe `IMPROVEMENT_LOG.md` (v4 §19 fields, `Not verifiable here`
mandatory), `STATUS.md` rows updated through `check_docs.sh --emit` (never by hand),
`SESSION_HANDOFF.md` top updated, every edit committed, CI run ID quoted. In this repo:
defect log committed, `validate_skills.py` green, CI run ID quoted.

## 4. DECISIONS NEEDED (breakpoints — do not guess past them)

| ID | Question | Recommendation (reasoned, reversible) |
|---|---|---|
| **OD-15** | How external tooling (this repo's skills/lint) may enter gifscythe | PLANNING §3 recommends (a) pinned submodule, quarantined, inert. Until answered: run the lint from outside, baseline kept here (B1). |
| **OD-21** | Preset wording / Output-tab mapping — gates *any* GUI edit | Already recommended (a)+(b) in gifscythe; this session cannot proceed past B2 step 4 without it. |
| **OD-22** | XnView/XnConvert material in the repo | Already recommended (a) text-only; mockups in B2 are text + the app's own screenshots, nothing copied. |
| **U-12 disposition under the lint** | Baseline the five QL003 sites, or re-open the rewrite? | **Baseline.** OD-19 closed U-12 on measurement with T26 as guard; re-opening would be the "unverified refactor" the owner declined. |
| **D-06 in scope of the redesign?** | Palette roles make dark mode nearly free | Fix QL006 (palette roles) as part of B3 because it is a correctness fix for the light theme too; **do not** ship a dark theme without an explicit yes. |
| **Mockup choice** | Which of the three | Decided in B2 step 4, by the owner, against the harness-contract diff. |

## 5. STANDING CONSTRAINTS (gifscythe's rules; they apply to the agent, not the owner)

- Commit every edit before merge/close; never merge without an explicit yes.
- Never ask the owner for tokens or credentials.
- CI workflow edits in gifscythe go as a byte copy to `docs/ci/build.yml.proposed`; extend
  `build.yml`/`check_docs.sh`, never add a parallel pipeline (v4 §3).
- CMake must never write to the source tree (U-15); MinGW static runtime; `-DBUILD_GUI=ON`.
- W-18 / W-19 Windows probes are owner-only; do not claim Windows results from Linux.
- No GUI edit before OD-21; no reference folder under `docs/` before OD-22.
- Every claim in the session log carries executed evidence; "Not verifiable here" is
  mandatory, not optional.
- The skills repo never receives gifscythe state; gifscythe never receives skill prose
  except by pointer (OD-15 permitting).

## 6. What this block does not know

Whether gifscythe moved past `97b0758`; whether the owner answered OD-15/OD-21/OD-22
between sessions; whether the templates in `skills/qt6-cmake-cpp/templates/` compile
(never built — no cmake/Qt in the authoring sandbox); the lint's precision on any Qt
code base other than this one. Each of these is the first thing to check, not assume.
