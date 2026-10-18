# Codebase sweep audit — 2026-10-18

> **Scope:** all 513 files tracked at baseline `1049968` were inventoried.
> Deep code inspection concentrated on the fork-owned work under
> `workbench/` plus `.github/workflows/skills-gate.yml`; upstream
> `assets/` and `dotfiles/` were scanned read-only and were not edited.
> Linked project repositories were checked read-only at their current
> default-branch heads.
>
> **Short verdict:** the repository's mechanical gates and tested tools are
> in good shape, but the AI Team Kit v1 still carries the known P0 safety
> and correctness queue, most v2 behaviour is still absent, and several
> one-off scripts/templates have no rerunnable gate. No Python, JSON, YAML,
> TOML, shell-syntax, or notebook-syntax parse failure was found.

## 1. Evidence actually run in this sweep

| Check | Result in this session |
|---|---|
| `python3 skills/validate_skills.py` from `workbench/` | PASS: 356 checks at baseline, 377 after this delivery's files |
| Python AST parse | 21/21 tracked `.py` files parse |
| JSON / YAML / TOML parse | 21/21 JSON, 11/11 YAML (PyYAML in a scratch venv), 1/1 TOML parse |
| Shell syntax | 43 bash/sh-shebang files pass `bash -n`/`sh -n` |
| ShellCheck 0.11.0 | 0 errors; 60 warnings, mostly expected Neofetch config variables; the actionable warnings are below |
| Ruff 0.17.1, bug-oriented subset | 6 minor findings, no syntax/pyflakes-class error |
| Magnet Excavator tests | **142 passed** (`test_magnet_excavator`, `test_magnet_excavator_gui`) |
| `qt_lint.py --selftest` and templates | PASS; 0 template findings |
| Gifscythe `qt_lint` against current `97b0758…` | 9 known findings, all in the committed baseline; exit 0 when run from `working_code/gifscythe` as documented |
| Skills-repo drop-in on a fresh `84c9518…` clone | 35 compiler tests passed; catalog gate 124 passed; regenerated packs byte-identical; 247 manifest hashes OK; the 198-entry `coding-agents.zip` matches the unpacked pack files |
| Shotgun experiment hashes | `script.lua` and harness hashes still match the evidence at shotgun `4c4bf1b…` |
| New Kobold notebook | JSON/AST parse OK; default preflight cells executed locally with no download; extra-arg guard and resumable-download helper passed a local range-capable HTTP fixture |
| Markdown local-link scan | 265 local links in 241 Markdown/MDC files; 39 do not resolve *in place*: 38 are inside the generated skills-repo drop-in/paste packs (overlay/flattened context), 1 is an upstream demo-image link |
| Remote pins | Gifscythe `97b0758…`, Shotgun `4c4bf1b…`, skills-repo `84c9518…`, and Odysseus `951d57db…` were still their default-branch heads when checked on 2026-10-18 |

The delivered `model_scout.py --selftest` was **not** rerun. The AI Team
Kit handoff reserves reruns for a named task that changes the scout or its
environment; the preserved one-run evidence remains 62 passed on
2026-10-17 with LiteLLM Router checks skipped.

## 2. Findings that need work

### SW-01 — P0: AI Team Kit v1 safety/correctness queue is still open

The detailed source audit remains
[`ai-team-kit/reports/CODE_AUDIT_2026-10-17.md`](ai-team-kit/reports/CODE_AUDIT_2026-10-17.md).
This sweep found no reason to downgrade A-01…A-08:

- NVIDIA/Mistral/Google free status is still encoded as `assume_free` in
  `model_scout.py`, while W-020 now proves the real rules are per-model and
  conditional. Research is newer than code.
- `install.sh` still uses a remote `curl … | sh`, unpinned LiteLLM, and a
  moving OAT installer script.
- `keys.env` is still sourced as shell code in two places (ShellCheck
  SC1090 at `harness.sh:43,116` is the visible tip of A-04).
- OAT lifecycle success messages can still mask failures; router/scout
  refresh can remain stale; dashboard/CLI jobs still have no shared
  single-flight lock.
- Skill installation still dereferences symlinks during `copytree`, so the
  preview-size/symlink story remains unsafe for untrusted skill repos.

**Owner queue:** W-010…W-015. Do not use real keys/tokens or untrusted
skills with v1 until those are fixed or explicitly accepted.

### SW-02 — P0/P1: the intended v2 behaviour is absent, not half-wired

The delivered kit still has four hard-coded providers and three roles.
Search found no dynamic endpoint command, Groq/Cloudflare provider,
quota ledger/circuit-breaker, Colab endpoint type, MCP loader/UI,
writer/editor roles, Odysseus/persona/council integration, `toolchains.sh`,
or delivered dashboard/MCP test harness. This matches W-030…W-060; it is a
missing-feature gap, not a newly discovered regression.

### SW-03 — P1: two false-green or weak-gate risks

