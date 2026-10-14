# skills-repo compile dry run — artefacts

Companion to `workbench/research/skills-repo-and-unified-2026-10-14.md`
(section 4). Everything here was produced in a scratch clone of
`freeforall1932-design/skills-repo` at commit `84c9518`; **nothing was pushed
to that repository**. The clone lives in `/tmp` and is gone after the session —
re-create it with the commands below.

## Files

| File | What it is |
|---|---|
| `compile-skill-assets.patch` | `git diff` against `84c9518` touching only `coding-agents/compile.py` and `coding-agents/tests/test_compile.py`. Makes the compiler carry non-markdown and top-level skill files byte-for-byte, discover variants from `variants/` instead of a hard-coded list, and paste "loader" skills as body + file list instead of inlining their references. |

## Re-run (about one minute, no network beyond github.com and pypi.org)

```sh
git clone -q --depth 1 https://github.com/freeforall1932-design/skills-repo /tmp/refs/skills-repo
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -q pytest pyyaml
cd /tmp/refs/skills-repo
/tmp/venv/bin/python -m pytest -q coding-agents/tests          # baseline: 33 passed

# 1. unpatched compiler + our skill as-is  → compiles, but v4 and PROVENANCE are dropped from every pack
cp -r <dionysus>/workbench/skills/universal-agent-context coding-agents/variants/
# (register the key in VARIANT_ORDER / VARIANT_LABEL / VARIANT_BLURB first — the unpatched compiler ignores unknown directories)
/tmp/venv/bin/python coding-agents/compile.py
find coding-agents/packs -name 'UNIVERSAL_AGENT_CONTEXT_v4.md'   # → nothing

# 2. patched compiler + both dionysus skills
git checkout -- . && git clean -fdq
git apply <dionysus>/workbench/research/skills-repo-compat/compile-skill-assets.patch
cp -r <dionysus>/workbench/skills/universal-agent-context <dionysus>/workbench/skills/qt6-cmake-cpp coding-agents/variants/
/tmp/venv/bin/python coding-agents/compile.py                   # Compiled 7 agents x 6 variants
/tmp/venv/bin/python -m pytest -q coding-agents/tests          # 36 passed
sha256sum coding-agents/packs/claude/skills/universal-agent-context/UNIVERSAL_AGENT_CONTEXT_v4.md   # 51f21f33… (same as source)
python3 coding-agents/packs/claude/skills/qt6-cmake-cpp/scripts/qt_lint.py --selftest             # selftest: PASS

# 3. patched compiler, upstream variants only → generated packs identical to upstream
rm -rf coding-agents/variants/universal-agent-context coding-agents/variants/qt6-cmake-cpp
/tmp/venv/bin/python coding-agents/compile.py && git status --short coding-agents/packs   # (empty)
/tmp/venv/bin/python -m pytest -q coding-agents/tests          # 33 passed, 1 skipped
```

## Measured on 2026-10-14

| Configuration | Compile | Tests | `UNIVERSAL_AGENT_CONTEXT_v4.md` in packs | Paste file for codex/copilot/opencode |
|---|---|---|---|---|
| upstream `84c9518`, four registers | ok | 33 passed | n/a | `unified.md` 10,799 B |
| upstream compiler + our skill as-is | ok (silently) | 3 failed / 31 passed | **absent from all 7 packs**; packed SKILL.md still tells the agent to read it | 19,084 B |
| upstream compiler, v4 moved under `references/` | ok | 3 failed / 31 passed | present, sha256 identical | **75,086 B / 930 lines** (v4 inlined on every request) |
| patched compiler + `universal-agent-context` + `qt6-cmake-cpp` | ok, 7 agents × 6 variants | **36 passed** | present in claude/qwen/codex skill dirs, sha256 `51f21f33…` identical; `qt_lint.py` sha256 identical, self-test PASS; all 8 templates present | `universal-agent-context.md` 3,375 B; `qt6-cmake-cpp.md` 8,746 B; cursor `.mdc` 4,074 B |
| patched compiler, upstream variants only | ok | 33 passed, 1 skipped | n/a | byte-identical to upstream packs (`git status` empty) |

The three upstream test failures in rows 2–3 are house rules, not Agent Skills
spec rules: the Cursor test hard-codes four rules (`assert 5 == 4`), and two
tests require an `examples.md` in every skill. The patch replaces the count with
the discovered variant count and accepts "examples.md **or** support files".
