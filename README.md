# Dionysus — skills testing ground and portable project support

The owner designates this repository as a **skills testing ground**. Keep reusable
skills available at the repository root even after promoting snapshots to
skills-repo. The original Hyprland configuration remains in assets and dotfiles;
other experiments remain under workbench.

## Four folders to download and drop into your repositories

| Root folder | Destination | Start here |
|---|---|---|
| `gifscythe/` | Existing gifscythe checkout, as a support subfolder of the same name | [Migration and dependencies](gifscythe/MIGRATION.md) |
| `shotgun-king-anew/` | Existing shotgun-king-anew checkout, as a support subfolder of the same name | [Migration and reproduction](shotgun-king-anew/MIGRATION.md) |
| `Odysseus API model team kit/` | Destination repository root; self-contained team-kit project folder | [Migration and dependencies](Odysseus%20API%20model%20team%20kit/MIGRATION.md) |
| `skills/` | skills-repo root; optionally copy into either project root too | [Skills catalog](skills/README.md), [installation](skills/INSTALL.md) |

These are **real directories, not symlinks**. Download the repository ZIP and
extract only the required folders, or generate four independent ZIPs:

```sh
python3 package_dropins.py
```

Output: dropins/gifscythe.zip, dropins/shotgun-king-anew.zip, dropins/skills.zip,
and dropins/Odysseus API model team kit.zip.
Each ZIP contains one top-level folder and a SHA-256 manifest. The archives are
reproducible and generated, not committed. Recreate them after merging at the
revision you intend to distribute. Never extract over existing files without
reviewing collisions. The Gifscythe and Shotgun King support ZIPs do not contain application source;
the team-kit ZIP includes its existing harness source, audits and planning.

Root AGENTS.md and CLAUDE.md tell repository-reading agents how to load these
skills; a harness that does not read them needs an explicit first-message
instruction. No claim is made that arbitrary folders are auto-discovered.

## Source of truth and migration policy

- Root skills is the live reusable catalog here. Test fixes here; promote a
  reviewed, revision-labelled snapshot to skills-repo for distribution.
- The Gifscythe and Shotgun King root folders hold supporting evidence/runbooks, not current
  application status. Authoritative project decisions remain in their repos.
- The Odysseus API model team kit folder is the live team-kit project, renamed
  for migration. Its planned Odysseus integration is not yet implemented.
- Old workbench paths are compatibility symlinks to these root directories;
  they are not additional copies. Windows checkouts without symlink support
  may not resolve old paths; use the real root folders and portable commands.
- Research drop-in bundles are historical snapshots, not an alternative live
  catalog. Do not apply their old destructive replacement recipes blindly.
- Keep application builds independent of downloading skills. Do not silently
  replace existing project instructions, universal-guide copies or decisions.

## Checks

```sh
python3 skills/validate_skills.py --quiet
python3 skills/validate_skills.py --root . --layout portable --quiet
python3 -m unittest -v test_package_dropins
python3 package_dropins.py
```

The first command checks workbench compatibility; portable mode checks an
independent skills installation. Packaging verifies every archived byte after
extraction, rejects symlinks inside payloads and validates the extracted skills
without access to workbench. None of these commands run the real game or certify
Qt template compilation. See MIGRATION_SESSION.md for this session's evidence.
