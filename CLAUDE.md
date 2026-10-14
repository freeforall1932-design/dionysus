# Agent instructions for this repository

Before touching this repository, load the skills in this order and say which you loaded:

1. `skills/universal-agent-context/SKILL.md`, then `skills/universal-agent-context/UNIVERSAL_AGENT_CONTEXT_v4.md` (§0–§3, §6, §16–§19 at minimum), then `skills/universal-agent-context/references/session-protocol.md`.
2. Inspect the repository's real build entry point; load the matching `skills/<workload>/SKILL.md` only if it matches (today: `skills/qt6-cmake-cpp/SKILL.md` for CMake + `find_package(Qt6)`).
3. If the task touches a UI or says "like app X": fill the tables in `skills/universal-agent-context/references/ui-behaviour-contract.md` before any mockup or widget edit.
4. If the task is about a project listed in `projects/README.md`, follow that pointer to the project's own overlay (status register, handoff, decisions) and treat **that** as the overlay. Repository evidence outranks every skill; the owner's latest explicit instruction outranks every document.

Stop at breakpoints that need the owner's decision. Before ending: `python3 skills/validate_skills.py` must pass if `skills/` or `projects/` changed; commit every edit; end with the v4 §19 session-log fields including "Not verifiable here".

Layout and the reasoning behind it: `skills/README.md`. Using these skills from another repository or harness: `skills/INSTALL.md`.
