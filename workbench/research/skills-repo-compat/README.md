# skills-repo compile dry run — artefacts

Companion to `workbench/research/skills-repo-and-unified-2026-10-14.md`
(section 4). Everything here was produced in a scratch clone of
`freeforall1932-design/skills-repo` at commit `84c9518`; **nothing was pushed
to that repository**. The clone lives in `/tmp` and is gone after the session —
re-create it with the commands below.

## Files

| File | What it is |
|---|---|
| `drop-in/` | **The folder to paste.** `drop-in/skills-repo/` is the final-state tree (`coding-agents/`, top-level `README.md`, `.github/workflows/tests.yml`) built on skills-repo `84c9518`; `drop-in/APPLY.md` has the three commands, the change table, what was verified and what is left to the owner; `drop-in/MANIFEST.sha256` hashes every file. The gate in this workbench fails if the skill copies inside it drift from `skills/`. |
| `catalog-changes.patch` | `git diff` of the drop-in against `84c9518` without the generated packs — for review (variants, compiler, tests, profiles, README, gate, CI). |
| `compile-skill-assets.patch` | The compiler + test part only: directory-discovered variants, verbatim asset copy, loader-mode paste with per-harness install dir, verbatim references for loader skills, layer-aware README text. A no-op for the four original registers (checked: packs byte-identical). |

## Re-run (about one minute, no network beyond github.com and pypi.org)

```sh
git clone -q --depth 1 https://github.com/freeforall1932-design/skills-repo /tmp/verify
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -q pytest pyyaml
cd /tmp/verify && rm -rf coding-agents && cp -r <dionysus>/workbench/research/skills-repo-compat/drop-in/skills-repo/. .
/tmp/venv/bin/python coding-agents/compile.py            # Compiled 8 agents x 3 variants
/tmp/venv/bin/python -m pytest -q coding-agents/tests   # 35 passed
python3 coding-agents/validate_skills.py                # validate_skills: 124 passed, 0 failed -> PASS
git add -A && /tmp/venv/bin/python coding-agents/compile.py && git diff --exit-code --stat -- coding-agents/packs   # (empty: CI's stale-pack check holds)
sha256sum coding-agents/packs/claude/skills/universal-agent-context/UNIVERSAL_AGENT_CONTEXT_v4.md   # 51f21f33… (same as source)
python3 coding-agents/packs/claude/skills/qt6-cmake-cpp/scripts/qt_lint.py --selftest             # selftest: PASS
```

The earlier experiments (unpatched compiler, v4 under references) are reproduced
by applying only `compile-skill-assets.patch` — or none of it — to the clone and
copying `workbench/skills/universal-agent-context` into `coding-agents/variants/`.

## Measured on 2026-10-14

| Configuration | Compile | Tests | `UNIVERSAL_AGENT_CONTEXT_v4.md` in packs | Paste file for codex/copilot/opencode |
|---|---|---|---|---|
| upstream `84c9518`, four registers | ok | 33 passed | n/a | `unified.md` 10,799 B |
| upstream compiler + our skill as-is | ok (silently) | 3 failed / 31 passed | **absent from all 7 packs**; packed SKILL.md still tells the agent to read it | 19,084 B |
| upstream compiler, v4 moved under `references/` | ok | 3 failed / 31 passed | present, sha256 identical | **75,086 B / 930 lines** (v4 inlined on every request) |
| patched compiler + `universal-agent-context` + `qt6-cmake-cpp` | ok, 7 agents × 6 variants | **36 passed** | present in claude/qwen/codex skill dirs, sha256 `51f21f33…` identical; `qt_lint.py` sha256 identical, self-test PASS; all 8 templates present | `universal-agent-context.md` 3,375 B; `qt6-cmake-cpp.md` 8,746 B; cursor `.mdc` 4,074 B |
| patched compiler, upstream variants only | ok | 33 passed, 1 skipped | n/a | byte-identical to upstream packs (`git status` empty) |
| **drop-in bundle** on a fresh clone (patched compiler v2, three registers retired, both skills in, 8 profiles, gate in CI) | ok, 8 agents × 3 variants, 199 pack files, deterministic | **35 passed**; gate 124 passed; SkillOpt tests 23 passed / 2 skipped | present in 6 skill-capable packs, sha256 identical; `qt_lint.py` identical, self-test PASS | `universal-agent-context.md` 3,747 B; `qt6-cmake-cpp.md` 9,453 B; `unified.md` 10,799 B; cursor `.mdc` 4,446 B |

The three upstream test failures in rows 2–3 are house rules, not Agent Skills
spec rules: the Cursor test hard-codes four rules (`assert 5 == 4`), and two
tests require an `examples.md` in every skill. The patch replaces the count with
the discovered variant count and accepts "examples.md **or** support files".
