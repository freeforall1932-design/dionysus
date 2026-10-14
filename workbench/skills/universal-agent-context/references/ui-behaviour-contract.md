# UI ↔ engine behaviour contract (layer 1 — any stack)

**Why this file exists.** Agents asked to "design the UI like app X" or "make the
GUI behave properly with the engine" tend to do one of two wrong things: draw
screens with no idea what the engine can actually do, or wire controls to the
engine with no idea what the user should see in each state. Both produce a UI
that lies (fake progress, "success" on partial output, buttons that do nothing
in half the states). This file is the method that prevents it. It expands v4 §10
(visual evidence) and §11.5 (engine boundary options) into **one contract that
must exist before any widget is drawn**, on any stack. Stack-specific files
(Qt, a sibling skill, path from this skill's root: `../qt6-cmake-cpp/references/ui-redesign.md` and
`subprocess-engine.md`) implement this; they do not replace it.

The evidence discipline and the "obligation ledger" idea come from
`morluto/rea` (MIT; the owner keeps a fork, `rea-fork`): every claim is an
*observation*, a *derivation*, an *inference*, or an *unknown* — never a vibe —
and a behaviour is "reproduced" only when a verifier of comparable authority
says so. REA the *tool* is not required for any of this; the method is.

---

## 0. The rule

> No UI change is designed, approved, or implemented until the four tables in
> §2–§5 exist for every screen it touches, and each row names its evidence.

A mockup without the tables is a picture. A picture is not a design.

## 1. Name the engine and its real interface first (30 minutes, not a day)

The "engine" is whatever does the work the UI presents: a CLI binary, a library,
a local service, a browser API, a remote API, a game process. Write down, with
evidence from the engine itself (its `--help`, headers, docs, or an executed run —
not from memory):

| Item | Record |
|---|---|
| Identity | name, version string, how the app locates it (bundled / PATH / configured path) |
| Inputs | every argument/option the UI will ever set; type, range, default, mutual exclusions |
| Outputs | files written (where, when, atomically or not), stdout/stderr shape, structured results |
| Progress signal | real (parsable per-item/percent) · coarse (per file) · **none** — if none, the UI must not show a percentage |
| Termination | exit codes and what each means; crash vs error vs cancelled; is a partial output possible on failure? |
| Cancellation | can it be interrupted safely? what is left on disk? can it resume? |
| Concurrency | may two instances run? shared files? |
| Timing | typical and worst-case durations on realistic input (measure one) |
| Failure families | the named reasons a run fails (not found, unsupported input, permission, disk full, timeout, engine bug) |

Label each cell **observed** (you ran it / read the source), **derived** (follows
from an observation), **inferred** (plausible, unverified), or **unknown**.
"Unknown" is an allowed answer and must stay visible; it is not allowed to turn
into "assumed fine" by the time code is written. Missing coverage is unknown,
not absence.

## 2. State table — what the whole app can be in

One row per state the user can perceive. Typical minimum: `empty`, `ready`,
`validating`, `running`, `paused` (if it exists), `cancelling`, `cancelled`,
`succeeded`, `partially-failed`, `failed`, `stale` (inputs changed after a
result), `engine-missing`, `busy-elsewhere` (another run / another instance).

| State | Entered by (engine event or user action) | Exits to | What the user sees (every region of the screen) | What is enabled / disabled | Evidence |
|---|---|---|---|---|---|

Rules:
- Every control on the screen appears in the "enabled/disabled" column of **every**
  state. A control with no entry in some state is a bug waiting to happen.
- "Running" must say what progress signal it shows and where that number comes
  from (§1). A spinner is honest; an invented percentage is not.
- `partially-failed` is a separate state from `failed` whenever the engine
  processes more than one item. Per-item results need their own table (§4).
- `stale` exists whenever a result is shown next to inputs the user can still
  edit. Say how staleness is detected (input digest, mtime, settings hash) and
  what the UI does about it (grey out, badge, auto re-run with debounce).

## 3. Control → engine mapping

One row per interactive control. This is where "UI logic tied to the engine"
becomes a checkable artefact instead of a feeling.

| Control (objectName / id) | Engine input it sets | Transform (unit, scale, rounding, enum map) | Shown to the user as | Validation and error text | Default | Evidence |
|---|---|---|---|---|---|---|

Rules:
- If a control does not map to an engine input or a documented app setting, it
  has no business on the screen (or it is a *presentation* control — filter,
  sort, zoom — and must be labelled as one).
- Plain-language labels are allowed and encouraged, but the **real engine
  argument is shown or available** next to them (the owner's standing rule in
  the proving-ground project: never hide what will actually be passed).
- A "preset" is a named set of rows from this table — list the rows it sets.
  A preset that sets something not in the table is a lie.
