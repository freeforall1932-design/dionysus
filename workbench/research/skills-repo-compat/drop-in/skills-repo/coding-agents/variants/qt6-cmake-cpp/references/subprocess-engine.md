# GUI over a command-line engine (QProcess) — the contract that keeps data safe

This is the architecture of a converter/optimizer/encoder desktop app: a first-
party Qt shell drives a third-party executable over argv. Generalized from a
long audit history on exactly such a project (the project's own register holds
the IDs and evidence; this file keeps only the rules). Each rule names the
failure it prevents.

## 1. Boundary and licensing

The engine stays a **separate process** invoked over argv. Do not link it, do
not vendor its source into the UI's translation units, do not expose its
internals over a socket "for speed" without a separate decision. A GPL engine
behind a process boundary keeps a differently-licensed UI possible; its license
text and notices still ship **beside** the binary in every package.

## 2. Building the command

- argv is a **list of strings**, never a shell string. Quoting bugs vanish; a
  file named `foo;rm -rf.gif` is just a file.
- One builder produces the list for every surface (GUI, CLI, web). Test it
  token by token against the engine's documented flags; keep the engine's
  man-page citation beside each flag that has a non-obvious meaning (e.g. a
  loop count of 0 meaning "forever").
- Empty or default-valued controls emit **nothing** — not an empty operand that
  the engine will read as the next file name.
- "Threads = auto" means the bare flag or the engine's own default, not `-j1`.
- Show the user the command you are about to run (one-way, read-only pane).
  It is the cheapest debugging tool and the honest answer to "what did it do?".

## 3. Locating the engine

Order: explicit override (env var or setting) → next to the application binary
(portable layout) → `PATH`. The `PATH` fallback must actually be implemented,
not just documented. Report which one won in the log and in an "about"/status
area. Non-ASCII install directories must work on Windows (UTF-16 APIs — see
`platform-notes.md`).

## 4. Running it

```cpp
process_ = new QProcess(this);
process_->setObjectName("engineProcess");
process_->setProgram(enginePath);
process_->setArguments(argv);                 // list, not string
process_->setProcessChannelMode(QProcess::SeparateChannels);
connect(process_, &QProcess::readyReadStandardError, this, &Runner::drainStderr);
connect(process_, &QProcess::readyReadStandardOutput, this, &Runner::drainStdout);
connect(process_, qOverload<int, QProcess::ExitStatus>(&QProcess::finished), this, &Runner::onFinished);
connect(process_, &QProcess::errorOccurred, this, &Runner::onError);   // FailedToStart, Crashed, Timedout…
process_->start();
```

- Connect **both** `finished` and `errorOccurred`. `FailedToStart` never emits
  `finished`.
- **Drain continuously.** A child that fills a pipe blocks; a parent that reads
  to EOF before waiting blocks forever on a stalled child and its own timeout
  path is never reached. Bounded buffers; never `readAllStandardError()` only
  at the end.
- Hide the console window of the child on Windows
  (`CREATE_NO_WINDOW` through `setCreateProcessArgumentsModifier`); the GUI
  itself is a `WIN32` subsystem app.
- A watchdog `QTimer` with a configurable deadline: on expiry, `terminate()`,
  then after a grace `kill()`, then wait a bounded time to reap, then report
  "timed out" — never "failed" and never "complete".

## 5. Exit codes and crash detection

- Exit status is a pair: `ExitStatus` (normal/crash) **and** the code. A crash
  is a failure regardless of the code value.
- On Windows a crashed child's "exit code" is an NTSTATUS such as
  `0xC0000005`; masking with `& 0xff` yields 5 — or 0 for some values — and
  turns a crash into a success. Compare the full 32-bit value and treat the
  `0xC0000000` range as a crash class.
- The CLI surface of your own app needs **one documented exit-code contract**
  (e.g. 0 ok · 1 engine failed · 2 usage/validation · 3 engine missing), shared
  by every port of the app; a second implementation must map onto it by test.
- Unknown arguments or malformed values must not exit 0.

