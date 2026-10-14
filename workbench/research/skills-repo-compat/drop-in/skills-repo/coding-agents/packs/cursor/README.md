# Cursor — install

Vendor: Cursor (Anysphere) · <https://cursor.com/docs/rules>

## Pick one variant

| Variant | File | Use when |
|---|---|---|
| Unified — grug decides, caveman measures, be-brief writes ★ | [`unified.md`](unified.md) | Recommended default. One agent, both jobs — developer chat and documents. |
| qt6-cmake-cpp | [`qt6-cmake-cpp.md`](qt6-cmake-cpp.md) | Workload skill for Qt 6 desktop applications in C++ built with CMake — new projects, UI redesigns of existing Qt Widgets apps, GUIs that drive a command-line engine through QProcess, offscreen GUI test harnesses, CI o… |
| universal-agent-context | [`universal-agent-context.md`](universal-agent-context.md) | Always-on process layer for any coding-agent session in one of this owner's Git repositories (Arena Agent Mode, Claude Code, or a comparable harness). |

★ = recommended default for Cursor.

**Load at most one output register** (`unified`): it decides how the visible answer reads and which of several acceptable solutions to prefer.

**Load the process layer every session** (`universal-agent-context`): it decides what must exist and be verified before "done" may be said. It is installed as a skill directory, never inlined — its guide is hash-pinned.

**Load a workload skill only when the repository matches it** (`qt6-cmake-cpp`); each description says when to skip it.

Precedence when texts collide: owner instruction → repository evidence → process layer → workload skill → register.

## Install

Install the agent: `https://cursor.com/download`

### Option A — paste into the instruction file

Project (this repo only):

- `.cursor/rules/*.mdc`
- `AGENTS.md`

Copy the contents of one variant file from this directory into it — no
frontmatter, ready to paste.

> Project rules live in .cursor/rules/ as .mdc files — Markdown WITH YAML frontmatter. The extension is load-bearing: a plain .md file in .cursor/rules/ is ignored, because it has no frontmatter to declare when it applies. Frontmatter has exactly three fields: description, globs, alwaysApply. The legacy root .cursorrules file is still read for backwards compatibility but is documented as legacy. Cursor also reads AGENTS.md (root and subdirectories) and CLAUDE.md.

### Option C — Cursor project rule

Generated `.mdc` rules with correct frontmatter: [`rules/`](rules/).

```bash
mkdir -p .cursor/rules
cp packs/cursor/rules/unified.mdc .cursor/rules/caveman-unified.mdc
```

> The `.mdc` extension is load-bearing — a plain `.md` file in
> `.cursor/rules/` is ignored, because it has no frontmatter to declare
> when it applies.

## Quirks

- Rules apply to Agent only — not Tab completion, Inline Edit, or Bugbot PR reviews. If a rule appears to do nothing, check the surface you tested it in.
- With alwaysApply: true, globs and description are ignored. With false, a glob auto-attaches the rule; a description lets the agent pull it in; neither means it loads only when @-mentioned.
- Team Rules > Project Rules > User Rules, and all applicable rules are MERGED — two rules that disagree both reach the model. Do not load two conflicting variants at once.
- Keep rules under ~500 lines. An always-applied rule is billed on every request.
- Cursor is listed as an Agent Skills client by the agentskills.io specification (docs: https://cursor.com/docs/context/skills), but its skill directory layout was not verifiable from this sandbox. Until it is, the .mdc rule is the loader paragraph and the skill files are read by path from .agents/skills/<name>/.

## Verification

- Tested agent version: `unverified`
- Last verified: 2026-10-14
- Verified by: documentation review of Cursor Rules reference (frontmatter fields, .mdc requirement, legacy .cursorrules status, AGENTS.md and CLAUDE.md support, Agent-only scope, merge precedence). Re-checked 2026-10-14: Cursor appears in agentskills/agentskills docs/snippets/clients.jsx as a skills client; cursor.com was unreachable, so skills stay null here.
- Source: <https://cursor.com/docs/rules>
