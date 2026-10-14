# Where grug, caveman, and be-brief conflict

The three philosophies in this repo are usually presented as a stack — grug
thinks, caveman speaks, be-brief writes. That story is *mostly* true, but it
glosses over real contradictions. This document states them plainly, because
"just combine them" produces a skill that fails in both directions at once.

---

## The short version

| | Grug | Caveman | Be Brief |
|---|---|---|---|
| **Domain** | Reasoning / deciding | Output to an agent user | Output to a document reader |
| **Register** | lowercase, blunt, deliberately ungrammatical | terse, fragments OK, articles optional | professional prose, full grammar |
| **Grammar** | broken, on purpose | broken, if shorter | **never** broken |
| **Articles** | n/a | dropped when cheap | kept |
| **Audience** | the model itself | the developer driving the agent | a human reading a finished artifact |
| **Persisted files** | n/a | code/comments/commits = normal prose | documents = compressed prose |
| **Failure mode** | over-abstraction, FOLD | ambiguity from over-compression | timidity — not cutting enough |

The single hardest conflict: **caveman says "fragments OK, drop articles";
be-brief says "professional prose, never broken grammar".** These cannot both
govern the same sentence. One of them has to win, and *which* one depends on
where the text is going.

---

## Conflict 1 — Output register (the big one)

**Caveman** (`skills/caveman/SKILL.md`, upstream):

> Drop: articles (a/an/the), filler… Fragments OK. Short synonyms…
>
> Never add word to sound caveman. **Compression only style never grow output.**
> No inserted pronoun or copula to fake broken grammar: "when it not" cost one
> token more than "when not" and say same thing.

**Be Brief** (this repo, `caveman-be-brief`):

> ### MODE 2: EXTERNAL OUTPUT (PROFESSIONAL VOICE)
> Voice: formal, academic, polite, precise, nuanced
> Style: professional prose with zero wasted words — **NOT broken grammar,
> NOT cartoon caveman speech**

**Why both are right.** They optimise for different readers. A developer
watching an agent stream tool calls wants the diagnosis in nineteen tokens. A
thesis examiner reading chapter four does not. Caveman's own upstream README
says the quiet part out loud: *"Caveman no make brain smaller. Caveman make
mouth smaller."* It is a mouth, not a pen.

**Resolution.** Pick by destination, not by vibe:

| Destination | Winner |
|---|---|
| Chat reply to a developer | caveman |
| Thesis, journal, report, memo, professional email | be-brief |
| Code, commands, paths, error strings | neither — untouched |
| Persisted artifacts (comments, commits, docs, issue bodies) | neither — normal prose |

**Do not** put both in one skill without this table. An unqualified "be terse"
next to "never break grammar" is a coin flip on every sentence.

---

## Conflict 2 — Verbosity vs completeness

**Caveman** cuts articles and conjunctions. **Be Brief** keeps every logical
connector:

> **Real logical connectors** — "because", "although", "therefore", "however"
> tell the reader how two ideas relate. That's information, not filler.

**Why it matters.** "Inline obj prop, new ref, re-render. `useMemo`." is
perfect for a developer who can reconstruct the causality. The same sentence
in a methodology section is a defect — the reader cannot tell whether the
re-render causes the new ref or the reverse.

**Resolution.** Caveman is allowed to drop a conjunction **only where
cause-and-effect stays unambiguous** (that is literally its `ultra` level).
Be Brief never does. When in doubt, keep the connector — it is one token, and
ambiguity costs a reader minutes.

---

## Conflict 3 — Grug's voice: internal or not at all

**Grug** is written to be *read*. It is a published essay in a deliberately
broken register: "complexity very bad", "grug no able see complexity demon".
Its whole rhetorical power comes from that voice.

**Be Brief** says the grug voice must never reach the user:

> NEVER output Grug voice to user. Internal only.

**Caveman** is adjacent to grug but is not grug — it is about *mouth*, not
about *simplicity as a decision rule*. Caveman will happily emit a long
technical explanation in fragments; grug would first ask whether you need the
feature at all.

**Resolution.** Three layers, one boundary:

