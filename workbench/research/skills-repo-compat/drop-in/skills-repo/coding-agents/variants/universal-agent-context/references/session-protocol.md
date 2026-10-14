# Session protocol — phases, gates, breakpoints, journal

**Status:** universal (stack-agnostic). **Borrowed from:** the discipline of
`a5c-ai/babysitter` (MIT) — *process as code, mandatory stop between steps,
gates that block, breakpoints that need a human, an append-only journal* — and
re-expressed as markdown so it runs in any harness without installing a
runtime. It adds structure to v4; where it seems to conflict, v4 wins.

## Why not just install babysitter?

Babysitter's enforcement lives in harness hooks (Claude Code, Codex, Cursor…)
and a Node CLI. Arena Agent Mode runs neither, and v4 §13 prefers gates the
repository itself can run (`check_docs.sh`, `pr_preflight.sh`, a pre-push hook)
because those survive a change of harness. The *idea* is kept; the dependency
is not. If the owner later works from a harness babysitter supports, each
runbook below maps one-to-one onto a `process()` with `ctx.task` /
`ctx.breakpoint` calls — nothing here would need to be rewritten.

## The phases

Every non-trivial task walks these in order. A phase ends with a **stop**: a
short report in the turn, in the shape of §19 of v4, before the next phase
begins. The stop is what prevents "I planned, implemented and declared success
in one breath".

| # | Phase | Exit gate (must be true to proceed) | Typical evidence |
|---|---|---|---|
| 0 | **Recover** | Clean tree or the dirt is explained; project gates run (or named as not runnable here); base commit recorded | `git status`, gate output, SHA |
| 1 | **Recon** | Baseline written (v4 §3.3): stack, build/test commands, CI, package path, biggest verified gap, smallest next step | file:line citations, run IDs |
| 2 | **Plan** | Required outcome / constraints / preferences / exclusions / open decisions separated (v4 §2); slices listed; each slice names its proof level | the plan itself |
| 3 | **Breakpoint** (conditional) | Owner has answered, or the question is logged as open and work proceeds only on slices that do not depend on it | decision ID or "open" |
| 4 | **Implement a slice** | One cohesive change; diff reviewed for unintended deletions, secrets, duplicate-config drift | `git diff --stat`, review notes |
| 5 | **Verify the slice** | Proof at the ladder level the claim needs (v4 §6); red→green kept where a defect was fixed | test names, counts from *this* run, CI run ID |
| 6 | **Record** | Register/board/log updated in this session; new findings registered; gates green; **committed** | gate output, commit SHA |
| 7 | **Handoff** | §19.1 report; next concrete action; "Not verifiable here" line present | the report |

Loop 4→6 per slice. Scale down for tiny tasks (a one-line fix still does 0, 5,
6, 7) — never skip 6.

## Breakpoints — when the agent must stop and ask

Ask **before** acting when the choice would materially affect any of:

- architecture or framework choice; a new dependency or runtime;
- appearance or interaction design (show 2–3 genuinely different mockups first — v4 §10.6);
- product scope, including "while I'm here" additions;
- privacy, telemetry, network exposure, data-loss behaviour;
- compatibility: dropping a platform, changing a file format, CLI flags, exit codes;
- licensing or copying code from another project;
- deleting history, force-pushing, merging, tagging, publishing, releasing;
- anything the project's decision log already lists as an open owner question.

Everything else: make the reversible choice, label it as an assumption, and keep
going (v4 §2). A breakpoint that is skipped because "it was obvious" is logged
as a labelled assumption so the owner can reverse it cheaply.

## Gates — code beats prose

A gate is a command that exits non-zero. Prefer one that already exists in the
project. When adding one, make it check the repository rather than re-assert a
sentence (v4 §13.2), give it a `--selftest` or a fixture that proves it can
fail, and make it skip *loudly* with a named reason where it cannot run.

Minimum gate set for a session boundary, in this order: the project's doc/status
gate → unit/regression suites that exist → lint/sentinels → clean-tree check →
push → CI on the pushed SHA (quote the run ID, not a memory of one).

## Journal — what "recorded" means

The project's own history log is the journal (gifscythe: `IMPROVEMENT_LOG.md`,
template in v4 §19.2). Each entry has `Changed / Partial / Left / Verified / Not
verifiable here / Docs touched`. Git history is the replay; the log is the
index. Do not keep a second journal in the skill tree.

## Retrospective (the "what went wrong" session)

After a skill is used on a real task for the first time, the **next** session
starts with a retrospective, not with more features:

1. Re-run the previous session's claimed proofs from the committed tree (v4 §13.3 — "verified previously on revision X" is not "verified now").
2. List every place the skill was wrong, silent, or too noisy, as a *skill defect log*: `rule/section · what happened · evidence · proposed fix · promote to universal? (y/n, why)`.
3. Fix the skill, re-run its gate, and only then continue the project task.
4. Promote to v4 only the rules that held without project details attached (v4 §17.6) — as a versioned bump, never an in-place edit.

The owner's workbench keeps the runbook for such a session under the project's
`projects/<name>/` pointer; the first one was written for the Qt proving ground.