1. **`qt_lint.py` silently passes nonexistent input paths.** Reproduction:
   `python3 workbench/skills/qt6-cmake-cpp/scripts/qt_lint.py /definitely/missing`
   exits 0 with “no findings”. `iter_files()` walks a missing path and
   yields nothing, so a CI path typo can look like a clean lint. Fix by
   failing on any nonexistent input (and consider failing when a run scans
   zero eligible files), add a self-test, then regenerate the skills-repo
   drop-in copies/packs/manifest in the same change.
2. **Coverage is uneven.** The root gate now syntax-checks all Python under
   `workbench/` and validates notebooks after this delivery, but it still
   does not run ShellCheck, the skills-repo compiler suite, Shotgun script
   tests (none exist), AI Team Kit shell/dashboard fixtures, or Qt template
   compilation. W-016 remains the right home for the AI-kit fixtures; the
   catalog suite belongs in the skills-repo's own CI or an explicit
   scheduled drift check, not silently assumed.

Fixed during this sweep in `.github/workflows/skills-gate.yml`: Python
syntax coverage widened from `workbench/skills/` to all of `workbench/`;
notebooks must parse, compile, and carry no outputs; the JSON loop is now
null-delimited so paths with spaces cannot split; the concurrency guard
now names this repo's real default branch (`dionysus`, not `main`).

### SW-04 — P1: Kobold notebook is test-ready code, not runtime proof

[`kobold-cli/kobold-cli.ipynb`](kobold-cli/kobold-cli.ipynb) was added at
the owner's request before W-021/Q14 is closed. Its default mode is
preflight-only (no download, no tunnel), and launch mode binds to
loopback, generates a password, pins KoboldCpp `v1.123.1`, and verifies
the release SHA-256. Remaining risks are explicit:

- Nothing in the notebook has run on a real Colab GPU yet; model fit,
  flash-attention behaviour, tunnel reachability, and tool-calling are
  unproven.
- KoboldCpp's own `--remotetunnel` downloads `cloudflared` from a moving
  latest-release URL. The notebook pins KoboldCpp, not that helper.
- KoboldCpp prints parsed arguments at startup; the generated password can
  therefore appear in launch output. Outputs must be cleared and never
  committed/shared.
- W-021/Q14 (current Colab terms, session/runtime rules, tunnel/API use)
  is still open. Owner-directed testing does not close it.

### SW-05 — P1: Magnet GUI is safe by default, sharp if exposed

`magnet_excavator_gui.py` binds to `127.0.0.1` by default and its 142 tests
pass. But `--host 0.0.0.0` exposes unauthenticated endpoints that can read
server-side paths, fetch caller-supplied HTTP(S) URLs, load tracker files,
and ask qBittorrent to add magnets. The README warns about trusted
networks, yet there is no token, no refusal to start exposed without an
explicit unsafe flag, and completed jobs in `JOBS` are never pruned.
Recommended hardening: require an explicit `--unsafe-expose` acknowledgement
or a per-start token for non-loopback binds, prune old jobs, and avoid
returning raw local filesystem error text to remote callers.

### SW-06 — P2: Shotgun REA scripts are evidence tools with weak rerun armour

The committed results are **not stale**: both target hashes still match
shotgun-king-anew at `4c4bf1b…`. But rerunning is fragile:

- `rea_mod_safety_experiment.py` restores files with `git checkout --`
  and does not first refuse a dirty/non-scratch checkout. Its docstring
  says “scratch clone”, but the code does not enforce it.
- `make-bundle.mjs` imports `rea-agents` with no local package manifest or
  version pin; `build_ledger_input.py` fails with raw `KeyError`s if a
  capture label is missing.
- There are no unit tests for the three scripts and CI does not run them.

Treat them as dated evidence generators. Before reuse, add a clean-tree
guard, pin/document the REA/lupa versions used, and add small fixture tests.

### SW-07 — P2: generated skills catalog is current but bulky and link-contextual

`workbench/research/skills-repo-compat/` holds 252 files because it is a
paste-ready bundle plus generated packs. A fresh overlay proved it is
deterministic and current against skills-repo `84c9518…`, so it should not
be deleted as “stale”. The caveat is navigation: 38 local links inside the
bundle assume the full skills-repo overlay or the flattened prompt-pack
context and do not resolve as Dionysus in-tree links. Any future compiler
fix (including SW-03's `qt_lint` fix) must regenerate packs, the zip, and
`MANIFEST.sha256` together, or the bundle becomes genuinely stale.

### SW-08 — P2: Qt template and GitHub Action upgrades need a dedicated trial

The Qt workflow template is explicitly unexecuted in its authoring
sandbox and installs `aqtinstall` unpinned. Current action releases found
on 2026-10-18 are newer than the repo's pins (for example
`actions/checkout` v7.0.1 vs v5 used here; `actions/setup-python` v7.0.0
vs v5 in the catalog bundle; upload/download-artifact v7/v8 vs v5/v6 in
the template). These are **upgrade candidates, not proven breakage**: the
templates themselves say to pin majors deliberately after checking the
declared runner/runtime. Bump them only in a focused change that runs the
affected workflows on GitHub and updates every mirrored copy.

### SW-09 — P2 (upstream, report-only): dotfiles battery/log defects

