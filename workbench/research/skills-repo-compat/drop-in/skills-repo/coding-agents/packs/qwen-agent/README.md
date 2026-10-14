# Qwen Chat Agent — install

Vendor: Alibaba / Qwen · <https://chat.qwen.ai/>

## Pick one variant

| Variant | File | Use when |
|---|---|---|
| Unified — grug decides, caveman measures, be-brief writes ★ | [`unified.md`](unified.md) | Recommended default. One agent, both jobs — developer chat and documents. |
| qt6-cmake-cpp | [`qt6-cmake-cpp.md`](qt6-cmake-cpp.md) | Workload skill for Qt 6 desktop applications in C++ built with CMake — new projects, UI redesigns of existing Qt Widgets apps, GUIs that drive a command-line engine through QProcess, offscreen GUI test harnesses, CI o… |
| universal-agent-context | [`universal-agent-context.md`](universal-agent-context.md) | Always-on process layer for any coding-agent session in one of this owner's Git repositories (Arena Agent Mode, Claude Code, or a comparable harness). |

★ = recommended default for Qwen Chat Agent.

**Load at most one output register** (`unified`): it decides how the visible answer reads and which of several acceptable solutions to prefer.

**Load the process layer every session** (`universal-agent-context`): it decides what must exist and be verified before "done" may be said. It is installed as a skill directory, never inlined — its guide is hash-pinned.

**Load a workload skill only when the repository matches it** (`qt6-cmake-cpp`); each description says when to skip it.

Precedence when texts collide: owner instruction → repository evidence → process layer → workload skill → register.

## Install

Install the agent: `Open https://chat.qwen.ai/ and start an agent session (no CLI to install)`

### Option A — upload [`workspace/`](workspace/) or paste its text

Attach one variant file from [`workspace/`](workspace/) to the agent's workspace, or paste its text at the start of a session.
No frontmatter — these read as ordinary text, which is the route that
works whether or not the agent parses skill files.

> This is the agent mode inside Qwen Chat, with a workspace you can attach files to. It is a DIFFERENT product from Qwen Code, the terminal CLI (see profiles/qwen.json). There is no ~/.qwen directory and no CLI to configure: instructions reach the agent by uploading a file into the workspace, or by pasting text at the start of a session. Because the workspace ingests uploaded files, a SKILL.md may or may not be parsed for its frontmatter — this is UNVERIFIED. The dependable route is a plain .md file with no frontmatter, which is read as ordinary text. That is why the pseudo-skill fallback exists.

## Quirks

- No verified skill-file convention. Treat SKILL.md frontmatter as a bonus if it is honoured, not as a dependency — the instructions must stand on their own as plain text.
- Upload size and file-type limits are set by the product and can change; keep the instruction file small so it survives them.
- Because there is no session-start hook, the instructions must be re-attached or re-pasted when a session resets.
- If the agent has a code-execution or file tool, the code-preservation rule matters here too: uploaded and generated files are real files.

## Verification

- Tested agent version: `unverified`
- Last verified: 2026-09-17
- Verified by: documentation review — no public specification of Qwen Chat Agent's instruction-file conventions was found, so nothing here is asserted about frontmatter parsing. Upload/paste is treated as the only dependable route.
- Source: <https://chat.qwen.ai/>
