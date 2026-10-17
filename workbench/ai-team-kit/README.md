# AI Team Kit — next session starts here

> **STOP — read this before doing anything.**
>
> Status on **2026-10-17**: **WAITING FOR THE OWNER'S FILES.**
>
> The v1 kit (`ai-team-kit.zip`) and the four handoff notes (`HANDOFF.md`,
> `PROVEN.md`, `OPEN.md`, `FILES.md`) are **not in this repository and did
> not arrive in the 2026-10-17 restart chat's workspace**, even though the
> owner believed they were attached. Until they are committed to this folder
> (or attached in chat), the only allowed work is: receive the files,
> compare them with `FILES.md`, list the zip without changing it, and run
> the model picker's selftest once as a baseline. Do not start research,
> do not start building v2, and do not regenerate kit files from memory.
>
> The owner names **one task at a time**. If the owner sends only "next"
> or "continue", ask which numbered task they mean (see the work queue).

This folder is the isolated home of the **AI Team Kit** project inside the
`dionysus` repository. Paths in this README are relative to the repository
root unless they say otherwise.

- Folder created: 2026-10-17 (owner's restart session)
- Repository base commit when this README was written: `cc8aa83`
- Session branch when this README was written: `arena/5bf33a0c-dionysus`
  (once this README is merged, use whatever branch the current session is
  actually on — check with `git branch --show-current`, never assume)

---

## 1. The project in one minute (plain words)

The owner wants an **"AI team"** that is:

- **Free models only, cloud APIs only** — the AI helpers run on free
  internet services; no paid models, no models running on the owner's PC
  as the core plan.
- **Beginner-friendly** — the owner should not have to memorize many
  terminal commands; simple buttons and plain wording are requirements,
  not extras.
- **Working through GitHub pull requests** — the helpers prepare changes
  as pull requests (PRs). **The owner reads and merges them.** Nothing may
  merge itself behind the owner's back.

Version 1 was reportedly delivered in the old chat as `ai-team-kit.zip`
plus a setup guide. According to that chat, v1 contains: OAT helpers (the
workers), a LiteLLM router (one doorway that can send requests to several
AI services), a model picker (`model_scout.py`) that finds and tests
currently-free models, a browser dashboard, and install scripts.

Version 2 (not designed yet, not built yet) is where these open wishes
belong: more model sources, a native "room" with personas for writing and
daily use, an orchestrator with specialist sub-agents, and MCP tools for
the pull-request team as well.

### Small glossary

| Word | Plain meaning here |
|---|---|
| OAT | The helper program reportedly used by the v1 kit to run the pull-request team. Do not guess its commands — read them from the real kit/guide when it arrives. |
| LiteLLM router | A middleman program. The helpers always talk to it using steady job names (for example architect / implementer / reviewer); it forwards each job to whichever free service is currently chosen, and can rotate API keys. |
| Model picker / scout | `model_scout.py` in the kit. It reportedly looks for currently-free models, tests them politely (paced, not all at once), ranks them per job, and rewrites the router's settings. |
| Dashboard | A local web page (buttons instead of commands) reportedly delivered in v1: chat, tasks, files, change counters, pull requests, models, keys, skills, logs. |
| Harness | The program the owner actually sits in front of (for example OAT, Odysseus, OpenCode, Goose). Which harness should do what in v2 is still undecided (Step 3). |
| MCP | A standard way to give an AI outside tools (GitHub, web search, step-by-step thinking, …) through a list file like LM Studio's `mcp.json`. |
| PAT | A GitHub "personal access token" — a password-like key that lets a program act on the owner's GitHub account with only the permissions the owner ticked. |
| Native install | Installed directly in Ubuntu/WSL, not inside Docker. |
| Persona "room" | A chat space where different made-up helpers (writer, editor, game designer, …) each have their own instructions, and the owner swaps the model behind each one. Not built yet. |
| Sandbox | The temporary computer an AI chat works on. A fresh chat starts with an empty one — nothing installed in an old chat exists in a new chat. |

---

## 2. What the next session NEEDS from the owner (the blocker)

Commit these files **unchanged** into `workbench/ai-team-kit/` — do not
unzip and re-zip the kit, so it can be compared with `FILES.md` exactly as
delivered:

| # | File | Here yet? (2026-10-17) |
|---|---|---|
| 1 | `HANDOFF.md` | ❌ Missing |
| 2 | `PROVEN.md` | ❌ Missing |
| 3 | `OPEN.md` | ❌ Missing |
| 4 | `FILES.md` | ❌ Missing |
| 5 | `ai-team-kit.zip` (the delivered v1) | ❌ Missing |
| 6 | `AI-Team-Setup-Guide.md` — only if it was a separate download and is **not** already inside the zip (the old chat showed it as a separate file) | ❌ Missing / unknown |

Also useful **only if the owner still has local copies** (the owner has
said these were never delivered and are gone, so expect "no"): the patched
`model_scout.py`, the MCP loader/apply files, the dashboard test files.
If they truly are gone, Step 4 rebuilds them from their descriptions and
says out loud what had to be guessed.

**Never commit:** API keys, GitHub tokens/PATs, `keys.env`, passwords, or
any file containing them.

After committing, the owner should tell the next session, in one message:

1. "Files committed" + the **branch name** they were committed to
   (so the agent can sync/fetch the right place), **or** simply attach the
   files in the chat instead — that is the easiest route and the agent
   will place them in this folder.
2. Whether the setup guide was separate or inside the zip.
3. **One** task name from the work queue (for example: "Do Step 0").

---

## 3. Why this folder does not affect the rest of the repo

This repository is a fork of a Hyprland dotfiles repo. The owner's own
work already lives only under `workbench/` (plus one workflow file that
GitHub requires at the root). The upstream parts are `assets/` and
`dotfiles/`; this project must never touch them.

`workbench/ai-team-kit/` was picked on purpose. The repo's checking
script, `workbench/skills/validate_skills.py`, was **read in this session
on 2026-10-17** and:

- It treats only `skills/`, `projects/`, and `tools/` directories (and
  `research/*.md` pages) as "units" that must appear in `workbench`'s
  index and README tables. A sibling folder named `ai-team-kit/` is none
  of those, so it is not forced into those tables.
- Its markdown link/path checking covers skills, projects, and the
  workbench loader/README files — not this folder — so handoff notes can
  be dropped in without instantly breaking the repo's gate.
- One caveat: the CI workflow (`.github/workflows/skills-gate.yml`) still
  triggers on any change under `workbench/`, and it checks that **every
  `.json` file under `workbench/` parses**. Any JSON this project commits
  here must be valid JSON.

If the project later grows up into a proper workbench "project" or "tool"
unit, that move (plus its index and README entries) is a separate, named
task — not something to do quietly.

---

## 4. Evidence: what was actually read, and what outranks what

Keep these layers separate. Never upgrade a lower layer into proof.

**For what the owner wants (requirements):**

1. The owner's latest explicit message (the 2026-10-17 restart message,
   and anything newer after it).
