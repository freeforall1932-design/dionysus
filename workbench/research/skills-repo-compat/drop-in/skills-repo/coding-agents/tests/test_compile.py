"""Tests for the coding-agent pack compiler.

These guard the packaging, not the prose: every profile must be well-formed
and honest about what was verified, and every generated file must be valid
for the agent it targets.
"""

from __future__ import annotations

import json
import yaml
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import compile as compile_mod  # noqa: E402

# The register every harness is recommended to load, plus the two layered skills.
VARIANT_KEYS = ("unified", "universal-agent-context", "qt6-cmake-cpp")
REGISTER_KEYS = ("unified",)


@pytest.fixture(scope="module")
def compiled():
    subprocess.run([sys.executable, str(ROOT / "compile.py")], check=True, cwd=ROOT.parent)
    return ROOT / "packs"


# ── profiles ─────────────────────────────────────────────────────────────────


def test_every_profile_validates():
    profiles = compile_mod.load_profiles()
    assert len(profiles) >= 6
    for profile in profiles:
        assert profile["schema_version"] == "1"


@pytest.mark.parametrize("agent", ["qwen", "claude", "codex", "cursor", "copilot", "opencode"])
def test_expected_agents_exist(agent):
    path = ROOT / "profiles" / f"{agent}.json"
    assert path.is_file(), f"missing profile for {agent}"


def test_qwen_is_a_first_class_profile():
    """Qwen Code is why this section exists — it must not silently regress."""
    profile = json.loads((ROOT / "profiles" / "qwen.json").read_text(encoding="utf-8"))
    assert profile["display_name"].startswith("Qwen Code")
    assert "~/.qwen/QWEN.md" in profile["instruction"]["global_paths"]
    assert "QWEN.md" in profile["instruction"]["project_paths"]
    assert profile["skills"]["supported"] is True
    assert "~/.qwen/skills" in profile["skills"]["user_dirs"]
    assert ".qwen/skills" in profile["skills"]["project_dirs"]


def test_malformed_profile_is_rejected():
    with pytest.raises(ValueError, match="missing required key"):
        compile_mod.validate_profile({"id": "broken"})
    with pytest.raises(ValueError, match="unknown instruction format"):
        compile_mod.validate_profile({
            "schema_version": "1", "id": "x", "display_name": "X", "vendor": "V",
            "homepage": "https://example.com", "binary_names": ["x"],
            "install": "true", "wire_protocol": "openai-chat",
            "instruction": {"method": "file", "format": "docx", "frontmatter": False,
                            "project_paths": ["a.md"]},
            "verification": {"tested_agent_version": "unverified",
                             "last_verified_at": "2026-01-01",
                             "verified_by": "documentation review",
                             "source": "https://example.com"},
        })


def test_unverified_versions_must_explain_themselves():
    base = {
        "schema_version": "1", "id": "x", "display_name": "X", "vendor": "V",
        "homepage": "https://example.com", "binary_names": ["x"],
        "install": "true", "wire_protocol": "openai-chat",
        "instruction": {"method": "file", "format": "markdown", "frontmatter": False,
                        "project_paths": ["a.md"]},
        "verification": {"tested_agent_version": "unverified",
                         "last_verified_at": "2026-01-01",
                         "verified_by": "vibes",
                         "source": "https://example.com"},
    }
    with pytest.raises(ValueError, match="does not say how"):
        compile_mod.validate_profile(dict(base))


# ── variants ─────────────────────────────────────────────────────────────────


def test_catalog_variants_load_with_frontmatter():
    variants = compile_mod.load_variants()
    assert set(VARIANT_KEYS) <= set(variants), "catalog lost a skill directory"
    for key in variants:
        assert key in variants, f"missing variant {key}"
        assert variants[key].name, f"{key} has no name"
        assert variants[key].description, f"{key} has no description"


def test_variant_layers_are_declared():
    """Every skill says which layer it is, so an agent can load at most one
    register, one process skill, and the workload skills that match the repo."""
    variants = compile_mod.load_variants()
    layers = {key: str(v.meta.get("layer", "")) for key, v in variants.items()}
    for key, layer in layers.items():
        assert layer, f"{key}: frontmatter declares no layer"
    assert layers["unified"].startswith("reasoning"), layers["unified"]  # "reasoning + output" = a register
    assert variants["unified"].meta["register"] == "unified"
    assert layers["universal-agent-context"] == "process"
    assert layers["qt6-cmake-cpp"] == "workload"
    assert sum(1 for key in REGISTER_KEYS if key in variants) == 1, "exactly one output register ships"


