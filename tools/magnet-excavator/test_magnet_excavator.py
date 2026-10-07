#!/usr/bin/env python3
"""Tests for magnet_excavator. Run with:  python3 -m unittest test_magnet_excavator -v"""

from __future__ import annotations

import gzip
import hashlib
import http.server
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import magnet_excavator as mg

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "magnet_excavator.py")


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, SCRIPT, *args], capture_output=True, text=True
    )


def _chunks(text: str, size: int):
    """Split text into fixed-size pieces, as iter_text_chunks would."""
    for i in range(0, len(text), size):
        yield text[i : i + size]


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


    def test_empty_params_are_dropped(self):
        """A stray && must not leave a trailing ampersand after stripping."""
        uri = "magnet:?xt=urn:btih:" + "a" * 40 + "&dn=Name&&tr=udp://x"
        [m] = mg.extract(f'<a href="{uri}">')
        self.assertFalse(m.clean_uri.endswith("&"))
        self.assertEqual(m.clean_uri, "magnet:?xt=urn:btih:" + "a" * 40 + "&dn=Name")


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


    def test_cross_source_attribution_and_richest_wins(self):
        """A hash in two files must list both, and keep the URI with more trackers."""
        a = os.path.join(self.dir, "srcA.html")
        b = os.path.join(self.dir, "srcB.html")
        h = "a" * 40
        with open(a, "w", encoding="utf-8") as fh:
            fh.write(f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=T&amp;tr=udp://one">x</a>')
        with open(b, "w", encoding="utf-8") as fh:
            fh.write(
                f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=T&amp;tr=udp://one'
                f'&amp;tr=udp://two&amp;tr=udp://three">x</a>'
            )
        r = cli(a, b, "--json")
        [rec] = json.loads(r.stdout)
        self.assertEqual(rec["trackers"], 3)
        self.assertEqual(len(rec["sources"]), 2)
        self.assertIn(a, rec["sources"])
        self.assertIn(b, rec["sources"])

    def test_pick_first_keeps_the_earlier_uri(self):
        a = os.path.join(self.dir, "srcA.html")
        b = os.path.join(self.dir, "srcB.html")
        h = "a" * 40
        with open(a, "w", encoding="utf-8") as fh:
            fh.write(f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=T&amp;tr=udp://one">x</a>')
        with open(b, "w", encoding="utf-8") as fh:
            fh.write(f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=T&amp;tr=udp://1&amp;tr=udp://2">x</a>')
        [rec] = json.loads(cli(a, b, "--pick", "first", "--json").stdout)
        self.assertEqual(rec["trackers"], 1)

    def test_pick_first_survives_intra_file_duplicates(self):
        """--pick first must not swap URIs even when one file repeats a hash."""
        a = os.path.join(self.dir, "srcA.html")
        b = os.path.join(self.dir, "srcB.html")
        h = "a" * 40
        with open(a, "w", encoding="utf-8") as fh:
            fh.write(f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=T&amp;tr=udp://one">x</a>'
                     f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=T&amp;tr=udp://1&amp;tr=udp://2">y</a>')
        with open(b, "w", encoding="utf-8") as fh:
            fh.write(f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=T&amp;tr=udp://z">x</a>')
        first = json.loads(cli(a, b, "--pick", "first", "--json").stdout)[0]
        richest = json.loads(cli(a, b, "--pick", "richest", "--json").stdout)[0]
        self.assertEqual(richest["trackers"], 2)
        self.assertEqual(first["trackers"], 1)
        self.assertEqual(len(first["sources"]), 2)

    def test_summary_reports_per_source_counts(self):
        r = cli(self.page, "--summary")
        self.assertEqual(r.returncode, 0)
        self.assertIn("page.html", r.stdout)
        self.assertIn("UNIQUE", r.stdout)

    def test_out_dir_writes_one_file_per_source(self):
        out = os.path.join(self.dir, "out")
        r = cli(self.page, "--out-dir", out)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")  # table suppressed when writing files
        written = os.path.join(out, "page.txt")
        self.assertTrue(os.path.exists(written))
        with open(written, encoding="utf-8") as fh:
            lines = fh.read().strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(x.startswith("magnet:?") for x in lines))

    def test_split_writes_part_files(self):
        many = os.path.join(self.dir, "many2.html")
        with open(many, "w", encoding="utf-8") as fh:
            for i in range(25):
                fh.write(f'<a href="magnet:?xt=urn:btih:{i:040x}&amp;dn=N{i}">x</a>')
        out = os.path.join(self.dir, "parts")
        r = cli(many, "--out-dir", out, "--split", "10")
        self.assertEqual(r.returncode, 0)
        names = sorted(os.listdir(out))
        self.assertEqual(names, ["many2.part01.txt", "many2.part02.txt", "many2.part03.txt"])
        counts = []
        for n in names:
            with open(os.path.join(out, n), encoding="utf-8") as fh:
                counts.append(len([x for x in fh.read().split("\n") if x]))
        self.assertEqual(counts, [10, 10, 5])
        self.assertEqual(sum(counts), 25)

    def test_table_is_capped_by_limit(self):
        many = os.path.join(self.dir, "many.html")
        with open(many, "w", encoding="utf-8") as fh:
            for i in range(120):
                h = f"{i:040x}"
                fh.write(f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=N{i}">x</a>')
        capped = cli(many, "--limit", "10")
        self.assertIn("... 110 more", capped.stdout)
        full = cli(many, "--limit", "0")
        self.assertNotIn("more (use --limit 0", full.stdout)
        self.assertEqual(len(full.stdout.strip().split("\n")), 122)  # header + rule + 120


class TestStreaming(unittest.TestCase):
    """The chunked reader must not lose or duplicate links at a boundary."""

    def test_magnet_straddling_chunk_boundary_is_found_once(self):
        h = "ab" * 20
        link = "magnet:?xt=urn:btih:" + h + "&dn=Straddle"
        text = "x" * 900 + link + '">' + "y" * 500
        # chunk at 1024 so the link is guaranteed to straddle the cut
        got = list(mg.iter_matches(_chunks(text, 1024)))
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0].name, "Straddle")

    def test_no_match_lost_across_many_chunks(self):
        """Force many boundaries with a tiny chunk size — deterministic, no big fixture."""
        d = tempfile.mkdtemp()
        path = os.path.join(d, "multi.html")
        n = 3000
        with open(path, "w", encoding="utf-8") as fh:
            for i in range(n):
                fh.write(
                    f'<tr><td><a href="magnet:?xt=urn:btih:{i:040x}&amp;dn=N{i}">m</a></td>'
                    f"<td>{i % 900 + 1} MB</td></tr>"
                )
        small = 4096
        self.assertGreater(os.path.getsize(path), small)
        got = list(
            mg.iter_matches_with_size(mg.iter_text_chunks(path, chunk_bytes=small))
        )
        self.assertEqual(len(got), n)
        self.assertEqual(len({m.infohash for m in got}), n)

    def test_magnet_at_every_boundary_offset(self):
        """Sweep a link across every byte offset around a chunk boundary."""
        d = tempfile.mkdtemp()
        path = os.path.join(d, "sweep.html")
        h = "ab" * 20
        link = "magnet:?xt=urn:btih:" + h + "&dn=Sweep"
        found = 0
        for offset in range(0, 300, 7):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("x" * offset + link + "\n")
            got = list(mg.iter_matches(mg.iter_text_chunks(path, chunk_bytes=64)))
            if len(got) == 1 and got[0].name == "Sweep":
                found += 1
        self.assertEqual(found, len(range(0, 300, 7)))

    def test_any_extension_is_scanned(self):
        d = tempfile.mkdtemp()
        for name in ("list.txt", "weird.xyz123", "dump.log"):
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                h = hashlib.sha1(name.encode()).hexdigest()
                fh.write(f"noise magnet:?xt=urn:btih:{h}&dn={name} noise")
        paths = mg.collect_paths([d])
        self.assertEqual(len(paths), 3)

    def test_binary_file_yields_clean_uri(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "blob.bin")
        h = "cd" * 20
        with open(path, "wb") as fh:
            fh.write(b"\x00\x01\xff\xfe" * 500)
            fh.write(f"magnet:?xt=urn:btih:{h}&dn=InBinary".encode())
            fh.write(b"\x00\xff\xfe" * 500)
        [m] = list(mg.iter_matches(mg.iter_text_chunks(path)))
        self.assertEqual(m.name, "InBinary")
        self.assertFalse(any(ord(c) > 126 for c in m.uri))

    def test_ext_filter_prunes_walk_only(self):
        d = tempfile.mkdtemp()
        for n in ("a.html", "b.txt"):
            with open(os.path.join(d, n), "w", encoding="utf-8") as fh:
                fh.write("x")
        self.assertEqual(len(mg.collect_paths([d], {".html"})), 1)
        # an explicitly named file is never pruned, so typos surface as errors
        named = os.path.join(d, "b.txt")
        self.assertEqual(mg.collect_paths([named], {".html"}), [named])


class TestSizes(unittest.TestCase):
    def test_parse_size_units_are_binary(self):
        self.assertEqual(mg.parse_size("1 MB"), 1 << 20)
        self.assertEqual(mg.parse_size("700MB"), 700 * (1 << 20))
        self.assertEqual(mg.parse_size("1.4 GB"), int(1.4 * (1 << 30)))
        self.assertEqual(mg.parse_size("12,5 KiB"), 12800)
        self.assertEqual(mg.parse_size("100 B"), 100)
        self.assertEqual(mg.parse_size("2 TB"), 2 * (1 << 40))
        self.assertIsNone(mg.parse_size("no size here"))

    def test_size_scraped_from_table_row(self):
        html = (
            '<tr><td><a href="magnet:?xt=urn:btih:' + "a" * 40 + '&amp;dn=X">m</a></td>'
            "<td>1.4 GB</td><td>52</td></tr>"
        )
        [m] = mg.extract(html)
        self.assertEqual(m.size, int(1.4 * (1 << 30)))

    def test_size_scrape_stops_at_row_end(self):
        """A size in the NEXT row must not be attributed to this link."""
        html = (
            '<tr><td><a href="magnet:?xt=urn:btih:' + "a" * 40 + '&amp;dn=X">m</a></td></tr>'
            "<tr><td>9.9 GB</td></tr>"
        )
        [m] = mg.extract(html)
        self.assertIsNone(m.size)

    def test_xl_param_wins_over_nothing(self):
        html = '<a href="magnet:?xt=urn:btih:' + "a" * 40 + '&xl=1234567&dn=X">'
        [m] = mg.extract(html)
        self.assertEqual(m.size, 1234567)

    def test_size_listed_before_the_link_in_same_row(self):
        """Common layout: Name | Size | Seeds | Magnet."""
        html = (
            "<tr><td>Ubuntu 24.04</td><td>4.7 GB</td><td>1204</td>"
            '<td><a href="magnet:?xt=urn:btih:' + "a" * 40 + '&amp;dn=X">Magnet</a></td></tr>'
        )
        [m] = mg.extract(html)
        self.assertEqual(m.size, int(4.7 * (1 << 30)))

    def test_link_outside_a_table_does_not_inherit_a_row_size(self):
        """A link after the table must not borrow the last row's size."""
        html = (
            "<table><tr><td>Thing</td><td>340 MB</td>"
            '<td><a href="magnet:?xt=urn:btih:' + "a" * 40 + '&amp;dn=InRow">m</a></td></tr></table>'
            '<p><a href="magnet:?xt=urn:btih:' + "b" * 40 + '&amp;dn=Outside">outside</a></p>'
        )
        found = {m.name: m.size for m in mg.extract(html)}
        self.assertEqual(found["InRow"], 340 * (1 << 20))
        self.assertIsNone(found["Outside"])

    def test_link_in_script_does_not_inherit_a_row_size(self):
        html = (
            "<table><tr><td>500 MB</td>"
            '<td><a href="magnet:?xt=urn:btih:' + "a" * 40 + '&amp;dn=InRow">m</a></td></tr></table>'
            '<script>var u = "magnet:?xt=urn:btih:' + "b" * 40 + '&dn=InJS";</script>'
        )
        found = {m.name: m.size for m in mg.extract(html)}
        self.assertIsNone(found["InJS"])

    def test_min_and_max_size_filters(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "p.html")
        with open(path, "w", encoding="utf-8") as fh:
            for i, size in enumerate(["100 MB", "5 GB", "900 GB"]):
                fh.write(
                    f'<tr><td><a href="magnet:?xt=urn:btih:{i:040x}&amp;dn=S{i}">m</a></td>'
                    f"<td>{size}</td></tr>"
                )
        kept = cli(path, "--min-size", "1GB", "--max-size", "10GB", "--json")
        names = [r["name"] for r in json.loads(kept.stdout)]
        self.assertEqual(names, ["S1"])

    def test_summary_reports_total_size(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "p.html")
        with open(path, "w", encoding="utf-8") as fh:
            for i, size in enumerate(["1 GB", "2 GB"]):
                fh.write(
                    f'<tr><td><a href="magnet:?xt=urn:btih:{i:040x}&amp;dn=S{i}">m</a></td>'
                    f"<td>{size}</td></tr>"
                )
        out = cli(path, "--summary").stdout
        self.assertIn("ESTIMATED TOTAL", out)
        self.assertIn("3.0 GiB", out)


class TestBareMode(unittest.TestCase):
    """--bare emits only what identifies the torrent."""

    def test_bare_keeps_only_xt(self):
        h = "a" * 40
        html = f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=Some+Name&amp;tr=udp://x&amp;xl=999">'
        [m] = mg.extract(html)
        self.assertEqual(m.bare_uri, "magnet:?xt=urn:btih:" + h)

    def test_bare_preserves_v2_hash(self):
        h = "c" * 64
        [m] = mg.extract(f'<a href="magnet:?xt=urn:btmh:1220{h}&amp;dn=X">')
        self.assertEqual(m.bare_uri, "magnet:?xt=urn:btmh:1220" + h)

    def test_bare_keeps_every_xt_on_a_dual_link(self):
        h1, h2 = "a" * 40, "c" * 64
        [m] = mg.extract(
            f'<a href="magnet:?xt=urn:btih:{h1}&amp;xt=urn:btmh:1220{h2}&amp;dn=Dual">'
        )
        self.assertIn("xt=urn:btih:" + h1, m.bare_uri)
        self.assertIn("xt=urn:btmh:1220" + h2, m.bare_uri)
        self.assertNotIn("dn=", m.bare_uri)

    def test_bare_flag_emits_one_bare_link_per_line(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "p.html")
        with open(path, "w", encoding="utf-8") as fh:
            for i in range(3):
                fh.write(
                    f'<tr><td><a href="magnet:?xt=urn:btih:{i:040x}&amp;dn=N{i}&amp;tr=udp://t">m</a></td>'
                    "<td>1 GB</td></tr>"
                )
        lines = cli(path, "--plain", "--bare").stdout.strip().split("\n")
        self.assertEqual(len(lines), 3)
        for i, line in enumerate(lines):
            self.assertEqual(line, f"magnet:?xt=urn:btih:{i:040x}")

    def test_bare_supersedes_strip_trackers(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "p.html")
        h = "a" * 40
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=Name&amp;tr=udp://t">x</a>')
        out = cli(path, "--plain", "--bare", "--strip-trackers").stdout.strip()
        self.assertEqual(out, "magnet:?xt=urn:btih:" + h)

    def test_bare_in_json_output(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "p.html")
        h = "a" * 40
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=Name&amp;tr=udp://t">x</a>')
        [rec] = json.loads(cli(path, "--json", "--bare").stdout)
        self.assertEqual(rec["magnet"], "magnet:?xt=urn:btih:" + h)
        # metadata is still reported even though the emitted link is bare
        self.assertEqual(rec["name"], "Name")
        self.assertEqual(rec["trackers"], 1)

    def test_bare_is_shorter_than_full(self):
        h = "a" * 40
        html = f'<a href="magnet:?xt=urn:btih:{h}&amp;dn=A+Fairly+Long+Name&amp;tr=udp://tracker">'
        [m] = mg.extract(html)
        self.assertLess(len(m.bare_uri), len(m.clean_uri))
        self.assertLess(len(m.clean_uri), len(m.uri))


class TestCanonicalization(unittest.TestCase):
    """Parameter names are case-sensitive, so an uppercase link must be fixed."""

    def test_all_uppercase_link_is_normalized(self):
        h = "a" * 40
        [m] = mg.extract(f'<a href="MAGNET:?XT=URN:BTIH:{h}&DN=Blender+4.2+LTS">')
        self.assertTrue(m.uri.startswith("magnet:?xt=urn:btih:" + h))
        self.assertIn("&dn=Blender+4.2+LTS", m.uri)

    def test_display_name_case_is_preserved(self):
        h = "a" * 40
        [m] = mg.extract(f'<a href="magnet:?xt=urn:btih:{h}&dn=MiXeD+CaSe+Name">')
        self.assertIn("dn=MiXeD+CaSe+Name", m.uri)

    def test_v2_namespace_is_normalized(self):
        h = "c" * 64
        [m] = mg.extract(f'<a href="magnet:?XT=URN:BTMH:1220{h}">')
        self.assertTrue(m.uri.startswith("magnet:?xt=urn:btmh:1220" + h))

    def test_every_emitted_line_is_paste_ready(self):
        h = "a" * 40
        text = (
            f'<a href="MAGNET:?XT=URN:BTIH:{h}&DN=Upper">x</a>'
            f'<a href="magnet:?xt=urn:btih:{"b" * 40}&dn=Lower">y</a>'
        )
        for m in mg.extract(text):
            self.assertRegex(m.uri, r"^magnet:\?xt=urn:bt(ih|mh):")


class TestRegexAnchoring(unittest.TestCase):
    def test_magnet_preceded_by_word_character_still_matches(self):
        got = mg.extract('{"url":"magnet:?xt=urn:btih:' + "a" * 40 + '&dn=J"}')
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0].name, "J")

    def test_plain_text_has_no_false_positives(self):
        self.assertEqual(mg.extract("just prose about magnet links and magnets"), [])


class TestQBittorrentAPI(unittest.TestCase):
    """Exercise the real login + multipart add path against a mock WebUI."""

    def setUp(self):
        self.received = {}
        self.active = 3          # how many torrents /torrents/info reports
        self.add_sizes = []      # urls per /torrents/add call
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                if self.path.startswith("/api/v2/torrents/info"):
                    payload = json.dumps([{"hash": f"{i:040x}"} for i in range(outer.active)]).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                else:
                    self.send_response(404)
                    self.end_headers()

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
                    m = re.search(rb'name="urls"\r\n\r\n(.*?)\r\n------', body, re.S)
                    n = len(m.group(1).decode().split("\n")) if m else 0
                    outer.add_sizes.append(n)
                    # simulate the queue draining as those links start and finish
                    outer.active = max(0, outer.active - n)
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


    def test_active_count_reads_torrent_list(self):
        client = mg.QBittorrent(f"http://127.0.0.1:{self.port}", "admin", "pw")
        self.active = 3
        self.assertEqual(client.active_count("downloading"), 3)
        self.active = 0
        self.assertEqual(client.active_count("downloading"), 0)

    def test_feeder_adds_only_into_available_headroom(self):
        """--max-active must add into the headroom and no further."""
        d = tempfile.mkdtemp()
        path = os.path.join(d, "many.html")
        with open(path, "w", encoding="utf-8") as fh:
            for i in range(10):
                fh.write(f'<a href="magnet:?xt=urn:btih:{i:040x}&amp;dn=N{i}">x</a>')

        # 4 already downloading, cap of 6 -> only 2 fit on the first pass.
        # The mock drains as links are added, so the run terminates.
        self.active = 4
        r = subprocess.run(
            [sys.executable, SCRIPT, path, "--add",
             "--host", f"http://127.0.0.1:{self.port}",
             "--username", "a", "--password", "b",
             "--max-active", "6", "--poll-interval", "0.1"],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.add_sizes, [2, 4, 4])
        self.assertEqual(sum(self.add_sizes), 10)

    def test_add_batches_urls_across_requests(self):
        client = mg.QBittorrent(f"http://127.0.0.1:{self.port}", "admin", "pw")
        uris = [f"magnet:?xt=urn:btih:{i:040x}" for i in range(5)]
        size = 2
        sent = 0
        for start in range(0, len(uris), size):
            client.add(uris[start : start + size])
            sent += len(uris[start : start + size])
        self.assertEqual(sent, 5)
        # the mock records only the last body, so assert its shape
        self.assertIn("magnet:?xt=urn:btih:" + f"{4:040x}", self.received["add"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestMetadataAttribution(unittest.TestCase):
    """A name and size must reach the right link wherever the page puts them.

    These five layouts are the ones that broke: metadata above the link, below
    it, in a separate table row, in the same row after the link, and inline in a
    paragraph. The old scraper keyed off character distance, which cannot tell
    "4.7 GB" sitting above a link from "4.7 GB" sitting below the previous one.
    """

    HASHES = ["%040x" % i for i in range(1, 4)]
    NAMES = ["Ubuntu 24.04", "Fedora 41", "Blender 4.2"]
    SIZES = ["4.7 GB", "2.3 GB", "340 MB"]
    EXPECTED = ["4.7 GiB", "2.3 GiB", "340.0 MiB"]

    def rows(self):
        return list(zip(self.HASHES, self.NAMES, self.SIZES))

    def assert_pairs(self, html):
        magnets = mg.extract(html)
        self.assertEqual(len(magnets), 3)
        for m, name, size in zip(magnets, self.NAMES, self.EXPECTED):
            self.assertEqual(m.name, name)
            self.assertEqual(mg.human_size(m.size), size)
            self.assertEqual(m.name_source, "page")

    def test_metadata_above_the_link(self):
        parts = []
        for h, n, s in self.rows():
            parts.append(
                f'<div class="item"><div class="title">{n}</div>'
                f'<div class="size">{s}</div>'
                f'<a href="magnet:?xt=urn:btih:{h}">Download</a></div>'
            )
        self.assert_pairs("".join(parts))

    def test_metadata_below_the_link(self):
        parts = []
        for h, n, s in self.rows():
            parts.append(
                f'<div class="item"><a href="magnet:?xt=urn:btih:{h}">Download</a>'
                f'<div class="title">{n}</div>'
                f'<div class="size">{s}</div></div>'
            )
        self.assert_pairs("".join(parts))

    def test_metadata_in_the_previous_table_row(self):
        parts = []
        for h, n, s in self.rows():
            parts.append(
                f"<tr><td>{n}</td><td>{s}</td></tr>"
                f'<tr><td><a href="magnet:?xt=urn:btih:{h}">get</a></td></tr>'
            )
        self.assert_pairs("<table>" + "".join(parts) + "</table>")

    def test_metadata_in_the_same_row_after_the_link(self):
        parts = []
        for h, n, s in self.rows():
            parts.append(
                f'<tr><td><a href="magnet:?xt=urn:btih:{h}">m</a></td>'
                f"<td>{n}</td><td>{s}</td></tr>"
            )
        self.assert_pairs("<table>" + "".join(parts) + "</table>")

    def test_metadata_inline_in_a_paragraph(self):
        parts = []
        for h, n, s in self.rows():
            parts.append(
                f'<p>{n} &mdash; {s}<br><a href="magnet:?xt=urn:btih:{h}">dl</a></p>'
            )
        self.assert_pairs("".join(parts))

    def test_size_in_a_following_row_is_not_taken(self):
        """A preceding row may feed a link; a following one must never feed it."""
        html = (
            '<table><tr><td><a href="magnet:?xt=urn:btih:' + "a" * 40 + '">m</a></td></tr>'
            "<tr><td>9.9 GB</td></tr></table>"
        )
        [m] = mg.extract(html)
        self.assertIsNone(m.size)

    def test_a_block_holding_two_links_gets_neither_size(self):
        """Crossing into another entry's magnet would risk a wrong total."""
        html = (
            '<div class="row"><a href="magnet:?xt=urn:btih:' + "a" * 40 + '">a</a>'
            '<a href="magnet:?xt=urn:btih:' + "b" * 40 + '">b</a>'
            "<span>5.0 GB</span></div>"
        )
        magnets = mg.extract(html)
        self.assertEqual(len(magnets), 2)
        self.assertTrue(all(m.size is None for m in magnets))

    def test_dn_in_the_uri_beats_the_page(self):
        html = (
            '<div><span>Page Name</span><span>1.0 GB</span>'
            '<a href="magnet:?xt=urn:btih:' + "c" * 40 + '&dn=URI+Name">dl</a></div>'
        )
        [m] = mg.extract(html)
        self.assertEqual(m.name, "URI Name")
        self.assertEqual(m.name_source, "dn")
        self.assertEqual(mg.human_size(m.size), "1.0 GiB")

    def test_xl_in_the_uri_beats_the_page(self):
        html = (
            '<div><span>7.0 GB</span>'
            '<a href="magnet:?xt=urn:btih:' + "d" * 40 + '&xl=12345">dl</a></div>'
        )
        [m] = mg.extract(html)
        self.assertEqual(m.size, 12345)
