# OpenAI Codex CLI — install

Vendor: OpenAI · <https://developers.openai.com/codex>

## Pick one variant

| Variant | File | Use when |
|---|---|---|
| Unified — grug decides, caveman measures, be-brief writes ★ | [`unified.md`](unified.md) | Recommended default. One agent, both jobs — developer chat and documents. |
| qt6-cmake-cpp | [`qt6-cmake-cpp.md`](qt6-cmake-cpp.md) | Workload skill for Qt 6 desktop applications in C++ built with CMake — new projects, UI redesigns of existing Qt Widgets apps, GUIs that drive a command-line engine through QProcess, offscreen GUI test harnesses, CI o… |
| universal-agent-context | [`universal-agent-context.md`](universal-agent-context.md) | Always-on process layer for any coding-agent session in one of this owner's Git repositories (Arena Agent Mode, Claude Code, or a comparable harness). |

★ = recommended default for OpenAI Codex CLI.

**Load at most one output register** (`unified`): it decides how the visible answer reads and which of several acceptable solutions to prefer.

**Load the process layer every session** (`universal-agent-context`): it decides what must exist and be verified before "done" may be said. It is installed as a skill directory, never inlined — its guide is hash-pinned.

**Load a workload skill only when the repository matches it** (`qt6-cmake-cpp`); each description says when to skip it.

Precedence when texts collide: owner instruction → repository evidence → process layer → workload skill → register.

## Install

Install the agent: `npm i -g @openai/codex`

### Option A — paste into the instruction file

Global (all projects):

- `~/.codex/AGENTS.md`

Project (this repo only):

- `AGENTS.md`

Copy the contents of one variant file from this directory into it — no
frontmatter, ready to paste.

> AGENTS.md is read from the project root and, for user-level defaults, from ~/.codex/AGENTS.md.

### Option B — install as a skill

- user: `~/.agents/skills/<name>/SKILL.md`
- user: `~/.codex/skills/<name>/SKILL.md`
- project: `.agents/skills/<name>/SKILL.md`
- project: `.codex/skills/<name>/SKILL.md`

Generated, frontmatter-complete skill files: [`skills/`](skills/).

> Skill roots in the current source: the project config folder's skills dir (.codex/skills, repo scope), .agents/skills in every directory between the project root and the cwd, ~/.agents/skills (user), $CODEX_HOME/skills (user, marked deprecated in the source but still read), plus system/admin roots. Project roots are only used when the repository filesystem is available to the session.

## Quirks

- .agents/skills/ is the interoperable project directory: Codex, Gemini CLI, OpenCode and Copilot all read it, so one checked-in folder serves four harnesses.
- AGENTS.md is still the most portable instruction surface — Copilot, Cursor and OpenCode read it too. Use it for the loader paragraph and let the skill directory carry the files.

## Verification

- Tested agent version: `unverified`
- Last verified: 2026-10-14
- Verified by: documentation review of the Codex repository (source file) — codex-rs/ext/skills/src/host_roots.rs at openai/codex@c22a06c (2026-10-14): .codex/skills (project), .agents/skills (project, walked from project root to cwd), ~/.agents/skills and $CODEX_HOME/skills (user). Instruction-file facts carried over from the 2026-09-17 review. Not executed against a binary.
- Source: <https://github.com/openai/codex/blob/c22a06c/codex-rs/ext/skills/src/host_roots.rs>
