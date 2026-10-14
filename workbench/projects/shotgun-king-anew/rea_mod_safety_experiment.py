#!/usr/bin/env python3
"""Mutation experiment: can the sk-rework mod's UI or logic be changed without
breaking it, and does the repo's own harness catch the breaking changes?

Every run is wrapped in REA's `capture-process` so each result is an Evidence
record that binds the exact `script.lua` SHA-256 to the exit code and the
terminal output. Nothing here runs the real game; see the experiment write-up
for what that means.

Usage (all paths explicit; nothing is guessed):
    python3 rea_mod_safety_experiment.py \
        --repo /tmp/refs/shotgun-king-anew \
        --rea /tmp/rea-run/node_modules/.bin/rea \
        --python /tmp/venv-lua/bin/python \
        --out /tmp/rea-exp

The repo checkout is mutated in place and restored with `git checkout --`
after every mutation. Run it only on a scratch clone.
"""
import argparse
import json
import os
import subprocess
import sys

SCRIPT = os.path.join("modded", "sk-rework", "script.lua")
TEST = os.path.join("tools", "mod_smoketest.py")

# (id, kind, description, [(relative file, old, new), ...], expectation)
MUTATIONS = [
    ("M1", "ui-layout", "widen the dev panel: PANEL_W 204 -> 216",
     [(SCRIPT, "local PANEL_W = 204\n", "local PANEL_W = 216\n")],
     "pass: the harness locates buttons from what the panel draws, so geometry may move"),
    ("M2", "ui-label", "rename the tab the player clicks: \"SK DEV\" -> \"SK-DEV\"",
     [(SCRIPT, 'draw_button(tx, ty, tw, th, "SK DEV", ui.hot == "tab", ui.open)',
       'draw_button(tx, ty, tw, th, "SK-DEV", ui.hot == "tab", ui.open)')],
     "fail: the visible label is a pinned contract row (it is how the player and the harness reach the panel)"),
    ("M3", "ui-behaviour", "re-introduce the run-6 click-through: stop consuming the click",
     [(SCRIPT, "\tmcl = false\n\tmcr = false\n\tmlb = false\n\tif ui.open and MOUSE then",
       "\tif ui.open and MOUSE then")],
     "fail: 'RUN-6 BUG: CLIP+ over the board never reaches a square' and the modal swallow row"),
    ("M4", "forbidden-engine-call", "CLIP+ calls the engine's remove_buts() (the build-7 mistake)",
     [(SCRIPT, "\tlog(\"SKE|cheat_clip|chamber_max=\" .. sv(stack.chamber_max)",
       "\tecall(\"remove_buts\", remove_buts)\n\tlog(\"SKE|cheat_clip|chamber_max=\" .. sv(stack.chamber_max)")],
     "fail: 'panel never calls remove_buts'"),
    ("M5a", "logic-knob", "+3 AMMO gives +5 but the contract still says 3",
     [(SCRIPT, 'ecall("inc_ammo", inc_ammo, 3)', 'ecall("inc_ammo", inc_ammo, 5)')],
     "fail: 'ammo buttons change state' pins +3; the log row still claims amount=3"),
    ("M5b", "logic-knob+contract", "+5 AMMO with the log line and the contract moved deliberately",
     [(SCRIPT, 'ecall("inc_ammo", inc_ammo, 3)', 'ecall("inc_ammo", inc_ammo, 5)'),
      (SCRIPT, 'log("SKE|cheat_ammo|kind=reserve|amount=3|ammo_before="',
       'log("SKE|cheat_ammo|kind=reserve|amount=5|ammo_before="'),
      (TEST, 'has("SKE|cheat_ammo|kind=reserve|amount=3")', 'has("SKE|cheat_ammo|kind=reserve|amount=5")'),
      (TEST, '("ammo buttons change state", ammo_after == before_ammo + 3',
       '("ammo buttons change state", ammo_after == before_ammo + 5'),
      (TEST, '("ammo cheat changes state", ammo_after == before_ammo + 3)',
       '("ammo cheat changes state", ammo_after == before_ammo + 5)')],
     "pass expected when written; the run shows one more pinned row (see write-up)"),
    ("M5c", "logic-knob+contract", "+5 AMMO with every row that encodes the step moved (4 rows, 2 scenarios)",
     [(SCRIPT, 'ecall("inc_ammo", inc_ammo, 3)', 'ecall("inc_ammo", inc_ammo, 5)'),
      (SCRIPT, 'log("SKE|cheat_ammo|kind=reserve|amount=3|ammo_before="',
       'log("SKE|cheat_ammo|kind=reserve|amount=5|ammo_before="'),
      (TEST, 'has("SKE|cheat_ammo|kind=reserve|amount=3")', 'has("SKE|cheat_ammo|kind=reserve|amount=5")'),
      (TEST, '("ammo buttons change state", ammo_after == before_ammo + 3',
       '("ammo buttons change state", ammo_after == before_ammo + 5'),
      (TEST, '("ammo cheat changes state", ammo_after == before_ammo + 3)',
       '("ammo cheat changes state", ammo_after == before_ammo + 5)'),
      (TEST, '("SAFE mode blocks the 2nd mutating call", safe_after == safe_before + 3',
       '("SAFE mode blocks the 2nd mutating call", safe_after == safe_before + 5')],
     "pass: a logic change is safe when every contract row that encodes it moves in the same commit"),
    ("M6", "engine-semantics", "card pool assumes value-yielding all() (LuaJIT (i,v) form breaks)",
     [(SCRIPT, "\tfor a, b in all(CARDS) do\n\t\tlocal c = iter_value(a, b)\n\t\tcard_count = card_count + 1",
       "\tfor a, b in all(CARDS) do\n\t\tlocal c = a\n\t\tcard_count = card_count + 1")],
     "fail only in the *-pair variants: an engine-version difference the fake engine models"),
]


