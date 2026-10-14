# The universal skill, the `unified` register, and the owner's skills-repo

**Date:** 2026-10-14 · **Session scope:** three questions from the owner —
keep projects/skills separable for other agents, does `universal-agent-context`
work with skills-repo's `unified`, and is skills-repo worth growing into a
catalog. **Inputs:** `freeforall1932-design/skills-repo` @ `84c9518` (Unlicense),
`freeforall1932-design/SkillOpt-fork` @ `343db22`, this repository's
`skills/universal-agent-context` (v4 sha256 `51f21f33…`). **Executed evidence:**
section 4 and `research/skills-repo-compat/README.md`. **Nothing was pushed to
skills-repo or SkillOpt-fork.** Statements are labelled *observation* (read or
measured), *inference* (follows from read code but was not executed) or
*proposal* (design, not verified).

---

## 1. Two different things are called "unified"

| Where | What the word means | Evidence |
|---|---|---|
| `UNIVERSAL_AGENT_CONTEXT_v4.md`, Appendix A | the v4 guide itself: "v4 unified" = the merged process guide | observation — Appendix A heading in the pinned copy |
| `skills-repo/coding-agents/variants/unified/SKILL.md` | a **writing register**: "Grug reasons internally, prose answers, code stays byte-exact" | observation — frontmatter line 4 |

They are not competing names for one thing; they are two layers that happen to
share a word. **Recommendation:** in prose and file names, call the process
layer *universal* (it already is: `universal-agent-context`) and the skills-repo
variant *the unified register*. Do not edit v4 to fix the heading — v4 is
hash-pinned and the heading is historical. `skills/README.md` carries a
one-line note so the next agent does not conflate them.

---

## 2. Does `universal-agent-context` work with the `unified` register?

**Yes, by destination.** The two documents govern different things and the
composition rule is one sentence: *unified decides how the visible answer reads
and which of several acceptable solutions to prefer; universal decides what must
exist and be verified before "done" may be said.* Everything below is the
evidence that this sentence holds, including the five places where the texts
look like they collide.

### 2.1 Division of labour (quoted)

| Concern | `unified` says | universal (v4 + references) says | Who governs |
|---|---|---|---|
| Visible reply length and register | "Complete sentences. Professional register." · "Internal budgets: **<80 words** simple, **120–250** typical" | nothing about word budgets | unified |
| Choosing between acceptable designs | "Prefer the boring solution. Say no to unneeded complexity." | v4 §0 "Scale the process to the task. A one-line fix needs focused verification, not a research program." | both agree; unified picks *within* the acceptance set universal defines |
| What counts as done | "**verify-and-stop** — Smallest sufficient proof set. **Stop the moment acceptance proof is complete.**" | v4 §6 "report at the correct level"; §13.5 Definition of done; §16 "**Never** report a build/test/PR/artifact as successful without executed evidence" | universal defines the proof set; unified stops exactly there |
| Code, commands, paths, errors | "Byte-for-byte exact. Always." | v4 §16 "Report changed files, executed commands, toolchains/platforms, test and CI results, run IDs/links, artifact paths" | identical intent |
| Uncertainty | "Admit uncertainty plainly: *'No clear answer. Best guess: X.'*" · self-check: "Every genuine hedge … survived?" | v4 §19.2 "The 'Not verifiable here' line is mandatory and must never be omitted or softened." | identical intent; universal makes one hedge *structural* |
| Persisted artefacts | "Persisted artifacts — code comments, commit messages, docs, issue/PR bodies — are read by other humans. Write them in normal prose." | v4 §19 session-log template; §13 status registers; `references/session-protocol.md` journal rules | unified explicitly hands these to universal |

### 2.2 Apparent conflicts and how each resolves

