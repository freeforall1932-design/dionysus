---
name: universal-agent-context
description: Always-on process layer for any coding-agent session in one of this owner's Git repositories (Arena Agent Mode, Claude Code, or a comparable harness). Load first, before inspecting the repo. Governs how to read a request, how to rank evidence, the verification ladder, CI and packaging strategy, truth-maintenance of status registers, patch intake, UI work from visual evidence, and end-of-session reporting. Stack-agnostic by rule; project facts live in the project's own overlay. Not a writing register (pair it with one, e.g. skills-repo `unified`), not stack guidance (that is a workload skill such as qt6-cmake-cpp), and not a project overlay.
metadata:
  layer: process
  paste: loader
---

# Universal agent context (layer 1)

This skill is a thin wrapper. The authority is the file next to it:

- **`UNIVERSAL_AGENT_CONTEXT_v4.md`** — read it in full on the first session of a
  task; afterwards re-read §0–§3, §6 and §16–§19 at the start of every session.
  It is byte-identical to the copy in gifscythe at the commit named in
  `PROVENANCE.md`; do not edit it in place — a change is a versioned bump with
  a new provenance appendix.
- **`references/session-protocol.md`** — the phase/gate/breakpoint discipline
  borrowed from babysitter, written as markdown so it runs in any harness.
- **`references/ui-behaviour-contract.md`** — **mandatory before any UI design,
  redesign, or "make it behave like app X" task on any stack**: the engine
  interface table, state table, control→engine and engine-event→UI mappings,
  per-item results, and reference-app obligations with verifiers. Expands v4
  §10/§11.5; evidence taxonomy and obligation ledger after `morluto/rea` (MIT).
  A mockup without these tables is a picture, not a design.

## Loading order (adds to v4 §0)

1. This file, then v4, then the session protocol.
2. Inspect the repository. **Only then** decide whether a workload skill applies
   (a sibling `<workload>/SKILL.md` installed beside this one); the match is the repository's real build
   entry point, not its README or its name.
3. If `projects/<name>/` exists in this repository, it is a *pointer*: follow it
   to the project's own overlay (status register, handoff, task board, decision
   log) and treat **that** as the overlay. Never copy overlay state into the
   skill tree.
4. Repository evidence outranks all three layers; the owner's latest explicit
   instruction outranks every document (v4 §2.1 — two separate orders, do not
   collapse them).

## What goes where (so the layers stay clean)

| Belongs in… | Examples | Test |
|---|---|---|
| v4 (universal) | a precedence rule, a verification-ladder level, a reporting field | Would it be true in a Python web repo *and* a C++ desktop repo? |
| a workload skill | a Qt plugin that must ship, a CMake preset shape, a lint rule | Would it be true in *every* project on that stack, on any machine? |
| the project overlay | a task ID, a version number, a base commit, an owner decision, a machine path | Does it stop being true when the project changes? |

A rule that only makes sense with project details attached stays in the overlay;
the *generalized* rule may be promoted later (v4 §17.6), and only after it has
been used on at least one real task.

## Minimum per-session obligations (the short list)

- Baseline before edits: stack, build/test commands, CI jobs, real package path,
  biggest **verified** gap (v4 §3.3).
- Report at the verification-ladder level actually reached; a compile is not a
  test, a green run is not a desktop acceptance (v4 §6).
- Record every new finding in the session it is found; keep "Not verifiable
  here" in the log entry, never softened (v4 §13.1, §19.2).
- Commit before the session can end (v4 §4.2).
- Run the project's gates until green before any PR boundary; never bypass a
  gate silently (v4 §13.2).
