# Coding agents

The rest of this repository targets **Claude (app/web) and paste-in chat
models** for academic and office writing. This section targets **coding
agents** — Qwen Chat Agent, Qwen Code, Claude Code, Codex, Cursor, Copilot,
OpenCode, Gemini CLI — where
the same three philosophies apply to a different job: reading and writing
code, not chapters.

Since 2026-10-14 it is also the **catalog**: one directory per skill under
`variants/`, three layers (register, process, workload), one compiler, one
gate (`validate_skills.py` + `index.json`). Add a skill by adding a directory;
the gate fails until the index and this page name it.

It exists because the three philosophies do **not** agree with each other,
and a coding agent is where that disagreement actually bites.

---

## Start here

**If you only read one file:** [`philosophy/conflicts.md`](philosophy/conflicts.md).

It states plainly where grug, caveman, and be-brief contradict each other, and
resolves each conflict by destination. The short version:

> **grug decides, caveman measures, be-brief writes, and nobody touches the
> code.**

**If you just want to install something:** pick your agent, open
`packs/<agent>/README.md`, and copy one variant file.

| Agent | Instruction file | Recommended |
|---|---|---|
| [Qwen Chat Agent](packs/qwen-agent/README.md) | upload `workspace/*.md` into the workspace, or paste | `unified` |
| [Qwen Code](packs/qwen/README.md) | `QWEN.md` / `~/.qwen/QWEN.md`, or `.qwen/skills/` | `unified` |
| [Claude Code](packs/claude/README.md) | `CLAUDE.md`, or `.claude/skills/` | `unified` |
| [Codex CLI](packs/codex/README.md) | `AGENTS.md` (no project skills dir) | `unified` |
| [Cursor](packs/cursor/README.md) | `.cursor/rules/*.mdc` | `unified` |
| [GitHub Copilot](packs/copilot/README.md) | `.github/copilot-instructions.md`, or `AGENTS.md` | `unified` |
| [OpenCode](packs/opencode/README.md) | `AGENTS.md` | `unified` |

Everything is also bundled in [`packs/coding-agents.zip`](packs/coding-agents.zip).

---

## The catalog — three layers

Sources of truth live in [`variants/`](variants/). Everything in
[`packs/`](packs/) is generated from them. [`index.json`](index.json) is the
triage table (`read_when` / `skip_when` per skill) and
[`validate_skills.py`](validate_skills.py) fails when a skill is missing from
it or from this page.

| Skill | Layer | What it governs | Open it when | Skip it when |
|---|---|---|---|---|
| [`unified`](variants/unified/SKILL.md) | register (reasoning + output) | How the visible answer reads; which of several acceptable solutions to prefer. Grug decides, caveman measures, be-brief writes, nobody touches the code. | every session — the one register | never; it is the only register shipped |
| [`universal-agent-context`](variants/universal-agent-context/SKILL.md) | process | What must exist and be verified before "done": inspect before changing, verification ladder, commit before session end, mandatory "Not verifiable here" line, UI behaviour contract before any widget. Wraps a hash-pinned `UNIVERSAL_AGENT_CONTEXT_v4.md`. | every session in one of the owner's repositories | never — but it is not a writing register and not stack guidance |
| [`qt6-cmake-cpp`](variants/qt6-cmake-cpp/SKILL.md) | workload | Qt 6 / CMake / C++ desktop apps: references, drop-in templates, `qt_lint.py`. | the real build entry point is CMake with `find_package(Qt6 …)` | no Qt 6 CMake target |

### Load one register, the process layer, and the matching workload skills

The register decides *how it is said*; the process layer decides *what must be
true before it may be said*; a workload skill adds *what this stack needs*.
Precedence when texts collide: owner instruction → repository evidence →
process layer → workload skill → register. The register never changes what is
required, only how it reads.

The former `be-brief-output`, `caveman-output` and `grug-reasoning` variants
were retired on 2026-10-14; `unified` is self-contained and carries all three
philosophies, one per layer. Their philosophy pages stay in
[`philosophy/`](philosophy/), and
[`philosophy/conflicts.md`](philosophy/conflicts.md) now also covers how the
register composes with the process layer.

---

## The three philosophies, kept honest

