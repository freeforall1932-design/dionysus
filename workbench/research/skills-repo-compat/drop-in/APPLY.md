# Drop-in for `freeforall1932-design/skills-repo` — the catalog state

Built 2026-10-14 against skills-repo commit `84c9518` (the current tip of its
default branch at build time). It is the **final state** of the coding-agent
catalog the owner described: the three register variants retired, `unified`
kept as the one register, the dionysus `universal-agent-context` and
`qt6-cmake-cpp` skills added, the compiler extended, a triage index and a gate
added, and all harness packs regenerated. Nothing here was pushed anywhere —
the owner applies it.

## Apply (three steps)

```sh
cd <your skills-repo clone>            # on a branch, from the tip of main
rm -rf coding-agents                   # the bundle replaces the directory wholesale
cp -r <this folder>/skills-repo/. .    # coding-agents/, README.md, .github/workflows/tests.yml
git add -A && git commit -m "coding-agents: catalog (unified + universal-agent-context + qt6-cmake-cpp), compiler assets, gate"
```

That is enough for the repository's own CI to pass: the packs in the bundle are
the ones `compile.py` regenerates, so the "generated packs are stale" job stays
green without running anything locally. If you prefer to see it yourself:

```sh
python -m pip install pytest pyyaml
python coding-agents/compile.py            # Compiled 8 agents x 3 variants
pytest coding-agents/tests -q              # 35 passed
python coding-agents/validate_skills.py    # validate_skills: 124 passed, 0 failed -> PASS
```

`MANIFEST.sha256` lists every file in `skills-repo/` with its hash; `sha256sum -c`
from inside that folder verifies the download.

## What changes versus `84c9518`

| Area | Change |
|---|---|
| `coding-agents/variants/` | `be-brief-output`, `caveman-output`, `grug-reasoning` removed. `unified` unchanged. `universal-agent-context` (hash-pinned `UNIVERSAL_AGENT_CONTEXT_v4.md`, `PROVENANCE.md`, two references) and `qt6-cmake-cpp` (eight references, eight templates, `scripts/qt_lint.py`) added, byte-identical to `dionysus/workbench/skills/`. |
| `coding-agents/compile.py` | Variants discovered from the directory (no `VARIANT_ORDER` edit per skill); every file beside `SKILL.md` that is not a one-level markdown reference is copied **verbatim** into the skill dirs; a skill with `metadata.paste: loader` (or any such files) is pasted as body + file list instead of inlined, and the list names the install directory for that harness; loader skills' references are copied verbatim too; README text about registers is generated from each skill's `layer`. For the previous four registers the compiler is a no-op (checked: packs byte-identical). |
| `coding-agents/tests/test_compile.py` | Variant list and Cursor rule count derived from the directory; `examples.md` **or** support files; new tests: assets byte-identical in packs, loader paste lists every file and names the install dir, loader references verbatim, exactly one register ships. 35 tests. |
| `coding-agents/profiles/` | `codex.json`: project skill dirs `.agents/skills` and `.codex/skills` (from the Codex source, `host_roots.rs`). `copilot.json`, `opencode.json`: skills now `supported` with their documented directories. `gemini.json`: new (GEMINI.md + `.agents/skills` / `.gemini/skills`). `cursor.json`, `qwen.json`: notes and re-check dates only. Every `verification` block names the file and commit it was read from and says "not executed". |
| `coding-agents/index.json`, `coding-agents/validate_skills.py` | Triage table and gate (same script as the dionysus workbench, `--layout catalog` auto-detected). The gate fails when a `variants/` directory has no index entry, an entry points at a missing file, or `coding-agents/README.md` does not name the skill; also checks frontmatter, path claims, the v4 hash pin, machine paths, Python syntax and the `qt_lint.py` self-test. |
| `coding-agents/README.md`, `README.md` (top level), `coding-agents/philosophy/conflicts.md` | Catalog table with open-when / skip-when, the loading rule for the three layers, the harness table with skill directories, and the `unified` + `universal-agent-context` composition note. The Claude-app sections of the top-level README are untouched. |
| `.github/workflows/tests.yml` | One added step after the pack tests: `python coding-agents/validate_skills.py`. |
| `coding-agents/packs/` | Regenerated: 8 agents × 3 skills, 199 files, deterministic (two consecutive compiles byte-identical). |

Full text diff without the packs: `../catalog-changes.patch` (5.7 k lines; the
variants are most of it). Compiler + tests only: `../compile-skill-assets.patch`.

## Verified before shipping (executed 2026-10-14)

- Fresh clone of `84c9518` + this bundle → `pytest`: 35 passed; gate: 124 passed; packs unchanged after a second `compile.py` (the CI stale-pack condition); `skillopt-integration` tests: 23 passed, 2 skipped (unchanged by the bundle).
- `UNIVERSAL_AGENT_CONTEXT_v4.md` sha256 `51f21f331b0b708e…` and `qt_lint.py` sha256 `50194e4e75efca45…` identical in source and in every skill pack; `qt_lint.py --selftest` passes when run from inside a pack.
- Paste sizes for the paste-only route (codex pack): `unified.md` 10,799 B (register, inlined as before); `universal-agent-context.md` 3,747 B and `qt6-cmake-cpp.md` 9,453 B (loader: body + file list); Cursor `.mdc` 4,446 B. The unpatched compiler would have produced 75 KB paste files or silently dropped the guide.

## Not done here — the owner decides

- **Claude-app product** (`claude-skills/`, `pseudo-skills/`, `caveman-universal/`, the top-level README's combos A–E): untouched. The retirement covers the *coding-agent* variants only; the office/academic zips still ship caveman, be-brief and grug.
- `docs/session-handoff.md` and `docs/improvement-log.md` still describe the four-variant era; they are dated handoff notes, left as history.
- `skillopt-integration/configs/{be-brief,caveman,grug}.yaml` still exist. They train seed copies under `envs/caveman_brief/skills/`, not the removed variants, so nothing breaks; delete them when the registers are not coming back.
- No harness was launched. Every profile change is a documentation/source review with the commit named in its `verification` block; a live install on each harness is the next evidence step (`../../harness-skill-support-2026-10-14.md` lists what to check).