2. Earlier owner messages, including the ones visible in the old shared
   chat, where they do not conflict with newer ones.

**For what the kit currently does (facts about the code):**

1. The real files inside `ai-team-kit.zip`, at the exact commit they were
   committed — once they exist here.
2. Test/CI output actually run in the current session, on those files.
3. `HANDOFF.md` / `PROVEN.md` / `OPEN.md` / `FILES.md` — useful, dated
   snapshots written from a long chat; the owner warns they **may
   contain errors**. "Tested" in them means "the old chat reported
   testing it in its own (now gone) sandbox".
4. This README — a summary. Where it and the files above disagree, the
   files win and this README must be corrected in the same session.
5. The old shared chat (link below) — history, not proof.
6. Memory or guessing — always labelled as not verified.

**Read in the 2026-10-17 restart session (verified as read, not as true):**

- The owner's restart message (requirements, preferences, file list,
  the words "Native and MCP also" explained as "MCP for the OAT
  pull-request team too").
- The full text the old shared chat exposes:
  https://claude.ai/share/4b76ad92-cfd8-443a-b686-9fa20f1c23aa
  (fetched and read in 4 chunks). Limits of that source: attachments are
  hidden ("Files hidden when shared"), tool runs are collapsed into
  one-liners, and it is a snapshot — it shows what the old chat *said*,
  not what is true today.