# ── generated packs ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("agent", ["qwen", "claude", "codex", "cursor", "copilot", "opencode"])
def test_every_agent_gets_every_variant(compiled, agent):
    agent_dir = compiled / agent
    assert (agent_dir / "README.md").is_file()
    for key in VARIANT_KEYS:
        assert (agent_dir / f"{key}.md").is_file(), f"{agent} missing {key}.md"


def test_paste_files_have_no_frontmatter(compiled):
    """A context file is pasted verbatim — frontmatter there is pure noise."""
    for path in compiled.glob("*/*.md"):
        if path.name == "README.md":
            continue
        assert not path.read_text(encoding="utf-8").startswith("---"), path


@pytest.mark.parametrize("agent", ["qwen", "claude", "codex"])
def test_skill_dirs_have_valid_frontmatter(compiled, agent):
    for skill in (compiled / agent / "skills").glob("*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        assert match, f"{skill} has unterminated frontmatter"
        block = match.group(1)
        assert "name:" in block, f"{skill} frontmatter missing name"
        assert "description:" in block, f"{skill} frontmatter missing description"
        yaml = pytest.importorskip("yaml")
        parsed = yaml.safe_load(block)
        assert "name" in parsed and "description" in parsed


def test_cursor_rules_use_mdc_frontmatter(compiled):
    rules = list((compiled / "cursor" / "rules").glob("*.mdc"))
    assert len(rules) == len(compile_mod.load_variants())
    yaml = pytest.importorskip("yaml")
    for rule in rules:
        text = rule.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        assert match, f"{rule} has no frontmatter — Cursor would ignore it"
        parsed = yaml.safe_load(match.group(1))
        # Cursor reads exactly three fields, and alwaysApply is what makes
        # the rule load without a glob match.
        assert set(parsed) == {"description", "globs", "alwaysApply"}, parsed
        assert parsed["alwaysApply"] is True


def test_zip_is_generated(compiled):
    import zipfile

    zip_path = compiled / "coding-agents.zip"
    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        assert "README.md" in names
        assert "qwen/unified.md" in names
        assert not any(name.endswith(".zip") for name in names)


# ── Qwen Chat Agent ──────────────────────────────────────────────────────────


def test_qwen_agent_profile_exists_and_is_honest():
    """The Qwen Chat agent is a distinct product from the Qwen Code CLI.

    It is a hosted agent with an uploadable workspace. Whether it parses
    SKILL.md frontmatter is unknown, so the profile must say so rather than
    claim a skill convention it has not earned.
    """
    profile = json.loads(
        (ROOT / "profiles" / "qwen-agent.json").read_text(encoding="utf-8")
    )
    assert profile["id"] == "qwen-agent"
    assert profile["wire_protocol"] == "web-workspace"
    assert profile["instruction"]["method"] == "upload"
    assert profile["instruction"]["paste_dir"] == "workspace"
    assert profile["skills"] is None  # unverified — not claimed as supported
    assert profile["verification"]["tested_agent_version"] == "unverified"


def test_qwen_agent_gets_a_workspace_folder(compiled):
    """Uploadable files land in workspace/, because there is no config dir."""
    workspace = compiled / "qwen-agent" / "workspace"
    assert workspace.is_dir()
    for key in VARIANT_KEYS:
        assert (workspace / f"{key}.md").is_file()
        # No frontmatter: this route must work as plain text.
        assert not (workspace / f"{key}.md").read_text(encoding="utf-8").startswith("---\n")


def test_no_profile_claims_a_path_it_cannot_name():
    """A hosted workspace agent must not be forced to invent a config path."""
    qa = json.loads((ROOT / "profiles" / "qwen-agent.json").read_text(encoding="utf-8"))
    assert qa["instruction"]["project_paths"] == []
    assert qa["instruction"]["global_paths"] == []


# ── spec conformance: are these real skills, not text files? ─────────────────


_NAME_RE = compile_mod.re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@pytest.mark.parametrize("skill_dir", sorted(ROOT.joinpath("variants").glob("*")))
def test_skill_meets_the_agent_skills_spec(skill_dir):
    """The checklist that separates a real skill from instructional prose."""
    skill = skill_dir / "SKILL.md"
    raw = skill.read_text(encoding="utf-8")
    match = compile_mod._FRONTMATTER_RE.match(raw)
    assert match, f"{skill_dir.name}: no YAML frontmatter"
    meta = yaml.safe_load(match.group(1))

    name = meta.get("name", "")
    assert _NAME_RE.match(name), f"{skill_dir.name}: name {name!r} is not a slug"
    assert len(name) <= 64
    assert name == skill_dir.name, f"name {name!r} must match directory {skill_dir.name!r}"

    description = meta.get("description", "")
    assert 0 < len(description) <= 1024
    assert not compile_mod.re.match(
        r"\s*(you|your)\b", description.strip(), compile_mod.re.I
    ), "description must be third person"

    body_lines = raw[match.end():].strip().splitlines()
    assert len(body_lines) <= 500, f"{skill_dir.name}: body is {len(body_lines)} lines"

    # Progressive disclosure: support files ship beside SKILL.md, one level deep.
    refs = skill_dir / "references"
    if refs.is_dir():
        assert not list(refs.rglob("*/*.md")), "reference files must be one level deep"
    # A register shows before/after examples; a process or workload skill
    # ships a guide, templates or scripts instead. One of the two must exist.
    variant = compile_mod.load_variants()[skill_dir.name]
    assert (skill_dir / "examples.md").is_file() or variant.assets, (
        f"{skill_dir.name}: neither examples.md nor support files"
    )


def test_generated_skill_dirs_ship_their_support_files(compiled):
    """A skill whose references stay behind is just a text file again."""
    for agent in ("qwen", "claude", "codex"):
        skills = compiled / agent / "skills"
        for skill in skills.glob("*/SKILL.md"):
            assert skill.read_text(encoding="utf-8").startswith("---\n")
            source = ROOT / "variants" / skill.parent.name
            for ref in (source / "references").glob("*.md"):
                assert (skill.parent / "references" / ref.name).is_file(), (
                    f"{agent}/{skill.parent.name}: missing {ref.name}"
                )
            variant = compile_mod.load_variants()[skill.parent.name]
            if variant.examples:
                assert (skill.parent / "examples.md").is_file()
            # Support files that are not markdown references travel byte-for-byte.
            for rel, data in variant.assets.items():
                packed = skill.parent / rel
                assert packed.is_file(), f"{agent}/{skill.parent.name}: missing {rel}"
                assert packed.read_bytes() == data, f"{agent}/{skill.parent.name}: {rel} was rewritten"


def test_loader_skills_paste_a_pointer_not_a_copy(compiled):
    """A skill with a hash-pinned guide or scripts is pasted as its SKILL.md body
    plus a file list. Inlining would bill the whole guide on every request and
    silently drop everything that is not markdown."""
    variants = compile_mod.load_variants()
    loaders = [v for v in variants.values() if v.is_loader]
    if not loaders:
        pytest.skip("no loader-style skill in variants/")
    for variant in loaders:
        text = (compiled / "codex" / f"{variant.key}.md").read_text(encoding="utf-8")
        assert "## Reference material (inlined)" not in text
        assert f"## Files of the `{variant.name}` skill" in text
        for rel in variant.assets:
            assert f"/{rel}`" in text, f"{variant.key}: loader does not list {rel}"
        for name in variant.references:
            assert f"/references/{name}`" in text
        assert len(text) < 20_000, f"{variant.key}: loader paste is {len(text)} bytes"


def test_loader_paste_names_the_install_dir_per_harness(compiled):
    """A pasted file has no directory beside it, so it must say where the
    skill's files live for that harness: its own skill dir when it has one,
    the interoperable .agents/skills/ path otherwise."""
    variants = compile_mod.load_variants()
    loaders = [v for v in variants.values() if v.is_loader]
    if not loaders:
        pytest.skip("no loader-style skill in variants/")
    for profile in compile_mod.load_profiles():
        paste_dir = compiled / profile["id"] / (profile["instruction"].get("paste_dir") or "")
        for variant in loaders:
            text = (paste_dir / f"{variant.key}.md").read_text(encoding="utf-8")
            where = compile_mod.skill_install_dir(profile, variant)
            assert f"`{where}/`" in text, f"{profile['id']}/{variant.key}: install dir not named"


def test_loader_skill_references_are_verbatim(compiled):
    """Loader skills carry their own gates (hash pins, path checks); their
    references must arrive unchanged, not link-rewritten."""
    variants = compile_mod.load_variants()
    for variant in variants.values():
        if not variant.is_loader:
            continue
        for agent in ("claude", "codex", "qwen"):
            for name, text in variant.references.items():
                packed = compiled / agent / "skills" / variant.name / "references" / name
                assert packed.read_text(encoding="utf-8") == text, f"{agent}/{variant.key}: {name} rewritten"


def test_pasted_files_are_self_contained(compiled):
    """A pasted file has no filesystem beside it — support content is inlined."""
    text = (compiled / "qwen-agent" / "workspace" / "unified.md").read_text(
        encoding="utf-8"
    )
    assert not text.startswith("---\n")
    assert "## Reference material (inlined)" in text
    assert "## Worked examples" in text
    # Cut-list content is present, not merely linked.
    assert "Indonesian — cut" in text
    # Links that would break outside the repo are plain text.
    assert "](../../" not in text
