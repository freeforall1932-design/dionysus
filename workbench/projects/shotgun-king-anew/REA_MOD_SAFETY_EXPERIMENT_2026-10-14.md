# Can the UI or logic of the sk-rework mod be changed without breaking it? — a REA-wrapped experiment

Date: 2026-10-14. Target: the owner's `shotgun-king-anew` repository at
`4c4bf1bcc9e21c4b274736363e88e3f99065f157`, mod `<shotgun-king-anew>/modded/sk-rework/script.lua`
(SHA-256 `86b3e1a21c95…`), harness `<shotgun-king-anew>/tools/mod_smoketest.py` (SHA-256
`5597e88bb08a…`). Tooling: REA 6.4.0 (`npm i rea-agents`, Node 22.22.3),
`lupa` 2.8 in a venv, Debian 12 sandbox.

**State up front — what this does and does not prove.** The real game (SUGAR
engine, Windows) and its `data.sgr` are not here and were not fetched. Every
run below drives the mod against the repository's *fake* SUGAR environment
(the lupa harness, 68 checks × 4 iterator variants). That harness is the
owner's executable UI↔engine behaviour contract; it is **integration**
authority. It can prove that a change keeps or breaks the contract. It cannot
prove the live game is safe. REA's obligation ledger says exactly that at the
end, which is why it was used.

## 1. Method

1. Baseline: run the harness unmodified inside `rea capture-process` (one
   Evidence record per run: exit code, terminal frames, SHA-256 of every file
   under `modded/sk-rework/` and of the harness before and after the run).
2. Apply one mutation to the scratch clone, capture again, restore with
   `git checkout --`. Nine captures in total.
3. `rea compare-process-captures baseline <mutant>` for each pair.
4. Build a canonical Evidence bundle from the nine records (REA's own
   `createEvidenceBundle`, then `rea evidence-export`), declare five
   obligations with the authority each one *really* needs, and run
   `rea build-reconstruction-obligation-ledger`.

Scripts (all in this folder, all re-runnable on a scratch clone):
`rea_mod_safety_experiment.py` (steps 1–3), `make-bundle.mjs` and
`build_ledger_input.py` (step 4). Outputs kept in `rea-experiment/`:
`results.json` (per-run evidence ids, hashes, exit codes, summary lines) and
`ledger-summary.json` (ledger status and diagnostics). The raw captures
(~180 KB) and bundle are regenerated, not committed.

## 2. Mutations and observed results

| id | kind | change (one edit) | exit | harness output (verbatim) | script sha | harness sha | REA evidence id |
|---|---|---|---|---|---|---|---|
| baseline | — | none | 0 | `68/68` in all four variants; `all()-semantics variants: value/pair passed for default, luajit21` | `86b3e1a21c95` | `5597e88bb08a` | `ev_c37000126c91ae2a…` |
| M1 | UI layout | `PANEL_W 204 → 216` | **0** | `68/68` ×4 | `ad6cd86f3072` | `5597e88bb08a` | `ev_57f04ec6296ec2a1…` |
| M2 | UI label | tab text `"SK DEV" → "SK-DEV"` | 1 | `FAIL[default-value]: SK DEV tab was not drawn` (×4 variants) | `46f677f5edac` | `5597e88bb08a` | `ev_668480509eb38951…` |
| M3 | UI behaviour | delete the three lines that consume the click (`mcl = false / mcr = false / mlb = false`) | 1 | `67/68` ×4 — `FAILED [...]: RUN-6 BUG: CLIP+ over the board never reaches a square` | `d6d7e754873f` | `5597e88bb08a` | `ev_911520e530c5fa10…` |
| M4 | forbidden engine call | `cheat_clip()` calls `ecall("remove_buts", remove_buts)` | 1 | `67/68` ×4 — `FAILED [...]: panel never calls remove_buts` | `91e8556566a0` | `5597e88bb08a` | `ev_bdff17b4cd949100…` |
| M5a | logic knob | `inc_ammo, 3 → 5`, contract untouched | 1 | `65/68` ×4 — `ammo buttons change state`, `SAFE mode blocks the 2nd mutating call`, `ammo cheat changes state` | `293bb176db95` | `5597e88bb08a` | `ev_7995855f6203cde8…` |
| M5b | logic knob + contract | +5 with the log line and **three** contract rows moved | 1 | `67/68` ×4 — `FAILED [...]: SAFE mode blocks the 2nd mutating call` | `3866438a2983` | `2a93297ffdde` | `ev_1918b7ba366c3629…` |
| M5c | logic knob + contract | +5 with **all four** rows that encode the step moved | **0** | `68/68` ×4 | `3866438a2983` | `76f7c6e70221` | `ev_31df0e6e896c8532…` |
| M6 | engine semantics | static card probe assumes value-yielding `all()` (`local c = a`) | 1 | `default-value: 68/68`, then the `default-pair` run **crashes the harness**: `KeyError: 'Right-hand'` at `<shotgun-king-anew>/tools/mod_smoketest.py:1126` | `4f91bc56b779` | `5597e88bb08a` | `ev_8a8ab02bcc2dd362…` |