## 6. Output safety — the data-loss rules

1. **Never truncate the user's existing output before the engine has
   succeeded.** Write to a sibling temp path (`out.gif.tmp-XXXX`), then promote
   with an atomic rename **only after** exit 0 *and* verification.
2. **Verify, then claim.** A successful run produces a file that: exists, is a
   regular file, is non-empty, carries the right magic bytes, and is *new or
   changed* relative to a snapshot taken before launch (size + mtime; still
   conservative within timestamp granularity — say so). An engine that exits 0
   and writes nothing is a failure.
3. **Explode/multi-output modes** verify by **directory diff** against a
   pre-launch snapshot (names + sizes), not by "exit 0".
4. **Cancel keeps the previous good output.** Cancel = kill, reap, delete the
   temp file, leave the original untouched, report "Cancelled". **The message
   describes the WRITE STRATEGY, not the mode name:** a mode that writes in
   place and already produced partial frames says so explicitly; a mode guarded
   by staging + promote (rule 1) writes nothing visible on cancel and reports a
   plain "Cancelled".
5. **Plan batch targets before starting**: detect two inputs mapping to one
   output, an output equal to an input, and a constant name template over N
   files — refuse up front with a dialog that names the collision.
6. **Settings snapshot per batch.** A control changed between item 1 and item 2
   must not change item 2's argv. Copy the settings at batch start.
7. **Destination lock during a run.** Browse buttons and path fields that
   decide where files go are disabled while running; the planned targets are
   captured at start.

## 7. State machine for the window

The states, transitions and per-control enablement below are the Qt rendering of
the stack-agnostic state table in
`../universal-agent-context/references/ui-behaviour-contract.md` §2–§4 (sibling
skill; path from this skill's root);
fill that contract first, then map it onto the `QStateMachine`/enum below.

States: `Idle → Starting → Running → (Succeeded | Failed | Cancelled | TimedOut) → Idle`.
Transitions only from signals. Rules that follow:

- A "cancel latch" set by the Cancel button is consumed by **that run's**
  completion only; a later genuine failure must still surface its dialog.
- Re-entrancy: Start is disabled from `Starting` until `Idle`; a preview
  process is killed before a main run starts and never restarted during one.
- Status text is derived from the state, not set ad hoc from five places.
- Progress is honest: per-item counts for batches; indeterminate when the
  engine gives no progress; never a fake percentage.

## 8. Preview pipelines

A debounced (~1 s) re-encode of the selected item into a temp directory, in a
**separate** process from the main run. Invalidate the in-flight preview when
the queue, the selection, or the mode changes; sweep superseded temp files;
large inputs opt out by default; captions say "preview (settings as of …)",
never "after".

## 9. Settings persistence

Atomic writes (`QSaveFile` or temp+fsync+rename); one parser shared with the
CLI so a GUI-saved file is CLI-readable; unknown keys preserved through a
side channel rather than dropped; load warnings surface in the status bar;
nothing per-run (queue, one-off output path) is persisted, because restoring a
stale output path can silently overwrite a file next session.

## 10. Tests that pin the contract (fixtures, not mocks)

Build tiny C++ "fake engines" and launch them for real:

| Fixture | Pins |
|---|---|
| exits 0, writes nothing | verification refuses the lie |
| writes garbage to `-o` then exits 1 | previous good output survives; partial removed |
| sleeps, logs argv to a file | batch settings snapshot; cancel against a live process |
| spawns a child that holds the pipes open after the parent dies | drain/kill/reap ordering; measures UI-thread freeze |
| crashes (`abort()`) | crash classification; NTSTATUS handling on Windows |

Run them under the offscreen harness (`testing.md`) and on both OS lanes; a
Linux pass proves nothing about the NTSTATUS path.

## 11. What the register should contain for this architecture

A "verified-correct guardrails" table (v4 §13.4) for every engine semantic that
*looks* like a bug but is correct (loop-count sentinels, "0 means to the edge",
bare flags), each with the man-page/source citation and a regression test, so
no later session "fixes" it.
