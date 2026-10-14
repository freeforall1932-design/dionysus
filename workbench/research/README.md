# research — dated surveys and assessments

Each page answers one question on one day, states what was verified and what
was not, and is listed in `index.json` with `read_when`/`skip_when` so an agent
can skip it. Pages are not updated in place; a new question gets a new dated
page. Executed artefacts that back a page (patches, measurements, scripts) live
in a sibling folder named after the page's topic.

| Page | Question | Artefacts |
|---|---|---|
| `research/modding-engines-2026-10-14.md` | which modding/reverse-engineering repositories apply to the owner's game projects, and is there a SUGAR playbook anywhere | none (survey; the REA experiment it motivated is under `projects/shotgun-king-anew/`) |
| `research/skills-repo-and-unified-2026-10-14.md` | does `universal-agent-context` compose with skills-repo's `unified` register; is skills-repo worth growing into a catalog; where should skills live | `research/skills-repo-compat/` — tested `compile.py` patch, re-run commands, measured sizes and hashes |
