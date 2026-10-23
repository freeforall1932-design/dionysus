# Dionysus — skills testing ground

The owner designates this repository as a **skills testing ground**. Keep reusable
skills available at the repository root even after promoting snapshots to
skills-repo. The original Hyprland configuration remains in assets and dotfiles;
other experiments remain under workbench.

## Portable skills drop-in

| Root folder | Destination | Start here |
|---|---|---|
| `skills/` | skills-repo root, or a consuming project checkout root | [Skills catalog](skills/README.md), [installation](skills/INSTALL.md), [defect log](skills/SKILL_DEFECT_LOG.md) |

The earlier three portable project drop-in folders (`gifscythe/`,
`shotgun-king-anew/`, and `Odysseus API model team kit/`) have been migrated to
their respective repositories and removed from this repository.

Generate a verified, reproducible `dropins/skills.zip` archive with a SHA-256
manifest:

```sh
python3 package_dropins.py
```

The archive is generated, not committed. Recreate it at the revision you intend
to distribute, and review diffs before extracting into an existing repository.

Root AGENTS.md and CLAUDE.md tell repository-reading agents how to load these
skills; a harness that does not read them needs an explicit first-message
instruction. No claim is made that arbitrary folders are auto-discovered.

## Source of truth and policy

- Root `skills/` is the live reusable catalog here. Test fixes here; promote a
  reviewed, revision-labelled snapshot to skills-repo for distribution.
- Authoritative project status, handoffs, and decisions live in each project's
  own repository (`freeforall1932-design/gifscythe`,
  `freeforall1932-design/shotgun-king-anew`,
  `freeforall1932-design/odysseus-fork-but-api-dev`).
- `workbench/skills` is a compatibility symlink to root `skills/`, not a second
  copy.
- Research drop-in bundles under `workbench/research/` are dated integration
  artifacts, not an alternative authoring catalog.
- Keep application builds independent of downloading skills. Do not silently
  replace existing project instructions, universal-guide copies, or decisions.

## Checks

```sh
python3 skills/validate_skills.py --quiet
python3 skills/validate_skills.py --root . --layout portable --quiet
python3 -m unittest -v test_package_dropins
python3 package_dropins.py
```

The first command checks workbench compatibility; portable mode checks an
independent skills installation. Packaging verifies every archived byte after
extraction, rejects symlinks inside payloads, and validates the extracted skills
without access to workbench. None of these commands run a live game or certify
Qt template compilation. See MIGRATION_SESSION.md for earlier migration history.
