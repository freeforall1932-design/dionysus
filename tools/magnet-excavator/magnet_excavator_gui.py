#!/usr/bin/env python3
"""Magnet Excavator — local GUI.

A single-file local web app: drag files onto the page, get a clean magnet list,
push it to qBittorrent. Standard library only, same as the CLI.

    python3 magnet_excavator_gui.py              # http://127.0.0.1:8765
    python3 magnet_excavator_gui.py --port 9000
    python3 magnet_excavator_gui.py --host 0.0.0.0   # reachable from another machine

It imports magnet_excavator.py, so the CLI and the GUI cannot disagree about
what a magnet is.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import magnet_excavator as mx  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "gui.html")
MAX_UPLOAD_BYTES = 64 * 1024 * 1024


def record_to_dict(m: mx.Magnet, bare: bool, strip: bool, hints: bool = False) -> dict:
    if bare:
        uri = m.bare_uri
    elif hints:
        uri = m.hints_uri
    elif strip:
        uri = m.clean_uri
    else:
        uri = m.uri
    return {
        "infohash": m.infohash,
        "version": m.version,
        "name": m.name,
        # "dn" = the URI carried it; "page" = scraped from the markup, so it is a
        # best guess. The page shows the difference because a wrong name is the
        # thing worth doubting.
        "name_source": m.name_source,
        "size": m.size,
        "size_text": mx.human_size(m.size),
        "trackers": len(m.trackers),
        "sources": [os.path.basename(s) for s in m.sources],
        "magnet": uri,
        # The front end offers bare/hints/full copies without a round trip, so
        # it needs the variants rather than having to rebuild them in JS.
        "magnet_hints": m.hints_uri,
        "magnet_bare": m.bare_uri,
    }


def process(files: list[dict], paths: list[str], options: dict) -> dict:
    """Run the same pipeline the CLI runs, over uploaded bytes and/or disk paths."""
    bare = bool(options.get("bare"))
    hints = bool(options.get("hints"))
    strip = bool(options.get("strip_trackers"))
    dedupe = not options.get("no_dedupe")
    # "richest" keeps whichever copy of a hash carries the most information
    # (usually the fullest tracker list); "first" keeps the earliest seen.
    pick = options.get("pick") or "richest"

    index: dict[str, mx.Magnet] = {}
    order: list[str] = []
    flat: list[mx.Magnet] = []
    sources: list[dict] = []
    errors: list[str] = []

    def absorb(chunks, source: str) -> None:
        entry = {"name": os.path.basename(source) or source, "raw": 0, "unique": 0,
                 "rejected": 0}
        local: dict[str, mx.Magnet] = {}
        local_order: list[str] = []
        counters: dict[str, int] = {}
        for m in mx.iter_matches_with_size(chunks, source, counters=counters):
            entry["raw"] += 1
            if not dedupe:
                flat.append(m)
            prev = local.get(m.infohash)
            if prev is None:
                local[m.infohash] = m
                local_order.append(m.infohash)
            elif len(m.uri) > len(prev.uri):
                local[m.infohash] = m
            known = index.get(m.infohash)
            if known is None:
                index[m.infohash] = mx.rebuild_with_sources(m, [source])
                order.append(m.infohash)
            else:
                if source not in known.sources:
                    known.sources.append(source)
                if known.size is None and m.size is not None:
                    known.size = m.size
                if pick == "richest" and len(m.uri) > len(known.uri):
                    index[m.infohash] = mx.rebuild_with_sources(m, known.sources)
        entry["unique"] = len(local)
        entry["hashes"] = list(local_order)
        entry["rejected"] = counters.get("rejected", 0)
        entry["sized"] = sum(1 for m in local.values() if m.size is not None)
        entry["bytes"] = sum(m.size for m in local.values() if m.size is not None)
        sources.append(entry)

    for f in files:
        name = f.get("name") or "<upload>"
        try:
            blob = base64.b64decode(f.get("b64", ""), validate=False)
        except Exception:  # noqa: BLE001 - malformed upload should not kill the run
            errors.append(f"{name}: could not decode upload")
            continue
        if len(blob) > MAX_UPLOAD_BYTES:
            errors.append(f"{name}: larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MiB limit")
            continue
        absorb([mx.decode_bytes(blob)], name)

    only_ext = None
    ext = options.get("ext")
    if ext:
        only_ext = {("." + e.strip().lstrip(".").lower()) for e in ext.split(",") if e.strip()}

    cap = options.get("max_file_size")
    cap = mx.parse_size(str(cap)) if cap else None

    for path in paths:
        for expanded in mx.collect_paths([path], only_ext, cap):
            if expanded == "-":
                continue
            try:
                absorb(mx.iter_text_chunks(expanded), expanded)
            except OSError as exc:
                errors.append(f"{expanded}: {exc}")

    for url in options.get("urls") or []:
        url = (url or "").strip()
        if not url:
            continue
        if not re.match(r"(?i)^https?://", url):
            errors.append(f"{url}: not an http(s) URL")
            continue
        try:
            absorb(mx.fetch_chunks(url, float(options.get("timeout", 20) or 20)), url)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            errors.append(f"{url}: {exc}")

    magnets = flat if not dedupe else [index[h] for h in order]

    name_filter = options.get("filter")
    if name_filter:
        try:
            rx = re.compile(name_filter, re.I)
            magnets = [m for m in magnets if rx.search(m.name or m.uri)]
        except re.error as exc:
            errors.append(f"invalid filter regex: {exc}")

    lo = mx.parse_size(options["min_size"]) if options.get("min_size") else None
    hi = mx.parse_size(options["max_size"]) if options.get("max_size") else None
    if lo is not None or hi is not None:
        def sized(m: mx.Magnet) -> bool:
            if m.size is None:
                return bool(options.get("keep_unknown_size"))
            return (lo is None or m.size >= lo) and (hi is None or m.size <= hi)

        magnets = [m for m in magnets if sized(m)]

    # Tracker hints are added last, after filtering, so nothing is spent on
    # magnets the user has already filtered out.
    augmented = 0
    t_path = (options.get("trackers_path") or "").strip()
    t_url = (options.get("trackers_url") or "").strip()
    if t_path or t_url:
        try:
            cap = int(options.get("max_trackers") or 5)
        except (TypeError, ValueError):
            cap = 5
        try:
            trackers = mx.load_trackers(t_path or None, t_url or None)
            augmented = mx.augment_trackers(magnets, trackers, cap)
        except Exception as exc:  # noqa: BLE001 - a bad list must not lose the scan
            errors.append(f"could not load tracker list: {exc}")

    # The CLI's --summary reports how much the sources overlap and what is
    # exclusive to each. The page showed neither, so multi-source runs could not
    # be audited without dropping back to the terminal.
    seen_in: dict[str, int] = {}
    if len(sources) > 1:
        for src in sources:
            for h in src["hashes"]:
                seen_in[h] = seen_in.get(h, 0) + 1
    cross = None
    if len(sources) > 1:
        cross = {
            "unique": len(magnets),
            "shared": sum(1 for n in seen_in.values() if n > 1),
            "exclusive": [
                {"name": src["name"],
                 "count": sum(1 for h in src["hashes"] if seen_in.get(h) == 1)}
                for src in sources
            ],
        }

    total = sum(m.size for m in magnets if m.size is not None)
    return {
        "augmented": augmented,
        "magnets": [record_to_dict(m, bare, strip, hints) for m in magnets],
        "sources": sources,
        "count": len(magnets),
        "raw": sum(s["raw"] for s in sources),
        "dupes": sum(s["raw"] for s in sources) - len(magnets),
        # strings that looked like magnets but did not validate - the signal
        # that a hand-edited list lost a line to a typo
        "rejected": sum(s.get("rejected", 0) for s in sources),
        "cross_source": cross,
        "sized": sum(1 for m in magnets if m.size is not None),
        "total_bytes": total,
        "total_text": mx.human_size(total) if total else None,
        "errors": errors,
    }


# Add jobs run in the background so a queue-aware feed - which can wait minutes
# or hours for headroom - does not hold an HTTP request open. The page polls.
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


def _job_update(job: dict, **fields) -> None:
    with JOBS_LOCK:
        job.update(fields)


def job_snapshot(job: dict) -> dict:
    with JOBS_LOCK:
        return dict(job)


def _run_add(job: dict, cfg: dict, magnets: list[str]) -> None:
    """Feed magnets into qBittorrent, optionally queue-aware.

    This mirrors the CLI's --max-active loop exactly. Magnets are cheap to add
    but expensive to resolve: each sits at "Downloading metadata" until a peer
    answers, and qBittorrent counts those towards its active download limit.
    Dumping thousands in at once locks the GUI and starves the queue, so when a
    cap is set we add only into the available headroom and wait for the rest.
    """
    max_active = int(cfg.get("max_active", 0) or 0)
    poll = float(cfg.get("poll_interval", 30) or 30)
    delay = float(cfg.get("batch_delay", 0) or 0)
    batch = int(cfg.get("batch", 0) or 0)
    savepath = cfg.get("savepath", "")
    category = cfg.get("category", "")
    paused = bool(cfg.get("paused"))
    queue = list(magnets)
    sent = 0

    try:
        client = mx.QBittorrent(
            cfg.get("host", "http://localhost:8080"),
            cfg.get("username", ""),
            cfg.get("password", ""),
            float(cfg.get("timeout", 20) or 20),
        )
        if max_active > 0:
            while queue:
                active = client.active_count("downloading")
                headroom = max_active - active
                if headroom <= 0:
                    _job_update(job, waiting=True, active=active, queued=len(queue))
                    time.sleep(poll)
                    continue
                take = min(headroom, batch if batch > 0 else headroom)
                chunk, queue = queue[:take], queue[take:]
                client.add(chunk, savepath, category, paused)
                sent += len(chunk)
                _job_update(job, sent=sent, queued=len(queue), active=active, waiting=False)
                if delay and queue:
                    time.sleep(delay)
        else:
            size = batch if batch > 0 else len(queue)
            while queue:
                chunk, queue = queue[:size], queue[size:]
                client.add(chunk, savepath, category, paused)
                sent += len(chunk)
                _job_update(job, sent=sent, queued=len(queue))
                if delay and queue:
                    time.sleep(delay)
        _job_update(job, done=True, sent=sent, queued=0, waiting=False)
    except (urllib.error.URLError, OSError, RuntimeError) as exc:
        _job_update(job, done=True, sent=sent, error=f"could not reach qBittorrent: {exc}")
    except Exception as exc:  # noqa: BLE001 - a job must never die silently
        _job_update(job, done=True, sent=sent, error=f"{type(exc).__name__}: {exc}")


def test_connection(cfg: dict) -> dict:
    """Actually reach qBittorrent: log in, read the version, count the queue.

    The page used to "test" by posting an empty magnet list, which the API
    rejects before any network call - so it always reported success, even for a
    wrong host or bad credentials. Reporting queue depth here also tells the
    user what max_active has to work with before they commit a big batch.
    """
    client = mx.QBittorrent(
        cfg.get("host", "http://localhost:8080"),
        cfg.get("username", ""),
        cfg.get("password", ""),
        float(cfg.get("timeout", 20) or 20),
    )
    out = {"ok": True, "host": client.host, "logged_in": bool(client.sid)}
    # This call is the actual probe. A network failure must propagate so the
    # handler can answer 502 - swallowing it here is what made the old "test"
    # report success for a host that was not there. Only a non-200 from a host
    # that *did* answer is treated as merely missing the endpoint.
    try:
        version = client.get_json("/api/v2/app/version")
        # a real client answers with a JSON string; anything else means we hit
        # the wrong endpoint or the wrong port, so do not render it as a version
        out["version"] = version if isinstance(version, str) else None
    except (RuntimeError, ValueError):
        out["version"] = None  # reachable, but no version endpoint
    try:
        out["downloading"] = client.active_count("downloading")
    except (RuntimeError, ValueError, urllib.error.URLError, OSError):
        out["downloading"] = None
    return out


def start_add(cfg: dict, magnets: list[str]) -> dict:
    """Kick off an add job and return its handle immediately."""
    job = {
        "id": uuid.uuid4().hex[:12],
        "total": len(magnets),
        "sent": 0,
        "queued": len(magnets),
        "active": None,
        "waiting": False,
        "done": False,
        "error": "",
        "queue_aware": int(cfg.get("max_active", 0) or 0) > 0,
    }
    with JOBS_LOCK:
        JOBS[job["id"]] = job
    threading.Thread(target=_run_add, args=(job, cfg, magnets), daemon=True).start()
    return job_snapshot(job)


class Handler(BaseHTTPRequestHandler):
    server_version = "MagnetExcavatorGUI/1.0"

    def log_message(self, fmt, *args):  # quieter console
        sys.stderr.write("[gui] " + (fmt % args) + "\n")

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload).encode(), "application/json")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_UPLOAD_BYTES + (1 << 20):
            raise ValueError("empty or oversized request")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                with open(PAGE, "rb") as fh:
                    self._send(200, fh.read(), "text/html; charset=utf-8")
            except OSError as exc:
                self._send(500, f"gui.html missing: {exc}".encode(), "text/plain")
        elif urllib.parse.urlparse(self.path).path == "/api/add/status":
            job_id = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("id", [""])[0]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                snapshot = dict(job) if job else None
            if snapshot is None:
                self._json(404, {"error": "unknown job"})
            else:
                self._json(200, snapshot)
        elif self.path == "/healthz":
            self._json(200, {"ok": True, "count": 0})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        try:
            payload = self._read_json()
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": f"bad request: {exc}"})
            return

        try:
            if self.path == "/api/extract":
                self._json(
                    200,
                    process(
                        payload.get("files", []),
                        payload.get("paths", []),
                        payload.get("options", {}),
                    ),
                )
            elif self.path == "/api/add":
                magnets = payload.get("magnets", [])
                if not magnets:
                    self._json(400, {"error": "no magnets to add"})
                    return
                # Returns immediately; the page polls /api/add/status. A
                # queue-aware feed can wait a long time for headroom and must
                # not hold the request open.
                self._json(200, start_add(payload.get("config", {}), magnets))
            elif self.path == "/api/test":
                self._json(200, test_connection(payload.get("config", {})))
            else:
                self._json(404, {"error": "not found"})
        except urllib.error.URLError as exc:
            self._json(502, {"error": f"could not reach qBittorrent: {exc}"})
        except RuntimeError as exc:
            self._json(502, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001 - surface anything else to the UI
            self._json(500, {"error": f"{type(exc).__name__}: {exc}"})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Magnet Excavator GUI (local web app)")
    ap.add_argument("--host", default="127.0.0.1", help="bind address (default 127.0.0.1)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true", help="do not open a browser")
    args = ap.parse_args(argv)

    if not os.path.exists(PAGE):
        ap.error(f"cannot find {PAGE}")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{'127.0.0.1' if args.host in ('0.0.0.0', '::') else args.host}:{args.port}"
    print(f"Magnet Excavator GUI -> {url}", file=sys.stderr)
    print("Ctrl+C to stop", file=sys.stderr)

    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped", file=sys.stderr)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