```
grug      → reasoning   (never emitted)
caveman   → how much    (how terse the emitted text is)
be-brief  → how it reads (register of the emitted text)
```

Grug is a **layer**, not a style you can mix into prose. This is why
`variants/grug-reasoning.md` ships as a reasoning-only document with no output
rules at all, and why the reward function in
`skillopt-integration/` treats any grug token in visible output as a hard
failure.

---

## Conflict 4 — "Say no" vs "just answer"

**Grug**: *"No, grug not build that feature."* Complexity is the enemy; the
answer to most requests is a smaller version of the request.

**Caveman/Be Brief**: both are **output** philosophies. Neither has an opinion
on whether the work should be done. They will compress a twenty-page design
doc for a feature that should not exist.

**Resolution.** Grug runs *first*, in the reasoning trace, and has veto power.
Then the output philosophy governs how the answer is phrased. In the unified
variant this is the `FEAR` stage: *what could go wrong? is there a simpler
thing that satisfies this?* — asked before any text is emitted.

---

## Conflict 5 — When *not* to compress

Both caveman and be-brief agree that compression yields to clarity, but they
draw the line differently.

**Caveman** auto-clarity: security warnings, irreversible-action
confirmations, multi-step sequences where fragment order risks a misread,
compression creating technical ambiguity.

**Be Brief** adds: legal disclaimers, genuine hedges, required structure, and
— most importantly — **entire document types** (casual chat, emotional
support, creative writing).

**Resolution.** Take the union. Be Brief's scope exclusions are a superset and
should win, because its downside is worse: an ambiguous agent reply gets a
clarifying question, whereas an ambiguous thesis paragraph gets a bad grade.

---

## The unified resolution

`variants/unified.md` fuses them by assigning each philosophy to the layer
where it does not conflict with the others:

| Layer | Governing philosophy | Rule |
|---|---|---|
| **Decide what to do** | grug | SNIFF → FEAR → PLAN → ACT → SPEAK. Prefer the boring solution. Say no to unneeded complexity. |
| **How much text** | caveman | Cut filler, narration, pleasantries. Drop articles only when meaning stays clear. |
| **How the text reads** | be-brief | Complete sentences, professional register, all logical connectors kept. |
| **Code / commands / paths / errors** | neither | Byte-for-byte exact. Always. |
| **Persisted artifacts** | neither | Normal prose — they are read by other humans. |
| **Security / irreversible / ambiguous** | auto-clarity | Full uncompressed sentences, then resume. |

The one-line version: **grug decides, caveman measures, be-brief writes, and
nobody touches the code.**

---

## If you only remember one thing

Training all three into a single document is what
`skillopt-integration/configs/default.yaml` does, and it works — but the
reward function has to score *per register*, or the optimizer averages the
conflict away and produces mush. That is why the environment carries a
`register` field on every item and why the per-variant configs
(`be-brief.yaml`, `caveman.yaml`, `grug.yaml`, `coding-agent.yaml`) train them
separately.

**If your output goes to one destination, use a pure variant. If it goes to
developers and documents alike, use `unified` and keep the layer table above
handy.**

---

## `unified` + `universal-agent-context` (added 2026-10-14)

Load both. `universal-agent-context` is a **process** skill: it fixes what must
exist and be verified before "done" — inspection before change, the
verification ladder, commit before the session ends, the mandatory
"Not verifiable here" line, a UI behaviour contract before any widget.
`unified` is the **register**: how the visible reply reads and which of several
acceptable solutions to prefer.

Precedence: owner instruction → repository evidence → process layer → workload
skill → register.

Three readings that look like conflicts and are not:

- **verify-and-stop** ends at the process layer's close duties (commit, log,
  "Not verifiable here"), not before them. "Stop" means "start nothing new".
- The **"Not verifiable here" line is a fact and a decision**, so it always
  passes the deletion test; cutting it fails the test.
- Registers, logs, commit messages and PR bodies are **persisted artefacts** and
  are written in normal prose — `unified` already says so.

Evidence and the longer table: the dionysus workbench page
`research/skills-repo-and-unified-2026-10-14.md`.
