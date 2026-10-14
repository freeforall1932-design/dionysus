#!/usr/bin/env python3
"""qt_lint.py - mechanical scan for Qt 6 / CMake anti-patterns.

Standard library only. Finds *candidates*; a human reads the site. A finding
never flips a project status on its own (universal guide §6).

Rules (ID · severity · what)
  QL001 error    string-based SIGNAL()/SLOT() connect
  QL002 warning  lambda connected without a context object (3-argument form)
  QL003 warning  blocking wait on a GUI-thread class (waitForFinished/Started/..., QThread::sleep)
  QL004 warning  processEvents() / nested QEventLoop::exec() in GUI code (re-entrancy)
  QL005 info     moveToThread() in a file with no explicit Qt::QueuedConnection
  QL006 info     hard-coded hex colour inside setStyleSheet() (theming/dark mode hazard)
  QL007 warning  QProcess used but QProcess::errorOccurred never connected in that file
  QL008 info     QFile opened for writing (consider QSaveFile / temp+rename for user data)
  QL009 info     mega-include <QtWidgets> / <QtCore> / <QtGui> (build time)
  QL011 warning  CMake: GUI test target without QT_QPA_PLATFORM in its properties
  QL012 info     CMake: add_executable() for a target linking Qt6::Widgets/Gui/Quick
  QL013 warning  CMake: find_package(Qt6) without qt_standard_project_setup() or CMAKE_AUTOMOC
  QL014 info     CMake: qt_add_executable() of a Widgets target without WIN32
  QL015 warning  hard-coded machine path (C:/Qt, C:\\..., /home/<user>, /Users/<user>, /opt/Qt)

Usage
  qt_lint.py PATH [PATH...]                 report; exit 1 if any finding at/above --fail-on
  qt_lint.py PATH --write-baseline FILE     record current findings as accepted
  qt_lint.py PATH --baseline FILE           fail only on findings not in FILE
  qt_lint.py PATH --json                    machine-readable output
  qt_lint.py --selftest                     every rule fires on its bad fixture and not on the clean one

Suppress a single site inline with a comment on the same or previous line:
  // ql-allow QL003: bounded 2 s wait at shutdown, measured S37 (register U-12)
The reason is mandatory and should name the register row that accepted it.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, asdict
from typing import Iterable

CPP_EXT = {".cpp", ".cc", ".cxx", ".h", ".hpp", ".hh", ".hxx"}
CMAKE_NAMES = {"CMakeLists.txt"}
CMAKE_EXT = {".cmake"}
PRESET_NAMES = {"CMakePresets.json", "CMakeUserPresets.json"}

SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}

RULES: dict[str, tuple[str, str]] = {
    "QL001": ("error", "string-based SIGNAL()/SLOT() connect - fails silently at run time"),
    "QL002": ("warning", "lambda connected without a context object - survives the receiver's death"),
    "QL003": ("warning", "blocking wait on the GUI thread - keep only if bounded, measured and registered (then baseline it)"),
    "QL004": ("warning", "processEvents()/nested event loop in GUI code - re-entrancy hazard"),
    "QL005": ("info", "moveToThread() with no explicit Qt::QueuedConnection in this file"),
    "QL006": ("info", "hard-coded hex colour in setStyleSheet() - breaks palette/dark mode"),
    "QL007": ("warning", "QProcess used but errorOccurred never connected - FailedToStart is silent"),
    "QL008": ("info", "QFile opened for writing - consider QSaveFile or temp+rename for user data"),
    "QL009": ("info", "mega-include (<QtWidgets>/<QtCore>/<QtGui>) - slow builds"),
    "QL011": ("warning", "GUI test target without QT_QPA_PLATFORM - needs a display to run"),
    "QL012": ("info", "add_executable() for a Qt GUI target - prefer qt_add_executable()"),
    "QL013": ("warning", "find_package(Qt6) without qt_standard_project_setup()/CMAKE_AUTOMOC"),
    "QL014": ("info", "qt_add_executable() Widgets target without WIN32 - console window on Windows"),
    "QL015": ("warning", "hard-coded machine path - not portable across machines/CI"),
}


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    path: str
    line: int
    text: str
    message: str

    def key(self) -> str:
        # Stable across line-number shifts: rule + path + normalized line text.
        return f"{self.rule}|{self.path}|{' '.join(self.text.split())}"


# --------------------------------------------------------------------------- helpers

def strip_comments_cpp(src: str) -> str:
    """Blank out // and /* */ comments and string literals, preserving newlines and length."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i))
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append("".join("\n" if ch == "\n" else " " for ch in src[i:j]))
            i = j
        elif c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append('"' + " " * max(0, j - i - 2) + ('"' if j - i >= 2 else ""))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def strip_comments_only_cpp(src: str) -> str:
    """Blank out // and /* */ comments but KEEP string literals (for path rules)."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i))
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append("".join("\n" if ch == "\n" else " " for ch in src[i:j]))
            i = j
        elif c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(src[i:j])
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def is_test_file(display: str) -> bool:
    d = display.replace("\\", "/")
    base = os.path.basename(d)
    return ("/tests/" in f"/{d}" or "/test/" in f"/{d}" or base.startswith("test_")
            or base.endswith(("_test.cpp", "_test.cc", "Test.cpp", "_tests.cpp")))


def line_of(src: str, pos: int) -> int:
    return src.count("\n", 0, pos) + 1


def line_text(lines: list[str], ln: int) -> str:
    return lines[ln - 1].strip() if 0 < ln <= len(lines) else ""


ALLOW_RE = re.compile(r"ql-allow\s+(QL\d{3})\s*:\s*(\S.*)$")


def allowed(lines: list[str], ln: int, rule: str) -> bool:
    for cand in (ln, ln - 1):
        if 0 < cand <= len(lines):
            m = ALLOW_RE.search(lines[cand - 1])
            if m and m.group(1) == rule and m.group(2).strip():
                return True
    return False


def split_args(arg_text: str) -> list[str]:
    """Split a C++ argument list at depth-0 commas (parens, brackets, braces, angle-ish)."""
    args, depth, cur = [], 0, []
    for ch in arg_text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        args.append("".join(cur).strip())
    return args


def extract_calls(src: str, name: str) -> Iterable[tuple[int, str]]:
    """Yield (position, argument_text) for every `name(` call, balancing parentheses."""
    pat = re.compile(r"(?<!\w)" + re.escape(name) + r"\s*\(")  # (?<!\w) keeps disconnect( from matching connect(
    for m in pat.finditer(src):
        start = m.end()
        depth, i = 1, start
        while i < len(src) and depth:
            if src[i] == "(":
                depth += 1
            elif src[i] == ")":
                depth -= 1
            i += 1
        if depth == 0:
            yield m.start(), src[start:i - 1]


GUI_HINT_RE = re.compile(r"#\s*include\s*[<\"]\s*(QMainWindow|QWidget|QDialog|QApplication|QtWidgets|Q\w*Widget|QPushButton|QLabel)\b")
MACHINE_PATH_RE = re.compile(
    r"(?<![\w])(?:[A-Za-z]:[\\/](?:Qt|Users|Projects|src|dev)\b|/home/[A-Za-z0-9_.-]+/|/Users/[A-Za-z0-9_.-]+/|/opt/Qt\b)"
)
HEX_COLOUR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
LAMBDA_START_RE = re.compile(r"^\[[^\]]*\]\s*(?:\(|mutable|->|\{)")


# --------------------------------------------------------------------------- C++ rules

def lint_cpp(path: str, display: str) -> list[Finding]:
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    lines = raw.splitlines()
    src = strip_comments_cpp(raw)
    out: list[Finding] = []

    def add(rule: str, ln: int) -> None:
        if allowed(lines, ln, rule):
            return
        sev, msg = RULES[rule]
        out.append(Finding(rule, sev, display, ln, line_text(lines, ln), msg))

    gui_file = bool(GUI_HINT_RE.search(raw)) or "/ui/" in display.replace("\\", "/") or "qtui" in display
    test_file = is_test_file(display)
    # Test harnesses legitimately pump events, sleep, wait on fixture processes
    # and write scratch files; only the connection-form and include rules apply there.
    if test_file:
        gui_file = False

    # QL001 / QL002 - connect() forms
    for pos, args_text in extract_calls(src, "connect"):
        ln = line_of(src, pos)
        if re.search(r"\bSIGNAL\s*\(|\bSLOT\s*\(", args_text):
            add("QL001", ln)
            continue
        args = split_args(args_text)
        if len(args) == 3 and LAMBDA_START_RE.match(args[2]):
            if test_file:
                if not allowed(lines, ln, "QL002"):
                    out.append(Finding("QL002", "info", display, ln, line_text(lines, ln),
                                       RULES["QL002"][1] + " (test file: info only)"))
            else:
                add("QL002", ln)

    # QL003 - blocking waits (GUI files only; worker/core files legitimately wait)
    if gui_file:
        for m in re.finditer(r"\bwaitFor(?:Finished|Started|ReadyRead|BytesWritten|Connected|Disconnected)\s*\(|\bQThread::(?:sleep|msleep|usleep)\s*\(", src):
            add("QL003", line_of(src, m.start()))
        # QL004 - processEvents / nested loop exec
        for m in re.finditer(r"\bprocessEvents\s*\(|\bQEventLoop\s+\w+\s*;|\bQEventLoop\s+\w+\s*\(", src):
            add("QL004", line_of(src, m.start()))

    # QL005 - moveToThread without an explicit queued connection anywhere in the file
    if "moveToThread" in src and "Qt::QueuedConnection" not in src and "Qt::BlockingQueuedConnection" not in src:
        for m in re.finditer(r"\bmoveToThread\s*\(", src):
            add("QL005", line_of(src, m.start()))

    # QL006 - hex colours inside setStyleSheet (use RAW: colours live in string literals)
    for pos, args_text in extract_calls(raw, "setStyleSheet"):
        if HEX_COLOUR_RE.search(args_text):
            add("QL006", line_of(raw, pos))

    # QL007 - QProcess without errorOccurred (not in test harnesses, which wait synchronously)
    if not test_file and re.search(r"\bQProcess\b", src) and "errorOccurred" not in src and display.endswith((".cpp", ".cc", ".cxx")):
        m = re.search(r"\bQProcess\b", src)
        add("QL007", line_of(src, m.start()))

    # QL008 - QFile write opens (not in tests: scratch files are fine there)
    for m in ([] if test_file else re.finditer(r"\bopen\s*\([^;]*?(?:QIODevice::WriteOnly|QIODevice::Truncate|QFile::WriteOnly|QFile::Truncate)", src)):
        ln = line_of(src, m.start())
        window = "\n".join(lines[max(0, ln - 4):ln])
        if "QSaveFile" in window:
            continue
        add("QL008", ln)

    # QL009 - mega includes
    for m in re.finditer(r"#\s*include\s*<\s*(QtWidgets|QtCore|QtGui|QtNetwork)\s*>", raw):
        add("QL009", line_of(raw, m.start()))

    # QL015 - machine paths in CODE and STRING LITERALS (comments are stripped; a
    # path in a comment is prose, not a build input). Not in test files, where a
    # Windows path is usually a fixture for a path-handling test.
    if not test_file:
        code_lines = strip_comments_only_cpp(raw).splitlines()
        for ln, text in enumerate(code_lines, 1):
            if MACHINE_PATH_RE.search(text) and "machine-specific example" not in lines[ln - 1]:
                add("QL015", ln)

    return out


# --------------------------------------------------------------------------- CMake rules

def cmake_calls(src: str, name: str) -> Iterable[tuple[int, str]]:
    pat = re.compile(r"(?im)^\s*" + re.escape(name) + r"\s*\(")
    for m in pat.finditer(src):
        start = m.end()
        depth, i = 1, start
        while i < len(src) and depth:
            if src[i] == "(":
                depth += 1
            elif src[i] == ")":
                depth -= 1
            i += 1
        yield m.start(), src[start:i - 1]


def strip_comments_cmake(src: str) -> str:
    return "\n".join(re.sub(r"#.*$", "", ln) for ln in src.splitlines())


def lint_cmake(path: str, display: str) -> list[Finding]:
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    lines = raw.splitlines()
    src = strip_comments_cmake(raw)
    out: list[Finding] = []

    def add(rule: str, ln: int) -> None:
        if allowed(lines, ln, rule):
            return
        sev, msg = RULES[rule]
        out.append(Finding(rule, sev, display, ln, line_text(lines, ln), msg))

    # which targets link Qt GUI modules
    gui_targets: set[str] = set()
    for _, a in cmake_calls(src, "target_link_libraries"):
        toks = a.split()
        if toks and re.search(r"Qt6::(Widgets|Gui|Quick|QuickWidgets)", a):
            gui_targets.add(toks[0])

    # QL012 / QL014
    for pos, a in cmake_calls(src, "add_executable"):
        toks = a.split()
        if toks and toks[0] in gui_targets:
            add("QL012", line_of(src, pos))
    for pos, a in cmake_calls(src, "qt_add_executable"):
        toks = a.split()
        if toks and toks[0] in gui_targets and "WIN32" not in toks and not toks[0].lower().startswith("test"):
            add("QL014", line_of(src, pos))

    # QL013
    if re.search(r"(?im)^\s*find_package\s*\(\s*Qt6\b", src):
        if not re.search(r"(?im)^\s*qt_standard_project_setup\s*\(", src) and not re.search(r"CMAKE_AUTOMOC\s+ON", src):
            m = re.search(r"(?im)^\s*find_package\s*\(\s*Qt6\b", src)
            add("QL013", line_of(src, m.start()))

    # QL011 - GUI tests without QT_QPA_PLATFORM
    test_names: dict[str, int] = {}
    for pos, a in cmake_calls(src, "add_test"):
        toks = a.split()
        if "NAME" in toks:
            name = toks[toks.index("NAME") + 1]
            cmd = toks[toks.index("COMMAND") + 1] if "COMMAND" in toks else ""
            if cmd in gui_targets:
                test_names[name] = line_of(src, pos)
    for name, ln in test_names.items():
        has_env = False
        for _, a in cmake_calls(src, "set_tests_properties"):
            if name in a.split() and "QT_QPA_PLATFORM" in a:
                has_env = True
        if not has_env:
            add("QL011", ln)

    # QL015 (comments stripped: a path in a CMake comment is prose)
    for ln, text in enumerate(src.splitlines(), 1):
        if MACHINE_PATH_RE.search(text) and "machine-specific example" not in lines[ln - 1]:
            add("QL015", ln)

    return out


def lint_presets(path: str, display: str) -> list[Finding]:
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    out: list[Finding] = []
    for ln, text in enumerate(lines, 1):
        if MACHINE_PATH_RE.search(text) and "machine-specific example" not in text and not allowed(lines, ln, "QL015"):
            sev, msg = RULES["QL015"]
            out.append(Finding("QL015", sev, display, ln, text.strip(), msg))
    return out


# --------------------------------------------------------------------------- driver

def display_path(full: str) -> str:
    """Paths in findings and baseline keys are relative to the current directory
    (run the lint from the project root, like a compiler), with forward slashes
    so a baseline written on Windows matches on Linux and vice versa."""
    rel = os.path.relpath(full)
    if rel.startswith(".."):
        rel = os.path.abspath(full)
    return rel.replace(os.sep, "/")


def iter_files(paths: list[str]) -> Iterable[tuple[str, str]]:
    skip_dirs = {".git", "build", "node_modules", ".cache", "out", "dist", "reference_code"}
    for p in paths:
        if os.path.isfile(p):
            yield p, display_path(p)
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = sorted(d for d in dirs if d not in skip_dirs and not d.startswith("build"))
            for fn in sorted(files):
                full = os.path.join(root, fn)
                yield full, display_path(full)


def lint_paths(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for full, display in iter_files(paths):
        base = os.path.basename(full)
        ext = os.path.splitext(base)[1]
        try:
            if ext in CPP_EXT:
                findings.extend(lint_cpp(full, display))
            elif base in CMAKE_NAMES or ext in CMAKE_EXT:
                findings.extend(lint_cmake(full, display))
            elif base in PRESET_NAMES:
                findings.extend(lint_presets(full, display))
        except OSError as e:  # unreadable file: report, do not hide
            findings.append(Finding("QL000", "warning", display, 0, "", f"unreadable: {e}"))
    return sorted(findings, key=lambda f: (f.path, f.line, f.rule))


def summary(findings: list[Finding], baseline: set[str]) -> dict:
    new = [f for f in findings if f.key() not in baseline]
    by_sev: dict[str, int] = {}
    by_rule: dict[str, int] = {}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
    return {"total": len(findings), "new": len(new), "baselined": len(findings) - len(new),
            "by_severity": dict(sorted(by_sev.items())), "by_rule": dict(sorted(by_rule.items()))}


def report(findings: list[Finding], as_json: bool, baseline: set[str]) -> None:
    if as_json:
        print(json.dumps({"tool": "qt_lint", "summary": summary(findings, baseline),
                          "findings": [{**asdict(f), "key": f.key(), "baselined": f.key() in baseline}
                                       for f in findings]}, indent=2))
        return
    if not findings:
        print("qt_lint: no findings")
        return
    for f in findings:
        tag = " (baselined)" if f.key() in baseline else ""
        print(f"{f.path}:{f.line}: {f.rule} [{f.severity}]{tag} {f.message}")
        if f.text:
            print(f"    {f.text[:160]}")


# --------------------------------------------------------------------------- selftest

BAD_CPP = r'''
#include <QtWidgets>
#include <QMainWindow>
#include <QProcess>
#include <QFile>
class W : public QMainWindow {
  void setup() {
    connect(btn, SIGNAL(clicked()), this, SLOT(onClick()));
    connect(btn, &QPushButton::clicked, [this] { onClick(); });
    connect(btn, &QPushButton::clicked, this, [this] { onClick(); });   // fine
    proc_->waitForFinished(30000);
    qApp->processEvents();
    worker_->moveToThread(thread_);
    label->setStyleSheet("QLabel { color: #202020; }");
    QFile f("x"); f.open(QIODevice::WriteOnly | QIODevice::Truncate);
    QString qt = "C:/Qt/6.7.3/mingw_64";
  }
  QProcess* proc_;
};
'''

CLEAN_CPP = r'''
#include <QMainWindow>
#include <QProcess>
#include <QSaveFile>
#include <QPointer>
class W : public QMainWindow {
  void setup() {
    connect(btn, &QPushButton::clicked, this, [self = QPointer(this)] { if (self) self->onClick(); });
    connect(proc_, qOverload<int, QProcess::ExitStatus>(&QProcess::finished), this, &W::onFinished);
    connect(proc_, &QProcess::errorOccurred, this, &W::onError);
    connect(worker_, &Worker::done, this, &W::onDone, Qt::QueuedConnection);
    worker_->moveToThread(thread_);
    label->setStyleSheet("QLabel[role=hint] { color: palette(mid); }");
    QSaveFile f("x"); f.open(QIODevice::WriteOnly);
    proc_->waitForFinished(2000);  // ql-allow QL003: bounded shutdown wait, measured and registered
  }
  QProcess* proc_;
};
'''

BAD_CMAKE = r'''
cmake_minimum_required(VERSION 3.21)
project(x CXX)
find_package(Qt6 REQUIRED COMPONENTS Widgets)
add_executable(app main.cpp)
target_link_libraries(app PRIVATE Qt6::Widgets)
qt_add_executable(app2 main.cpp)
target_link_libraries(app2 PRIVATE Qt6::Widgets)
add_test(NAME gui COMMAND app2)
set(CMAKE_PREFIX_PATH "C:/Qt/6.7.3/mingw_64")
'''

CLEAN_CMAKE = r'''
cmake_minimum_required(VERSION 3.21)
project(x CXX)
find_package(Qt6 REQUIRED COMPONENTS Widgets)
qt_standard_project_setup()
qt_add_executable(app WIN32 MACOSX_BUNDLE main.cpp)
target_link_libraries(app PRIVATE Qt6::Widgets)
qt_add_executable(test_gui tests/gui.cpp)
target_link_libraries(test_gui PRIVATE Qt6::Widgets)
add_test(NAME gui COMMAND test_gui)
set_tests_properties(gui PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen")
'''

TEST_HARNESS_CPP = r'''
#include <QApplication>
#include <QProcess>
#include <QTimer>
#include <QFile>
int main() {
  QProcess p; p.waitForFinished(60000);           // fixture engine - fine in a harness
  QCoreApplication::processEvents();              // pumping - fine in a harness
  QTimer t; QObject::connect(&t, &QTimer::timeout, [] {});   // info only here
  QFile f("scratch"); f.open(QIODevice::WriteOnly);
  const char* fixture = "C:\\Users\\someone\\in.gif";    // path-handling fixture
}
'''

COMMENT_PATH_CPP = r'''
#include <QMainWindow>
// a space in C:\Users\John Smith\in.gif used to split the argv  <- prose, must not fire
/* also /home/someone/x in a block comment */
class W : public QMainWindow {};
'''

EXPECT_BAD_CPP = {"QL001", "QL002", "QL003", "QL004", "QL005", "QL006", "QL007", "QL008", "QL009", "QL015"}
EXPECT_BAD_CMAKE = {"QL011", "QL012", "QL013", "QL014", "QL015"}


def selftest() -> int:
    failures = 0

    def check(cond: bool, what: str) -> None:
        nonlocal failures
        print(("ok   " if cond else "FAIL ") + what)
        if not cond:
            failures += 1

    with tempfile.TemporaryDirectory() as d:
        paths = {}
        for name, body in (("bad/ui/w.cpp", BAD_CPP), ("clean/ui/w.cpp", CLEAN_CPP),
                           ("bad/CMakeLists.txt", BAD_CMAKE), ("clean/CMakeLists.txt", CLEAN_CMAKE)):
            full = os.path.join(d, name)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                f.write(body)
            paths[name] = full

        bad_cpp = {f.rule for f in lint_cpp(paths["bad/ui/w.cpp"], "bad/ui/w.cpp")}
        for r in sorted(EXPECT_BAD_CPP):
            check(r in bad_cpp, f"{r} fires on the bad C++ fixture")
        check(not (bad_cpp - EXPECT_BAD_CPP), f"no unexpected C++ rule fired: {sorted(bad_cpp - EXPECT_BAD_CPP)}")

        clean_cpp = lint_cpp(paths["clean/ui/w.cpp"], "clean/ui/w.cpp")
        check(not clean_cpp, f"clean C++ fixture is silent: {[(f.rule, f.line) for f in clean_cpp]}")

        bad_cm = {f.rule for f in lint_cmake(paths["bad/CMakeLists.txt"], "bad/CMakeLists.txt")}
        for r in sorted(EXPECT_BAD_CMAKE):
            check(r in bad_cm, f"{r} fires on the bad CMake fixture")
        check(not (bad_cm - EXPECT_BAD_CMAKE), f"no unexpected CMake rule fired: {sorted(bad_cm - EXPECT_BAD_CMAKE)}")

        clean_cm = lint_cmake(paths["clean/CMakeLists.txt"], "clean/CMakeLists.txt")
        check(not clean_cm, f"clean CMake fixture is silent: {[(f.rule, f.line) for f in clean_cm]}")

        # Mutation check: the inline allow must be the ONLY thing silencing QL003 in the clean fixture.
        mutated = CLEAN_CPP.replace("// ql-allow QL003: bounded shutdown wait, measured and registered", "")
        with open(paths["clean/ui/w.cpp"], "w", encoding="utf-8") as f:
            f.write(mutated)
        check(any(f.rule == "QL003" for f in lint_cpp(paths["clean/ui/w.cpp"], "clean/ui/w.cpp")),
              "removing the ql-allow comment makes QL003 fire again (the guard can fail)")

        # An allow without a reason must not suppress.
        no_reason = CLEAN_CPP.replace("// ql-allow QL003: bounded shutdown wait, measured and registered", "// ql-allow QL003:")
        with open(paths["clean/ui/w.cpp"], "w", encoding="utf-8") as f:
            f.write(no_reason)
        check(any(f.rule == "QL003" for f in lint_cpp(paths["clean/ui/w.cpp"], "clean/ui/w.cpp")),
              "a ql-allow with an empty reason does not suppress")

        # Test-file policy: only QL002 (as info) may fire on a harness.
        tpath = os.path.join(d, "tests", "test_gui.cpp")
        os.makedirs(os.path.dirname(tpath), exist_ok=True)
        with open(tpath, "w", encoding="utf-8") as f:
            f.write(TEST_HARNESS_CPP)
        tf = lint_cpp(tpath, "tests/test_gui.cpp")
        check({(x.rule, x.severity) for x in tf} == {("QL002", "info")},
              f"test harness: only QL002/info fires: {[(x.rule, x.severity) for x in tf]}")

        # A machine path in a comment is prose and must not fire.
        cpath = os.path.join(d, "src", "ui", "c.cpp")
        os.makedirs(os.path.dirname(cpath), exist_ok=True)
        with open(cpath, "w", encoding="utf-8") as f:
            f.write(COMMENT_PATH_CPP)
        check(not [x for x in lint_cpp(cpath, "src/ui/c.cpp") if x.rule == "QL015"],
              "QL015 ignores paths that appear only in comments")

        # Baseline round trip: everything baselined -> zero new.
        all_bad = lint_paths([os.path.join(d, "bad")])
        base = {f.key() for f in all_bad}
        check(all(f.key() in base for f in lint_paths([os.path.join(d, "bad")])), "baseline keys are stable across runs")

    print(f"selftest: {'PASS' if failures == 0 else 'FAIL'} ({failures} failure(s))")
    return 0 if failures == 0 else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="files or directories")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--baseline", help="JSON file of accepted finding keys")
    ap.add_argument("--write-baseline", help="write current findings as the accepted baseline")
    ap.add_argument("--fail-on", choices=["info", "warning", "error"], default="warning",
                    help="exit 1 if a NON-baselined finding has at least this severity (default: warning)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()
    if not a.paths:
        ap.error("give at least one path, or --selftest")

    findings = lint_paths(a.paths)

    if a.write_baseline:
        # Writing a baseline IS the act of accepting today's findings: list them so the
        # acceptance is visible in the log, then exit 0. Review the file before committing it.
        keys = sorted({x.key() for x in findings})
        with open(a.write_baseline, "w", encoding="utf-8") as f:
            json.dump({"generated_by": "qt_lint.py", "keys": keys}, f, indent=2)
        report(findings, a.json, set())
        print(f"qt_lint: wrote baseline with {len(keys)} key(s) for {len(findings)} finding(s) to {a.write_baseline} "
              f"- review it, then commit it next to the project's CI config")
        return 0

    baseline: set[str] = set()
    if a.baseline:
        with open(a.baseline, encoding="utf-8") as f:
            baseline = set(json.load(f).get("keys", []))

    report(findings, a.json, baseline)

    threshold = SEVERITY_ORDER[a.fail_on]
    bad = [f for f in findings if f.key() not in baseline and SEVERITY_ORDER.get(f.severity, 0) >= threshold]
    if not a.json:
        sm = summary(findings, baseline)
        print(f"qt_lint: {sm['total']} finding(s) ({', '.join(f'{k}: {v}' for k, v in sm['by_severity'].items()) or 'none'}); "
              f"{sm['new']} not in baseline; {len(bad)} at or above --fail-on={a.fail_on} -> exit {1 if bad else 0}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
