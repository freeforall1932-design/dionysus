# OpenCode — install

Vendor: Anomaly (formerly SST) · <https://opencode.ai/docs>

## Pick one variant

| Variant | File | Use when |
|---|---|---|
| Unified — grug decides, caveman measures, be-brief writes ★ | [`unified.md`](unified.md) | Recommended default. One agent, both jobs — developer chat and documents. |
| qt6-cmake-cpp | [`qt6-cmake-cpp.md`](qt6-cmake-cpp.md) | Workload skill for Qt 6 desktop applications in C++ built with CMake — new projects, UI redesigns of existing Qt Widgets apps, GUIs that drive a command-line engine through QProcess, offscreen GUI test harnesses, CI o… |
| universal-agent-context | [`universal-agent-context.md`](universal-agent-context.md) | Always-on process layer for any coding-agent session in one of this owner's Git repositories (Arena Agent Mode, Claude Code, or a comparable harness). |

★ = recommended default for OpenCode.

**Load at most one output register** (`unified`): it decides how the visible answer reads and which of several acceptable solutions to prefer.

**Load the process layer every session** (`universal-agent-context`): it decides what must exist and be verified before "done" may be said. It is installed as a skill directory, never inlined — its guide is hash-pinned.

**Load a workload skill only when the repository matches it** (`qt6-cmake-cpp`); each description says when to skip it.

Precedence when texts collide: owner instruction → repository evidence → process layer → workload skill → register.

## Install

Install the agent: `curl -fsSL https://opencode.ai/install | bash`

### Option A — paste into the instruction file

Global (all projects):

- `~/.config/opencode/AGENTS.md`

Project (this repo only):

- `AGENTS.md`

Copy the contents of one variant file from this directory into it — no
frontmatter, ready to paste.

> OpenCode traverses up from the current directory looking for AGENTS.md and CLAUDE.md, then falls back to ~/.config/opencode/AGENTS.md, then ~/.claude/CLAUDE.md unless disabled. Precedence: local > global > ~/.claude/CLAUDE.md. The `instructions` array in opencode.json can add more files or glob patterns (remote URLs supported, 5s timeout).

### Option B — install as a skill

- user: `~/.config/opencode/skills/<name>/SKILL.md`
- user: `~/.claude/skills/<name>/SKILL.md`
- user: `~/.agents/skills/<name>/SKILL.md`
- project: `.opencode/skills/<name>/SKILL.md`
- project: `.claude/skills/<name>/SKILL.md`
- project: `.agents/skills/<name>/SKILL.md`

Generated, frontmatter-complete skill files: [`skills/`](skills/).

> OpenCode walks up from the cwd to the git worktree loading .opencode/skills/*/SKILL.md, .claude/skills/*/SKILL.md and .agents/skills/*/SKILL.md, plus the three global locations. A skill becomes available to the model through its skill tool; permissions can be set per agent.

## Quirks

- Because OpenCode reads ~/.claude/CLAUDE.md by default, a Claude Code install can leak into OpenCode. Disable that fallback if you run different variants in each.
- opencode.json `instructions` accepts globs like `packages/*/AGENTS.md` — the cleanest way to share one rule set across a monorepo.

## Verification

- Tested agent version: `unverified`
- Last verified: 2026-10-14
- Verified by: documentation review on 2026-10-14 of packages/web/src/content/docs/skills.mdx at sst/opencode@5aabb61 (skill locations, discovery order); rules facts carried over from the 2026-09-17 review. Not executed.
- Source: <https://github.com/sst/opencode/blob/5aabb61/packages/web/src/content/docs/skills.mdx>