- `dotfiles/waybar/scripts/battery.sh` says “dynamic tooltip”, computes
  `time_to_empty`/`time_to_full`, then emits unset `$tooltip`; the feature
  is incomplete. Its `seq 1 $filled` / `seq 1 $empty` bar also misbehaves
  at 0/100 because `seq 1 0` still emits values, and the script assumes
  `BAT0` exists. It is referenced by Waybar, so this is a real user-facing
  bug candidate.
- `dotfiles/hypr/scripts/refresh-eww.sh:3` has a minor ShellCheck SC2046
  quoting warning.
- `dotfiles/hypr/hypr.log` is a tracked 704-byte runtime log with no
  references — a removal/ignore candidate.
- `dotfiles/cava/README.md` links missing `assets/demo-cava.png`.

No upstream files were edited in this sweep, in line with the fork's
“work lives under `workbench/`” convention. These need an owner-named
dotfiles slice if they are worth fixing.

### SW-10 — P3: minor lint/style debt

Ruff's bug-oriented pass found only: two `try/except/pass` sites that could
use `contextlib.suppress` in `harness_ui.py`, one unused `dirnames`
variable in both copies of `validate_skills.py`, and two `zip()` calls
without `strict=` in Magnet tests. ShellCheck additionally flags one
unused loop variable in `harness.sh`. None is a demonstrated runtime bug;
fix them opportunistically with their owning changes rather than a
style-only churn commit.

## 3. Stale-file disposition

| Area | Disposition |
|---|---|
| AI Team Kit `archive/` snapshots and harness-zip extras | **Keep.** They are labelled history/evidence; current docs point forward to the reorganised files. |
| Skills-repo drop-in, generated packs, patches, manifest, zip | **Keep; verified current** against skills-repo `84c9518…` on 2026-10-18. Regenerate as one set after any source skill/compiler change. |
| Project pins for Gifscythe, Shotgun, Odysseus | **Keep; verified still at default-branch HEAD** on 2026-10-18. Index `last_verified` dates were refreshed where this sweep actually rechecked them. |
| W-020 provider research | **Fresh but perishable.** Same-day official-source check; re-verify quarterly or on provider change, as the report says. |
| Qt lint baseline for Gifscythe | **Current.** All 9 findings at `97b0758…` are the baselined ones. |
| `dotfiles/hypr/hypr.log` | **Removal candidate** in a future owner-named dotfiles slice. |
| Kobold CLI status text saying “research only / no code yet” | **Updated in this delivery** now that the owner-directed test notebook exists. |

## 4. Recommended order (owner chooses; nothing auto-starts)

1. Owner runs the Kobold notebook in preflight mode and reports the output;
   separately, W-021 answers Colab terms/limits before the endpoint is
   relied on.
2. Fix SW-03's `qt_lint` missing-path false green and regenerate the
   skills catalog bundle in the same slice.
3. AI Team Kit P0s in order: W-010 → W-015, then W-016 fixtures.
4. Magnet GUI exposed-mode hardening (SW-05) if LAN use is actually wanted.
5. Shotgun rerun armour (SW-06) only before the experiment is rerun.
6. A focused GitHub Actions major-upgrade trial (SW-08), and an
   owner-named upstream dotfiles fix for SW-09 if desired.

## 5. Changed in this sweep / not changed

**Changed:** the Kobold test notebook and one-line Colab link file; the
root gate improvements listed in SW-03; `.ipynb_checkpoints/` ignored;
status/index text refreshed for the notebook and rechecked pins.

**Not changed:** extracted AI Team Kit code under `ai-team-kit/kit/`,
Magnet/Shotgun/Qt code, the generated skills catalog, and all upstream
`assets/`/`dotfiles/`. Findings about those areas are recommendations
above, not silent fixes.

**Not verifiable here:** real Colab/GPU/model behaviour; installer/OAT/
LiteLLM/dashboard runtime; real provider accounts; Qt/CMake compilation
(no Qt/CMake in this sandbox); Hyprland/Waybar desktop behaviour; any
linked repo's full test suite beyond the hash/lint checks named above.

## Postscript — owner Colab runtime correction (later on 2026-10-18)

The Kobold notebook described in SW-04 was then run by the owner in real
Colab and failed with `FileNotFoundError: /content/kobold-cli`: its
custom preflight called `shutil.disk_usage()` on that child directory
before creating it. The local evidence in §1 therefore did **not** cover
the exact fresh-Colab filesystem state. At the owner's correction, the
notebook was replaced by an adaptation of the actual official KoboldCpp
`colab.ipynb` at `concedo@f41f621…`, retaining upstream's
download/load/launch cell and changing coding/API presets/defaults; the
silent-audio cell was omitted. The replacement was executed locally in a
Jupyter kernel with `/content` present and no `/content/kobold-cli`,
using stubbed `wget`/`apt`/KoboldCpp commands, and all presets/manual
override reached the expected fake launch. The current description and
remaining limits are in `kobold-cli/README.md` and §7 of
`kobold-cli/COLAB_NOTEBOOK_DISSECTION_2026-10-18.md`; treat SW-04's
custom-notebook details as superseded history.
