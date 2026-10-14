# Provenance

Every rule in `coding-agents/` traces back to one of three upstream sources.
This file records exactly what was taken from where, so the section can be
re-synced when upstream moves — and so nobody has to guess which parts are
ours.

---

## The three sources

### 1. Grug — [grugbrain.dev](https://grugbrain.dev/)

*"The Grug Brained Developer: A layman's guide to thinking like the
self-aware smol brained"* — Carson Gross (author of
[htmx](https://htmx.org/)).

- **Canonical URL:** https://grugbrain.dev/
- **Used in:** `philosophy/grug.md`, `variants/grug-reasoning.md`
- **What was taken:** the belief system — complexity as the apex predator,
  saying no, the 80/20 compromise, late factoring and "trapping the demon in
  crystal", the testing sweet spot, Chesterton's Fence, small refactors,
  expression complexity for debuggability, salt-not-main-course DRY/SoC,
  type systems as autocomplete, tooling and debuggers, profile-before-
  optimizing, layered APIs, logging, concurrency fear, fad scepticism, FOLD,
  and impostor syndrome.
- **What was condensed:** the essay is ~4,000 words of deliberate broken
  English. `philosophy/grug.md` preserves the substance and the best quotes
  but writes the connective tissue in normal prose, because the goal here is
  an agent instruction file, not a reprint.
- **Not taken:** grug's front-end opinions (htmx advocacy) and the
  microservices aside, which are not relevant to academic/office work.

### 2. Caveman — [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman)

*"why use many token when few token do trick."*

- **Canonical URL:** https://github.com/JuliusBrussee/caveman
- **Primary files read:** `skills/caveman/SKILL.md`, `README.md`,
  `AGENTS.md`, `CLAUDE.md`, `agents/agents.json`, `agents/profiles/qwen.json`,
  and the six work-pattern skills (`investigate-first`, `lean-build`,
  `surgical-patch`, `safe-refactor`, `migration`, `verify-and-stop`).
- **Used in:** `philosophy/caveman.md`, `variants/caveman-output.md`
- **What was taken:** the output rules verbatim in substance — drop
  articles/filler/pleasantries, fragments OK, no tool-call narration, the two
  token traps (invented abbreviations and arrows), "never add words to sound
  caveman", the ASD-STE100 clarity register, never compress code/commands/
  paths/errors, never drop negations, the intensity ladder, auto-clarity
  triggers, persisted-output-stays-normal, and the six work patterns.
- **Also borrowed:** the structural idea of `agents/profiles/*.json` plus an
  `agents.json` registry, which is why `coding-agents/` looks the way it does.
- **Not taken:** the proxy / CLI / engine (Go), the `wenyan-*` classical
  Chinese intensity levels, the cavecrew subagents, the browsing tooling, and
  the pixel-mode skill rendering. All are out of scope for a prompt-only
  repository.
- **Note:** this repo already carried a copy of the v1.9.x-era official skill
  at `caveman-universal/references/upstream/`. Upstream has since grown
  substantially (proxy, agent profiles, work patterns). `philosophy/caveman.md`
  is written against current upstream; the older copy is left in place as
  history.

### 3. Be Brief — this repository

- **Canonical files:** `.claude/skills/caveman-be-brief/SKILL.md`,
  `caveman-universal/references/upstream/official-caveman-skill.md`
- **Used in:** `philosophy/be-brief.md`, `variants/be-brief-output.md`
- **What was taken:** the deletion test, the cut lists (English and
  Indonesian), the never-cut list including genuine hedges, the code
  preservation rule, the two-modes internal/external split, the intensity
  levels, and the review-without-rewriting format.
- **Relationship to caveman:** be-brief is the official caveman deletion test
  applied to *documents* rather than agent chatter. The upstream official
  skill's "What never to cut" section is quoted almost directly.

---

## What is ours

These parts are this repository's own contribution, not upstream:

- **The layer resolution in [`conflicts.md`](conflicts.md).** The three
  sources do not describe how to combine themselves; the conflict matrix and
  the "grug decides, caveman measures, be-brief writes" split are ours.
- **`variants/unified.md`.** A fusion document that exists nowhere upstream.
- **The reward function** in
  [`skillopt-integration/`](../skillopt-integration/) — the encoding of all
  three philosophies as a scored, gateable training signal.
- **The Indonesian half.** Upstream caveman is English-only; the Indonesian
  cut lists and examples come from this repo's `caveman-universal/`.
- **The coding-agent packaging** in `coding-agents/` — profiles, generated
  packs, and the compile script.

---

## Re-syncing

Upstream caveman moves fast. To refresh:

1. Read `skills/caveman/SKILL.md` and `README.md` from
   [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman).
2. Update `philosophy/caveman.md` — it is the source of truth for
   `variants/caveman-output.md`.
3. Regenerate the packs: `python coding-agents/compile.py`
4. Re-run the SkillOpt tests: `pytest skillopt-integration/tests -q`

Grug's essay has been stable for years and rarely needs touching.

---

## Licensing

- Grug: original text © Carson Gross. Quoted here as brief excerpt with
  attribution; the essay is freely available at grugbrain.dev.
- Caveman: MIT (skill) + BSL-1.1 (runtime). The skill document — which is all
  this repo uses — is MIT.
- Be Brief: this repository, Unlicense (root) / MIT (`caveman-universal/`).
