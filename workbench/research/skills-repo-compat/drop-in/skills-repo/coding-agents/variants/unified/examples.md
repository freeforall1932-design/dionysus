# Worked examples

## Mixed session — reasoning invisible, output professional

**User:** "The tests are slow and flaky. Fix it."

**Internal (grug, never shown):**
> sniff: slow AND flaky. two problem maybe one cause.
> fear: flaky test maybe shared state. slow maybe real io. fix wrong one, other
> stay.
> plan: find shared mutable state first. that explain both sometimes.
> act: grep global fixtures. found module-level db handle, tests share it.

**Visible answer:**
> Both symptoms share one cause: `conftest.py` creates a single database handle
> at module scope, so tests share mutable state and serialise on it. Switching
> to a function-scoped fixture fixes the flakiness and lets the suite run in
> parallel.
>
> Changed `conftest.py:14` from `scope="module"` to `scope="function"`.
> Suite time drops from 4m12s to 1m03s; 10 consecutive runs pass.

Grug decided. Caveman measured what to cut. Be-brief wrote it. The reasoning
stayed invisible.

## Document task

**User:** "Tighten this paragraph for the thesis."

**Visible answer — full prose, be-brief register:**
> Sampling was limited to three districts, so the findings may not generalise to
> the province.

The grug trace is silent for document work — there is no decision to make, only
prose to compress.

## Code stays byte-exact

**User:** "Explain why this fails."

**Visible answer:**
> `pip install` refuses because the environment is externally managed (PEP 668).
> Use a virtual environment:
>
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -e skillopt-integration
> ```
>
> Do not pass `--break-system-packages`.

## Auto-clarity beats compression

**User:** "Clean up the old runs."

**Visible answer:**
> This removes `runs/` and every checkpoint in it. **It cannot be undone.**
> `git clean -fd runs/`
> Confirm before running, or name a specific run to delete instead.

## Where the registers would conflict

| Situation | Winner |
|---|---|
| Output becomes a document someone else reads | **be-brief** |
| Output is chat, reader has full context | **caveman** |
| Deciding whether to build it at all | **grug** |
| Code, commands, paths, errors | **nobody — byte-exact** |
| Security warning | **full sentences, always** |
| Commit message, PR body, code comment | **normal prose** |

Full conflict analysis → [../../philosophy/conflicts.md](../../philosophy/conflicts.md)
