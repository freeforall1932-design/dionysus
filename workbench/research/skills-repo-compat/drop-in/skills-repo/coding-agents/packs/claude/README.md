# Claude Code — install

Vendor: Anthropic · <https://code.claude.com/docs>

## Pick one variant

| Variant | File | Use when |
|---|---|---|
| Unified — grug decides, caveman measures, be-brief writes ★ | [`unified.md`](unified.md) | Recommended default. One agent, both jobs — developer chat and documents. |
| qt6-cmake-cpp | [`qt6-cmake-cpp.md`](qt6-cmake-cpp.md) | Workload skill for Qt 6 desktop applications in C++ built with CMake — new projects, UI redesigns of existing Qt Widgets apps, GUIs that drive a command-line engine through QProcess, offscreen GUI test harnesses, CI o… |
| universal-agent-context | [`universal-agent-context.md`](universal-agent-context.md) | Always-on process layer for any coding-agent session in one of this owner's Git repositories (Arena Agent Mode, Claude Code, or a comparable harness). |

★ = recommended default for Claude Code.

**Load at most one output register** (`unified`): it decides how the visible answer reads and which of several acceptable solutions to prefer.

**Load the process layer every session** (`universal-agent-context`): it decides what must exist and be verified before "done" may be said. It is installed as a skill directory, never inlined — its guide is hash-pinned.

**Load a workload skill only when the repository matches it** (`qt6-cmake-cpp`); each description says when to skip it.

Precedence when texts collide: owner instruction → repository evidence → process layer → workload skill → register.

## Install

Install the agent: `npm i -g @anthropic-ai/claude-code`

### Option A — paste into the instruction file

Global (all projects):

- `~/.claude/CLAUDE.md`

Project (this repo only):

- `CLAUDE.md`
- `.claude/CLAUDE.md`

Copy the contents of one variant file from this directory into it — no
frontmatter, ready to paste.

> CLAUDE.md is auto-loaded from the project root and the user home directory. It is the canonical instruction surface for Claude Code.

### Option B — install as a skill

- user: `~/.claude/skills/<name>/SKILL.md`
- project: `.claude/skills/<name>/SKILL.md`

Generated, frontmatter-complete skill files: [`skills/`](skills/).

> Skills are directories holding SKILL.md with YAML frontmatter (name + description). Project skills auto-load when the repo is opened in Claude Code. This repo already ships .claude/skills/ in that format.

## Quirks

- Claude Code is the strongest reader of YAML-frontmatter skills — prefer the skills directory over pasting into CLAUDE.md when the variant has frontmatter.
- Extended thinking is separate from the <thinking> tag used by the grug variant. If thinking is enabled, keep the grug trace short or it double-counts tokens.

## Verification

- Tested agent version: `2.1.259`
- Last verified: 2026-09-17
- Verified by: documentation review; version pinned from the official caveman profile (agents/profiles/claude.json), verified there by a local pinned-binary probe.
- Source: <https://code.claude.com/docs>