- This repository at `cc8aa83`: the `workbench` README and index, the
  agent loader instructions, the gate script named above, and
  `git status` (clean). Skills loaded before editing, per the repo's own
  rules: `universal-agent-context` (its `SKILL.md`, the full v4 guide,
  and the session-protocol reference). The Qt workload skill was checked
  and does **not** apply to this docs task (no Qt/CMake build entry
  point); re-check that decision when real kit code is being worked on.

**NOT read (because missing), NOT checked, NOT researched yet:**

- `HANDOFF.md`, `PROVEN.md`, `OPEN.md`, `FILES.md` — contents unknown.
- Everything inside `ai-team-kit.zip`, including the real
  `model_scout.py`, dashboard, router config, and setup guide.
- Current free-tier limits and terms of any AI service (OpenRouter,
  NVIDIA NIM, Google AI Studio, Mistral, AI Horde, …). These change and
  must be looked up from official sources when the matching task is
  named — never from memory, never from the old chat's numbers.
- OAT, Odysseus, OpenCode, Goose, OpenMAIC, "The Agency", SkillOpt —
  nothing about them was re-checked in this session.
- Google Colab's current terms for the KoboldCpp notebook.

---

## 5. Story so far — as *reported* by the old chat (not re-proven here)

Everything in this section is "the old chat said so on that date". It is
kept so the next session does not redo finished thinking — but any claim
that matters must be re-checked against the real kit files (Step 0) or
against current official pages (later steps).

- **Oct 2 — flaw hunt on the original plan.** The owner asked for a
  review of flaws, then for smart model selection (new free models appear
  every few months, so hard-coding one free list is brittle) and skill
  integration without knowing if a custom harness was needed. The old
  chat reported, among other things: the plan's OAT install link and
  several OAT commands/settings did not exist; the router settings only
  honoured part of the fallback lists, leaving some jobs with no backup
  model; a key-rotating helper rejected `nvidia` and was unnecessary
  because the router itself rotates keys; the router was reachable from
  the whole network without a password; OAT's merge queue could merge
  PRs by itself, which clashes with "owner reviews and merges"; helpers
  run shell commands unattended; OpenRouter free use was 50 requests/day
  (not 200) and extra keys did not raise it; some other services' numbers
  could not be verified; OAT was macOS/Linux only (Windows untested), a
  local background program needing WSL2 or a cloud box; and the token
  steps mixed up token types. It also reported: OAT loads Agent Skills
  (`SKILL.md` folders) natively, so no custom harness was needed for
  skills, and MCP was the only missing piece, with "one small patch
  point" identified.
- **Oct 3 — model picker + plan v2, then a beginner guide.** A first
  `model_scout.py` plus a corrected plan were delivered. The owner then
  asked for a streamlined, step-by-step, beginner-worded install guide
  (old-plan notes moved to the bottom for troubleshooting), instructions
  to implement and test the picker, and a check of the picker file
  itself. The old chat reported finding and fixing real picker bugs
  (dry-run wasting probes, a maintenance page marking good models
  unusable for a week, a crash on a differently-shaped tool reply, both
  bug-finding questions secretly having the same answer, empty results
  saved on network loss, a missing folder crash, half-written config
  reads, long silence) and added a `--check` key test, reporting 34
  self-checks passing on three Python versions. A one-command helper
  (`harness`) was added.
