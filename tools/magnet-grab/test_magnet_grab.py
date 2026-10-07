#!/usr/bin/env python3
"""Tests for magnet_grab. Run with:  python3 -m unittest test_magnet_grab -v"""

from __future__ import annotations

import gzip
import http.server
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import magnet_grab as mg

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "magnet_grab.py")


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, SCRIPT, *args], capture_output=True, text=True
    )


class TestExtract(unittest.TestCase):
    def test_html_escaped_ampersand_is_not_truncated(self):
        """Saved HTML writes & as &amp;; a naive regex stops at the first tracker."""
        html = '<a href="magnet:?xt=urn:btih:' + "a" * 40 + '&amp;dn=X&amp;tr=udp%3A%2F%2Ft">'
        [m] = mg.extract(html)
        self.assertIn("tr=udp%3A%2F%2Ft", m.uri)
        self.assertEqual(len(m.trackers), 1)

    def test_magnets_inside_script_strings(self):
        html = '<script>var m = "magnet:?xt=urn:btih:' + "b" * 40 + '&dn=JS";</script>'
        [m] = mg.extract(html)
        self.assertEqual(m.name, "JS")

    def test_uppercase_scheme(self):
        html = '<a href="MAGNET:?XT=URN:BTIH:' + "c" * 40 + '&dn=Upper">'
        [m] = mg.extract(html)
        self.assertEqual(m.infohash, "c" * 40)

    def test_v2_multihash(self):
        h = "d" * 64
        [m] = mg.extract(f'<a href="magnet:?xt=urn:btmh:1220{h}">')
        self.assertEqual(m.version, 2)
        self.assertEqual(m.infohash, h)

    def test_v1_base32_hash(self):
        [m] = mg.extract('<a href="magnet:?xt=urn:btih:ABCDEFGHIJKLMNOPQRSTUVWXYZ234567&dn=B32">')
        self.assertEqual(m.infohash, "abcdefghijklmnopqrstuvwxyz234567")
        self.assertEqual(m.version, 1)

    def test_duplicate_hash_collapses(self):
        html = (
            '<a href="magnet:?xt=urn:btih:' + "e" * 40 + '&dn=one">a</a>'
            '<a href="magnet:?xt=urn:btih:' + "e" * 40 + '&dn=two">b</a>'
        )
        self.assertEqual(len(mg.extract(html)), 1)

    def test_dedupe_false_returns_every_occurrence(self):
        html = (
            '<a href="magnet:?xt=urn:btih:' + "e" * 40 + '&dn=one">a</a>'
            '<a href="magnet:?xt=urn:btih:' + "e" * 40 + '&dn=two">b</a>'
        )
        got = mg.extract(html, dedupe=False)
        self.assertEqual(len(got), 2)
        self.assertEqual([m.name for m in got], ["one", "two"])

    def test_extract_dedupes_by_default(self):
        html = (
            '<a href="magnet:?xt=urn:btih:' + "e" * 40 + '&dn=one">a</a>'
            '<a href="magnet:?xt=urn:btih:' + "e" * 40 + '&dn=two">b</a>'
        )
        self.assertEqual(len(mg.extract(html)), 1)

    def test_longest_uri_wins_when_deduping(self):
        html = (
            '<a href="magnet:?xt=urn:btih:' + "f" * 40 + '">short</a>'
            '<a href="magnet:?xt=urn:btih:' + "f" * 40 + '&tr=udp://tracker">long</a>'
        )
        [m] = mg.extract(html)
        self.assertEqual(len(m.trackers), 1)


class TestRejection(unittest.TestCase):
    """Things that look like magnets but must not be emitted."""

    def test_css_class_name(self):
        self.assertEqual(mg.extract("<style>.magnet-link{}</style>"), [])

    def test_truncated_hash(self):
        self.assertEqual(mg.extract('<a href="magnet:?xt=urn:btih:tooshort">'), [])

    def test_ed2k_is_not_bittorrent(self):
        self.assertEqual(mg.extract('<a href="magnet:?xt=urn:ed2k:' + "a" * 32 + '">'), [])

    def test_missing_xt(self):
        self.assertEqual(mg.extract('<a href="magnet:?dn=nohash">'), [])

    def test_trailing_punctuation_stripped(self):
        [m] = mg.extract("grab it: magnet:?xt=urn:btih:" + "a" * 40 + ".")
        self.assertFalse(m.uri.endswith("."))


class TestCleanUri(unittest.TestCase):
    def test_strip_trackers_keeps_xt_and_dn(self):
        uri = "magnet:?xt=urn:btih:" + "a" * 40 + "&dn=Name&tr=udp://x&tr=udp://y"
        [m] = mg.extract(f'<a href="{uri}">')
        clean = m.clean_uri
        self.assertNotIn("tr=", clean)
        self.assertIn("xt=urn:btih:" + "a" * 40, clean)
        self.assertIn("dn=Name", clean)