def sh(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and r.returncode != 0:
        raise SystemExit(f"command failed ({r.returncode}): {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    return r


def apply(repo, edits):
    """Apply every edit or none: each `old` must occur exactly once."""
    staged = {}
    for rel, old, new in edits:
        path = os.path.join(repo, rel)
        src = staged.get(path)
        if src is None:
            with open(path, encoding="utf-8") as fh:
                src = fh.read()
        if src.count(old) != 1:
            raise SystemExit(f"{rel}: expected exactly one occurrence of {old!r}, found {src.count(old)}")
        staged[path] = src.replace(old, new, 1)
    for path, src in staged.items():
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(src)


def restore(repo):
    sh(["git", "checkout", "--", SCRIPT, TEST], cwd=repo)


def capture(rea, python, repo, out, label):
    scenario = {
        "executable": python,
        "arguments": [TEST],
        "working_directory": repo,
        "environment": {"PYTHONDONTWRITEBYTECODE": "1"},
        "filesystem_observation_paths": [os.path.join(repo, "modded", "sk-rework"),
                                         os.path.join(repo, "tools", "mod_smoketest.py")],
        "terminal": {"columns": 120, "rows": 40, "scrollback": 2000},
        "events": [],
        "timeout_ms": 120000,
        "idle_timeout_ms": 60000,
        "settle_ms": 200,
    }
    spath = os.path.join(out, f"scenario-{label}.json")
    cpath = os.path.join(out, f"capture-{label}.json")
    with open(spath, "w", encoding="utf-8") as fh:
        json.dump(scenario, fh, indent=2)
    with open(cpath, "w", encoding="utf-8") as fh:
        r = subprocess.run([rea, "capture-process", spath, "--format", "json"],
                           stdout=fh, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise SystemExit(f"rea capture-process failed for {label}: {r.stderr[-2000:]}")
    with open(cpath, encoding="utf-8") as fh:
        ev = json.load(fh)
    n = ev["normalized_result"]
    lines = [ln.rstrip() for ln in n["rendered_frames"][-1]["lines"]]
    text = "\n".join(ln for ln in lines if ln.strip())
    # REA names observation roots by index: root_0 = modded/sk-rework (a
    # directory, entries "root_0:<name>"), root_1 = the harness file itself,
    # which appears as the single entry "root_1:.".
    sha = next(f["sha256"] for f in n["files_before"] if f["path"] == "root_0:script.lua")
    test_sha = next(f["sha256"] for f in n["files_before"] if f["path"] == "root_1:.")
    return {
        "label": label,
        "evidence_id": ev["evidence_id"],
        "authority": ev.get("authority"),
        "confidence": ev.get("confidence"),
        "exit": n["exit"],
        "script_sha256": sha,
        "harness_sha256": test_sha,
        "script_unchanged_during_run": all(e["status"] == "unchanged" for e in n["filesystem_effects"]),
        "summary_lines": [ln for ln in text.splitlines() if "checks passed" in ln or ln.startswith("FAIL") or "variants" in ln],
        "fail_lines": [ln for ln in text.splitlines() if ln.startswith("FAIL") or ln.startswith("  FAIL") or "FAIL" in ln][:12],
        "capture_path": cpath,
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--rea", required=True)
    ap.add_argument("--python", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    restore(a.repo)
    results = [capture(a.rea, a.python, a.repo, a.out, "baseline")]
    results[0]["expectation"] = "pass: unmodified mod"
    for mid, kind, desc, edits, expect in MUTATIONS:
        apply(a.repo, edits)
        try:
            res = capture(a.rea, a.python, a.repo, a.out, mid)
        finally:
            restore(a.repo)
        res.update({"kind": kind, "description": desc, "expectation": expect})
        results.append(res)
    for res in results[1:]:
        cmp_path = os.path.join(a.out, f"compare-baseline-vs-{res['label']}.json")
        with open(cmp_path, "w", encoding="utf-8") as fh:
            r = subprocess.run([a.rea, "compare-process-captures", results[0]["capture_path"], res["capture_path"], "--format", "json"],
                               stdout=fh, stderr=subprocess.PIPE, text=True)
        res["compare_exit"] = r.returncode
        res["compare_path"] = cmp_path
    with open(os.path.join(a.out, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    for res in results:
        print(f"{res['label']:9} exit={res['exit']['code']} script={res['script_sha256'][:12]} harness={res['harness_sha256'][:12]} ev={res['evidence_id'][:16]}  {res.get('description', 'baseline')}")
        for ln in res["summary_lines"]:
            print("          ", ln)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
