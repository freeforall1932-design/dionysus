# Redesigning an existing Qt Widgets UI

v4 §10 is mandatory and stack-agnostic: visual evidence first, several distinct
mockups, implement once direction is clear, capture and compare. This file is
the Qt-specific method on top of it. A redesign is **three contracts**: the
behaviour contract (unchanged unless the register says otherwise), the test
contract (object names, harness blocks), and the visual/interaction contract
(what actually changes).

> **Prerequisite (any stack):** the four tables of
> `../universal-agent-context/references/ui-behaviour-contract.md` (sibling skill;
> path from this skill's root) — engine
> interface, states, control→engine, engine-event→UI — plus the reference-app
> obligation table. This file is the Qt Widgets implementation of that
> contract; it does not replace it.

## 1. Before drawing anything — inventory the current UI

Produce, from the real source, a table per top-level area:

| Area | Widgets (objectName) | State it shows | Signals it reacts to | Harness blocks that touch it |
|---|---|---|---|---|

Then list the **states** the UI must render: empty · queue loaded · running
(single / batch item k of N / preview) · succeeded · partial failure · failed
(engine error / engine missing / refused up front) · cancelled · timed out ·
settings load warning. A mockup that only shows the happy path is not a mockup.

Capture the **current** UI offscreen (§7) so the comparison later is against
pixels, not memory.

## 2. Reference-driven, not prose-driven

- Use the owner's supplied references first (screenshots, named apps). Inspect
  them with image tools; write down observations separately from inferences.
- Extract *features and hierarchy* (how a batch app shows a queue, per-item
  results, destination, actions) — not branding, icons or protected assets.
- When the register already contains a design draft or a contract proposal for
  a new area (e.g. a per-file results table), that is an input to the mockups,
  not an approved design.

## 3. Two or three genuinely different directions

Not three colour schemes of one layout. For a converter-style app the usual
axes are:

1. **Workflow tabs** (Input → Actions → Output → Results): linear, discoverable,
   wastes width on wide screens.
2. **Single-screen with docks**: queue left, settings right, results bottom,
   preview floating; power-user density; needs `QMainWindow::addDockWidget` and
   saved layouts.
3. **Wizard/stepper over a persistent results pane**: casual-user first; power
   features behind an "advanced" disclosure.

For each: a low-cost mockup (an HTML/SVG sketch, or a throwaway Qt layout
captured offscreen), the state list from §1 covered, keyboard path, and the
cost of migrating the harness. Show them and **stop** (session protocol
breakpoint) — appearance is an owner decision.

## 4. Theming and palette

- Prefer `QPalette` roles over hard-coded colours. `setStyleSheet("background:#202020")`
  silently breaks the light theme, high-contrast modes, and any later dark-mode
  toggle (`qt_lint` QL006 flags hex colours in stylesheets).
- One application-level QSS loaded from resources, with named properties
  (`QLabel[role="hint"]`) instead of per-widget sheets scattered in code.
- Dark mode on Qt 6.5+: follow the system via `QStyleHints::colorScheme()`
  (signal `colorSchemeChanged`); on Windows the `windows11`/`fusion` styles
  honour it; on Linux the platform theme does. Never ship a dark theme that is a
  pile of per-widget overrides.
- Icons: SVG from resources, tinted by palette where possible; provide the
  `imageformats/qsvg` plugin at deploy time.

## 5. High-DPI and layout

Qt 6 is per-monitor DPI aware by default. Rules: no fixed pixel sizes for text
containers; `sizeHint`-driven layouts; `QSplitter` between queue/preview;
minimum window size that still shows every state; test at 100 % and 200 % with
`QT_SCALE_FACTOR=2` offscreen.

## 6. The results table (per-item outcomes)

A redesign of a batch tool almost always adds "one row per file". Build it as:

- a Qt-free row struct (`input, output, before_bytes, after_bytes, state, reason`),
  with a fixed state enum (`pending · running · succeeded · failed · cancelled · skipped`)
  — `skipped` = never attempted, distinct from cancelled;
- a `QAbstractTableModel` over a vector of rows, `dataChanged` per row;
- a `QTableView` with a proxy for sorting; totals in a footer label derived
  from the model, never counted separately;
- failure reasons as **named** categories (engine error, verification failed,
  refused up front, timed out) plus the engine's message.

The same row struct serializes to JSON for a CLI or web surface, so the
contract is proven once.

## 7. Capturing the implemented UI (evidence)

Offscreen, from the real window class:

```cpp
qputenv("QT_QPA_PLATFORM", "offscreen");
QApplication app(argc, argv);
MainWindow w; w.resize(1280, 800); w.show();
QApplication::processEvents();
// drive the window into each state with the harness helpers, then:
w.grab().save(QStringLiteral("shots/%1.png").arg(stateName));
```

Produce the same set for the old and the new UI at the same size; put them
side by side in the review; never describe a screenshot you did not take.
If the repo policy is binary-free, store the recipe and attach the PNGs to the
PR instead of committing them.

## 8. Harness migration plan (write it before coding)

| Harness block | Touches objectNames | Change needed | Owner of the change |
|---|---|---|---|

Rules: keep names where the widget survives; rename only with the harness in
the same commit; add blocks for every new state; keep the "lying engine",
"partial failure", "cancel mid-run" and "settings snapshot" blocks green at
every step — the redesign is not allowed to regress a data-safety proof.

## 9. Acceptance

- Hierarchy matches the owner's workflow; the primary action is obvious in
  every state.
- Queue, progress, per-item results, errors and cancellation are truthful.
- All states from §1 are visible and were captured.
- Keyboard-only path exists for add → run → open output.
- Old-vs-new captures reviewed by the owner; the owner's decision recorded in
  the decision log; register rows for the redesign moved only with that proof.