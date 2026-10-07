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
import urllib.error
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import magnet_excavator as mx  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "gui.html")
MAX_UPLOAD_BYTES = 64 * 1024 * 1024


def record_to_dict(m: mx.Magnet, bare: bool, strip: bool) -> dict:
    if bare:
        uri = m.bare_uri
    elif strip:
        uri = m.clean_uri
    else:
        uri = m.uri
    return {
        "infohash": m.infohash,
        "version": m.version,
        "name": m.name,
        "size": m.size,
        "size_text": mx.human_size(m.size),
        "trackers": len(m.trackers),
        "sources": [os.path.basename(s) for s in m.sources],
        "magnet": uri,
    }


def process(files: list[dict], paths: list[str], options: dict) -> dict:
    """Run the same pipeline the CLI runs, over uploaded bytes and/or disk paths."""
    bare = bool(options.get("bare"))
    strip = bool(options.get("strip_trackers"))
    dedupe = not options.get("no_dedupe")

    index: dict[str, mx.Magnet] = {}
    order: list[str] = []
    flat: list[mx.Magnet] = []
    sources: list[dict] = []
    errors: list[str] = []

    def absorb(chunks, source: str) -> None:
        entry = {"name": os.path.basename(source) or source, "raw": 0, "unique": 0}
        local: dict[str, mx.Magnet] = {}
        local_order: list[str] = []
        for m in mx.iter_matches_with_size(chunks, source):
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
                if len(m.uri) > len(known.uri):
                    index[m.infohash] = mx.rebuild_with_sources(m, known.sources)
        entry["unique"] = len(local)
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

    for path in paths:
        for expanded in mx.collect_paths([path], only_ext):
            if expanded == "-":
                continue
            try:
                absorb(mx.iter_text_chunks(expanded), expanded)
            except OSError as exc:
                errors.append(f"{expanded}: {exc}")

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

    total = sum(m.size for m in magnets if m.size is not None)
    return {
        "magnets": [record_to_dict(m, bare, strip) for m in magnets],
        "sources": sources,
        "count": len(magnets),
        "raw": sum(s["raw"] for s in sources),
        "sized": sum(1 for m in magnets if m.size is not None),
        "total_bytes": total,
        "total_text": mx.human_size(total) if total else None,
        "errors": errors,
    }


def add_to_qbittorrent(cfg: dict, magnets: list[str]) -> dict:
    client = mx.QBittorrent(
        cfg.get("host", "http://localhost:8080"),
        cfg.get("username", ""),
        cfg.get("password", ""),
        float(cfg.get("timeout", 20) or 20),
    )
    batch = int(cfg.get("batch", 0) or 0)
    size = batch if batch > 0 else len(magnets)
    sent = 0
    for start in range(0, len(magnets), size):
        chunk = magnets[start : start + size]
        client.add(
            chunk,
            cfg.get("savepath", ""),
            cfg.get("category", ""),
            bool(cfg.get("paused")),
        )
        sent += len(chunk)
    return {"sent": sent}


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
                result = add_to_qbittorrent(payload.get("config", {}), magnets)
                self._json(200, result)
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
