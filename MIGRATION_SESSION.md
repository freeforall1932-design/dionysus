# Portable-folder migration — 2026-10-18

Repository: freeforall1932-design/dionysus
Branch: arena/529d6ec3-dionysus
Base: 7a2c7103061b1cda390bd18a8d05946200e6a508

Loaded: universal-agent-context wrapper, v4 guide and session protocol; Qt
workload wrapper for applicability/packaging assessment. Existing project
reports, defect logs, experiment scripts and validator were inspected.

## Owner intent

Keep Dionysus as a testing ground with root-accessible skills. Provide three
real folders that can be downloaded and dropped into the existing project and
skills repositories. Do not move or overwrite the destination repositories in
this session. Do not merge automatically.

## Changed

- Moved the live skills and two project-support folders to the root; retained
  three compatibility symlinks so historical workbench paths keep resolving.
- Added project MIGRATION.md files for dependencies, copy layout, exact command
  cwd, optional tool versions, evidence limits and safe scratch reproduction.
- Added an original experimental lua-game-modding skill; retained all original
  Qt/universal assets and the original universal v4 bytes/hash.
- Added root loaders, catalog/install instructions and policy distinguishing
  Dionysus testing from skills-repo distribution. Kept historical source
  attributions in skills/HISTORY.md, not as current installation instructions.
- Added isolated portable validation, deterministic ZIP creation with manifests,
  extraction/byte checks, regression tests and CI artifact upload.
- Updated workbench index/readme/loaders and CI path triggers.

## Verified locally

- Workbench compatibility validation: 375 passed, 0 failed.
- Portable skills validation: 74 passed, 0 failed, including after independent
  extraction into a temporary directory without the workbench.
- Packaging regression suite: 5 passed. Covers deterministic archives, real
  roots/legacy links, symlink refusal, output containment and negative reference
  detection. The initial extracted-README failure was fixed before completion.
- Qt lint self-test: PASS; own templates: no lint findings.
- Existing magnet-excavator suites: 142 passed.
- Python compileall on live roots/workbench: passed.
- git diff --check: passed before commit.
- Three generated ZIPs: each contains one top-level folder, every payload byte
  verified after extraction, plus a SHA-256 file manifest. Generated archives
  live in ignored dropins and are rebuilt/uploaded by CI, not stored in Git.

## Partial / left

No changes to gifscythe, shotgun-king-anew or skills-repo remotes. The old
research integration bundle is intentionally left historical. No external
register retirement or compiler integration was silently applied. No new game
or Qt application behavior was implemented. Root project folders contain
supporting material, not application source or authoritative project state.

## Not verifiable here

Real-game behavior, desktop GUI acceptance, clean-machine package acceptance,
Qt template compilation and measured with/without-skill output uplift. REA's
historical capture experiment was not rerun. Destination harness discovery and
Windows compatibility-link behavior were not executed. Portable root payloads
do not require symlinks; only historical workbench paths do.

## Docs touched / next action

Root README/loaders, this log, both project migration guides, skill README and
INSTALL, experimental Lua skill, workbench README/index/loaders. Review the PR,
inspect CI for its exact revision, then merge only on owner direction. After
merge, download the three root folders from the repository ZIP or the CI
portable-dropins artifact; append loaders instead of overwriting existing ones.
Record source and destination commit IDs in each destination's own handoff.

## First remote CI and follow-up

Push run 39106408930 passed all jobs on commit 53a750e, including ZIP artifact
upload. It reported upload-artifact v5 targeting deprecated Node 20. Checked
upstream action metadata on 2026-10-18: v6 declares node24; changed the new
artifact step to v6. Final-revision CI is reported in the PR/session response.
PR: https://github.com/freeforall1932-design/dionysus/pull/4
