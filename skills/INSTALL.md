# Installing the portable skills folder

## Whole-folder route (recommended first migration)

Copy the downloaded skills folder into the target repository root. This is
independent of application runtime/build dependencies and needs no submodule
or network access once copied. Validate with Python 3.10+:

```sh
python3 skills/validate_skills.py --root . --layout portable --quiet
```

Append this paragraph to the destination's existing root AGENTS.md / CLAUDE.md
(or the instruction file your harness actually reads); **do not overwrite its
existing instructions or project decisions**:

> Read skills/universal-agent-context/SKILL.md and its required guide/session
> references. Read this project's authoritative status, handoff and decisions.
> Inspect the real build/source entry point. Load skills/qt6-cmake-cpp/SKILL.md
> only for Qt 6 CMake C++ work, or skills/lua-game-modding/SKILL.md for Lua mod
> work. Open only references relevant to the task. For UI/engine behavior changes,
> read skills/universal-agent-context/references/ui-behaviour-contract.md before
> editing. State what was actually tested and what remains unverified.

A folder at an arbitrary path is not automatically a discovered harness skill.
A loader explicitly reading these files works with a repository-reading agent.
For native discovery, install complete skill directories together under the
harness's documented skills directory (for example .agents/skills or
.claude/skills), preserving sibling relationships. Check the current harness
version/documentation rather than assuming support. In a chat-only interface,
attach the files or paste the relevant text; a local file path alone is not access.

## Integrating with skills-repo's generated catalog

The destination has an existing compiler and generated packs. Simply copying
new skill folders into its variants tree is not enough: the old compiler has
a fixed variant list and does not preserve all nested assets.

1. First keep this folder as skills/ and use the explicit loader above. This
   avoids touching the existing register/compiler products during migration.
2. Review the historical compiler-assets patch in the testing repository's
   research material against the destination's **current** revision. Do not
   apply the old full-directory replacement blindly: it also retires registers.
3. If adopting the catalog route, copy each complete skill into the catalog's
   variants tree, preserve sibling names, support dynamic discovery and copy
   every non-generated supporting asset verbatim into generated skill packs.
4. Adapt catalog README/index entries, run compiler tests, regenerate packs
   twice and compare bytes. Check nested scripts/templates and the universal
   guide hash in every pack. Test an actual destination harness session.
5. Keep a single authoring source per repository. Never independently edit
   generated packs. Record the source commit and promotion date.

Optional compiler-test dependencies are pytest and PyYAML; they are not
requirements for reading these skills or running the portable validator.
Dionysus remains the testing ground; skills-repo is the distribution copy.
Application builds must not depend on downloading either repository.

## Verification limits

A passing skill gate proves structure and the checks it executes, not that an
agent followed instructions, compiled templates, or improved output. Evaluate
usefulness with comparable real tasks: same starting revision, tests and
acceptance criteria, then compare regressions, missed requirements and review
work with/without the relevant skill. Historical experiment results are not a
controlled measurement of skill effectiveness.