- **Oct 4 — audit request + the big question list.** The owner asked for
  a code audit, and added: will helpers pick up the owner's handoff /
  improvement-log / worklist markdown files and orchestrate themselves?
  Browser-only Codespace pros/cons and warnings; isolated folder vs
  Docker on Ubuntu; do weak passwords (`word`, `1234`, empty) work? Is
  the browser path the same install as Ubuntu? How to restart everything
  on Windows (PowerShell? Ubuntu first? `harness start`?); are keys
  entered one at a time, what happens on skip/failure, what happens to
  the old key; make the picker test **one model at a time per service
  with gaps** (no spam flags), starting from the biggest or the week's
  most-used model; what "EMPTY" even meant (suggested `[offline]`
  wording instead); the GitHub token needed more permissions than the
  guide's three (the owner's wider set was listed in that message —
  re-read it in the real files, do not reconstruct it from here); the
  confusing "`--repo`" instruction; a GUI/dashboard instead of
  remembering commands (chat-like, Arena/Qwen agent-style, with folders,
  files and +/- change counters; Replit's GitHub/MCP connections as
  inspiration; possibly design/skill repos such as Microsoft's
  SkillOpt); helpers that research and add missing skills/workflows
  themselves; and whether paying OpenRouter $10 really raises the free
  limit to 1,000/day and whether that can be taken away later.
- **Oct 5–8 — v1 kit built and delivered (reported).** Picker v3
  (reported: 68 self-checks), improved helper command, a browser
  dashboard (opened by double-clicking "Start AI Team" / `harness
  open`; chat shown as a transcript, not chat bubbles; tasks, files,
  +/- counters, PRs with Merge/Close, models, keys, skills, logs; **no
  MCP plug-ins**), a `team-workflow` skill so helpers know where the
  owner's handoff/worklist/log files live and how to update them (they
  do **not** pick them up by themselves), a `self-extend` skill (research
  → check licence/scripts → add through a PR; ask the owner first for
  third-party skills and workflow changes), paced model testing
  (reported default: one model at a time per service with a 20-second
  rest, adjustable in `scout.yaml`), clearer status words replacing
  "EMPTY" (roles borrow models or say `UNAVAILABLE`; services show
  `[offline]`, `[refused]`, `[limit]`, `[blocked]`, `[skip]`), careful
  key handling (ask per service, Enter skips, test before saving, a
  refused new key keeps the old one, `keys.env.bak` kept), answers on
  passwords (Ubuntu refuses empty, accepts weak ones at your risk;
  router password is generated), isolation (a folder alone does not
  isolate; a separate Linux user or a Codespace does; Docker strongest
  but **not built**), a Codespace section (almost the same install as
  Ubuntu; stops after 30 idle minutes; monthly free allowance figures
  were quoted differently in different messages — re-check the current
  official number when needed), the OpenRouter $10 question (reported:
  buying ≥ $10 credit in total raises free use to 1,000/day and is not
  lost by spending the balance, but the terms allow changes at any time
  and credits may expire; the terms were only read through search
  excerpts — re-check before paying), the `--repo` answer (full project
  name at the end of an `oat` command about a project; `harness
  add-repo` sets a default), and an audit list of found-and-fixed bugs
  (among them: OAT refusing a project without a provider key, refused
  keys retried forever, a privacy setting that would have blacklisted
  every free model for a week, a redirect that could carry a key to
  another site, one odd reply crashing a whole test run, the dashboard's
  Stop button stopping the dashboard itself, chat text shifting on
  non-English characters, messages pointing at guide sections that did
  not exist; reported: 68 picker checks, 84 dashboard checks, and a
  fresh install working with the newest LiteLLM at that time). Reported
  as **not tested**: real accounts, real GitHub steps (token, project
  setup, real PRs), Windows/Mac/Codespace specifics, real helper chat
  output. Delivered as `ai-team-kit.zip` (reported 84 KB, installs
  cleanly into a fresh home) plus `AI-Team-Setup-Guide.md`.
