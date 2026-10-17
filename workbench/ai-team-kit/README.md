# AI Team Kit

> **Status on 2026-10-17: extracted, reorganised, and statically audited —
> waiting for the owner to name the next worklist item.**
>
> The canonical v1 kit is now visible as source in `kit/harness/`. Both old
> zip files were deleted only after their contents were extracted and the
> extraction was recorded. No installer, router, OAT agent team, dashboard,
> model provider, or GitHub runtime was started for the audit, and no kit code
> was fixed or changed.

This folder contains the AI Team Kit project for the owner's Gifscythe
repository. The kit's aim is a beginner-friendly team of cloud AI helpers that
uses free models only, works through GitHub pull requests, and leaves merging
to the owner.

## Start here

| If you want to… | Read |
|---|---|
| Understand what to read and in what order | [`READING_GUIDE.md`](READING_GUIDE.md) |
| Resume the project safely | [`SESSION_HANDOFF.md`](SESSION_HANDOFF.md) |
| Choose or track remaining work | [`WORKLIST.md`](WORKLIST.md) |
| Understand the goal, parts, decisions, and old-chat direction | [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) |
| See what is risky, broken, partial, or missing in code | [`reports/CODE_AUDIT_2026-10-17.md`](reports/CODE_AUDIT_2026-10-17.md) |
| See how delivered v1 works and how old-chat claims matched it | [`reports/KIT_LEARNING_AND_CHAT_MATCH.md`](reports/KIT_LEARNING_AND_CHAT_MATCH.md) |
| Check research findings and still-open questions | [`RESEARCH_AND_OPEN_QUESTIONS.md`](RESEARCH_AND_OPEN_QUESTIONS.md) |
| Find any file or the zip-deletion record | [`FILE_MAP.md`](FILE_MAP.md) |
| Find the separate Odysseus program source | [`ODYSSEUS_SOURCE.md`](ODYSSEUS_SOURCE.md) |

Shortest useful path: this README → handoff Sections 1–4 → audit short
verdict/P0 → worklist W-001 and the item you are considering.

## Current verdict

**V1 is coherent source, not yet a runtime-proven install.**

What lines up: the installer, `harness` command, model picker, local
dashboard, built-in skills, launchers, and guide mostly agree with each other.
Static checks found no syntax failure and no obvious placeholder feature.

What must not be overstated:

- OpenRouter free status is price-checked, but NVIDIA, Mistral, and Google are
  currently `assume_free` in the scout.
- Installer downloads/versions are not pinned and verified strongly enough.
- Helpers and kit secrets share one OS account; environment cleanup and skill
  instructions are not a complete security boundary.
- Some shell flows can report started/stopped/auto-merge-off after an OAT
  command failed.
- Model refresh can remain stale when key checks update state or when an
  already-running router is not restarted.
- Dashboard mutating jobs have no single-flight lock.
- Third-party skill installation can copy through symlinks.
- Dynamic roles/services, MCP, Odysseus/personas, extra providers, Docker,
  toolchains, and the lost test harnesses are absent from v1.

The full findings, evidence, and suggested fix order are in
[`reports/CODE_AUDIT_2026-10-17.md`](reports/CODE_AUDIT_2026-10-17.md). The
corresponding tasks are W-010…W-016 in [`WORKLIST.md`](WORKLIST.md).

## Folder map

```text
workbench/ai-team-kit/
├─ README.md                         This index
├─ SESSION_HANDOFF.md                Current state + next-session gate
├─ WORKLIST.md                       Single actionable queue
├─ PROJECT_CONTEXT.md                Goal, architecture, decisions, old-chat intent
├─ RESEARCH_AND_OPEN_QUESTIONS.md    Findings and Q/A status
├─ READING_GUIDE.md                  Section-by-section summaries for the owner
├─ FILE_MAP.md                       File locations + extraction record
├─ ODYSSEUS_SOURCE.md                Pointer to the separate Odysseus repo/pin
├─ kit/harness/                      Canonical extracted v1 source
├─ reports/                          Learning report + code audit
└─ archive/                          Original snapshots, former README, zip extras
```

There is no top-level zip anymore. The former duplicate
`AI-Team-Setup-Guide.md` was also removed; the only guide to edit in a future
guide task is `kit/harness/GUIDE.md`. A new distributable zip should be made
only in worklist item W-080, after the code and guide it contains are ready.

## Done / not done

### Done as delivered v1 source

- Installer and one `harness` command.
- Model scout for OpenRouter, NVIDIA, Mistral, and Google.
- Three stable roles: architect, implementer, reviewer.
- LiteLLM router-list generation and OAT connection helpers.
- Local dashboard for chat, tasks, files/changes, PRs, models, keys, skills,
  and logs.
- Two built-in skills with project-memory templates.
- Windows/Mac launchers and a beginner guide.

### Not done or not present

- Any audit fix (the audit was read-only for kit code).
- Writer/editor roles, dynamic endpoints/services, `add-endpoint`.
- MCP loader/apply, `harness mcp`, and dashboard MCP controls.
- Odysseus integration or persona room; only a source pointer exists.
- Groq, Cerebras, GitHub Models, Cloudflare, AI Horde, or Colab support.
- `toolchains.sh`, Docker packaging, and a harness-comparison verdict.
- Delivered dashboard/MCP test harnesses claimed in the old chat.
- A real install/runtime proof with the owner's keys, GitHub account, and
  target platforms.

## Tested / not tested

### Tested or verified in this restart

- Both zips were inventoried and compared byte-for-byte; extraction into
  `kit/harness/` and `archive/harness-zip-extras/` preserved their contents
  and modes.
- The delivered scout self-test was run **once** in an earlier owner-named
  task: Python 3.11.2, exit 0, **62 passed, 0 failed**, empty stderr, with the
  LiteLLM Router checks skipped. It was **not rerun** for the audit.
- Python AST parsing, `bash -n`, inline-JavaScript syntax checking, and
  command/route/action cross-checks all passed as static checks.
- The Odysseus pointer repo was inspected/read at a dated pin; it was not
  installed or run.

### Not tested here

Installer execution; LiteLLM; OAT; dashboard runtime; real providers, models,
keys, quotas, or terms; real GitHub login/PR/merge/close; Windows/WSL; macOS;
Codespaces; Odysseus; MCP; Docker. Old-chat “tested” statements remain
old-chat reports unless the learning/audit report explicitly reproduced them.

## Owner's next step

1. Review draft PR #3 and, if desired, use
   [`READING_GUIDE.md`](READING_GUIDE.md) for the short path.
2. Name **one** item from [`WORKLIST.md`](WORKLIST.md). The recommended order
   starts with P0 hardening and the missing tests, then fresh provider
   research, then the old v2 expansion slices.
3. If the reply is only “next” or “continue”, the agent must ask which `W-`
   item rather than guessing.

Standing rules: free/cloud models only; owner reviews and merges PRs;
beginner wording; downloadable results; read real files before editing; look
up current free-tier terms from official sources; never commit secrets or
runtime state.
