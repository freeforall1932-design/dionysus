"""Portable distribution regressions; no third-party dependencies."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import package_dropins as pkg


class DropinTests(unittest.TestCase):
    def test_real_roots_and_legacy_targets(self):
        self.assertTrue((pkg.ROOT / "skills").is_dir())
        self.assertFalse((pkg.ROOT / "skills").is_symlink())
        self.assertEqual((pkg.ROOT / "workbench/skills").resolve(), pkg.ROOT / "skills")
        for removed in ("gifscythe", "shotgun-king-anew", "Odysseus API model team kit",
                        "workbench/projects/gifscythe", "workbench/projects/shotgun-king-anew",
                        "workbench/projects/ai-team-kit"):
            self.assertFalse((pkg.ROOT / removed).exists())
            self.assertFalse((pkg.ROOT / removed).is_symlink())

    def test_symlink_payload_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "file").write_text("payload")
            (root / "link").symlink_to(root / "file")
            with self.assertRaisesRegex(ValueError, "Symlink"):
                pkg.payload(root)

    def test_output_inside_payload_refused(self):
        with self.assertRaisesRegex(ValueError, "inside"):
            pkg.build(pkg.ROOT, pkg.ROOT / "skills" / "archives")

    def test_repeatable_complete_archives(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            paths = pkg.build(pkg.ROOT, output)
            self.assertEqual({p.stem for p in paths}, set(pkg.NAMES))
            self.assertEqual(len(paths), 1)
            first = {p.name: hashlib.sha256(p.read_bytes()).digest() for p in paths}
            for p in pkg.build(pkg.ROOT, output):
                self.assertEqual(hashlib.sha256(p.read_bytes()).digest(), first[p.name])
                with zipfile.ZipFile(p) as zf:
                    names = zf.namelist()
                    self.assertTrue(all(n.startswith(p.stem + "/") for n in names))
                    self.assertIn(p.stem + "/" + pkg.MANIFEST, names)

    def test_portable_gate_detects_missing_reference(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(pkg.ROOT / "skills", root / "skills", ignore=shutil.ignore_patterns("__pycache__"))
            (root / "skills/qt6-cmake-cpp/references/testing.md").unlink()
            result = subprocess.run([sys.executable, str(root / "skills/validate_skills.py"),
                                     "--root", str(root), "--layout", "portable", "--quiet"],
                                    cwd=root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("testing.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