class TestDecoding(unittest.TestCase):
    def test_gzip_payload(self):
        blob = gzip.compress(b'<a href="magnet:?xt=urn:btih:' + b"a" * 40 + b'">')
        text = mg.decode_bytes(blob)
        self.assertEqual(len(mg.extract(text)), 1)

    def test_cp1252_page_with_meta_charset(self):
        page = (
            '<html><meta charset="windows-1252">'
            '<a href="magnet:?xt=urn:btih:' + "a" * 40 + '&dn=Caf%E9">x</a></html>'
        ).encode("cp1252")
        text = mg.decode_bytes(page)
        [m] = mg.extract(text)
        self.assertEqual(m.name, "Café")

    def test_percent_encoded_utf8_name(self):
        [m] = mg.extract(
            '<a href="magnet:?xt=urn:btih:' + "a" * 40 + '&dn=%E6%97%A5%E6%9C%AC%E8%AA%9E">'
        )
        self.assertEqual(m.name, "日本語")


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.page = os.path.join(self.dir, "page.html")
        with open(self.page, "w", encoding="utf-8") as fh:
            fh.write(
                '<a href="magnet:?xt=urn:btih:' + "a" * 40 + '&amp;dn=Alpha&amp;tr=udp://t">a</a>'
                '<a href="magnet:?xt=urn:btih:' + "b" * 40 + '&amp;dn=Beta">b</a>'
            )

    def test_plain_emits_one_per_line(self):
        r = cli(self.page, "--plain")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(x.startswith("magnet:?") for x in lines))

    def test_table_is_default(self):
        r = cli(self.page)
        self.assertIn("Alpha", r.stdout)
        self.assertIn("a" * 40, r.stdout)
        self.assertIn("2 unique magnet link(s)", r.stderr)

    def test_json_shape(self):
        r = cli(self.page, "--json")
        data = json.loads(r.stdout)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Alpha")
        self.assertEqual(data[0]["trackers"], 1)

    def test_filter(self):
        r = cli(self.page, "--plain", "--filter", "beta")
        self.assertEqual(r.stdout.strip().count("\n"), 0)
        self.assertIn("b" * 40, r.stdout)

    def test_bad_filter_is_clean_usage_error(self):
        r = cli(self.page, "--filter", "[")
        self.assertEqual(r.returncode, 2)
        self.assertIn("invalid --filter regex", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_missing_file_warns_and_fails(self):
        r = cli(os.path.join(self.dir, "nope.html"), "--plain")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout, "")
        self.assertIn("No such file", r.stderr)

    def test_no_inputs_is_usage_error(self):
        r = cli()
        self.assertEqual(r.returncode, 2)

    def test_binary_file_does_not_crash(self):
        junk = os.path.join(self.dir, "junk.html")
        with open(junk, "wb") as fh:
            fh.write(os.urandom(4096))
        r = cli(junk)
        self.assertEqual(r.returncode, 0)
        self.assertIn("no magnet links found", r.stdout)

    def test_stdin(self):
        r = subprocess.run(
            [sys.executable, SCRIPT, "-", "--plain"],
            input=pathlib.Path(self.page).read_text(encoding="utf-8"),
            capture_output=True,
            text=True,
        )
        self.assertEqual(len(r.stdout.strip().split("\n")), 2)

    def test_no_dedupe_flag_keeps_duplicates(self):
        dup = os.path.join(self.dir, "dup.html")
        h = "e" * 40
        with open(dup, "w", encoding="utf-8") as fh:
            fh.write(f'<a href="magnet:?xt=urn:btih:{h}&dn=one">a</a>'
                     f'<a href="magnet:?xt=urn:btih:{h}&dn=two">b</a>')
        self.assertEqual(len(cli(dup, "--plain").stdout.strip().split("\n")), 1)
        self.assertEqual(len(cli(dup, "--plain", "--no-dedupe").stdout.strip().split("\n")), 2)

    def test_legacy_latin1_percent_encoding_in_name(self):
        legacy = os.path.join(self.dir, "legacy.html")
        with open(legacy, "w", encoding="utf-8") as fh:
            fh.write('<a href="magnet:?xt=urn:btih:' + "a" * 40 + '&dn=Caf%E9">x</a>')
        r = cli(legacy, "--json")
        self.assertEqual(json.loads(r.stdout)[0]["name"], "Café")

    def test_directory_walk_includes_gz(self):
        with gzip.open(os.path.join(self.dir, "z.html.gz"), "wb") as fh:
            fh.write(b'<a href="magnet:?xt=urn:btih:' + b"c" * 40 + b'&dn=Gz">')
        r = cli(self.dir, "--plain")
        self.assertEqual(len(r.stdout.strip().split("\n")), 3)


class TestQBittorrentAPI(unittest.TestCase):
    """Exercise the real login + multipart add path against a mock WebUI."""

    def setUp(self):
        self.received = {}
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                if self.path == "/api/v2/auth/login":
                    outer.received["login"] = body.decode()
                    outer.received["login_cookie"] = self.headers.get("Cookie")
                    self.send_response(200)
                    self.send_header("Set-Cookie", "SID=testsid; path=/")
                    self.end_headers()
                    self.wfile.write(b"Ok.")
                else:
                    outer.received["add_cookie"] = self.headers.get("Cookie")
                    outer.received["ctype"] = self.headers.get("Content-Type")
                    outer.received["add"] = body.decode()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Ok.")

        self.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_add_sends_sid_and_newline_separated_urls(self):
        client = mg.QBittorrent(f"http://127.0.0.1:{self.port}", "admin", "pw")
        self.assertEqual(self.received["login"], "username=admin&password=pw")
        self.assertIsNone(self.received["login_cookie"])

        client.add(["magnet:?xt=urn:btih:aaa", "magnet:?xt=urn:btih:bbb"], savepath="/dl")

        self.assertEqual(self.received["add_cookie"], "SID=testsid")
        self.assertTrue(self.received["ctype"].startswith("multipart/form-data; boundary="))
        self.assertIn('name="urls"', self.received["add"])
        self.assertIn("magnet:?xt=urn:btih:aaa\nmagnet:?xt=urn:btih:bbb", self.received["add"])
        self.assertIn("/dl", self.received["add"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
