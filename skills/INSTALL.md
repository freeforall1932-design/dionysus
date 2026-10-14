# Using these skills from another repository (or another harness)

The most common reason "the agent did not follow the instructions" is that the
instructions were never loaded: skills in a directory no harness scans, or a
long guide pasted once and forgotten by the next session. This page fixes the
loading problem; `skills/validate_skills.py` and the project's own gates fix the
"loaded but ignored" problem (a gate that fails is harder to ignore than prose).

## 1. The loader paragraph (works pasted into any harness, any session)

```
Before touching this repository, load the skills in this order and say which you loaded:
1. <SKILLS>/universal-agent-context/SKILL.md, then UNIVERSAL_AGENT_CONTEXT_v4.md (§0–§3, §6, §16–§19 at minimum), then references/session-protocol.md.
2. Inspect the repo's real build entry point; load the matching <SKILLS>/<workload>/SKILL.md only if it matches (today: qt6-cmake-cpp for CMake + find_package(Qt6)).
3. If the task touches a UI or says "like app X": fill <SKILLS>/universal-agent-context/references/ui-behaviour-contract.md tables before any mockup or widget edit.
4. Read this project's own overlay (STATUS / HANDOFF / decisions) and treat it as the overlay; repository evidence outranks every skill; my latest explicit instruction outranks every document.
Stop at breakpoints that need my decision. End with the §19 session-log fields including "Not verifiable here".
```

Replace `<SKILLS>` with wherever the skills live in that checkout (§2).

## 2. Getting the files into the other repository

Pick one; record the choice and the commit in that project's own overlay.

| Option | Command / layout | When |
|---|---|---|
| **Pinned submodule** (quarantined, inert — the shape gifscythe's planning §3 prefers for external tooling) | `git submodule add https://github.com/freeforall1932-design/dionysus external/dionysus` then point loaders at `external/dionysus/skills` | the project wants updates by explicit bump only |
| **Copied snapshot** | copy `skills/` to `<repo>/.agents/skills/` (or `.claude/skills/`) and write the source commit hash into a `PROVENANCE.md` next to it | the project must build offline / without submodules |
| **Pointer only** | no files; the loader paragraph names the dionysus URL + commit | one-off sessions |

Never let a copy drift silently: the universal file's sha256 is pinned in
`skills/universal-agent-context/PROVENANCE.md`; a copied tree can re-run
`validate_skills.py --root <repo>` only if the whole `skills/` layout is copied.

## 3. Where each harness looks (so the loader is read automatically)

| Harness | Reads automatically | Put there |
|---|---|---|
| Claude Code | `CLAUDE.md` at repo root; project skills in `.claude/skills/<name>/SKILL.md` | the loader paragraph in `CLAUDE.md`; optionally copy/symlink the two skill directories into `.claude/skills/` |
| Codex CLI, OpenCode | `AGENTS.md` at repo root | the loader paragraph |
| Cursor | `.cursor/rules/*.mdc` | one rule file containing the loader paragraph (`alwaysApply: true`) |
| GitHub Copilot | `.github/copilot-instructions.md` (also reads `AGENTS.md`) | the loader paragraph |
| Qwen Code | `QWEN.md` at repo root | the loader paragraph |
| Harnesses following the Agent Skills convention (skills.sh, REA's installer) | `.agents/skills/<name>/SKILL.md` | copy the skill directories |
| Arena Agent Mode | nothing automatic | paste the loader paragraph as the first message, or say "read AGENTS.md first" if the repo has one |

This repository ships `AGENTS.md` and `CLAUDE.md` at its root with exactly the
loader paragraph, so any of the above harnesses opened on *this* repo loads the
layers without being asked.

## 4. Composing with a style register

The owner's `skills-repo` (caveman / grug / be-brief) sets *how the agent
reasons and how terse it writes*; these skills set *process and workload*. Load
one register from there **and** the layers here. If a harness allows only one
instruction file, put the register paragraph first and the loader paragraph
second — the loader contains no style rules, so nothing collides.

## 5. Checking that loading actually happened

Ask, at the start of the session: *"Which skill files did you read, and what is
the sha256 recorded in PROVENANCE.md?"* An agent that loaded the layers answers
with the file list and `51f21f33…`; one that did not will paraphrase. Make this
the first line of the session log.