| # | `unified` text | universal text | Resolution |
|---|---|---|---|
| 1 | Deletion test: "if I delete this, does the reader lose a fact, a number, a name, a decision, or a logical link? No loss → cut." | v4 §19.2: the "Not verifiable here" line is mandatory. | No conflict once read precisely: the line *is* a decision and a fact (what was not run, and why). Unified's own self-check keeps "every genuine hedge". An agent that cuts it has failed the deletion test, not passed it. |
| 2 | "No pleasantries, no 'Sure!', no tool-call narration, no commentary on what was cut." | v4 §13 truth maintenance: close items in the register, record what was deferred; §4.2 "Commit every edit before the session ends". | "Commentary on what was cut" is about the *reply's* prose, not the project's registers. The register entries are persisted artefacts, which unified explicitly writes "in normal prose". No conflict. |
| 3 | verify-and-stop: "Stop the moment acceptance proof is complete." | v4 §16/§19: session close = commit, push, log, Not-verifiable line; `references/session-protocol.md` exit gates. | Close duties are **part of the acceptance set**, not work after it. "Stop" means "do not start a new investigation", not "skip the commit". State this once in the composition note (2.4) so a model does not read it the other way. |
| 4 | grug: "Say no to unneeded complexity." · lean-build: "Omit modes, providers, config and polish unless acceptance needs them." | v4 §10 "Reference-driven UI (mandatory when appearance matters)" — "two or three meaningfully different, low-cost mockups"; `references/ui-behaviour-contract.md`: the contract "must exist before any widget is drawn". | The contract and mockups are acceptance criteria for UI tasks, so lean-build's own rule ("unless acceptance needs them") keeps them. Grug decides *which* of the two or three mockups and how small the engine interface is; it does not decide whether the table exists. |
| 5 | Per-turn loop SNIFF → FEAR → PLAN → ACT → SPEAK with internal budgets. | Per-session loop: recover state → inspect → plan → act → verify → report (v4 §1–§3, §16; session-protocol phases). | Different time scales; the per-turn loop nests inside each per-session phase. FEAR ("what could go wrong") is exactly where v4's "inspect before changing" and the breakpoints list get consulted. |

Two further places where they simply agree and reinforce: "Invest before
editing: do not edit until one credible mechanism explains the evidence"
(unified) ≡ v4 §0 "Inspect before changing … Never infer the stack from a
README"; and unified's auto-clarity list (security, irreversible, multi-step)
≡ the breakpoint list in `references/session-protocol.md`.

### 2.3 Precedence when something new collides

owner's latest explicit instruction → repository evidence (build files, CI,
registers) → universal process (v4, protocol, contract) → workload skill →
register (`unified`). The register is last because it never changes *what* is
true or required, only how it is said. This is the same order as
`skills/README.md` plus one trailing entry.

### 2.4 Drop-in composition note (for skills-repo, not applied)

Text the owner can paste into `skills-repo/coding-agents/philosophy/conflicts.md`
or into a new `coding-agents/philosophy/with-universal.md`; it is deliberately
short enough to survive the deletion test.

> **`unified` + `universal-agent-context`.** Load both. `universal-agent-context`
> is a process skill: it fixes what must exist and be verified before "done"
> (inspection, verification ladder, commit before session end, the mandatory
> "Not verifiable here" line, UI behaviour contract before any widget). `unified`
> is the register: how the visible reply reads and which of several acceptable
> solutions to prefer. Precedence: owner instruction → repository evidence →
> universal process → workload skill → register. "Verify-and-stop" ends at the
> universal close duties, not before them; the "Not verifiable here" line is a
> fact and a decision and therefore always passes the deletion test; registers,
> logs, commit messages and PR bodies are persisted artefacts and are written in
> normal prose.

---

## 3. What skills-repo is today (observation)

