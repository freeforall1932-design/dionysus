# Provenance — universal-agent-context

| Field | Value |
|---|---|
| Authority file | `UNIVERSAL_AGENT_CONTEXT_v4.md` |
| Version | v4 (unified), prepared 2026-10-13 |
| Source repository | `freeforall1932-design/gifscythe`, path `UNIVERSAL_AGENT_CONTEXT_v4.md` |
| Source commit (main tip when copied) | `97b075829cb0a2b52a9d34e45d275cd68bfba32a` (merge of PR #16, 2026-10-13) |
| Copied on | 2026-10-13 |
| SHA-256 | `51f21f331b0b708ed65824253e15ca73259e8fcc80dbf1d0439c60c207eda0d5` |
| Size | 54326 bytes, 563 lines |

The gate script (`validate_skills.py`, beside the skills directory) recomputes the hash and fails if the file drifts
from this record. To change the universal guide: write the new version as a new
file (`…_v5.md`) with its own "Appendix — provenance" naming what was promoted
and from which project session; update the table above; update the wrapper
`SKILL.md`; then retire the old file in the same commit so two versions never
appear equally authoritative (v4 §17.5).

## The two copies, and which is authoritative

As of 2026-10-13 the same bytes exist in two repositories: here and in
gifscythe's root. v4 §17.1 wants exactly one authoritative universal guide.
**This repository is the intended home** (the guide is cross-project by
definition; gifscythe is one consumer). The gifscythe copy should become either
(a) a pinned mirror that names this file's commit and hash, or (b) a one-line
pointer. That is a change *in gifscythe* and was deliberately not made in the
session that created this directory — it is recorded as a next action in
the owner's workbench runbook for that project (`dionysus/workbench/projects/gifscythe/NEXT_SESSION.md`). Until it lands, the hash above is how a
reader proves the copies have not diverged.
