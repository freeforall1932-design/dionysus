#!/usr/bin/env python3
"""Turn the mutation-experiment captures into a REA reconstruction obligation
ledger request.

The obligations are the mod's UI<->engine behaviour-contract rows, stated as
claims about the mod against the engine. Each one names the authority that
could really close it. The lupa harness is `integration` authority: it can
close rows that are properties of the mod's own code and log, and it must NOT
close rows that only the running game can prove (`live-observation`). REA's
ledger enforces that; this script just supplies the evidence honestly.

Usage:
    node make-bundle.mjs /tmp/rea-exp/bundle.json /tmp/rea-exp/capture-*.json
    rea evidence-export /tmp/rea-exp/bundle.json /tmp/rea-exp/bundle-canonical.json
    python3 build_ledger_input.py --exp /tmp/rea-exp --bundle /tmp/rea-exp/bundle-canonical.json \
        --out /tmp/rea-exp/ledger-input.json
    rea build-reconstruction-obligation-ledger /tmp/rea-exp/ledger-input.json --format json
"""
import argparse
import json
import os

HARNESS_CMD = "python tools/mod_smoketest.py"


def load(exp, label):
    with open(os.path.join(exp, f"capture-{label}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bundle", required=True,
                    help="canonical bundle written by `rea evidence-export` (see make-bundle.mjs)")
    a = ap.parse_args()
    with open(os.path.join(a.exp, "results.json"), encoding="utf-8") as fh:
        results = {r["label"]: r for r in json.load(fh)}
    records = {lab: load(a.exp, lab) for lab in results}
    ev = {lab: rec["evidence_id"] for lab, rec in records.items()}
    script_sha = results["baseline"]["script_sha256"]

    def obligation(oid, title, layer, family, location, kinds, original, fixture, verifier,
                   residual=(), unavailable=(), next_evidence=()):
        return {
            "obligation_id": oid, "obligation_version": 1, "title": title,
            "application_layer": layer, "family": family,
            "target": {"artifact_sha256": script_sha, "application_node_id": None,
                       "semantic_node_id": None, "location": location},
            "required": True, "required_case_kinds": list(kinds),
            "required_original_authority": original,
            "required_fixture_authority": fixture,
            "required_verifier_authority": verifier,
            "requires_parser_type": False,
            "dependency_obligation_ids": [], "residual_unknown_ids": list(residual),
            "unavailable_authority": list(unavailable),
            "required_next_evidence": list(next_evidence),
            "disposition": "active",
            "review_evidence_ids": [ev["baseline"]],
        }

    def binding(oid, symbol, pos_label, neg_label, verifier_authority, verifier_status, result_label,
                original_labels=None):
        cases = []
        for kind, lab in (("positive", pos_label), ("negative", neg_label)):
            if lab is not None:
                cases.append({"kind": kind, "evidence_id": ev[lab], "location": f"capture-{lab}.json"})
        original_cases = cases if original_labels is None else [
            {"kind": k, "evidence_id": ev[l], "location": f"capture-{l}.json"} for k, l in original_labels]
        return {
            "obligation_id": oid,
            "owner": {"module_path": "modded/sk-rework/script.lua", "symbol": symbol,
                      "owner_sha256": script_sha},
            "parser_type": None,
            "original_cases": original_cases,
            "fixtures": [
                {"fixture_id": f"{oid}.{c['kind']}", "case_kind": c["kind"],
                 "authority": verifier_authority, "evidence_ids": [c["evidence_id"]]}
                for c in cases
            ],
            "verifier": {
                "verifier_id": f"{oid}.harness", "claim_id": f"{oid}.v1",
                "command": HARNESS_CMD, "authority": verifier_authority,
                "status": verifier_status, "result_evidence_id": ev[result_label],
                "enumerated_obligation_ids": [oid],
                "nondeterminism": {"mode": "total-order",
                                   "specification": "the harness drives the fake engine frame by frame; no concurrency"},
            },
        }

    reviewed = [
        # 1. Only the running game can prove this one. The harness models the
        #    engine's click path from the owner's notes; that is integration
        #    authority, below the live-observation authority the claim needs.
        obligation("ui.panel.click-isolation",
                   "A click on the dev panel never reaches a board square and never breaks the turn (run-6 class)",
                   "runtime", "ui-input", "panel_frame(): click consumption over the tab/modal box",
                   ("positive", "negative"), "runtime", "integration", "live-observation",
                   residual=["sugar-input-path-not-observed-here"],
                   unavailable=["live-observation"],
                   next_evidence=["Run the real game with the mod, click CLIP+ over an occupied square, record the log and a video."]),
        # 2-5. Properties of the mod's own code and log. REA accepts a
        #      controlled-replay capture as evidence of the original's *runtime*
        #      behaviour ("static" would need an analysed shipped artifact).
        obligation("ui.panel.no-remove-buts",
                   "The mod never calls the engine's remove_buts() (build-7 mistake)",
                   "runtime", "engine-api-boundary", "cheat_clip() and every panel action",
                   ("positive", "negative"), "runtime", "integration", "integration"),
        obligation("ui.panel.tab-label",
                   "The panel tab the player clicks is labelled 'SK DEV'",
                   "application", "ui-surface", "draw_button(... \"SK DEV\" ...)",
                   ("positive", "negative"), "runtime", "integration", "integration"),
        obligation("logic.cheat-ammo.step",
                   "+3 AMMO adds exactly 3 reserve rounds, logged as amount=3, and SAFE mode blocks the second call",
                   "runtime", "cheat-action", "cheat_ammo_reserve()",
                   ("positive", "negative"), "runtime", "integration", "integration"),
        obligation("runtime.all-iterator.dual-semantics",
                   "Every all() loop works under value-yielding and (index,value)-yielding iterators",
                   "runtime", "engine-compat", "iter_value(a, b) at every all() site",
                   ("positive", "negative"), "external", "integration", "integration",
                   residual=["sugar-all-semantics-unconfirmed"],
                   next_evidence=["Confirm which form the shipped SUGAR/LuaJIT build yields; one log line from the real game decides it."]),
    ]
    bindings = [
        binding("ui.panel.click-isolation", "panel_frame", "baseline", "M3", "integration", "pass", "baseline",
                original_labels=[]),
        binding("ui.panel.no-remove-buts", "cheat_clip", "baseline", "M4", "integration", "pass", "baseline"),
        binding("ui.panel.tab-label", "draw_panel", "baseline", "M2", "integration", "pass", "baseline"),
        binding("logic.cheat-ammo.step", "cheat_ammo_reserve", "baseline", "M5a", "integration", "pass", "baseline"),
        binding("runtime.all-iterator.dual-semantics", "iter_value", "baseline", "M6", "integration", "pass", "baseline"),
    ]
    with open(a.bundle, encoding="utf-8") as fh:
        bundle = json.load(fh)   # must be byte-for-byte canonical; never hand-edit it
    request = {
        "evidence_bundle": bundle,
        "reviewed_obligations": reviewed,
        "manifest": {"bindings": bindings, "contradictions": []},
    }
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(request, fh, indent=1)
    print(f"wrote {a.out}: {len(reviewed)} obligations, {len(bindings)} bindings, {len(request['evidence_bundle']['records'])} records")


if __name__ == "__main__":
    main()
