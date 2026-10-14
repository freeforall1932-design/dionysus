# Qwen Code (CLI) — install

Vendor: QwenLM · <https://github.com/QwenLM/qwen-code>

## Pick one variant

| Variant | File | Use when |
|---|---|---|
| Unified — grug decides, caveman measures, be-brief writes ★ | [`unified.md`](unified.md) | Recommended default. One agent, both jobs — developer chat and documents. |
| qt6-cmake-cpp | [`qt6-cmake-cpp.md`](qt6-cmake-cpp.md) | Workload skill for Qt 6 desktop applications in C++ built with CMake — new projects, UI redesigns of existing Qt Widgets apps, GUIs that drive a command-line engine through QProcess, offscreen GUI test harnesses, CI o… |
| universal-agent-context | [`universal-agent-context.md`](universal-agent-context.md) | Always-on process layer for any coding-agent session in one of this owner's Git repositories (Arena Agent Mode, Claude Code, or a comparable harness). |

★ = recommended default for Qwen Code (CLI).

**Load at most one output register** (`unified`): it decides how the visible answer reads and which of several acceptable solutions to prefer.

**Load the process layer every session** (`universal-agent-context`): it decides what must exist and be verified before "done" may be said. It is installed as a skill directory, never inlined — its guide is hash-pinned.

**Load a workload skill only when the repository matches it** (`qt6-cmake-cpp`); each description says when to skip it.

Precedence when texts collide: owner instruction → repository evidence → process layer → workload skill → register.

## Install

Install the agent: `npm i -g @qwen-code/qwen-code@latest`

### Option A — paste into the instruction file

Global (all projects):

- `~/.qwen/QWEN.md`

Project (this repo only):

- `QWEN.md`

Copy the contents of one variant file from this directory into it — no
frontmatter, ready to paste.

> The context filename is configurable via `context.fileName` in ~/.qwen/settings.json or .qwen/settings.json; QWEN.md is the default. Hierarchical: the global file supplies defaults for all projects, the project file overrides it.

### Option B — install as a skill

- user: `~/.qwen/skills/<name>/SKILL.md`
- project: `.qwen/skills/<name>/SKILL.md`

Generated, frontmatter-complete skill files: [`skills/`](skills/).

> Each skill is a directory containing SKILL.md with YAML frontmatter. Priority: Project > User > Extension > Bundled. Qwen Code watches the personal and project skill directories and refreshes automatically after a short delay — except in bare mode, which needs a restart. Re-checked 2026-10-14 against docs/users/features/skills.md at QwenLM/qwen-code@3071807: personal ~/.qwen/skills/, project .qwen/skills/ (requires a trusted workspace); skills are enabled by default, with skills.disabled / skills.defaultDisabled / skills.enabled settings.

## Quirks

- Qwen Code is the actively maintained CLI (v0.24.0, released 2026-09-16). It is NOT the same product as the Qwen Chat agent — see profiles/qwen-agent.json.
- A structured <thinking> trace is the natural fit here: Qwen models expose reasoning, so the grug variant's internal trace costs little and reads cleanly.
- Skills are model-invoked: Qwen Code matches your request against the description field. A vague description means the skill never fires.
- Skill directories are watched during a normal session and refresh automatically; bare mode needs a restart.

## Verification

- Tested agent version: `0.24.0`
- Last verified: 2026-10-14
- Verified by: npm registry (@qwen-code/qwen-code dist-tags.latest = 0.24.0, published 2026-09-16) and GitHub releases (v0.24.0, 2026-09-16); instruction-file conventions from the Qwen Code docs. Paths re-confirmed 2026-10-14 from the repository docs (not executed).
- Source: <https://github.com/QwenLM/qwen-code/blob/main/docs/users/configuration/settings.md>
