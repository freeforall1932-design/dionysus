#!/usr/bin/env python3
"""validate_skills.py - the mechanical gate for skills/ and projects/.

Enforces exactly the rules listed in skills/README.md ("Rules this directory
enforces mechanically"). Promises that are not checked do not survive sessions.

  1. every skills/<dir>/ has a SKILL.md with YAML frontmatter containing
     `name` and `description`; name == directory name, kebab-case, <= 64 chars;
     description <= 1024 chars
  2. every relative markdown link and every backticked repo path in SKILL.md,
     references/*.md, skills/README.md and projects/**/*.md resolves to a file
     (paths are judged relative to the skill dir first, then the repo root)
  3. no machine-specific path (C:\\..., C:/..., /home/<user>/..., /Users/<user>/...)
     anywhere in skills/ - except scripts/*.py (lint fixtures) and lines that
     carry the literal tag "(machine-specific example)"
  4. the universal file's sha256 equals the value recorded in PROVENANCE.md
  5. every python file under skills/ byte-compiles
  6. skills/qt6-cmake-cpp/scripts/qt_lint.py --selftest exits 0
  7. the harness loader files AGENTS.md and CLAUDE.md at the repo root exist,
     are byte-identical (one source of truth), and every repo path they name
     resolves; README.md paths resolve too

Usage:  python3 workbench/skills/validate_skills.py [--root DIR] [--quiet]
        (--root defaults to the parent of skills/, i.e. the workbench folder;
         paths inside the workbench's documents are relative to that folder)
Exit 0 = all checks passed, 1 = at least one failure.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys

KNOWN_ROOTS = ("skills", "projects", "references", "templates", "scripts", "tools", "research", ".github", "workbench")
MACHINE_PATH_RE = re.compile(r"(?<![\w])(?:[A-Za-z]:[\\/][A-Za-z]|/home/[A-Za-z0-9_.-]+/|/Users/[A-Za-z0-9_.-]+/)")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
SKIP_CHARS = set("…<>*$ {}|\\\"'")
SHA_RE = re.compile(r"\b[0-9a-f]{64}\b")

results: list[tuple[bool, str]] = []


def check(ok: bool, msg: str) -> bool:
    results.append((ok, msg))
    return ok


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def parse_frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fm: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fm
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return None  # never closed


def looks_like_repo_path(tok: str) -> bool:
    if any(c in SKIP_CHARS for c in tok) or "/" not in tok:
        return False
    if tok.startswith(("http://", "https://")):
        return False
    first, _, rest = tok.partition("/")
    if first in ("references", "templates", "scripts") and rest == "":
        return False  # bare layout descriptor ("put files in `references/`"), not a path claim
    return first in KNOWN_ROOTS


def resolve(tok: str, bases: list[str]) -> bool:
    tok = tok.rstrip("/").split("#", 1)[0]
    return any(os.path.exists(os.path.join(b, tok)) for b in bases)


def check_paths_in(md_path: str, root: str, skill_dir: str | None) -> None:
    text = read(md_path)
    # root = the workbench (parent of skills/); its parent is the repository root,
    # so both `skills/x` and `workbench/skills/x` and `.github/...` resolve.
    bases = [root, os.path.dirname(root)] + ([skill_dir] if skill_dir else [])
    rel = os.path.relpath(md_path, root)
    seen: set[str] = set()
    for m in MD_LINK_RE.finditer(text):
        tok = m.group(1)
        if tok.startswith(("http://", "https://", "mailto:")) or tok in seen:
            continue
        seen.add(tok)
        check(resolve(tok, bases + [os.path.dirname(md_path)]), f"{rel}: link target exists: {tok}")
    for m in BACKTICK_RE.finditer(text):
        tok = m.group(1).strip()
        if tok in seen or not looks_like_repo_path(tok):
            continue
        seen.add(tok)
        check(resolve(tok, bases), f"{rel}: backticked path exists: {tok}")


def check_machine_paths(skills_dir: str, root: str) -> None:
    offenders: list[str] = []
    for dirpath, dirnames, filenames in os.walk(skills_dir):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            if os.path.basename(dirpath) == "scripts" and fn.endswith(".py"):
                continue  # lint fixtures legitimately contain bad examples
            try:
                text = read(full)
            except (UnicodeDecodeError, OSError):
                continue
            for ln, line in enumerate(text.splitlines(), 1):
                if MACHINE_PATH_RE.search(line) and "(machine-specific example)" not in line:
                    offenders.append(f"{os.path.relpath(full, root)}:{ln}: {line.strip()[:90]}")
    check(not offenders, "no machine-specific paths in skills/ " + (f"- offenders: {offenders}" if offenders else ""))


def check_universal_hash(root: str) -> None:
    udir = os.path.join(root, "skills", "universal-agent-context")
    v4 = os.path.join(udir, "UNIVERSAL_AGENT_CONTEXT_v4.md")
    prov = os.path.join(udir, "PROVENANCE.md")
    if not check(os.path.isfile(v4), "universal file present: skills/universal-agent-context/UNIVERSAL_AGENT_CONTEXT_v4.md"):
        return
    if not check(os.path.isfile(prov), "PROVENANCE.md present"):
        return
    with open(v4, "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    recorded = SHA_RE.findall(read(prov))
    check(bool(recorded), "PROVENANCE.md records a sha256")
    if recorded:
        check(actual in recorded, f"universal file sha256 matches PROVENANCE.md (actual {actual[:12]}…, recorded {[r[:12] for r in recorded]})")


def check_skill(skill_dir: str, root: str) -> None:
    name = os.path.basename(skill_dir)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    rel = os.path.relpath(skill_md, root)
    if not check(os.path.isfile(skill_md), f"{name}: SKILL.md exists"):
        return
    fm = parse_frontmatter(read(skill_md))
    if not check(fm is not None, f"{rel}: has closed YAML frontmatter"):
        return
    assert fm is not None
    check("name" in fm and bool(fm["name"]), f"{rel}: frontmatter has name")
    check("description" in fm and bool(fm["description"]), f"{rel}: frontmatter has description")
    n = fm.get("name", "")
    check(n == name, f"{rel}: name == directory ({n!r} vs {name!r})")
    check(bool(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", n)), f"{rel}: name is kebab-case")
    check(len(n) <= 64, f"{rel}: name <= 64 chars ({len(n)})")
    check(len(fm.get("description", "")) <= 1024, f"{rel}: description <= 1024 chars ({len(fm.get('description', ''))})")
    check_paths_in(skill_md, root, skill_dir)
    refs = os.path.join(skill_dir, "references")
    if os.path.isdir(refs):
        for fn in sorted(os.listdir(refs)):
            if fn.endswith(".md"):
                check_paths_in(os.path.join(refs, fn), root, skill_dir)
    for extra in ("PROVENANCE.md", "README.md"):
        p = os.path.join(skill_dir, extra)
        if os.path.isfile(p):
            check_paths_in(p, root, skill_dir)


def check_python(skills_dir: str, root: str) -> None:
    for dirpath, dirnames, filenames in os.walk(skills_dir):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__",)]
        for fn in filenames:
            if fn.endswith(".py"):
                full = os.path.join(dirpath, fn)
                try:
                    with open(full, "rb") as f:
                        compile(f.read(), full, "exec")  # syntax only, no .pyc written
                    check(True, f"py_compile: {os.path.relpath(full, root)}")
                except SyntaxError as e:
                    check(False, f"py_compile: {os.path.relpath(full, root)}: line {e.lineno}: {e.msg}")


def check_qt_lint_selftest(root: str, quiet: bool) -> None:
    lint = os.path.join(root, "skills", "qt6-cmake-cpp", "scripts", "qt_lint.py")
    if not check(os.path.isfile(lint), "qt_lint.py present"):
        return
    r = subprocess.run([sys.executable, lint, "--selftest"], capture_output=True, text=True)
    tail = (r.stdout.strip().splitlines() or ["<no output>"])[-1]
    check(r.returncode == 0, f"qt_lint.py --selftest exit 0 ({tail})")
    if r.returncode != 0 and not quiet:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    help="repository root (default: parent of skills/)")
    ap.add_argument("--quiet", action="store_true", help="print failures and the summary only")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    skills_dir = os.path.join(root, "skills")
    projects_dir = os.path.join(root, "projects")

    if not check(os.path.isdir(skills_dir), f"skills/ exists under {root}"):
        return finish(a.quiet)

    skill_dirs = sorted(os.path.join(skills_dir, d) for d in os.listdir(skills_dir)
                        if os.path.isdir(os.path.join(skills_dir, d)) and not d.startswith((".", "_")))
    check(bool(skill_dirs), "at least one skill directory")
    for sd in skill_dirs:
        check_skill(sd, root)

    readme = os.path.join(skills_dir, "README.md")
    if check(os.path.isfile(readme), "skills/README.md exists"):
        check_paths_in(readme, root, None)
        text = read(readme)
        for sd in skill_dirs:
            check(os.path.basename(sd) in text, f"skills/README.md mentions {os.path.basename(sd)}")

    check_machine_paths(skills_dir, root)
    check_universal_hash(root)

    if check(os.path.isdir(projects_dir), "projects/ exists"):
        check(os.path.isfile(os.path.join(projects_dir, "README.md")), "projects/README.md exists")
        for dirpath, dirnames, filenames in os.walk(projects_dir):
            for fn in sorted(filenames):
                if fn.endswith(".md"):
                    check_paths_in(os.path.join(dirpath, fn), root, None)

    check_loader_files(root)
    check_index(root)
    check_python(skills_dir, root)
    check_qt_lint_selftest(root, a.quiet)
    return finish(a.quiet)


def check_index(root: str) -> None:
    """index.json is the triage table: every unit an agent might open has one
    entry with read_when/skip_when, every entry path exists, and README.md names
    every unit. Units = skills/*, projects/* (dirs), research/*.md, tools/*."""
    import json
    p = os.path.join(root, "index.json")
    if not check(os.path.isfile(p), "index.json exists (triage table)"):
        return
    try:
        data = json.loads(read(p))
    except json.JSONDecodeError as e:
        check(False, f"index.json parses: {e}")
        return
    units = data.get("units", [])
    ids = {u.get("id") for u in units}
    readme = read(os.path.join(root, "README.md")) if os.path.isfile(os.path.join(root, "README.md")) else ""
    for u in units:
        uid = u.get("id", "?")
        for key in ("kind", "entry", "read_when", "skip_when", "session_added"):
            check(bool(str(u.get(key, "")).strip()), f"index.json {uid}: has {key}")
        entry = u.get("entry", "")
        check(os.path.isfile(os.path.join(root, entry)), f"index.json {uid}: entry exists: {entry}")
        check(f"`{uid}`" in readme, f"index.json {uid}: named in README.md triage table")
    expected: set[str] = set()
    for group in ("skills", "projects", "tools"):
        d = os.path.join(root, group)
        if os.path.isdir(d):
            expected.update(f"{group}/{n}" for n in os.listdir(d)
                            if os.path.isdir(os.path.join(d, n)) and not n.startswith((".", "_")))
    rd = os.path.join(root, "research")
    if os.path.isdir(rd):
        expected.update(f"research/{n}" for n in os.listdir(rd) if n.endswith(".md") and n != "README.md")
    for uid in sorted(expected):
        check(uid in ids, f"index.json covers {uid}")
    for uid in sorted(ids - expected):
        check(False, f"index.json entry {uid} has no unit on disk")


def check_loader_files(root: str) -> None:
    agents = os.path.join(root, "AGENTS.md")
    claude = os.path.join(root, "CLAUDE.md")
    have_a = check(os.path.isfile(agents), "AGENTS.md exists at the repo root (Codex/OpenCode/Copilot loader)")
    have_c = check(os.path.isfile(claude), "CLAUDE.md exists at the repo root (Claude Code loader)")
    if have_a and have_c:
        with open(agents, "rb") as fa, open(claude, "rb") as fc:
            check(fa.read() == fc.read(), "AGENTS.md and CLAUDE.md are byte-identical (one loader, two names)")
    for name in ("AGENTS.md", "CLAUDE.md", "README.md"):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            check_paths_in(p, root, None)


def finish(quiet: bool) -> int:
    failures = [m for ok, m in results if not ok]
    for ok, m in results:
        if not ok or not quiet:
            print(("ok   " if ok else "FAIL ") + m)
    print(f"validate_skills: {len(results) - len(failures)} passed, {len(failures)} failed -> "
          + ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
