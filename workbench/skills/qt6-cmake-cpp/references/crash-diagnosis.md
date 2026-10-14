# Crash and hang diagnosis — Linux and Windows

Goal: when it crashes or freezes, a reader with the log and the crash record
can say what was alive, who owned it, which thread touched it, and what the
last state transitions were — without a debugger session. The ideas are
standard Qt practice; the drop-in pieces are in `templates/` (written fresh;
no third-party file copied).

## 1. First response — pick the fastest reproducer

| Symptom | Fastest tool |
|---|---|
| Deterministic crash | ASan build (`-DENABLE_ASAN=ON`), run, read the first report |
| Crash only in release / rare | core dump (Linux) or minidump (Windows) + symbols |
| Freeze | attach `gdb -p`/`lldb -p`, `thread apply all bt`; on Windows a dump from Task Manager → WinDbg `!analyze -v`, `~*k` |
| "Slot runs on a deleted object" | ASan + `QT_FATAL_WARNINGS=1`, QPointer audit (§4) |
| Cross-thread widget access | `ASSERT_THREAD`, `QT_FATAL_WARNINGS=1` turns Qt's own warnings into aborts |
| Shutdown crash | log the `aboutToQuit` sequence; stop timers first; look for `deleteLater` after the loop stopped |

## 2. Linux

- **Sanitizers:** ASan + UBSan preset in CI; locally `ASAN_OPTIONS=detect_leaks=0`
  for Qt (its global statics produce leak noise) and
  `UBSAN_OPTIONS=print_stacktrace=1`. TSan is a separate build (incompatible
  with ASan) and finds the "connected before moveToThread" class.
- **Core dumps:** `coredumpctl list` / `coredumpctl gdb <pid>` on systemd
  systems; otherwise `ulimit -c unlimited` and check
  `/proc/sys/kernel/core_pattern`. Build with `-g` even in Release
  (`RelWithDebInfo`) so the dump symbolizes.
- **Backtrace in-process:** `backtrace()`/`backtrace_symbols_fd()` from
  `<execinfo.h>` inside a `SIGSEGV/SIGABRT` handler is async-signal-unsafe in
  theory and useful in practice; write only to an already-open fd, then
  re-raise. Prefer core dumps for anything serious.
- **Qt's own diagnostics:** `QT_LOGGING_RULES="*.debug=true"`,
  `QT_DEBUG_PLUGINS=1` for "could not load the Qt platform plugin",
  `QT_QPA_PLATFORM=xcb` vs `wayland` to isolate a platform-plugin crash.

## 3. Windows

- **MSVC:** `/Zi` + `/DEBUG` so a PDB exists for Release; keep the PDB with the
  build artifact. ASan is available on MSVC (`/fsanitize=address`, disable
  incremental linking).
- **MinGW:** `-g` and keep the unstripped binary; `gdb` from the same toolchain
  reads it. No ASan on MinGW-w64 in practice — use the Linux ASan lane for
  memory errors and Windows for platform behaviour.
- **Minidumps:** `MiniDumpWriteDump` from `dbghelp` in an unhandled-exception
  filter (and a vectored handler as a backstop, because the CRT may replace the
  filter). Full-memory dumps are large but conclusive; write a **companion
  text file** next to the `.dmp` with the object census, connection summary and
  log tail (§5) so the dump is rarely needed. Guard every Windows-only include
  with `#ifdef Q_OS_WIN`.
- **Exit codes:** a crashed process reports an NTSTATUS (`0xC0000005` access
  violation, `0xC0000409` stack buffer overrun / fail-fast). Never mask with
  `& 0xff` — see `subprocess-engine.md` §5.
- **Qt fatal path:** `qFatal` calls `abort()`; install a message handler that
  writes the companion record *before* the abort.

## 4. QPointer discipline (the use-after-free preventer)

Every `QObject*` member that is **not** a child of `this` is a `QPointer<T>`.
Every lambda capture of a QObject outside the connection's context object is a
`QPointer` copy with a null check. Every `deleteLater()` target must only be
referenced through `QPointer`s afterwards. The cost is a hash lookup per
dereference; the alternative is a 2 a.m. heap corruption.

Review grep: raw `Q[A-Z]\w+\*\s+m_\w+;` members in headers → is `this` the
parent? If not, QPointer.

## 5. A readable crash record (what to write when things go wrong)

Three sections, plain text, one line per item:

1. **Object census** — long-lived QObjects registered at construction
   (`class name objectName parent thread created=file:line age pendingDeleteLater`).
   Register services, windows, processes, workers; not every label.
2. **Connections of interest** — for the objects above, outgoing/incoming
   connection summaries (sender → receiver::slot [type] at file:line). Qt's own
   `dumpObjectInfo()` prints this in debug builds; a thin wrapper around
   `connect` that records the site gives the same in release.
3. **Log tail** — the last N lines from the ring buffer (`templates/logging.h`),
   which already contain state transitions, thread transfers and process
   events.

Write it on `qFatal`, on the unhandled-exception path, and on demand from a
hidden "Save diagnostics" action. Plain text, so it can be pasted into a chat
or a bug report.

## 6. Thread-safety audit

- `moveToThread()` is always logged (`core.lifecycle`: class, name, from, to).
- Connections made **before** a `moveToThread` were typed at connect time if a
  type was given; `AutoConnection` resolves at emit time and is fine — but be
  explicit anyway for readability (`Qt::QueuedConnection`).
- `ASSERT_THREAD(this)` at the top of every public method of a worker/service
  that touches members (`templates/thread_guard.h`).
- Widgets are GUI-thread only. A worker emits a signal with plain data; the
  window updates widgets in its slot.
- `QMutex` is non-recursive; a re-entrant lock deadlocks. Use
  `QRecursiveMutex` only as a documented exception.

| Pattern | Symptom | Where it shows |
|---|---|---|
| slot on deleted object | SIGSEGV inside signal dispatch | census: object destroyed; connection audit: dangling |
| direct call from wrong thread | corruption, later random crash | `ASSERT_THREAD` fires; log shows thread ids |
| timer fires during shutdown | access violation in a slot after `aboutToQuit` | census: timer alive, parent gone; shutdown log incomplete |
| child holds pipe open | parent "hangs" at wait | process log shows kill sent, no reap; drain thread blocked |

## 7. Hangs specifically

1. Is the GUI thread inside a `waitFor*`, `exec()` of a nested loop, or a mutex?
   The stack says. 2. Is a child process alive with its stdout unread? `ls -l
   /proc/<pid>/fd` / Process Explorer handles. 3. Did a modal dialog open on a
   non-GUI thread (invisible, blocking)? 4. Is the event loop starved by a
   `processEvents()` loop re-entering the same slot?

An event-loop **heartbeat** (a 50 ms timer that records gaps > 250 ms with the
last log line) turns "it felt sluggish" into a measurement and is cheap enough
to leave on in debug builds.
