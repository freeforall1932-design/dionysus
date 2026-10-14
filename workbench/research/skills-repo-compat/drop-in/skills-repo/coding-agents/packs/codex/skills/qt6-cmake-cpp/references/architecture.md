# Architecture — ownership, lifetimes, signals, startup/shutdown, diagnosability

Qt crashes are overwhelmingly lifetime bugs: a slot runs on a deleted object, a
timer fires during shutdown, a lambda captured a dangling `this`, a worker
touched a widget from the wrong thread. Every rule here exists to make those
impossible or at least *visible*.

## 1. Ownership rules

| Situation | Rule |
|---|---|
| Widget inside a widget | `new QWidget(parent)` — parent deletes child. Raw pointer member is fine **only** when `this` is the parent. |
| A `QObject*` member you do not own (document, model, service, process owned elsewhere) | `QPointer<T>` — nulls itself on destruction. Check before use; log when null. |
| Non-QObject state | `std::unique_ptr`, value members, `std::optional`. Do not make things QObjects to get a parent. |
| Objects shared across threads | Explicit owner thread; `moveToThread` once, logged; delete via `deleteLater()` **on the owning thread** or from `QThread::finished`. |
| Temporary dialogs | Stack-allocate for modal `exec()`; or `setAttribute(Qt::WA_DeleteOnClose)` for modeless. Never leak a `new QDialog` with no parent. |

Lambda captures: a lambda given to `connect` must have a context object
(4-argument form) — it is auto-disconnected when the context dies — **and**
must not capture raw pointers to other QObjects whose lifetime is not tied to
that context. Capture `QPointer` copies for those.

```cpp
// good: context object, auto-disconnect
connect(button, &QPushButton::clicked, this, [this] { save(); });

// good: guarded capture of a non-owned object
connect(timer, &QTimer::timeout, this, [self = QPointer(this), doc = QPointer(m_document)] {
    if (!self || !doc) return;
    self->refresh(*doc);
});

// defect: 3-argument lambda form — survives the death of `this`
connect(button, &QPushButton::clicked, [this] { save(); });   // qt_lint QL002
```

## 2. Signal/slot rules

- Pointer-to-member syntax only. String-based `SIGNAL()/SLOT()` fails at run
  time, silently, on a typo or a signature change (QL001).
- `qOverload<int>(&QComboBox::currentIndexChanged)` for overloaded signals.
- `Qt::UniqueConnection` in any method that can be called more than once
  (`setModel`, `setDocument`, `reload`) — the alternative is N connections and
  a slot that fires N times.
- Across threads: name the type (`Qt::QueuedConnection`). `AutoConnection`
  decides at *emit* time by comparing the receiver's thread with the emitting
  thread, which is correct, but being explicit documents intent and survives a
  later `moveToThread`.
- `QSignalBlocker` when programmatically setting several controls, then one
  explicit refresh — otherwise each `setValue` cascades.
- Emit *after* the object is in a consistent state; never emit from a
  destructor.

## 3. Startup and shutdown order

```cpp
int main(int argc, char* argv[]) {
    QApplication app(argc, argv);                 // 1. first, always
    QCoreApplication::setOrganizationName(...);   // 2. before QSettings/QStandardPaths users
    QCoreApplication::setApplicationName(...);
    QCoreApplication::setApplicationVersion(...);
    installLogging();                              // 3. categories + handler + ring buffer
    installCrashRecord();                          // 4. (platform-specific; see crash-diagnosis.md)
    Settings settings = loadSettings();            // 5. config before services
    Engine engine(settings);                       // 6. services
    MainWindow w(engine);                          // 7. UI last
    w.show();
    QObject::connect(&app, &QCoreApplication::aboutToQuit, [&] {
        w.stopTimers();                            // timers first: #1 shutdown crash
        w.shutdown();                              // UI
        engine.shutdown();                         // services — may wait a bounded time for children
        flushLogging();
    });
    return app.exec();
}
```

Rules: no reliance on static destruction order; every manager has an explicit
`shutdown()` that runs while `QApplication` is alive; `deleteLater()` during
shutdown may never run — delete directly in `shutdown()`; a child process must
be terminated, then killed after a bounded grace, then reaped — see
`subprocess-engine.md`.

## 4. The GUI thread

The GUI thread must stay responsive for the *duration* of work. Acceptable:
a short, bounded wait at process start or cancel if it was measured and the
measurement is recorded in the project register. Not acceptable without that
evidence: `waitForFinished()` with no or a long timeout, a nested
`QEventLoop::exec()` to "wait for a signal", `processEvents()` loops to keep the
UI alive (re-entrancy: a second click can start a second run inside the first).

Preferred shapes:

- Work in a child process → `QProcess` signals (`finished`, `errorOccurred`,
  `readyReadStandardError`), state machine in the window.
- CPU work in-process → `QThread` + worker object (`moveToThread`), or
  `QtConcurrent::run` + `QFutureWatcher`; results come back through queued
  signals; the worker never touches a widget.
- Long I/O → `QFile` in a worker, or `QNetworkAccessManager` (already async).

`ASSERT_THREAD(this)` at the top of methods that touch member state from a
worker-capable class turns a wrong-thread call into a logged assertion instead
of heap corruption three minutes later (`templates/thread_guard.h`).

## 5. Error reporting — one path, structured

All failures flow through one object (an error bus / reporter) with
`level · category · message · context map`. Subscribers render: status bar for
warnings, dialog for errors, log for everything. Modules never call
`QMessageBox` directly — it couples business logic to the window and makes the
offscreen harness fight modal dialogs. Return `std::optional`/`expected`-style
results from core functions; translate to the bus at the UI boundary.

Status text shown to the user must be **truthful**: "Complete" only after the
output was verified (exists, non-empty, right magic, newer than before);
"Cancelled" only when the child really stopped; "Failed" with the engine's
message and exit code; "Partial" when some items in a batch failed.

## 6. Logging categories

Per module, not per class: `core.lifecycle`, `core.process`, `ui.main`,
`ui.preview`, `io.settings`. One line per event, greppable, no multi-line
messages, key=value pairs for context. Mandatory events: object created /
destroyed for long-lived services, thread transfers, process start/exit with
pid and exit code, state transitions, every error-bus event, timer start/stop
for long timers. See `templates/logging.h`.

Enable at run time without a rebuild: `QT_LOGGING_RULES="core.process.debug=true"`.

## 7. Models and views

- One `QAbstractItemModel` (or `QStandardItemModel` for small, static data),
  many views; `QSortFilterProxyModel` for filtering/sorting without copying.
- Mutations go through `beginInsertRows/endInsertRows` and friends — never
  mutate the backing container without the bracket calls; views will crash on
  stale indexes.
- A per-item results table (file → before/after/delta/state/reason) is a model
  with a fixed column enum and a `dataChanged` per row update, not a
  `QTableWidget` rebuilt from scratch per event.
- Keep the model Qt-only, the row *struct* Qt-free, so the same result record
  can be serialized by a CLI or a web surface.

## 8. Project layout that scales

```
src/
  core/        Qt-free (or Qt Core only): settings, validation, argv builder, planner, verifiers
  app/         QObject services: engine runner, settings store, error bus, logging
  ui/          widgets, panels, dialogs, models (depends on app + core)
  main.cpp
tests/
  test_core.cpp            no Qt required
  test_gui_offscreen.cpp   real widgets under offscreen QPA
  fixtures/                text-encoded binary fixtures + checksums, decoded on demand
scripts/                   build, package, verify, gates
```

The dependency direction is `ui → app → core`; a `core` file that includes a
`QWidget` header is a layering defect.