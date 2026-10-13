# Skills — the agent context layers

**Prepared:** 2026-10-13 (session 1 of this layer) · **Gate:** `python3 skills/validate_skills.py`

This directory is the home of the reusable context a coding agent loads before
working in one of this owner's repositories. It replaces the habit of carrying
one giant context file per project with **three layers that compose**:

| Layer | What it holds | Where it lives | Loaded when |
|---|---|---|---|
| **1 — Universal** | *How to work* in any repository: precedence orders, verification ladder, CI strategy, truth maintenance, patch intake, reporting templates. Stack-agnostic by rule. | `skills/universal-agent-context/` (wraps `UNIVERSAL_AGENT_CONTEXT_v4.md`, byte-identical to the copy in gifscythe — hash recorded in `PROVENANCE.md`) | **Always.** |
| **2 — Workload** | *What this kind of work needs*: toolchain facts, patterns, anti-patterns, templates, mechanical lint for one technology lane. No project names, no machine paths. | `skills/<workload>/` — today only `qt6-cmake-cpp/` | When the repository's real stack matches (verified by inspection, never by README). |
| **3 — Project overlay** | *Where this project is*: status register, handoff, task board, decision log, IDs, versions, next actions. | **Inside each project repo** (gifscythe: `STATUS.md`, `SESSION_HANDOFF.md`, `WORKLIST.md`, `IMPROVEMENT_LOG.md`, `docs/planning/`). This repo only keeps a *pointer* in `projects/`. | When working in that project. |

## The answer to "should we have three skills — unified, workload-specific, and v4?"

**Three layers, yes. But v4 is not a third thing — v4 *is* the unified layer.**
The third layer is the per-project overlay, which already exists in gifscythe
and must stay there (v4 §17: process in the universal guide, facts in the
overlay; two copies of the same state are corrupted input for the next session).

So the installable *skills* are two: `universal-agent-context` (always on) and
one skill per workload (`qt6-cmake-cpp` today; more only when a real repository
needs them). The project overlay is a convention, not a package, and `projects/`
holds only pointers plus a copy-paste next-session prompt that carries **no
state**.

What the four source references contributed, and what was deliberately **not**
taken from each:

| Source | Taken | Not taken, and why |
|---|---|---|
| `UNIVERSAL_AGENT_CONTEXT_v4.md` (gifscythe, 2026-10-13) | The whole file, unchanged, as layer 1. Its §8 "lane notes" are the seed of layer 2; its §17 defines layer 3. | Nothing removed. It is **not** forked into a "v5" here — the next universal bump happens only after the retrospective session proves which rules in the wrapper deserve promotion (v4 §17.6). |
| `jessicalh/qt-skill-claude` (`feba82d`, 2026-03-27) | The *shape* of a workload skill (`SKILL.md` + `references/` + `templates/`) and its best principle: diagnosability first — QPointer discipline, logging categories, thread-affinity asserts, an offscreen-readable crash record. | **No file copied.** The repository has **no license** (GitHub API: `license: null`, checked 2026-10-13), so verbatim reuse is not permitted; every reference and template here is written fresh from standard Qt practice. Also dropped: its machine facts (`C:\Qt\6.10.2` (machine-specific example), VTK paths, one laptop's hardware) — those are overlay-class facts that do not belong in a skill. |
| `a5c-ai/babysitter` (`feb68ab`, MIT) incl. the `qt-cmake-project-generator` listed on mcpmarket.com | Its *discipline*: process-as-code with gates that block, breakpoints where the owner must decide, a journal of every step — captured as `skills/universal-agent-context/references/session-protocol.md`. From the Qt generator: the cross-platform `CMakePresets.json` layout and the modern-CMake checklist (adapted, attributed). | **The runtime is not installed.** It is a Node toolchain with hooks for Claude Code/Codex/Cursor sessions; Arena Agent Mode does not run those hooks, and v4 §3 says prefer mechanical gates the repository itself can run. If the owner later works from Claude Code locally, the same runbooks map onto babysitter processes without rewriting the skills. |
| `freeforall1932-design/gifscythe` (`97b0758`, 2026-10-13) | The proving ground. Its register, harness and CI are what the workload skill was checked against (`projects/gifscythe/SKILL_DRY_RUN_2026-10-13.md`), and the generalized lessons — subprocess-engine GUIs, offscreen harness contracts, atomic output promotion — became `qt6-cmake-cpp/references/`. | **No project state copied here.** Its overlay stays in its own repo; `projects/gifscythe/` points at it and dates every pointer. |

## How a session loads the layers

1. Read `skills/universal-agent-context/SKILL.md` (it tells you to read v4 and the session protocol).
2. Inspect the repository. If its real stack matches a workload skill, read that `SKILL.md` and only the references the task needs.
3. If `projects/<name>/` exists, follow its pointer to the project's own overlay and read **that** — the pointer file is not the overlay.
4. Repository evidence outranks every layer (v4 §0.1).

## Rules this directory enforces mechanically

`skills/validate_skills.py` fails on: a `SKILL.md` without `name`/`description`
frontmatter, a `name` that does not match its directory, a relative link or
backticked path that does not resolve, a machine-specific path in universal or
workload material (`C:\…`, `/home/<user>/…`, `/Users/…`), a drift in the
universal file's recorded hash, a `projects/` pointer to a missing local file,
and a failing `qt_lint.py --selftest`. CI runs it on every push
(`.github/workflows/skills-gate.yml`). Promises that are not checked do not
survive sessions — v4 §17.7.

## Adding a workload skill

Only when a real repository needs it. Create `skills/<kebab-name>/SKILL.md`
with frontmatter (`name` = directory name, `description` = when to activate,
written so an agent can decide without opening the file), put long material in
`references/`, drop-in files in `templates/`, mechanical checks in `scripts/`,
and add a row to the table above. Then run the gate.