- **Audience split.** The top-level README is the Claude-app side ("Caveman or
  Be Brief — for Academic & Office Work", EN + ID zips, combos, intensities).
  `coding-agents/` is the harness side: four variants (`unified` recommended;
  `be-brief-output`; `caveman-output`; `grug-reasoning`), a compiler, seven
  harness profiles, tests, and `philosophy/conflicts.md` as the designated
  start file.
- **The compiler is the asset.** `coding-agents/compile.py` (586 lines) reads
  `variants/*/SKILL.md` + `profiles/*.json` and writes `packs/<agent>/` for
  claude, codex, qwen, qwen-agent, cursor (`.mdc`), copilot, opencode, plus a
  deterministic zip (fixed 1980 timestamps). CI compiles, runs the tests and
  **fails if the committed packs are stale** — so the packs are always
  consistent with the sources. Measured: 33 tests pass at `84c9518`; a second
  compile produces a zero-line `git status`.
- **Evaluation is wired in.** `skillopt-integration/` is a SkillOpt environment
  (`caveman_brief`) whose evaluator scores an answer deterministically for facts
  kept (`must_keep`), hedges preserved, code byte-exact, compression ratio and
  register; `configs/coding-agent.yaml` trains the `unified` seed
  (`initial_coding_agent.md`). CI has a "SkillOpt reward function" job that
  scores a reference baseline. The seeds under `envs/caveman_brief/skills/` are
  **copies**, not reads of `variants/` — removing register variants does not
  break the environment (observation: no runtime reference to `variants/` in
  `skillopt-integration/` outside a README comment).

---

## 4. Compile dry run — can the universal skill live in skills-repo as-is?

Full table, commands and the patch: `research/skills-repo-compat/README.md`.

| Configuration | Result |
|---|---|
| Upstream compiler + our skill copied in as-is | Compiles with exit 0, **but `UNIVERSAL_AGENT_CONTEXT_v4.md` and `PROVENANCE.md` are absent from all seven packs**; the packed SKILL.md still tells the agent to read them. Paste file 19 KB. 3 of 34 tests fail (Cursor rule count hard-coded to 4; `examples.md` required by a house rule). |
| Upstream compiler, v4 moved under the skill's references directory | v4 arrives byte-identical in the claude/qwen/codex skill dirs, **but every paste file becomes 75,086 bytes / 930 lines** (vs 10,799 for `unified`) because references are inlined — the whole guide billed on every request, which is the opposite of what a loader skill wants. |
| Patched compiler (`compile-skill-assets.patch`, 242 lines) + `universal-agent-context` + `qt6-cmake-cpp` | 7 agents × 6 variants; **36 tests pass**; v4 sha256 identical to source in the skill dirs; `qt_lint.py` sha256 identical and its self-test passes from inside the pack; all 8 templates present; paste files are 3,375 B (universal) and 8,746 B (qt6) — body plus a file list, nothing inlined. |
| Patched compiler, upstream variants only | Generated packs byte-identical to upstream (`git status` empty); 33 passed, 1 skipped. The patch is a no-op for the existing registers. |

What the patch changes, in one line each: variants are discovered from the
directory (new skill = new folder, no edit to `VARIANT_ORDER`); every file
beside SKILL.md that is not a one-level markdown reference is copied verbatim
into the skill dirs; a skill with `metadata.paste: loader` (or any such files) is
pasted as body + file list; tests derive the Cursor count from the discovered
variants and accept "examples.md or support files". Both dionysus skills now
declare `metadata.paste: loader` and `metadata.layer` in their frontmatter;
this is valid YAML, parses under the Agent Skills spec check in their test
suite, and is ignored by harnesses that do not know the key (inference for the
harness side — see section 7).

**Answer:** as-is, no — the compiler silently produces a broken skill. With a
242-line, test-covered, backward-compatible patch, yes, and the same patch is
what makes any future workload skill with templates or scripts shippable.

---

## 5. Is skills-repo of any use? Assessment

**Yes — as the catalog, compiler and evaluation harness. Not as the proving
ground.** The things that make it worth keeping are exactly the things dionysus
does not have: seven verified install surfaces generated from one source, a CI
rule that keeps generated packs honest, and a scored environment for tuning a
skill's wording. The things it does not have — projects to apply skills to,
executed evidence, per-project overlays — are what `workbench/` has.

### 5.1 The owner's plan, checked against the code

| Plan item | What it touches | Verdict |
|---|---|---|
| Remove `caveman-output`, `grug-reasoning`, `be-brief-output` | `unified` is self-contained (its SKILL.md repeats the three layers; references are its own). Must also edit: `VARIANT_ORDER/LABEL/BLURB` (or apply the patch, after which only the folders matter), `tests/test_compile.py` (`VARIANT_KEYS` at line 24 and the literal tuple at line 202), `coding-agents/README.md`, the top-level README's "never both" rules, `skillopt-integration/configs/{be-brief,caveman,grug}.yaml` (orphaned, harmless). | Safe. Keep the Claude-app zips only if the office/academic audience is still wanted; they are a separate product. |
| Put the unified/universal skill there | After the patch: copy `skills/universal-agent-context/` and `skills/qt6-cmake-cpp/` into `coding-agents/variants/`, move `skills/validate_skills.py` with them (it needs `KNOWN_ROOTS` extended with `variants`/`coding-agents`), keep the v4 hash pin. | Do it, with the patch applied first; without it the pack is broken (section 4). |
| Alongside SkillOpt "with documented synergies as an example" | The real synergy is narrow and already exists: SkillOpt tunes the **register** (`unified`) against the `caveman_brief` scorer. The **universal** skill must stay hand-maintained and hash-pinned — an optimiser that rewrites the verification ladder to score better on a compression rubric is a defect, not an improvement. A second, honest synergy is *proposal* only: a `process_report` environment that scores a session report for "every success claim has an executed command or run ID", "Not verifiable here present", "paths byte-exact" — the same deterministic-metrics style as `evaluator.py`, needs a labelled dataset that does not exist yet. | Document the first; label the second as proposal in the README rather than promising it. |
| Grow into a catalog: "whenever I want there's always a skill for it" | Needs three things the repo lacks and `workbench/` has prototyped: a triage index with `read_when/skip_when` per skill (`index.json` + the README table), a gate that fails when a skill is added without an index entry (`validate_skills.py` → `check_index`), and a layer tag per skill so an agent loads at most one register, one process skill and the workload skills that match the repo. | Feasible; section 6 gives the layout. |

### 5.2 What would make the catalog *not* useful

- Skills whose descriptions do not say when **not** to load them. Both
  dionysus skills now carry a "Not …/Skip when …" clause in `description` for
  this reason; the catalog gate should require one.
- Packs that drift from sources — already prevented by the stale-pack CI rule;
  keep it.
- A proving ground inside the catalog. Executed evidence (dry runs, defect
  logs, experiments) is project-specific and dated; it belongs next to the
  project pointer in `workbench/projects/<name>/`, pinned to a catalog commit,
  not in the catalog itself.

---

## 6. Recommended layout and migration (proposal; not executed)

```
skills-repo/                               ← the catalog
  coding-agents/
    compile.py, profiles/*.json, packs/     (unchanged roles; patch applied)
    variants/
      unified/                              register   (paste: flatten)
      universal-agent-context/              process    (paste: loader, hash-pinned v4)
      qt6-cmake-cpp/                        workload   (paste: loader, templates + lint)
      <next workload skill>/                workload
    index.json                              one entry per variant: kind, layer, entry,
                                            read_when, skip_when, session_added, last_verified
    tests/test_compile.py                   + a test that index.json covers variants/ both ways
    validate_skills.py                      moved from workbench/skills, KNOWN_ROOTS += variants
    philosophy/conflicts.md                 + the composition note from §2.4
  skillopt-integration/                     unchanged; configs for removed registers deleted

dionysus/workbench/                        ← the proving ground
  projects/<name>/                          overlays, dry runs, defect logs, experiments,
                                            each README pinned to skills-repo@<commit>
  research/                                 dated surveys and assessments (this file)
  tools/                                    standalone utilities
  index.json + README triage table          unchanged mechanism
```

Migration order (each step leaves both repos green):

1. Apply `compile-skill-assets.patch` to skills-repo; CI stays green (packs
   unchanged, 33 passed + 1 skipped).
2. Copy the two skills in; recompile; commit packs; CI green (36 passed).
3. Move `validate_skills.py` + `index.json` + `check_index` over; wire into
   `tests.yml` after the compile step.
4. Remove the three registers and their mentions (table in 5.1); recompile.
5. In dionysus: replace `workbench/skills/*` with a pointer file naming the
   skills-repo commit, keep `workbench/projects`, `research`, `tools`, keep the
   loader `AGENTS.md`/`CLAUDE.md` pointing at the installed pack. Until step 5,
   dionysus remains the source of truth for the two skills — do not maintain
   both copies.

---

## 6a. Same-day follow-up: the drop-in bundle exists

The owner asked for a folder to paste. `research/skills-repo-compat/drop-in/`
is the final-state catalog built on `84c9518`: steps 1–4 of the migration
above are done inside it (patched compiler and tests, both skills in, the three
registers out, `index.json` + `validate_skills.py` wired into `tests.yml`),
plus eight harness profiles updated from the vendors' repositories
(`research/harness-skill-support-2026-10-14.md`). Verified by copying it onto a
fresh clone: 35 tests, gate 124 passed, packs stable across recompiles,
SkillOpt tests unchanged. `drop-in/APPLY.md` has the three commands. Step 5
(making dionysus point at the catalog instead of carrying the skills) is still
the owner's call; until then `workbench/skills/` is the source and the gate
fails if the drop-in copies drift from it.

## 7. Not verifiable here

- **Harness behaviour with extra frontmatter keys.** `metadata.paste` and
  `metadata.layer` parse as YAML and pass skills-repo's spec test; whether each
  of the seven harnesses ignores unknown keys silently was not executed (no
  harness binaries in this sandbox).
- **Live install.** The packs were generated and inspected, not installed into
  Claude Code, Codex, Qwen Code, Cursor, Copilot or OpenCode.
- **The qt6 asset drop under the unpatched compiler** was inferred from
  `compile.py`'s copy loop, not executed as a separate experiment; the executed
  evidence is the v4/PROVENANCE drop for the universal skill (same code path).
- **SkillOpt on process skills** (the `process_report` environment) is a
  proposal; no dataset, scorer or run exists.
- **Owner-side removals** (registers, README edits, config deletions) were
  listed from the code, not performed.
- Clones used: skills-repo `84c9518`, SkillOpt-fork `343db22`; both shallow,
  both in `/tmp`, both discarded at session end. Nothing was pushed to either.