- A disabled-until-later control (planned format, unimplemented feature) is
  marked `PLANNED` here and in the UI; it does not pretend to work.

## 4. Engine event → UI reaction mapping

One row per thing the engine can do while running. This is the other half of
the wiring, and the half agents most often skip.

| Engine event | Detected how (exit code, stderr pattern, file appears, API callback, timeout) | State transition (§2) | UI reaction (log line, row update, dialog, badge) | Must never do | Evidence |
|---|---|---|---|---|---|

Rules:
- `started`, `progress`, `item-done`, `item-failed`, `finished-ok`,
  `finished-with-errors`, `crashed`, `timed-out`, `cancelled`, `failed-to-start`
  (engine missing / not executable) are the minimum rows. If the engine cannot
  signal one of them, the row says **"not detectable — UI shows X instead"**.
- Output is reported as produced only after it is **verified** (file exists, is
  non-empty, has the expected signature/size, is not the stale previous output)
  — verification happens after the terminal event, never before.
- "Must never do" is mandatory: e.g. *never overwrite the input*, *never show
  success when exit code ≠ 0*, *never leave a half-written output under the
  final name*, *never block the UI thread waiting for the engine* (or: only
  with a bound, a measurement, and a registered exception).

## 5. Per-item results (when the engine handles more than one input)

| Column | Source | Shown when | Formatting rule |
|---|---|---|---|

Minimum: item identity, before/after measure (bytes, duration, count — whatever
is true), delta, status (one of a fixed set, including `skipped` = never
attempted, distinct from `failed`), named failure reason, link to the log
lines. Totals are computed from rows, never kept separately. The honest scope
of Cancel is written here: which rows become `cancelled`, which stay `done`.

## 6. Obligations from a reference app ("behave like X")

When the request is "like XnConvert / like app X", the reference is evidence of
**features and behaviours**, not a design to copy (v4 §10.5; no assets, no
branding, licence-checked). Turn it into obligations:

| Obligation id | Observed behaviour in X (observation, with how it was observed) | Our equivalent (state / control / event rows it maps to) | Required cases (positive · negative · malformed · cancellation) | Verifier (test / harness / manual runsheet) and its authority | Status |
|---|---|---|---|---|---|

Rules (from REA's obligation ledger, kept deliberately strict):
- An obligation closes only when its verifier **ran** and its authority is
  comparable to the observation: a unit test cannot close "the packaged app
  opens the result on double-click"; a screenshot cannot close "cancel leaves
  no partial file".
- `blocked` and `out-of-scope` are honest statuses; they are never counted as
  done.
- Observed-in-X ≠ required: the owner picks which obligations are in scope. The
  table makes that a decision instead of an accident.
- Separate *observed behaviour* from *our design choices* in the handoff —
  the reader must be able to tell which is which.

## 7. From contract to screens

Only now: visual inventory and 2–3 **structurally different** mockups (v4
§10.6) — each one annotated with which rows of §2–§5 it renders where, and
which rows it leaves out (that is a defect, not a simplification). Pick with
the owner (a breakpoint). Then the harness/test contract: which existing
tests change, which new rows need tests, before the first widget edit.

## 8. Acceptance — the questions a reviewer asks

1. Can I point at any control and find its row in §3? Any engine outcome and
   its row in §4? Any state the user can perceive and its row in §2?
2. Is every number on the screen traceable to a real engine signal?
3. Does the UI tell the truth in `partially-failed`, `stale`, `cancelled`,
   `engine-missing`?
4. Which obligations from §6 are closed by an executed verifier today, and which
   are open — and does the session log say so in those words?
5. What is *unknown* about the engine, and is it still visible as unknown?

## 9. Minimal example (eight lines, any stack)

```
Engine: gif optimiser CLI, exit 0 ok / 1 usage / 2 io; no progress signal; writes <out> non-atomically.
State  running:  entered by started; shows spinner + per-file rows "queued/working/done/failed"; Cancel enabled, Run disabled.
Control  "Extra compression %" (slider 0-100) -> --lossy=<n> via n = round(pct*2); argument shown under slider.
Event  finished-with-errors: exit 0 but a row's output missing -> state partially-failed; row=failed "no output written"; never report size delta for that row.
Item   columns: file, before B, after B, delta %, status{queued,working,done,failed,skipped,cancelled}, reason.
Obligation  X-03 "cancel keeps already-finished outputs" (observed in X by cancelling at item 3 of 5) -> verifier: harness T-cancel-mid-queue (offscreen) — status: open.
Mockup  B renders §2 all states; omits `stale` -> defect, fixed before review.
Unknown  engine behaviour on read-only output dir: not tested yet -> row in §1, UI treats as failure family "permission" (inferred).
```

If a session cannot produce these eight lines for its screen, it is not ready
to draw that screen.