| Document | Source | What it governs |
|---|---|---|
| [`philosophy/grug.md`](philosophy/grug.md) | [grugbrain.dev](https://grugbrain.dev/) | How to decide. Complexity is the eternal enemy. |
| [`philosophy/caveman.md`](philosophy/caveman.md) | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | How much to say. Terse output, code untouched. |
| [`philosophy/be-brief.md`](philosophy/be-brief.md) | this repo, built on official caveman | How it should read. Professional prose for documents. |
| [`philosophy/conflicts.md`](philosophy/conflicts.md) | ours | Where they clash, and which one wins where. |
| [`philosophy/sources.md`](philosophy/sources.md) | — | Exactly what came from where, and what is ours. |

Grug is the only one of the three that is **not** an output style. It is a way
of deciding, and its broken register is part of its rhetorical power — which
is exactly why it must never leak into user-facing text.

---

## Why Qwen specifically

There are **two Qwen surfaces** and they are not the same product.

**Qwen Chat Agent** ([`packs/qwen-agent/`](packs/qwen-agent/)) is the agent mode
inside Qwen Chat, with a workspace you attach files to. It has no config
directory and no CLI. Whether it parses `SKILL.md` frontmatter is **unknown** —
no public specification was found — so its pack ships plain `.md` files with no
frontmatter, which read as ordinary text either way. That is the pseudo-skill
route, and it is the dependable one.

**Qwen Code** ([`packs/qwen/`](packs/qwen/)) is the terminal CLI, actively
maintained (v0.24.0 released 2026-09-16). It reads `QWEN.md` and discovers
`.qwen/skills/<name>/SKILL.md`, so its pack ships both the paste files and real
skill directories.

Both are priority targets, for two reasons.

First, its instruction surface is a plain Markdown context file
(`QWEN.md`, configurable via `context.fileName`), plus a genuine skills
directory at `~/.qwen/skills/` and `.qwen/skills/` — so both delivery routes
work, and the generated pack ships both.

Second, Qwen models expose a reasoning trace, which makes the `grug_reasoning`
register a natural fit: the internal SNIFF → FEAR → PLAN → ACT → SPEAK flow
costs little and reads cleanly. The SkillOpt integration trains against Qwen
as the target by default — see
[`skillopt-integration/configs/coding-agent.yaml`](../skillopt-integration/configs/coding-agent.yaml).

---

## Training these skills instead of hand-tuning them

[`skillopt-integration/`](../skillopt-integration/) adds a SkillOpt
environment that treats these documents as the trainable state of a frozen
model and optimises them behind a validation gate. It scores **per register**,
which is what makes training a register meaningful — and why only the register
is trained:

```bash
python -m caveman_skillopt.train --config skillopt-integration/configs/coding-agent.yaml
```

If you flatten the registers into one, the optimizer averages the conflict
away and you get mush.

The process and workload skills are **not** trained. An optimiser that rewrites
the verification ladder or the hash-pinned guide to score better on a
compression rubric is a defect, not an improvement; those two layers stay
hand-maintained and gated.

---

## Layout

```
coding-agents/
├── README.md              ← you are here
├── philosophy/            ← the three upstream philosophies, plus the conflicts
├── index.json             ← triage table: kind / layer / read_when / skip_when per skill
├── validate_skills.py     ← gate: frontmatter, paths, hash pin, index coverage, qt_lint self-test
├── variants/              ← one skill directory each — SOURCE OF TRUTH
│   └── <skill>/           ← SKILL.md + references/ (+ examples.md, templates/, scripts/, pinned guides)
├── profiles/              ← 8 agent profiles (JSON) + schema.md
├── packs/                 ← GENERATED: per-agent × per-skill files + zip
│   └── coding-agents.zip
├── compile.py             ← variants + profiles → packs
└── tests/                 ← tests on profiles and generated output
```

**Do not hand-edit `packs/`.** Change `variants/` or `profiles/`, then:

```bash
python coding-agents/compile.py
pytest coding-agents/tests -q
python coding-agents/validate_skills.py
```

### What the compiler emits, and why the formats differ

| Output | Format | Why |
|---|---|---|
| `packs/<agent>/<variant>.md` | plain Markdown, **frontmatter stripped** | Pasted into a context file, where frontmatter is noise billed on every request |
| `packs/<agent>/skills/<variant>/SKILL.md` | full frontmatter, emitted verbatim | Claude Code, Qwen Code, Codex, Gemini CLI, OpenCode and Copilot discover a skill by it; the optional fields are what make it a skill rather than a text file |
| `packs/<agent>/skills/<variant>/references/*.md` | plain markdown | progressive disclosure — loaded only when the task needs them |
| `packs/<agent>/skills/<variant>/**` (other files) | **byte-for-byte copies** | pinned guides, templates and scripts; rewriting them would break the pin the skill's own gate checks |
| `packs/<agent>/<variant>.md` for a register | no frontmatter, references inlined | paste route; a pasted file has no filesystem beside it |
| `packs/<agent>/<variant>.md` for a process or workload skill (`metadata.paste: loader`) | no frontmatter, **body + file list, nothing inlined** | inlining a 560-line guide bills it on every request and drops everything that is not markdown; the list names where the files live for that harness |
| `packs/cursor/rules/<variant>.mdc` | `description` + `globs` + `alwaysApply` | Cursor **ignores** a plain `.md` file in `.cursor/rules/` — the `.mdc` extension and frontmatter are load-bearing |

Agents with no verified skill convention (Cursor, Qwen Chat Agent) get the
paste file and, for Cursor, the `.mdc` rule, pointing at `.agents/skills/<name>/`
for the files. No invented paths.

---

## Verification honesty

Three profiles carry a tested binary version, inherited from the official
caveman profile registry where they were verified by a local pinned-binary
probe. Three are marked `"unverified"` and say so, with a documentation
source, because they were established from vendor docs only.

`compile.py` fails closed on a profile that claims a version it never tested.
See [`profiles/schema.md`](profiles/schema.md).

---

## Relationship to the rest of the repo

| | `caveman-universal/` + `pseudo-skills/` | `coding-agents/` |
|---|---|---|
| Audience | Claude app/web, paste-in chat models | Coding agent CLIs |
| Work | Thesis, journals, reports, office docs | Reading and writing code |
| Languages | English + Indonesian | Follows the user's language |
| Philosophy | Grug thinks, caveman/be-brief speaks | Same three, resolved per layer |
| Packaging | zips + `.md` | profiles + generated packs |

They are complementary, not competing. The deletion test is identical; only
the register and the destination differ.
