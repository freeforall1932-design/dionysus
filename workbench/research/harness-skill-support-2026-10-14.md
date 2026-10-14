# Which harnesses can actually use a skill — and what the others get

**Date:** 2026-10-14 · **Question:** when the catalog ships `universal-agent-context`
and `qt6-cmake-cpp`, which agents load them as real skills (a `SKILL.md`
directory with files beside it), which only read an instruction file but can
still open the files by path, and which get a pseudo-skill (pasted text with no
filesystem)? **Method:** the vendor documentation or source *inside each
project's GitHub repository* was read on 2026-10-14 at the commit named below
(vendor websites are unreachable from this sandbox). **No harness was
launched** — every row is a documentation/source review, not an executed
install. The catalog's `profiles/*.json` carry the same facts with the same
sources.

## Three classes

| Class | What it means for the two layered skills | Harnesses (verified below) |
|---|---|---|
| **Real skill** | The harness discovers `<dir>/<name>/SKILL.md`, shows the model name + description, and loads the body and the files beside it on demand. The hash-pinned guide, templates and `qt_lint.py` arrive byte-for-byte; the paste file is optional. | Claude Code, Codex CLI, Gemini CLI, OpenCode, GitHub Copilot (coding agent, CLI, code review, VS Code), Qwen Code |
| **Semi** | The harness reads an instruction file (`AGENTS.md`, `.mdc` rule) but has no verified skill directory. The agent still has a filesystem, so the loader paste names `.agents/skills/<name>/…` and the agent opens the files by path. Progressive disclosure is manual, not automatic. | Cursor (skills claimed by the Agent Skills client list; layout not verifiable here) |
| **Pseudo** | A chat/web agent with an uploaded workspace and no config directory. Only pasted text works. The register (`unified`) inlines fine; a loader skill cannot point at files that are not there, so the paste tells the user to upload the skill directory into the workspace. | Qwen Chat Agent |

## Per-harness facts (read 2026-10-14)

| Harness | Project skill dir(s) | User skill dir(s) | Instruction file | Pack produced by the catalog | Source read | How verified |
|---|---|---|---|---|---|---|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` | `CLAUDE.md` | skill dir + paste | profile `claude.json` (2026-09-17 review); corroborated today by OpenCode and Copilot docs, which both read `.claude/skills/` | documentation review; not executed |
| Codex CLI | `.codex/skills/` (project config folder), `.agents/skills/` (every directory from the project root down to the cwd) | `~/.agents/skills/`, `$CODEX_HOME/skills` (marked deprecated in the source, still read) | `AGENTS.md` | skill dir + paste | `codex-rs/ext/skills/src/host_roots.rs` at `openai/codex@c22a06c` | source review; not executed. **This supersedes the 2026-09-17 profile note "Codex discovers user-level skills only".** |
| Gemini CLI | `.gemini/skills/` or `.agents/skills/` (workspace tier; `.agents` wins inside a tier) | `~/.gemini/skills/` or `~/.agents/skills/` | `GEMINI.md` (hierarchical, concatenated) | skill dir + paste (**new profile**) | `docs/cli/skills.md`, `docs/cli/gemini-md.md` at `google-gemini/gemini-cli@42c5182` | documentation review; not executed |
| OpenCode | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` (walks up to the git worktree) | `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/` | `AGENTS.md` | skill dir + paste (**was paste-only**) | `packages/web/src/content/docs/skills.mdx` at `sst/opencode@5aabb61` | documentation review; not executed |
| GitHub Copilot (coding agent, CLI, code review, VS Code agent) | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.copilot/skills/`, `~/.agents/skills/` | `.github/copilot-instructions.md`, `AGENTS.md` | skill dir + paste (**was paste-only**) | `content/copilot/concepts/agents/about-agent-skills.md` in `github/docs`; `docs/agent-customization/agent-skills.md` in `microsoft/vscode-docs` | documentation review; not executed. VS Code's page adds: discovery makes a skill available, it does not guarantee the model invokes it |
| Qwen Code | `.qwen/skills/` (needs a trusted workspace) | `~/.qwen/skills/` | `QWEN.md` | skill dir + paste | `docs/users/features/skills.md` at `QwenLM/qwen-code@3071807` | documentation review; not executed. Skills are on by default; `skills.disabled` / `skills.defaultDisabled` / `skills.enabled` settings exist |
| Cursor | not verifiable here | not verifiable here | `.cursor/rules/*.mdc`, `AGENTS.md` | `.mdc` rule + paste, both pointing at `.agents/skills/<name>/` | `docs/snippets/clients.jsx` in `agentskills/agentskills` lists Cursor as a client with docs at cursor.com/docs/context/skills | client-list review only; cursor.com unreachable |
| Qwen Chat Agent (web) | none | none | uploaded workspace file | paste only; loader paste says "upload `universal-agent-context/` into the workspace" | profile `qwen-agent.json` (no public spec) | unchanged from 2026-09-17 |

The Agent Skills specification repository (`agentskills/agentskills`, last push
2026-08-09, 26 k stars) lists 46 client products, including all of the above
except Qwen Code and Qwen Chat Agent, plus Goose, Roo Code, Kiro, Amp,
OpenHands, JetBrains Junie, TRAE and others. That list is a claim by the spec
site, not a verification of any directory layout; it is useful only as the
place to start when a new harness has to be added to `profiles/`.

## What this means in practice

1. **One checked-in directory serves most harnesses.** `.agents/skills/<name>/`
   is read natively by Codex, Gemini CLI, OpenCode and Copilot. Add
   `.claude/skills/<name>/` for Claude Code (also read by OpenCode and Copilot)
   and `.qwen/skills/<name>/` for Qwen Code. Three copies — or one directory and
   two symlinks where the platform allows — and every real-skill harness in the
   table finds the same files. The catalog packs put the identical directory
   under `packs/<agent>/skills/<name>/` for each.
2. **The paste file is a loader, not the skill.** For the two layered skills
   the pasted text (3.7 KB and 9.5 KB) is the `SKILL.md` body plus a file list
   that names the harness's directory. Inlining the guide would cost 75 KB on
   every request and would still lose the templates and the lint script — the
   measured outcome of the unpatched compiler.
3. **A model that "half-supports" skills is fine for the universal layer.** The
   process layer is a reading discipline: as long as the agent can open
   `UNIVERSAL_AGENT_CONTEXT_v4.md` by path when the loader tells it to, the
   layer works. What semi/pseudo harnesses lose is automatic triggering
   (description-based activation) and, for pseudo, the files themselves unless
   uploaded.
4. **Verify by install, not by table.** Each profile's `verification` block
   says "not executed". The next evidence step is cheap: in a scratch repo,
   place the three directories, start each harness, and ask it to list its
   skills (`/skills` in Qwen Code, the skills list in Claude Code, Codex's
   `SkillsList` surface, `gemini` skills listing, OpenCode's skill tool, Copilot
   CLI's skill listing). Record the harness version in `tested_agent_version`.

## Not verifiable here

- No harness binary was run; every "supported" is a documentation/source
  claim at the commit named.
- Cursor's skill directory layout (its docs are off-GitHub).
- Whether each harness ignores the extra `metadata.paste` / `metadata.layer`
  frontmatter keys silently (expected under the spec, not executed).
- Qwen Chat Agent's behaviour with an uploaded skill directory.
- Whether description-based activation actually fires for the two skills in
  each harness (VS Code's docs warn that discovery ≠ invocation).
