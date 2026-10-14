# Gemini CLI — install

Vendor: Google · <https://geminicli.com/docs>

## Pick one variant

| Variant | File | Use when |
|---|---|---|
| Unified — grug decides, caveman measures, be-brief writes ★ | [`unified.md`](unified.md) | Recommended default. One agent, both jobs — developer chat and documents. |
| qt6-cmake-cpp | [`qt6-cmake-cpp.md`](qt6-cmake-cpp.md) | Workload skill for Qt 6 desktop applications in C++ built with CMake — new projects, UI redesigns of existing Qt Widgets apps, GUIs that drive a command-line engine through QProcess, offscreen GUI test harnesses, CI o… |
| universal-agent-context | [`universal-agent-context.md`](universal-agent-context.md) | Always-on process layer for any coding-agent session in one of this owner's Git repositories (Arena Agent Mode, Claude Code, or a comparable harness). |

★ = recommended default for Gemini CLI.

**Load at most one output register** (`unified`): it decides how the visible answer reads and which of several acceptable solutions to prefer.

**Load the process layer every session** (`universal-agent-context`): it decides what must exist and be verified before "done" may be said. It is installed as a skill directory, never inlined — its guide is hash-pinned.

**Load a workload skill only when the repository matches it** (`qt6-cmake-cpp`); each description says when to skip it.

Precedence when texts collide: owner instruction → repository evidence → process layer → workload skill → register.

## Install

Install the agent: `npm i -g @google/gemini-cli`

### Option A — paste into the instruction file

Global (all projects):

- `~/.gemini/GEMINI.md`

Project (this repo only):

- `GEMINI.md`
- `.gemini/GEMINI.md`

Copy the contents of one variant file from this directory into it — no
frontmatter, ready to paste.

> GEMINI.md is Gemini CLI's hierarchical context file (global, project root and subdirectories are concatenated). The Copilot coding agent also reads GEMINI.md.

### Option B — install as a skill

- user: `~/.agents/skills/<name>/SKILL.md`
- user: `~/.gemini/skills/<name>/SKILL.md`
- project: `.agents/skills/<name>/SKILL.md`
- project: `.gemini/skills/<name>/SKILL.md`

Generated, frontmatter-complete skill files: [`skills/`](skills/).

> Discovery tiers, lowest to highest precedence: built-in, extension, user (~/.gemini/skills or ~/.agents/skills), workspace (.gemini/skills or .agents/skills). Within a tier the .agents/skills alias wins over the .gemini/skills directory.

## Quirks

- Context files are concatenated, so a loader paragraph in GEMINI.md and the skill under .agents/skills/ do not duplicate each other — keep the paragraph short.
- .agents/skills/ is shared with Codex, OpenCode and Copilot; .gemini/skills/ is Gemini-only.

## Verification

- Tested agent version: `unverified`
- Last verified: 2026-10-14
- Verified by: documentation review on 2026-10-14 of docs/cli/skills.md at google-gemini/gemini-cli@42c5182 (discovery tiers, .agents/skills alias) and the GEMINI.md context-file documentation in the same repository. Wire protocol recorded as openai-chat only because the schema requires one of its fixed values; Gemini CLI speaks the Gemini API natively. Not executed.
- Source: <https://github.com/google-gemini/gemini-cli/blob/42c5182/docs/cli/skills.md>