- **Oct 8 — the big v2 question.** The owner asked: does this plan
  already take into account Odysseus or a similar harness; multiple
  popular sources (NVIDIA NIM, Google AI Studio, Google Colab with the
  KoboldCpp notebook at
  https://colab.research.google.com/github/lostruins/koboldcpp/blob/concedo/colab.ipynb
  ); MCP plug-ins/tools like LM Studio's `mcp.json` (GitHub via the
  owner's PAT, web search, sequential thinking, …); other
  "council / dev-team" repos with an orchestrator and specialist
  sub-agents (game code, programming, front-end/GUI, design, …);
  test environments for hard stacks (Qt6, CMake, C#); and daily-use /
  writing (fanfic) versatility by swapping models in a "room" where each
  persona has its own specialization.
- **Oct 10 — a research answer exists in the shared snapshot.** It began
  "Not yet" and reported: the v1 kit has no MCP, no persona rooms, no
  Colab endpoints, no toolchain installer, and Odysseus had only been a
  name in the owner's handoff; Odysseus was then checked (self-hosted AI
  workspace; agent mode reported as built on OpenCode, bringing MCP,
  skills and shell tools; talks to any OpenAI-compatible endpoint, so it
  could use the kit's router; licence reported as AGPL-3.0; runs with
  Docker or natively; powerful shell tools = treat like an admin
  console; it is **not** a PR dev team; one review's claim of persona
  group chats was **not tested**); model sources reported as covered —
  NVIDIA NIM, Google AI Studio (Flash models), OpenRouter, Mistral —
  with Groq, Cerebras and GitHub Models not added and their free limits
  not verified; Colab/KoboldCpp advised against as a core source
  (reported reading of Colab's FAQ: web services / bypassing the
  notebook UI restrictions, runtimes can end without warning) though the
  router could treat it as a custom endpoint; MCP options were OpenCode
  (reported MIT; MCP, sub-agents, skills, web UI, can use the router) or
  Odysseus, since OAT cannot load MCP and patching it is possible but
  fragile (GitHub commits via `gh`/git already work with the PAT);
  orchestration: OAT already has supervisor/workers/reviewers; "The
  Agency" was mentioned as 147+ specialist persona files (personas, not
  a runtime; convertible to skills; licence to check); ChatDev, MetaGPT
  and CrewAI were explicitly **not evaluated**; test environments
  (reported on Ubuntu 24.04: a Qt 6.4 + CMake 3.28 + Ninja project built
  and its QtTest ran headless; a C# SDK installed but the sandbox's
  NuGet block stopped a build; Linux builds only — a Windows `.exe`
  needs Windows or GitHub Actions `windows-latest` plus the Workflows
  permission; the helper user has no sudo, so toolchains are installed
  once by the owner — the kit does not automate this yet); writing roles
  (`writer`/`editor`) would be easy router names, but free models'
  content filters vary and fanfic results cannot be promised; the
  dashboard has no persona room yet. Recommended path (a recommendation,
  not an owner decision): one shared router; OAT + dashboard for the
  GitHub team; Odysseus as the chat/persona/MCP room; add OpenCode only
  if MCP is wanted in a coding terminal; running three harnesses at once
  adds upkeep. It ended with two owner decisions: Docker or native for
  Odysseus? Is MCP in Odysseus/OpenCode enough, or must the OAT team have
  MCP too (a patch the old chat would have to maintain)?
- **After Oct 10 — two short owner messages, then the chat ran out of
  road.** (1) "Native and MCP also does it support AI Horde from
  community backed models that run on kudos" — no answer about AI Horde
  ever appears in the snapshot. The visible tool notes afterwards
  mention writing "the MCP manager: presets, an LM Studio style
  `mcp.json`, and a safe, reversible patch that gives OAT helpers MCP
  tools" — but **no such files were delivered**; the owner confirms the
  MCP loader/apply files are gone. (2) "Continue where you left off
  (also what do you think about openmaic repo)" — no opinion was given.
  Finally the owner had the old chat write `HANDOFF.md`, `PROVEN.md`,
  `OPEN.md`, then `FILES.md` for this restart. Their contents are hidden
  in the shared snapshot.

### The 2026-10-17 restart (this session, verified here)

- Baseline inventory done: this repo at `cc8aa83`, clean tree; none of
  the five expected files present anywhere in the workspace; no
  `model_scout.py` anywhere. **The selftest baseline could not be run —
  0 runs. That is "not run", not "failed", and not "passed".** No other
  script was run as a substitute.
- The shared old chat was fetched and read (Section 4). No other
  research was started and nothing was built, exactly as the owner
  ordered for the first reply.
- The owner answered the MCP multiple-choice question: **YES — give the
  OAT pull-request team MCP too** (see Decisions).
- This README in the new isolated folder is the second named task.

---

