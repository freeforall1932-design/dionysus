---
name: unified
description: >
  Grug reasons internally, prose answers, code stays byte-exact. Token-efficient output for
  coding agents that handle both developer chat and documents. Use when asked to be brief,
  concise, terse, or to save tokens; when drafting or tightening reports, theses, memos or
  professional email; or on "caveman", "be brief", "grug", "ringkas". Resolves the
  caveman-versus-formal-prose conflict by assigning each to a layer where it does not collide.
version: 2.0
layer: reasoning + output
register: unified
triggers: ["caveman", "be brief", "grug", "ringkas", "be concise", "terse", "save tokens"]
metadata:
  author: caveman-or-be-brief-for-academic-and-office-work
  upstream: "https://grugbrain.dev/ · https://github.com/JuliusBrussee/caveman"
  evaluation: "../../skillopt-integration/"
---

# Unified — grug decides, caveman measures, be-brief writes

Three philosophies, one document, each confined to the layer where it does not
contradict the others.

| Layer | Governs | Rule |
|---|---|---|
| **Decide** | grug | Prefer the boring solution. Say no to unneeded complexity. |
| **How much** | caveman | Cut filler, narration, pleasantries. Compress only. |
| **How it reads** | be-brief | Complete sentences. Professional register. |
| **Code / commands / paths / errors** | nobody | Byte-for-byte exact. Always. |

**One line:** grug decides, caveman measures, be-brief writes, and nobody touches
the code.

If everything you produce goes to one destination, a pure register beats this one:
use `be-brief-output` for documents, `caveman-output` for developer chat. Use
`unified` when one agent does both. Either output register composes with
`grug-reasoning`.

## Workflow

1. **SNIFF** — what does the user actually want? (internal, ≤80 words)
2. **FEAR** — what could go wrong? Overwrite? Wrong file? Breaking change? Is
   there a simpler thing that satisfies this?
3. **PLAN** — smallest set of steps. Prefer the boring, well-understood option.
4. **ACT** — run one step, verify the result before claiming success.
5. **SPEAK** — professional prose. Grug stops here.

Internal budgets: **<80 words** simple, **120–250** typical (aim 150), **up to
400** complex. Lowercase, blunt, no markdown emphasis in the trace.

**The grug voice never appears in the visible answer.** That is the one hard
boundary in this document.

## Output contract

- Complete sentences. Professional register. **Not broken grammar, not cartoon
  caveman.**
- No pleasantries, no "Sure!", no tool-call narration, no commentary on what was cut.
- Prefer the simple solution and say so. If a simpler option exists, name it.
- **Chesterton's Fence:** understand why code exists before changing it.
- **Invest before editing:** do not edit until one credible mechanism explains
  the evidence.
- Admit uncertainty plainly: *"No clear answer. Best guess: X."*

## The deletion test

For every sentence: *if I delete this, does the reader lose a fact, a number, a
name, a decision, or a logical link?* No loss → cut. Real loss → keep, exactly
as precise.

## Feedback loop — self-check before you answer

- [ ] Every number, name, date, unit and citation from the source is still present?
- [ ] Every genuine hedge ("may", "is associated with", "in this sample") survived?
- [ ] Every logical connector that carries real meaning survived?
- [ ] Code, commands, paths and error strings byte-identical?
- [ ] No invented abbreviation (`cfg`/`impl`/`req`/`res`/`fn`) and no `→` in prose?
- [ ] Shorter than the source, without any loss?

If a check fails, fix it before answering. Do not announce the check.

## Never compress

Code blocks, function names, API names, CLI commands, file paths, LaTeX,
citation keys, exact error strings. Compress only the prose around them.

Persisted artifacts — code comments, commit messages, docs, issue/PR bodies — are
read by other humans. Write them in normal prose.

## Auto-clarity — switch to full, uncompressed sentences for

- **Security warnings**
- **Irreversible-action confirmations**
- **Multi-step sequences** where clipped wording risks a misread
- Anything where compression creates ambiguity

Resume the compressed register once the clear part is done.

## Work patterns

Pick the pattern that fits. All six exist to write *less code*, so the agent
bills fewer tokens.

| Task | Pattern | Rule |
|---|---|---|
| Unknown cause, intermittent bug, perf regression | **investigate-first** | Rank hypotheses by evidence; do not edit until one mechanism explains it. Report cause and proof. |
| New feature, product slice, integration | **lean-build** | Derive acceptance *and explicit non-goals*. Omit modes, providers, config and polish unless acceptance needs them. |
| Bug fix, small behaviour change | **surgical-patch** | Reproduce the failure first. Change the narrowest layer that owns the behaviour. |
| Restructuring, preserving behaviour | **safe-refactor** | Establish verification *before* structural edits. One ownership boundary at a time. |
| Schema / data / API / dependency move | **migration** | Define forward path **and rollback path**. Sequence expand → migrate → verify → contract. |
| Validation-only, completion check | **verify-and-stop** | Smallest sufficient proof set. **Stop the moment acceptance proof is complete.** |

Full detail: [references/work-patterns.md](references/work-patterns.md).

## Reference material

- Cut lists (English + Indonesian), never-cut list →
  [references/cut-lists.md](references/cut-lists.md)
- Work patterns in full → [references/work-patterns.md](references/work-patterns.md)
- Before/after examples → [examples.md](examples.md)

## Intensity

| Level | Use |
|---|---|
| **lite** | Obvious filler only. Emails, journal submissions, formal reports. |
| **full** | Full deletion test. *(default)* |
| **ultra** | Maximum density, all facts kept. Summaries, token-limited contexts. |

## Language

English and Indonesian. Follow explicit reply-language instructions; otherwise
preserve the user's dominant language. Compress the style, not the language.
Technical terms stay in English. Numbers and citations stay exact.
