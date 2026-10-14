#!/usr/bin/env python3
"""Tests for the GUI backend. Run with:  python3 -m unittest test_magnet_excavator_gui -v"""

from __future__ import annotations

import base64
import collections
import http.server
import json
import os
import pathlib
import re
import tempfile
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import magnet_excavator as mx  # noqa: E402
import magnet_excavator_gui as gui  # noqa: E402

FIXTURE = os.path.join(HERE, "examples", "raw_dump.txt")


def upload(path: str = FIXTURE) -> dict:
    with open(path, "rb") as fh:
        return {"name": os.path.basename(path), "b64": base64.b64encode(fh.read()).decode()}


class TestProcess(unittest.TestCase):
    def test_upload_matches_the_cli(self):
        """The GUI must not disagree with the CLI about what is in the file."""
        res = gui.process([upload()], [], {})
        with open(FIXTURE, encoding="utf-8", errors="replace") as fh:
            cli = mx.extract(fh.read())
        self.assertEqual(res["count"], len(cli))
        self.assertEqual(
            {m["infohash"] for m in res["magnets"]}, {m.infohash for m in cli}
        )
        self.assertEqual(res["raw"], 11)
        self.assertEqual(res["sized"], 3)
        self.assertEqual(res["total_text"], mx.human_size(7872708607))

    def test_disk_path_matches_upload(self):
        up = gui.process([upload()], [], {})
        disk = gui.process([], [FIXTURE], {})
        self.assertEqual(up["count"], disk["count"])
        self.assertEqual(up["total_bytes"], disk["total_bytes"])

    def test_hints_option_keeps_trackers_without_the_name(self):
        res = gui.process([upload()], [], {"hints": True})
        self.assertTrue(res["magnets"])
        for m in res["magnets"]:
            self.assertNotIn("dn=", m["magnet"])
        # the fixture's links carry trackers, so hints must keep them
        self.assertTrue(any("tr=" in m["magnet"] for m in res["magnets"]))
        # names and sizes are still reported even though dn is gone from the link
        self.assertTrue(any(m["name"] for m in res["magnets"]))

    def test_bare_wins_over_hints(self):
        res = gui.process([upload()], [], {"bare": True, "hints": True})
        for m in res["magnets"]:
            self.assertNotIn("&", m["magnet"])

    def test_every_record_carries_all_three_variants(self):
        """The front end builds bare/hints copies locally, so it needs them."""
        res = gui.process([upload()], [], {})
        for m in res["magnets"]:
            self.assertNotIn("&", m["magnet_bare"])
            self.assertNotIn("dn=", m["magnet_hints"])
            self.assertIn("xt=", m["magnet_hints"])

    def test_bare_option_strips_parameters(self):
        res = gui.process([upload()], [], {"bare": True})
        for m in res["magnets"]:
            self.assertRegex(m["magnet"], r"^magnet:\?xt=urn:bt(ih|mh):")
            self.assertNotIn("&", m["magnet"])
            # metadata is still reported even though the link is bare
        self.assertTrue(any(m["name"] for m in res["magnets"]))

    def test_strip_trackers_keeps_name(self):
        """Pick a magnet whose name came from dn=; a scraped name has no dn to keep.

        Scraped names now survive dedupe, so "first magnet with a name" is no
        longer necessarily one that carries dn= in its URI.
        """
        res = gui.process([upload()], [], {"strip_trackers": True})
        from_dn = [m for m in res["magnets"] if m["name_source"] == "dn"]
        self.assertTrue(from_dn)
        self.assertIn("dn=", from_dn[0]["magnet"])
        self.assertNotIn("tr=", from_dn[0]["magnet"])
        # and a scraped name still shows in the table even though the URI has no dn
        scraped = [m for m in res["magnets"] if m["name_source"] == "page"]
        self.assertTrue(scraped)
        self.assertTrue(scraped[0]["name"])
        self.assertNotIn("dn=", scraped[0]["magnet"])

    def test_no_dedupe_keeps_duplicates(self):
        deduped = gui.process([upload()], [], {})
        raw = gui.process([upload()], [], {"no_dedupe": True})
        self.assertEqual(raw["count"], raw["raw"])
        self.assertGreater(raw["count"], deduped["count"])

    def test_name_filter(self):
        res = gui.process([upload()], [], {"filter": "ubuntu|fedora"})
        self.assertEqual(res["count"], 2)
        self.assertTrue(all(m["name"] for m in res["magnets"]))

    def test_size_filter(self):
        res = gui.process([upload()], [], {"min_size": "1GB"})
        self.assertEqual(res["count"], 2)

    def test_bad_base64_is_reported_not_fatal(self):
        res = gui.process([{"name": "broken.txt", "b64": "!!!not base64!!!"}], [], {})
        self.assertEqual(res["count"], 0)
        self.assertTrue(any("could not decode" in e for e in res["errors"]))

    def test_missing_path_is_reported(self):
        res = gui.process([], ["/nonexistent/nope.html"], {})
        self.assertEqual(res["count"], 0)
        self.assertTrue(res["errors"])

    def test_invalid_filter_regex_is_reported(self):
        res = gui.process([upload()], [], {"filter": "["})
        self.assertTrue(any("invalid filter regex" in e for e in res["errors"]))

    def test_multiple_sources_are_separate(self):
        res = gui.process([upload(), upload()], [], {})
        self.assertEqual(len(res["sources"]), 2)
        # same file twice still dedupes to one set of magnets
        self.assertEqual(res["count"], 9)


class TestHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), gui.Handler)
        cls.port = cls.server.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=10) as r:
            return r.status, r.read()

    def get_json(self, path):
        """GET that survives a 4xx, since urlopen raises on those."""
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def wait_job(self, job_id, timeout=15.0):
        """Poll /api/add/status the way the page does."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            _status, body = self.get_json(f"/api/add/status?id={job_id}")
            if body.get("done"):
                return body
            time.sleep(0.02)
        raise AssertionError(f"job {job_id} did not finish within {timeout}s")

    def post(self, path, payload):
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_index_page_is_served(self):
        status, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"<title>Magnet Excavator</title>", body)
        self.assertIn(b"id=\"drop\"", body)

    def test_healthz(self):
        status, body = self.get("/healthz")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["ok"])

    def test_unknown_path_404s(self):
        status, body = self.post("/api/nope", {})
        self.assertEqual(status, 404)
        self.assertIn("error", body)

    def test_extract_endpoint(self):
        status, body = self.post("/api/extract", {"files": [upload()], "paths": [], "options": {}})
        self.assertEqual(status, 200)
        self.assertEqual(body["count"], 9)

    def test_extract_with_path_endpoint(self):
        status, body = self.post("/api/extract", {"files": [], "paths": [FIXTURE], "options": {}})
        self.assertEqual(status, 200)
        self.assertEqual(body["count"], 9)

    def test_add_rejects_empty_list(self):
        status, body = self.post("/api/add", {"config": {}, "magnets": []})
        self.assertEqual(status, 400)
        self.assertIn("no magnets", body["error"])

    def test_add_reports_unreachable_client(self):
        """/api/add now returns a job handle at once, so the failure surfaces
        when the job is polled rather than in the POST status."""
        status, body = self.post(
            "/api/add",
            {"config": {"host": "http://127.0.0.1:9", "timeout": 2},
             "magnets": ["magnet:?xt=urn:btih:" + "a" * 40]},
        )
        self.assertEqual(status, 200)
        job = self.wait_job(body["id"])
        self.assertTrue(job["done"])
        self.assertIn("qBittorrent", job["error"])
        self.assertEqual(job["sent"], 0)

    def test_name_source_is_reported(self):
        """The page marks scraped names as guesses, so name_source must ship."""
        _status, body = self.post("/api/extract", {"files": [upload()], "paths": [], "options": {}})
        for m in body["magnets"]:
            self.assertIn(m["name_source"], ("dn", "page", ""))
        self.assertTrue(any(m["name_source"] == "dn" for m in body["magnets"]))

    def test_rejected_count_is_reported(self):
        """Malformed magnets are counted, not silently dropped."""
        blob = ("magnet:?xt=urn:btih:" + "a" * 40 + "\n"
                "magnet:?xt=urn:btih:tooshort\n"
                "magnet:?dn=nohash\n").encode()
        up = {"name": "edited.txt", "b64": base64.b64encode(blob).decode()}
        _status, body = self.post("/api/extract", {"files": [up], "paths": [], "options": {}})
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["rejected"], 2)

    def test_duplicate_count_is_reported(self):
        _status, body = self.post("/api/extract", {"files": [upload()], "paths": [], "options": {}})
        self.assertEqual(body["dupes"], body["raw"] - body["count"])
        self.assertEqual(body["dupes"], 2)  # the fixture has 11 raw, 9 unique

    def test_test_endpoint_fails_for_an_unreachable_host(self):
        """Test connection must actually reach the network. It used to post an
        empty magnet list, which is rejected before any request, so it reported
        success for a host that was not even there."""
        status, body = self.post(
            "/api/test", {"config": {"host": "http://127.0.0.1:9", "timeout": 2}}
        )
        self.assertEqual(status, 502)
        self.assertIn("qBittorrent", body["error"])

    def test_add_status_for_unknown_job_is_404(self):
        status, body = self.get_json("/api/add/status?id=nope")
        self.assertEqual(status, 404)
        self.assertIn("unknown job", body["error"])

    def test_malformed_json_is_400(self):
        req = urllib.request.Request(
            self.base + "/api/extract", data=b"{not json",
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            self.fail("expected 400")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)


class TestAddFlow(unittest.TestCase):
    """The GUI's add path must send what the CLI sends."""

    def setUp(self):
        self.got = {"urls": [], "cookie": None}
        outer = self

        class Mock(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                if self.path == "/api/v2/auth/login":
                    self.send_response(200)
                    self.send_header("Set-Cookie", "SID=mock; path=/")
                    self.end_headers()
                    self.wfile.write(b"Ok.")
                else:
                    outer.got["cookie"] = self.headers.get("Cookie")
                    import re as _re
                    m = _re.search(rb'name="urls"\r\n\r\n(.*?)\r\n------', body, _re.S)
                    outer.got["urls"] += m.group(1).decode().split("\n") if m else []
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Ok.")

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Mock)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    @staticmethod
    def wait(job, timeout=10.0):
        """Block until a job finishes; a GUI add is a background job now."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            snap = gui.job_snapshot(gui.JOBS[job["id"]])
            if snap["done"]:
                return snap
            time.sleep(0.01)
        raise AssertionError(f"job did not finish: {gui.job_snapshot(gui.JOBS[job['id']])}")

    def test_add_batches_and_carries_session(self):
        res = gui.process([upload()], [], {"bare": True})
        magnets = [m["magnet"] for m in res["magnets"]]
        job = gui.start_add(
            {"host": f"http://127.0.0.1:{self.port}", "username": "u",
             "password": "p", "batch": 4, "category": "c"},
            magnets,
        )
        out = self.wait(job)
        self.assertEqual(out["sent"], 9)
        self.assertEqual(out["error"], "")
        self.assertEqual(self.got["urls"], magnets)
        self.assertEqual(self.got["cookie"], "SID=mock")


class TestFullParityWithCLI(unittest.TestCase):
    """Everything the CLI can do, the page can do too."""

    HASH = "c" * 40

    def page(self, hashes, size="2.0 GB"):
        return "<table>" + "".join(
            f'<tr><td>Item</td><td>{size}</td>'
            f'<td><a href="magnet:?xt=urn:btih:{h}">dl</a></td></tr>'
            for h in hashes) + "</table>"

    def up(self, name, text):
        return {"name": name, "b64": base64.b64encode(text.encode()).decode()}

    def test_url_input_is_fetched_and_scanned(self):
        body = self.page([self.HASH]).encode()

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            res = gui.process([], [], {"urls": [f"http://127.0.0.1:{port}/page"]})
        finally:
            srv.shutdown(); srv.server_close()
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["magnets"][0]["infohash"], self.HASH)
        self.assertEqual(res["magnets"][0]["size_text"], "2.0 GiB")

    def test_a_non_http_url_is_rejected_not_crashed(self):
        res = gui.process([], [], {"urls": ["not-a-url", ""]})
        self.assertEqual(res["count"], 0)
        self.assertTrue(any("not an http(s) URL" in e for e in res["errors"]))

    def test_pick_richest_keeps_the_fuller_link(self):
        thin = f'<a href="magnet:?xt=urn:btih:{self.HASH}&dn=Thin">y</a>'
        rich = f'<a href="magnet:?xt=urn:btih:{self.HASH}&dn=Full&tr=udp%3A%2F%2Ft">x</a>'
        files = [self.up("thin.html", thin), self.up("rich.html", rich)]
        self.assertEqual(gui.process(files, [], {"pick": "richest"})["magnets"][0]["name"], "Full")
        self.assertEqual(gui.process(files, [], {"pick": "first"})["magnets"][0]["name"], "Thin")

    def test_cross_source_overlap_is_reported(self):
        a = self.page(["1" * 40, "2" * 40, "3" * 40])
        b = self.page(["3" * 40, "4" * 40])
        res = gui.process([self.up("a.html", a), self.up("b.html", b)], [], {})
        cross = res["cross_source"]
        self.assertEqual(cross["unique"], 4)
        self.assertEqual(cross["shared"], 1)
        self.assertEqual({e["name"]: e["count"] for e in cross["exclusive"]},
                         {"a.html": 2, "b.html": 1})

    def test_no_cross_source_block_for_one_source(self):
        res = gui.process([self.up("a.html", self.page(["1" * 40]))], [], {})
        self.assertIsNone(res["cross_source"])

    def test_max_file_size_skips_big_files(self):
        d = tempfile.mkdtemp()
        big = os.path.join(d, "big.html")
        text = self.page([self.HASH])
        with open(big, "w", encoding="utf-8") as fh:
            fh.write(text)
        size = os.path.getsize(big)
        under = f"{size - 1}B"   # cap below the file -> skipped
        over = f"{size + 1}B"    # cap above it -> scanned
        self.assertEqual(gui.process([], [d], {})["count"], 1)
        self.assertEqual(gui.process([], [d], {"max_file_size": under})["count"], 0,
                         f"{size}-byte file should have been skipped by a {under} cap")
        self.assertEqual(gui.process([], [d], {"max_file_size": over})["count"], 1)

    def test_records_carry_everything_the_json_export_needs(self):
        """The page builds magnets.json itself, so each record must be complete."""
        res = gui.process([self.up("a.html", self.page([self.HASH]))], [], {})
        m = res["magnets"][0]
        for key in ("infohash", "version", "name", "name_source", "size",
                    "size_text", "trackers", "sources",
                    "magnet", "magnet_hints", "magnet_bare"):
            self.assertIn(key, m, f"missing {key}")


class TestPageConsistency(unittest.TestCase):
    """Static checks on gui.html, so markup edits cannot silently break wiring.

    These exist because the table grew a "Name from" column and the
    "N more rows" note kept colspan="5", leaving it one column short. Nothing
    at runtime would have complained.
    """

    def setUp(self):
        self.html = pathlib.Path(gui.PAGE).read_text(encoding="utf-8")

    def test_row_template_has_one_cell_per_header(self):
        head = re.search(r"<thead><tr>(.*?)</tr></thead>", self.html, re.S).group(1)
        headers = re.findall(r"<th[^>]*>", head)
        body = self.html[self.html.index("const rows = res.magnets.slice"):]
        row = body[: body.index("</tr>`;")]
        cells = re.findall(r"<td[^>]*>", row)
        self.assertEqual(len(headers), len(cells),
                         f"{len(headers)} headers but {len(cells)} cells per row")
        self.assertEqual(len(headers), 6)

    def test_every_id_referenced_by_js_exists(self):
        ids = set(re.findall(r'\bid="([^"]+)"', self.html))
        refs = set(re.findall(r'\$\("([^"]+)"\)', self.html))
        self.assertFalse(refs - ids, f"JS references missing ids: {sorted(refs - ids)}")

    def test_no_duplicate_ids(self):
        seen = collections.Counter(re.findall(r'\bid="([^"]+)"', self.html))
        self.assertEqual([k for k, v in seen.items() if v > 1], [])


class TestQueueAwareAdd(unittest.TestCase):
    """max_active must pace the feed, exactly as the CLI's --max-active does.

    Dumping thousands of magnets in at once is the documented failure mode:
    each one sits at "Downloading metadata" and counts against the client's
    active download limit, so the queue starves and the GUI locks up.
    """

    def setUp(self):
        self.state = {"added": 0, "drained": 0, "add_sizes": []}
        outer = self

        class Mock(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                if self.path == "/api/v2/auth/login":
                    self.send_response(200)
                    self.send_header("Set-Cookie", "SID=mock; path=/")
                    self.end_headers()
                    self.wfile.write(b"Ok.")
                    return
                n = len(re.search(rb'name="urls"\r\n\r\n(.*?)\r\n------', body, re.S)
                        .group(1).decode().split("\n"))
                outer.state["added"] += n
                outer.state["add_sizes"].append(n)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Ok.")

            def do_GET(self):
                # every added torrent becomes active, and one drains per poll,
                # so the feeder has to keep waiting for headroom
                outer.state["drained"] += 1
                active = max(0, outer.state["added"] - outer.state["drained"])
                payload = json.dumps([{"hash": str(i)} for i in range(active)]).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Mock)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_feed_respects_max_active_headroom(self):
        magnets = ["magnet:?xt=urn:btih:%040x" % i for i in range(9)]
        job = gui.start_add(
            {"host": f"http://127.0.0.1:{self.port}", "max_active": 5,
             "poll_interval": 0.01, "batch": 0},
            magnets,
        )
        self.assertTrue(job["queue_aware"])
        deadline = time.time() + 20
        while time.time() < deadline:
            snap = gui.job_snapshot(gui.JOBS[job["id"]])
            if snap["done"]:
                break
            time.sleep(0.01)
        self.assertTrue(snap["done"], f"job never finished: {snap}")
        self.assertEqual(snap["error"], "")
        self.assertEqual(snap["sent"], 9)
        self.assertEqual(sum(self.state["add_sizes"]), 9)
        # it must have paced, not dumped all nine in one request
        self.assertGreater(len(self.state["add_sizes"]), 1, self.state["add_sizes"])
        self.assertLessEqual(max(self.state["add_sizes"]), 5, self.state["add_sizes"])

    def test_without_max_active_it_still_sends_everything(self):
        magnets = ["magnet:?xt=urn:btih:%040x" % i for i in range(9)]
        job = gui.start_add(
            {"host": f"http://127.0.0.1:{self.port}", "batch": 4}, magnets
        )
        self.assertFalse(job["queue_aware"])
        deadline = time.time() + 20
        while time.time() < deadline:
            snap = gui.job_snapshot(gui.JOBS[job["id"]])
            if snap["done"]:
                break
            time.sleep(0.01)
        self.assertEqual(snap["error"], "")
        self.assertEqual(snap["sent"], 9)
        self.assertEqual(self.state["add_sizes"], [4, 4, 1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