## 6. Owner's standing instructions and preferences (keep these)

1. **One task at a time**, named by the owner. "Next" / "continue" alone
   means: ask which task.
2. **Beginner wording** in anything the owner must read: plain words,
   step-by-step, no unexplained jargon breaking the flow. Troubleshooting
   and "what was wrong with v1" details go at the bottom of guides.
3. **Downloadable files**: deliver results as files the owner can save,
   not only as chat text.
4. **Say what you tested and what you couldn't**, every time. Never turn
   "the old chat reported it" into "verified".
5. **Read the real kit files before changing anything; edit them in
   place** instead of regenerating them. Do not repeat research that
   `PROVEN.md` already covers — after actually reading `PROVEN.md`.
6. **Lost files** (patched `model_scout.py`, MCP loader/apply, dashboard
   tests) get rebuilt from their descriptions, with guesses said out
   loud.
7. **Free-tier limits and terms must be looked up fresh** from official
   sources at task time. Old numbers in any document (including this
   one) are dated claims, not facts.
8. **The owner reviews and merges all pull requests.** No auto-merge, no
   publishing, no spending money, no licence-risky copying without the
   owner deciding first.
9. Work stays inside `workbench/ai-team-kit/` unless a named task says
   otherwise. Upstream `assets/` and `dotfiles/` are never touched.

---

## 7. Decisions and non-decisions

### Decided by the owner

| ID | Decision | When / source | Meaning |
|---|---|---|---|
| D1 | The room side (Odysseus or similar) runs **native**, not Docker | Owner: "Native and MCP also" (old chat), carried into the 2026-10-17 restart | Install directly in the same Ubuntu/WSL. Exact host and steps are a Step 3 design detail. This decision was about Odysseus; it does not ban Docker as an *isolation* idea elsewhere, but do not build Docker anything unless re-named as a task. |
| D2 | **MCP for the OAT pull-request team too: YES** | Owner picked YES in the 2026-10-17 multiple-choice question | Queued only — nothing built. Means: rebuild a small, undoable patch/loader plus an owner-controlled `mcp.json`-style list so OAT workers/reviewers can call approved MCP tools (examples the owner named: GitHub via PAT, sequential thinking, web search) during PR work. Known cost accepted by the owner: OAT has no native MCP, so this is custom work that must be tested and may need care after OAT updates. Tools must be allowed one by one; read-only where possible. |
| D3 | Work lives in an isolated folder in this repo that does not affect the rest of it | Owner's restart message; owner then asked for this README in "the separate folder", 2026-10-17 | The exact path `workbench/ai-team-kit/` is this session's working choice (picked for the gate reasons in Section 3), not a path the owner dictated. Reversible: it can be renamed, moved, or promoted later as a named task. |

### Explicitly NOT decided yet (do not build on these)

- Which harness is the persona room (Odysseus vs OpenCode vs Goose vs …)
  and which should do what — that is the Step 3 comparison. The old
  chat's "recommended path" was its own suggestion, never approved.
- Orchestrator/sub-agent role design (game code, programming,
  front-end/GUI, design) and the writing/daily-use personas.
- Whether the KoboldCpp Colab endpoint is used at all (Step 1b), and
  whether AI Horde is supported/added (Step 1c).
- Any opinion on, or use of, OpenMAIC (Step 1d).
- Extra model sources beyond NVIDIA NIM + Google AI Studio (Groq,
  Cerebras, GitHub Models were only mentioned by the old chat).
- "The Agency" personas, SkillOpt, ChatDev/MetaGPT/CrewAI — mentions, not
  approvals. Licence checks come before any use.
- Paying OpenRouter (or anyone) anything.

---

## 8. Discrepancies — do not "fix" these by guessing

