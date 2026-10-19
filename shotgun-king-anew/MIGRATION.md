# Shotgun King Anew drop-in: dependencies and reproduction

Prepared 2026-10-18. Copy this entire folder as shotgun-king-anew inside the
existing project checkout; it is an experiment/support folder, **not the game
or full mod source**. Compare any existing destination folder before copying.
Keep root HANDOFF.md, WORKLIST.md, engine notes and the real mod/test code.
Copy the separate skills folder into the checkout root and append its loader
to existing agent instructions. Load the universal and lua-game-modding lanes,
**not the Qt lane**. Record source/destination revisions and date in the handoff.

The historical experiment targets project commit
4c4bf1bcc9e21c4b274736363e88e3f99065f157. Its saved source hashes and conclusions
must not silently become claims about a newer project revision.

## Required vs optional dependencies

| Operation | Dependencies |
|---|---|
| Read skills and validate them | Repository-reading agent; Python 3.10+ for the stdlib-only portable gate |
| Existing mod smoke tests | Python with lupa; historical experiment used lupa 2.8 and its default/LuaJIT 2.1 runtimes |
| Run the actual mod | Legitimately installed compatible Shotgun King/SUGAR game and its mod loader; see project INSTALL.md |
| Optional REA capture/ledger experiment | Git; disposable project clone; Node/npm; rea-agents 6.4.0; Python/lupa environment |
| Existing project install/save tools | Python and/or PowerShell as required by their own instructions; backup user data first |

REA, Node and lupa are **development/experiment dependencies**, not additions
to the shipped Lua mod. Qt/CMake are not needed. Game binaries and data.sgr
are neither included nor to be fetched by these instructions. Audit asset and
code redistribution permissions independently.

## Basic checks (no REA)

From the destination checkout root after copying skills:

```sh
python3 skills/validate_skills.py --root . --layout portable --quiet
python3 -m venv .venv-mod
.venv-mod/bin/python -m pip install lupa==2.8
.venv-mod/bin/python tools/mod_smoketest.py
```

POSIX syntax shown; Windows uses the virtual environment's Scripts/python.exe.
Check the reported runtimes: a missing LuaJIT variant must be reported, not
silently counted as a pass. The historical harness result was 68 checks for
each of four runtime/iterator variants, not proof of real-game execution.

## Reproduce the optional mutation/capture experiment safely

**Danger:** rea_mod_safety_experiment.py calls git checkout -- on tracked mod
and harness files at startup and after mutations. It discards local edits in
those files. Never aim it at the working project. The sequence below creates
an independent scratch clone and keeps dependencies/output out of the repo.

From the destination project root, use a POSIX shell (Linux/WSL/macOS):

```sh
PROJECT="$(pwd)"
SUPPORT="$PROJECT/shotgun-king-anew"
SCRATCH="$(mktemp -d)"
git clone https://github.com/freeforall1932-design/shotgun-king-anew "$SCRATCH/project"
git -C "$SCRATCH/project" checkout --detach 4c4bf1bcc9e21c4b274736363e88e3f99065f157
python3 -m venv "$SCRATCH/venv"
"$SCRATCH/venv/bin/python" -m pip install lupa==2.8
mkdir "$SCRATCH/rea"
(cd "$SCRATCH/rea" && npm init -y && npm install --save-exact rea-agents@6.4.0)
REA="$SCRATCH/rea/node_modules/.bin/rea"
python3 "$SUPPORT/rea_mod_safety_experiment.py" --repo "$SCRATCH/project" --rea "$REA" --python "$SCRATCH/venv/bin/python" --out "$SCRATCH/results"
cp "$SUPPORT/make-bundle.mjs" "$SCRATCH/rea/make-bundle.mjs"
node "$SCRATCH/rea/make-bundle.mjs" "$SCRATCH/results/bundle.json" "$SCRATCH"/results/capture-*.json
"$REA" evidence-export "$SCRATCH/results/bundle.json" "$SCRATCH/results/bundle-canonical.json"
python3 "$SUPPORT/build_ledger_input.py" --exp "$SCRATCH/results" --bundle "$SCRATCH/results/bundle-canonical.json" --out "$SCRATCH/results/ledger-input.json"
"$REA" build-reconstruction-obligation-ledger "$SCRATCH/results/ledger-input.json" --format json > "$SCRATCH/results/ledger.json"
printf 'Keep results and npm lockfile for reproduction: %s\n' "$SCRATCH"
```

Run commands in order and stop on any error. Historical Node was 22.22.3;
check the pinned package's engine requirements against your installed Node.
Keep its generated package-lock.json and dependency/runtime versions with new
evidence: pinning the top-level package alone does not freeze transitive deps.

Copying make-bundle.mjs beside node_modules is intentional: it imports internal
rea-agents/dist modules, which resolve relative to the script, not simply the
current shell directory. A future REA version may break these private imports.
Do not upgrade it as part of a reproduction without recording the difference.

Mutation-run exit zero means the capture pipeline completed, **not that every
mutant passed or every expected outcome was asserted**. Inspect results.json:
baseline, M1 and M5c historically exit 0; M2, M3, M4, M5a, M5b and M6 exit 1.
Compare failures and source hashes; regenerated evidence IDs/timings can differ.
Exact-text mutation patches intentionally fail when source assumptions drift.

## Bonus skill and next useful improvements

The new lua-game-modding skill covers hook chains, allowed engine globals,
input consumption, iterator conventions, Lua version compatibility, save safety
and honest fake-engine evidence. It is experimental guidance, not a certified
mod framework. Keep project-specific constants and decisions in this project.

Candidate follow-ups (not silently implemented by this migration): name the
ammo step once in the harness; turn iterator-regression KeyError into a clear
failed assertion; add an automatic expected-mutant-outcome check; add a dirty
checkout refusal to the mutation runner. Until then, use scratch clones only.

## Evidence limits

Read the dated experiment report and saved results for historical evidence.
The saved REA ledger has zero verified obligations; weak evidence-authority
bindings and missing live observation remain visible. It is not a mod safety
certificate. **Not verifiable here:** real-game click-through, rendering,
shipped iterator semantics, interaction with other mods and actual agent-output
uplift. Record a live-game test separately if the owner can run one.