Every mutant's capture shows `filesystem_effects: unchanged` for the run
itself (the mod does not write to its own folder) and the mutated hash in
`files_before`, so each verdict is bound to the exact bytes that produced it.

## 3. What the results say

Observation / derivation / inference labels follow REA's rule.

- **Observation.** A UI *layout* change (M1) passes untouched: the harness
  finds buttons from what the panel draws, so geometry is free to move.
- **Observation.** A UI *label* change (M2) fails immediately in all four
  variants. **Derivation:** the player-facing label is a pinned contract
  row because it is the handle both the player and the harness use to reach
  the panel. Renaming is allowed, but only together with the contract — and
  the owner's notes also pin the menu id `SK Rework`, so that is a second row
  to move.
- **Observation.** The run-6 defect class (M3) and the build-7 mistake (M4)
  are each caught by exactly one named row. **Derivation:** the owner already
  turned both live failures into executable contract rows; this is the
  UI↔engine behaviour contract working as intended
  (`workbench/skills/universal-agent-context/references/ui-behaviour-contract.md`).
- **Observation.** A logic knob (M5a) is pinned in **four** places across two
  scenarios (`amount=3` log row, `ammo buttons change state`, `ammo cheat
  changes state`, `SAFE mode blocks the 2nd mutating call`). My first
  "deliberate" contract update (M5b) moved three and the harness caught the
  fourth. Only M5c passes. **Derivation:** logic can be changed without
  breaking the mod when *every* row that encodes the value moves in the same
  commit; the harness enumerates the rows you missed. **Inference
  (recommendation to the owner):** name the step once in the harness
  (`AMMO_RESERVE_STEP = 3`) so an intended change is one edit, not four.