| # | Discrepancy | What to do |
|---|---|---|
| X1 | Owner said 5 files were attached; none arrived in the restart sandbox, and the shared chat hides its attachments. | Step 0 only starts when the files are committed here or attached in chat. |
| X2 | Old chat (Oct 10) said NVIDIA NIM and Google AI Studio were already covered; the restart message says the handoff leaves them out and missing pieces should be added. | The real kit config/code decides (Step 0/2). Report what the kit actually contains before adding anything. |
| X3 | Owner lists Odysseus-coverage and Colab-usability as "replies I never got", yet the shared snapshot contains an Oct 10 answer covering both. | Treat those questions as still open (Steps 1a/1b). Possibly the owner never saw it or found it incomplete — answer fresh and briefly, with current sources. |
| X4 | Self-check counts in the old chat grew as the code grew (23 → 33/34 → 68 for the picker; 84 for the dashboard). | Expect the delivered zip's own number, measured in Step 0. Never quote an old count as the current result. |
| X5 | Codespace free allowance was quoted in two different shapes ("about 60 hours a month" vs "about 120 core-hours"). | Look up the current official figure only when a Codespace task is named. |
| X6 | Odysseus persona group chats rest on "one review" and were never tested, even by the old chat. | Do not claim the room feature exists until Step 3 checks primary sources (docs/source/licence). |

---

## 9. Work queue (the order agreed on 2026-10-17)

The order is provisional until Step 0 is done: `HANDOFF.md` / `OPEN.md`
may re-order it. If they do, say so before touching code.

### Step 0 — Unblock + baseline (no building, no research)

Entry: the Section 2 files are in this folder (or attached in chat).
Do: compare every file with `FILES.md` and flag mismatches → list the
zip's contents with sizes (and hashes if `FILES.md` gives any) without
modifying anything → read `HANDOFF.md`, `PROVEN.md`, `OPEN.md` → find the
selftest command from the **real** `model_scout.py`/guide → run it
**once** and record the exact command, Python version, exit code, and
output → report which model services the kit's real config actually
supports.
Done means: a baseline report a stranger could re-run. If the selftest
fails, report and stop — fixing it is a separate named task.

### Step 1 — Quick answers the owner never got (answers only)

Current official sources and licences checked at task time; short,
beginner-worded answers; no building.

- **1a.** Does the plan already cover Odysseus or similar harnesses?
  (Straight yes/no + what exists today.)
- **1b.** Is the owner's KoboldCpp Colab link usable for this project
  under Colab's current terms?
- **1c.** AI Horde (community models, kudos): does the kit/router support
  it today; if not, could it, and what would it cost in upkeep? Check
  what kind of API it actually offers before answering.
- **1d.** OpenMAIC repo: read its README **and licence**, then give an
  opinion — useful here, reference only, or avoid, and why.

### Step 2 — Model sources: NVIDIA NIM + Google AI Studio

From the Step 0 inventory: state what is already in the kit. Look up both
services' **current** free limits and terms from official pages. Add only
what is missing, editing the real files in place. Test what can be tested
without the owner's keys (for example against a fake local service, as
the old chat reportedly did) and say plainly what still needs the owner's
real keys to prove.

### Step 3 — Compare harnesses + design v2 (design only, owner approves)

