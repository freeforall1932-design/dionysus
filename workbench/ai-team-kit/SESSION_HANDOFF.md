# AI Team Kit — session handoff

**Status on 2026-10-17:** extraction, repository reorganisation, and a static
code audit are complete. **No next build task has been named yet.** The next
session must stop at [`WORKLIST.md`](WORKLIST.md) item **W-001** and wait for
the owner to name one item.

> If the owner sends only “next” or “continue”, ask which `W-` item they mean.
> Do not choose one.

---

## 1. What just changed

The owner-named 2026-10-17 reorganisation/audit task did the following:

- Safely fast-forwarded the session branch to the learning-report commit
  `935b179fdf2553dd3cfbd4243a3a9e1ca14b5526` after proving a restored
  untracked copy of the folder was byte-identical to that commit.
- Extracted the canonical 16-file v1 kit from `ai-team-kit.zip` to
  `kit/harness/`, preserving bytes and executable bits.
- Extracted the four documents that existed only in `harness.zip` to
  `archive/harness-zip-extras/`.
- Reassembled the old all-in-one README and the four 2026-10-16 snapshot
  files into:
  - this session handoff;
  - one [`WORKLIST.md`](WORKLIST.md);
  - [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md);
  - [`RESEARCH_AND_OPEN_QUESTIONS.md`](RESEARCH_AND_OPEN_QUESTIONS.md);
  - [`FILE_MAP.md`](FILE_MAP.md);
  - [`READING_GUIDE.md`](READING_GUIDE.md).
- Kept raw history:
  - `archive/2026-10-16-handoff-snapshot/` — original
    `HANDOFF.md`, `PROVEN.md`, `OPEN.md`, `FILES.md`;
  - `archive/2026-10-17-next-session-readme.md` — former detailed README.
- Moved the learning report to `reports/KIT_LEARNING_AND_CHAT_MATCH.md` and
  added [`reports/CODE_AUDIT_2026-10-17.md`](reports/CODE_AUDIT_2026-10-17.md).
- Removed `ai-team-kit.zip`, `harness.zip`, and the duplicate top-level
  `AI-Team-Setup-Guide.md` **after** extraction. The canonical guide is now
  only `kit/harness/GUIDE.md`; the deletion record and zip hashes are in
  [`FILE_MAP.md`](FILE_MAP.md), Section 5.
- Did **not** edit any extracted kit code or guide. Audit findings are
  recommendations in the worklist, not silent fixes.

Branch/PR state changes outside files, so treat GitHub as the source of truth:
this work is on session branch `arena/5bf33a0c-dionysus`, with draft PR #3
intended for owner review. Check `git status`, `git log -1`, and the PR's
current head/checks at the start of the next session.

---

## 2. Current truth in one screen

- **Delivered v1 exists as source** in `kit/harness/`: installer, `harness`
  command, model scout, dashboard, two skills/templates, launchers, guide.
- **Providers in v1:** OpenRouter, NVIDIA, Mistral, Google. Roles:
  architect, implementer, reviewer.
- **Not in v1:** patched creative-roles scout, dynamic endpoints/services,
  MCP files/commands/UI, Odysseus integration/persona room, extra providers,
  Docker, `toolchains.sh`, and delivered dashboard/MCP test harnesses.
- **Audit verdict:** coherent v1, no obvious stub feature, but do not trust a
  real install until the P0 items are addressed or consciously accepted:
  free-status assumptions, installer pinning, secret/helper boundary, shell
  key sourcing, masked OAT failures, stale refresh, concurrent jobs, and
  skill-install symlink handling.
- **Odysseus:** only a pinned source pointer exists
  ([`ODYSSEUS_SOURCE.md`](ODYSSEUS_SOURCE.md), pin `951d57db…` when last
  checked on 2026-10-17). No code was copied, installed, or run. Re-check that
  repo's `main` before calling the pin current.
- **Owner-confirmed future directions:** MCP for OAT is wanted; Odysseus is
  native rather than Docker *if* chosen. Neither is built.

---

## 3. Evidence carried forward — and its limits

### Verified in the restart/audit sessions

- Zip inventories and member hashes; 16/16 common files identical between the
  two zips; the top-level guide was identical to the in-zip guide.
- Extraction into the repo preserved the canonical/extras bytes and modes.
- Both Python files AST-parse; both shell scripts pass `bash -n`; dashboard
  inline JavaScript passes a syntax check.
- Guide commands, shell dispatch, dashboard routes, and job actions were
  cross-checked statically.
- The delivered model-picker self-test was run **exactly once** on
  2026-10-17 under isolated scratch `HOME`/`TMPDIR`: Python 3.11.2, exit 0,
  **62 passed, 0 failed, empty stderr**, with LiteLLM Router checks skipped.
  Full output is in the learning report, Appendix B.

### Not tested here

- The installer, LiteLLM proxy, OAT daemon/agents, dashboard server/browser
  flow, real provider accounts/models, real GitHub token/PR/Merge/Close,
  Windows/WSL, macOS, Codespaces, Odysseus runtime, MCP, and Docker.
- Current free-tier limits/terms for any provider.
- Any audit fix—none has been implemented yet.

Do **not** rerun the scout self-test just to “check the baseline”. Rerun it
only inside a named task that changes the scout or its environment, and
report that new run exactly.

---

## 4. Exact next gate

1. Owner reviews the reorganisation, preferably through
   [`READING_GUIDE.md`](READING_GUIDE.md), then decides the draft PR's fate.
   Agents do not merge it.
2. Owner names **one** worklist item (for example `W-010`, `W-021`, or
   `W-050`).
3. The next agent does only that item, updates the worklist/handoff in the
   same session, and reports tested/not-tested.

Recommended order is in `WORKLIST.md`, but a recommendation is not permission.

---

## 5. Start-of-session checklist for the next agent

1. Obey the repo/workbench instructions that are actually in force for the
   checkout; record branch, HEAD, and `git status` before editing.
2. Fetch/sync carefully. This workspace has previously been restored at an
   old base with the whole kit folder untracked: **never reset blindly**.
   Compare unexpected untracked files to the remote branch blobs first, back
   them up in scratch if needed, then fast-forward only when proven safe.
3. Read `README.md`, this handoff, and the top of `WORKLIST.md`. Then read
   only the topic/report files the named task needs.
4. For “what does code do”, read the real file in `kit/harness/` before
   editing. For “what should happen”, the owner's latest instruction wins.
5. Keep changes inside `workbench/ai-team-kit/` unless the named task says
   otherwise. Never touch upstream `assets/` or `dotfiles/`.
6. Before finishing a workbench change, run the repo gate from inside
   `workbench/` (`python3 skills/validate_skills.py`), inspect `git diff`,
   and state exactly what was and was not tested.
7. If updating draft PR #3's title/body, `gh pr edit` previously failed with a
   Projects-classic GraphQL error and could appear to do nothing. Use a REST
   `PATCH` via `gh api repos/.../pulls/3` and read the PR back. Do not merge
   unless the owner explicitly instructs it.

---

## 6. Safety reminders

- Never commit or paste API keys, GitHub tokens, `keys.env`, dashboard tokens,
  OAT config/env files, runtime state, logs with secrets, or private chats.
- Read installer/download code before running it; W-011 exists because v1 is
  not sufficiently pinned.
- Helpers run commands as the install user. Treat skill repos, MCP servers,
  and agent shell access as code execution, not as harmless text.
- Terms/licences come before using a provider, persona pack, skill, or
  third-party code.
- The owner reviews and merges pull requests. No auto-merge assumption.