- **Observation.** The engine-semantics mutation (M6) passes under
  value-yielding `all()` and fails under the (index, value) form — but it
  fails as a Python `KeyError` inside the harness rather than as a `FAILED`
  row. **Derivation:** the verdict is still non-pass (exit 1), which is
  fail-closed by accident, not by design. **Inference (harness defect for
  the owner's WORKLIST):** `<shotgun-king-anew>/tools/mod_smoketest.py:1126` should report a
  `FAILED [mode]: parser all card fields` row when `card_fields` lacks the
  key, so a semantics regression reads like every other regression.
- **Observation.** `rea compare-process-captures` reports `status: changed`
  for every pair, including M1 and M5c, with `first_divergence` in the
  `filesystem` dimension at the `before` snapshot (the mutated script hash)
  and `exit: changed` because exit comparison includes `settlement.elapsed_ms`
  (62 ms vs 65 ms). **Derivation:** REA's compare is a difference reporter,
  not a pass/fail oracle; the pass/fail judgement comes from the harness
  rows inside the Evidence frames. Use it to prove *what* differed, not
  *whether it is fine*.

## 4. The obligation ledger (REA 6.4.0)

`rea build-reconstruction-obligation-ledger` over the nine records and five
reviewed obligations. Ledger `rol_2ff17443401b5513…`, closure digest
`802e29d908dc8350…`, status **unknown**, 6 obligations (5 reviewed + 1
generated from the captures), **0 verified**, 6 required open.

| obligation | authority it really needs | ledger status | why it stays open (REA diagnostics, verbatim codes) |
|---|---|---|---|
| `ui.panel.click-isolation` — a panel click never reaches a board square (run-6 class) | original: `runtime`; verifier: **`live-observation`** | `unknown` | `unavailable-authority: live-observation`; `missing-original-case` ×2 (the live runs 5/6 exist only as the owner's prose, not as Evidence); `residual-unknown: sugar-input-path-not-observed-here`; `weak-verifier-authority: Verifier authority does not satisfy live-observation` |
| `ui.panel.no-remove-buts` | original `runtime`; verifier `integration` | `implemented` | `weak-fixture-authority` ×2, `weak-verifier-authority` (see below) |
| `ui.panel.tab-label` | original `runtime`; verifier `integration` | `implemented` | same |
| `logic.cheat-ammo.step` | original `runtime`; verifier `integration` | `implemented` | same |
| `runtime.all-iterator.dual-semantics` | original **`external`** (which form the shipped SUGAR yields) | `unknown` | `residual-unknown: sugar-all-semantics-unconfirmed`; `static-only: No external authority characterizes the original finite behavior` |
| generated `obl_82bad73e…` (captured packaged-process lifecycle) | — | `unknown` | `missing-owner`; `duplicate-definition` (nine captures share one scenario commitment); four `unavailable-authority` rows copied from the capture's residual unknowns |

Two things the ledger made explicit that a green test run would have hidden:

1. **The run-6 row cannot be closed from here.** It needs live observation of
   the real game. The harness models the engine's click path from the owner's
   notes (`<shotgun-king-anew>/notes/game-internals.md`); that is a model, and REA refuses to let
   a model close a live-behaviour claim. The "required next evidence" is
   recorded in the ledger input: run the real game with the mod, click CLIP+
   over an occupied square, keep the log and a video.
2. **REA 6.4.0 cannot mark anything `verified` from CLI captures at all.**
   Reading `dist/application/ReconstructionObligationAuthority.js`: fixture
   and verifier evidence must be a record with `predicate_type
   "rea.reconstruction-proof"` and `operation "verify_reconstruction_obligations"`
   whose result enumerates the obligation, fixture, case and claim ids. A
   `grep -rn` over the installed package and over the owner's `rea-fork`
   (`f178bf1`, same version) finds that string only in the consumer; nothing
   produces such records. So the best reachable state for the three
   code-property rows is `implemented` (owner, fixtures, verifier and runtime
   original cases all bound). That is a property of this REA release, not of
   the mod.

## 5. Answer to the question

*Can the UI or logic be changed without breaking the game?*

- Within what is testable here: **yes, for changes that keep the contract**
  (M1, M5c), and the contract tells you in one run which rows an intended
  change must move (M2, M5a/M5b). Breaking changes of the two classes that
  actually hurt the owner in runs 6–7 (M3, M4) are caught by name.
- For the live game: **unknown by construction.** The harness is a fake
  engine; REA's ledger keeps the live-behaviour row open until a real-game
  observation exists. Nothing in this sandbox can change that, and nothing
  here claims otherwise.

## 6. Not verifiable here

- Live game behaviour (no binary, no `data.sgr`, no Windows; none fetched).
- Whether SUGAR's `all()` yields values or pairs (the harness tests both; the
  shipped engine decides).
- REA's host check reports `unsupported_host: debian 12`; process capture and
  the ledger ran anyway, but the native providers (Hopper/Ghidra/IDA) were
  absent and were not needed.
- The REA compare's `process: unknown` dimension (sampled process trees) —
  stated by REA itself in every capture's `limitations`.

## 7. Reproduce

```sh
git clone --depth 1 https://github.com/freeforall1932-design/shotgun-king-anew /tmp/refs/shotgun-king-anew
python3 -m venv /tmp/venv-lua && /tmp/venv-lua/bin/pip install lupa
mkdir -p /tmp/rea-run && cd /tmp/rea-run && npm init -y >/dev/null && npm i rea-agents@6.4.0
python3 rea_mod_safety_experiment.py --repo /tmp/refs/shotgun-king-anew \
  --rea /tmp/rea-run/node_modules/.bin/rea --python /tmp/venv-lua/bin/python --out /tmp/rea-exp
cp make-bundle.mjs /tmp/rea-run/ && cd /tmp/rea-run && node make-bundle.mjs /tmp/rea-exp/bundle.json /tmp/rea-exp/capture-*.json
./node_modules/.bin/rea evidence-export /tmp/rea-exp/bundle.json /tmp/rea-exp/bundle-canonical.json
python3 build_ledger_input.py --exp /tmp/rea-exp --bundle /tmp/rea-exp/bundle-canonical.json --out /tmp/rea-exp/ledger-input.json
./node_modules/.bin/rea build-reconstruction-obligation-ledger /tmp/rea-exp/ledger-input.json --format json
```

Evidence ids and hashes will differ per run (REA ids include timing); the
exit codes, failing rows and ledger statuses are the reproducible part.