Compare **OAT, Odysseus, OpenCode, Goose** from primary sources (docs,
source, licence, releases): who runs the PR team, who is the native
persona room for writing/daily use, who carries MCP where, orchestrator
+ specialist sub-agents (game code, programming, front-end/GUI, design),
and how test toolchains (Qt6/CMake, C#, …) fit. Deliver a
beginner-friendly design naming who does what and why — and stop for the
owner's approval before any installation.

### Step 4 — Rebuild the lost files (say what you guessed)

Rebuild, from their descriptions in the handoff files: the patched
`model_scout.py` changes, the dashboard test files, and the MCP
loader/apply files for OAT (see decision D2; design settled in Step 3).
Every guess gets labelled in the file and in the report. Each rebuilt
piece needs a test that can fail, run for real.

### Step 5 — Build v2, one approved slice at a time

Native room, orchestrator/sub-agent roles, MCP for the OAT team, new
model sources wired in. Each slice: small diff, real tests at the level
the claim needs, honest "tested / couldn't test" report, downloadable
result, owner merges the PR.

### Parked (not authorized until the owner names them)

Groq / Cerebras / GitHub Models · SkillOpt integration · "The Agency"
persona conversion · ChatDev / MetaGPT / CrewAI · any Docker build ·
promoting this folder into the workbench index/README tables · paying
for any credit.

---

## 10. Next-session checklist

### For the owner (2 minutes)

1. Commit the Section 2 files to `workbench/ai-team-kit/` (or attach
   them in the chat). No keys/tokens, ever.
2. Say which branch you committed to (or "attached"), whether the guide
   was a separate file, and name **one** task — suggested first words:
   **"Do Step 0."**

### For the next agent

1. You are in the `dionysus` repo: obey `workbench/AGENTS.md` first —
   load the `universal-agent-context` skill (SKILL.md → v4 guide →
   session-protocol) and say what you loaded. Load a workload skill only
   if the repo's real build entry point matches it.
2. Read this README, then — once present — `FILES.md` (inventory),
   `HANDOFF.md` (route), `PROVEN.md` (do not redo its research),
   `OPEN.md` (its own work list). Real kit files outrank all four for
   "what the code does"; the owner's latest message outranks everything
   for "what to do".
3. Record the baseline before edits: branch, base commit, `git status`
   (explain any dirt), and sync/fetch the branch the owner named.
4. Inventory the zip read-only. Read scripts before running anything —
   never blind-run installers or self-modifying "apply" steps.
5. Run the picker's selftest once (Step 0) and report it exactly:
   command, Python version, exit code, counts from *this* run.
6. Do the one named task only. Keep diffs small; prove claims at the
   level they need (a syntax check is not a test; a test pass here is
   not proof on Windows/Mac/Codespace).
7. Before finishing: if anything under `workbench/` changed, run
   `python3 skills/validate_skills.py` from inside `workbench/` and make
   it pass; commit; update this README's status, decisions,
   discrepancies, and session log **in the same session** (correct it,
   don't layer a second handoff on top); end with what changed, what was
   verified, and a "Not verifiable here" line.

---

## 11. Safety rules (plain words)

- **Secrets stay out of git and out of chat logs**: API keys and PATs
  live only in the kit's local key file on the owner's machine.
- **Least power for the PAT**: only the permissions the guide/owner
  agree on. (Reported detail to re-verify in the real guide: "Actions"
  is not "Workflows" — editing `.github/workflows` needs the Workflows
  permission.)
- **Helpers run commands unattended**: isolation matters. A plain folder
  does not isolate them; the kit's reported answers were a separate
  Linux user or a Codespace. Re-read the real guide before advising.
- **The router must not be open to the network without its password**
  (the original plan's flaw, reportedly fixed in v1 — verify in the real
  config during Step 0 if `FILES.md` makes that checkable without
  running it).
- **MCP tools are power tools**: allow-list one by one, read-only first,
  and remember the OAT patch (D2) is custom work to re-check after OAT
  updates.
- **Terms before use**: Colab, AI Horde, and every free tier get a fresh
  official-terms check in the step that touches them. "Free today" is a
  dated claim.
- **Licences before copying**: no third-party skill/persona/code is
  copied in until its licence is read and compatible (Odysseus was
  reported as AGPL-3.0 — verify in Step 3 before relying on it).

---

## 12. Session log for this folder

### 2026-10-17 — restart + this README (Arena session)

- Changed: created `workbench/ai-team-kit/README.md` (this file). First
  reply of the session was inventory-only and changed nothing.
- Partial: Step 0 cannot start — the five files in Section 2 are still
  missing, so there is still **no selftest baseline** (0 runs).
- Left (on purpose): all research and all v2 building; every numbered
  step awaits the owner naming it.
- Verified in this session: repo/branch/base commit and clean tree by
  `git status`; absence of the five files and of any `model_scout.py` by
  searching the workspace; the gate script's scope by reading it; the
  old chat's visible text by fetching the shared link. The workbench
  gate result for this change is reported in the chat turn that commits
  this file (run after writing, per the checklist) — re-run it rather
  than trusting any number quoted here later.
- Not verifiable here: everything inside the missing zip and handoff
  files; every "tested" claim from the old chat; current free-tier
  limits/terms of any service; Windows/Mac/Codespace behaviour; real
  GitHub/PR flows with the owner's accounts.
- Docs touched: only this README.
