# GitHub Copilot — install

Vendor: GitHub / Microsoft · <https://docs.github.com/en/copilot>

## Pick one variant

| Variant | File | Use when |
|---|---|---|
| Unified — grug decides, caveman measures, be-brief writes ★ | [`unified.md`](unified.md) | Recommended default. One agent, both jobs — developer chat and documents. |
| qt6-cmake-cpp | [`qt6-cmake-cpp.md`](qt6-cmake-cpp.md) | Workload skill for Qt 6 desktop applications in C++ built with CMake — new projects, UI redesigns of existing Qt Widgets apps, GUIs that drive a command-line engine through QProcess, offscreen GUI test harnesses, CI o… |
| universal-agent-context | [`universal-agent-context.md`](universal-agent-context.md) | Always-on process layer for any coding-agent session in one of this owner's Git repositories (Arena Agent Mode, Claude Code, or a comparable harness). |

★ = recommended default for GitHub Copilot.

**Load at most one output register** (`unified`): it decides how the visible answer reads and which of several acceptable solutions to prefer.

**Load the process layer every session** (`universal-agent-context`): it decides what must exist and be verified before "done" may be said. It is installed as a skill directory, never inlined — its guide is hash-pinned.

**Load a workload skill only when the repository matches it** (`qt6-cmake-cpp`); each description says when to skip it.

Precedence when texts collide: owner instruction → repository evidence → process layer → workload skill → register.

## Install

Install the agent: `https://docs.github.com/en/copilot/get-started`

### Option A — paste into the instruction file

Project (this repo only):

- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`
- `AGENTS.md`

Copy the contents of one variant file from this directory into it — no
frontmatter, ready to paste.

> .github/copilot-instructions.md is the repo-wide surface. Scoped instructions live in .github/instructions/*.instructions.md with YAML frontmatter (applyTo for path globs, excludeAgent to hide a file from code-review or coding-agent). The Copilot coding agent additionally reads AGENTS.md, CLAUDE.md and GEMINI.md, including nested AGENTS.md files for subdirectories.

### Option B — install as a skill

- user: `~/.copilot/skills/<name>/SKILL.md`
- user: `~/.agents/skills/<name>/SKILL.md`
- project: `.github/skills/<name>/SKILL.md`
- project: `.claude/skills/<name>/SKILL.md`
- project: `.agents/skills/<name>/SKILL.md`

Generated, frontmatter-complete skill files: [`skills/`](skills/).

> GitHub's docs: project skills in .github/skills, .claude/skills or .agents/skills; personal skills in ~/.copilot/skills or ~/.agents/skills. Apply to the Copilot coding agent, code review, Copilot CLI and VS Code agent sessions. VS Code's docs add that discovery makes a skill available but does not guarantee the model invokes it.

## Quirks

- applyTo uses glob patterns; without excludeAgent, a file is used by all agents. Set excludeAgent: "code-review" to keep a writing-style rule out of review passes.
- AGENTS.md is the portable option here and is read by Copilot, Codex, Cursor and OpenCode — one file, four agents.
- Put the loader paragraph in .github/copilot-instructions.md or AGENTS.md and the skill directory in .github/skills/<name>/ (or .agents/skills/ to share with Codex, Gemini CLI and OpenCode).

## Verification

- Tested agent version: `unverified`
- Last verified: 2026-10-14
- Verified by: documentation review on 2026-10-14 of github/docs content/copilot/concepts/agents/about-agent-skills.md and microsoft/vscode-docs docs/agent-customization/agent-skills.md (skill directories, surfaces); instruction-file facts carried over from the 2026-09-17 changelog review. Not executed.
- Source: <https://github.com/github/docs/blob/main/content/copilot/concepts/agents/about-agent-skills.md>
