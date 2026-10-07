#!/usr/bin/env python3
"""
magnet-grab — pull every magnet link out of saved HTML and hand it to a torrent client.

Stdlib only. No BeautifulSoup, no requests.

    ./magnet_grab.py page.html                 # table of what was found
    ./magnet_grab.py page.html --plain         # one magnet per line -> paste into qBittorrent
    ./magnet_grab.py dir/ *.html --plain > m.txt
    cat page.html | ./magnet_grab.py -
    ./magnet_grab.py page.html --add           # POST straight to the qBittorrent WebUI
    ./magnet_grab.py --url https://site/list   # fetch + extract in one go

Why it is not just `grep -o 'magnet:...'`:
  * saved HTML escapes `&` as `&amp;`, so a naive regex truncates at the first tracker
  * magnets live in href, in data-* attributes, and inside <script> string literals
  * the scheme may be uppercase, the hash may be v1 hex, v1 base32, or v2 multihash
  * the same torrent is usually listed several times and must be deduped by infohash
"""

from __future__ import annotations

import argparse
import gzip
import html
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

# A magnet URI is a scheme plus a query string. Everything up to whitespace or a
# quoting/delimiting character belongs to the URI. Backslash is excluded because
# magnets embedded in JS string literals are often followed by a closing quote
# that we want to leave behind.
MAGNET_RE = re.compile(r"(?i)\bmagnet:\?[^\s\"'<>\\]+")

# Accepted infohash encodings:
#   v1  40 hex chars, or 32 chars of base32
#   v2  "1220" prefix + 64 hex chars (sha256 multihash, urn:btmh)
BTIH_V1_HEX = re.compile(r"(?i)xt=urn:btih:([0-9a-f]{40})\b")
BTIH_V1_B32 = re.compile(r"(?i)xt=urn:btih:([a-z2-7]{32})\b")
BTMH_V2 = re.compile(r"(?i)xt=urn:btmh:1220([0-9a-f]{64})\b")
ANY_XT = re.compile(r"(?i)[?&]xt=")

TRAILING_JUNK = ".,;:!?)'\""


@dataclass
class Magnet:
    uri: str
    infohash: str
    version: int
    name: str = ""
    trackers: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    @property
    def clean_uri(self) -> str:
        """Magnet with the tracker list stripped off (xt + dn only)."""
        kept = []
        for part in self.uri.split("?", 1)[1].split("&"):
            if part.startswith("tr="):
                continue
            kept.append(part)
        return "magnet:?" + "&".join(kept)


def classify(uri: str) -> tuple[str, int] | None:
    """Return (infohash, bittorrent_version) or None if this is not a valid magnet."""
    if not ANY_XT.search(uri):
        return None
    for rx, version in ((BTIH_V1_HEX, 1), (BTIH_V1_B32, 1), (BTMH_V2, 2)):
        m = rx.search(uri)
        if m:
            return m.group(1).lower(), version
    return None


def normalize(raw: str) -> str:
    """Undo the escaping that HTML and JS string literals apply to a magnet URI."""
    uri = html.unescape(raw)
    # JSON/JS embedding: \u0026 is '&' and \/ is '/'
    uri = uri.replace("\\u0026", "&").replace("\\/", "/")
    # Strip punctuation that a sentence or an attribute may have left on the tail.
    while uri and uri[-1] in TRAILING_JUNK:
        uri = uri[:-1]
    return uri


def parse_query(uri: str) -> dict[str, list[str]]:
    query = uri.split("?", 1)[1] if "?" in uri else ""
    out: dict[str, list[str]] = {}
    for pair in query.split("&"):
        if not pair or "=" not in pair:
            continue
        key, _, value = pair.partition("=")
        out.setdefault(key.lower(), []).append(value)
    return out


def unquote_smart(value: str) -> str:
    """Percent-decode a magnet parameter, tolerating legacy non-UTF-8 escapes."""
    decoded = urllib.parse.unquote_plus(value, encoding="utf-8", errors="replace")
    if "\ufffd" not in decoded:
        return decoded
    # Older pages percent-encode in latin-1/cp1252 rather than UTF-8.
    try:
        fallback = urllib.parse.unquote_plus(value, encoding="cp1252", errors="strict")
    except (UnicodeDecodeError, ValueError):
        return decoded
    return fallback


def decode_name(values: list[str]) -> str:
    if not values:
        return ""
    return unquote_smart(values[0]).strip()


def build(uri: str, infohash: str, version: int) -> Magnet:
    params = parse_query(uri)
    return Magnet(
        uri=uri,
        infohash=infohash,
        version=version,
        name=decode_name(params.get("dn", [])),
        trackers=[unquote_smart(t) for t in params.get("tr", [])],
    )


def extract(text: str, source: str = "<input>", dedupe: bool = True) -> list[Magnet]:
    """Find every magnet URI in `text`.

    With dedupe=True (default) each infohash appears once, keeping the richest URI.
    With dedupe=False every occurrence is returned, in document order.
    """
    found: dict[str, Magnet] = {}
    order: list[str] = []
    all_matches: list[Magnet] = []

    for raw in MAGNET_RE.findall(text):
        uri = normalize(raw)
        info = classify(uri)
        if info is None:
            continue
        infohash, version = info
        magnet = build(uri, infohash, version)
        magnet.sources = [source]

        if not dedupe:
            all_matches.append(magnet)
            continue

        if infohash in found:
            existing = found[infohash]
            if source not in existing.sources:
                existing.sources.append(source)
            # Prefer the longest URI seen: it usually carries more trackers.
            # Rebuild so name/trackers reflect the URI we actually keep.
            if len(uri) > len(existing.uri):
                replacement = build(uri, infohash, version)
                replacement.sources = existing.sources
                found[infohash] = replacement
            continue

        found[infohash] = magnet
        order.append(infohash)

    return all_matches if not dedupe else [found[h] for h in order]


def read_file(path: str) -> str:
    with open(path, "rb") as fh:
        blob = fh.read()
    return decode_bytes(blob)


def decode_bytes(blob: bytes) -> str:
    """Decode saved-page bytes, honouring gzip and any <meta charset>."""
    if blob[:2] == b"\x1f\x8b":
        blob = gzip.decompress(blob)

    # Peek at a leading meta charset before committing to a decoder.
    head = blob[:4096].decode("ascii", "ignore").lower()
    m = re.search(r'charset=["\']?\s*([a-z0-9_\-]+)', head)
    if m:
        try:
            return blob.decode(m.group(1), "replace")
        except LookupError:
            pass
    for encoding in ("utf-8", "cp1252"):
        try:
            return blob.decode(encoding)
        except UnicodeDecodeError:
            continue
    return blob.decode("utf-8", "replace")


def fetch(url: str, timeout: float) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) magnet-grab",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        blob = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            blob = gzip.decompress(blob)
    return decode_bytes(blob)


def collect_paths(inputs: list[str]) -> list[str]:
    paths: list[str] = []
    for item in inputs:
        if item == "-":
            paths.append(item)
            continue
        if os.path.isdir(item):
            for root, _dirs, files in os.walk(item):
                for name in sorted(files):
                    low = name.lower()
                    if low.endswith((".html", ".htm", ".xhtml", ".mhtml", ".mht", ".html.gz")):
                        paths.append(os.path.join(root, name))
        else:
            paths.append(item)
    return paths


# ---------------------------------------------------------------- qBittorrent


def multipart(fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = "----magnetgrabboundary7d4a1b"
    buf = io.BytesIO()
    for key, value in fields.items():
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        buf.write(value.encode("utf-8"))
        buf.write(b"\r\n")
    buf.write(f"--{boundary}--\r\n".encode())
    return buf.getvalue(), f"multipart/form-data; boundary={boundary}"


class QBittorrent:
    """Minimal client for the qBittorrent WebUI API v2."""

    def __init__(self, host: str, username: str = "", password: str = "", timeout: float = 20.0):
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.sid = ""
        if username:
            self.login(username, password)

    def _request(self, path: str, data: bytes | None = None, content_type: str | None = None):
        req = urllib.request.Request(self.host + path, data=data)
        req.add_header("User-Agent", "magnet-grab")
        if content_type:
            req.add_header("Content-Type", content_type)
        if self.sid:
            req.add_header("Cookie", f"SID={self.sid}")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            cookie = resp.headers.get("Set-Cookie") or ""
            m = re.search(r"SID=([^;]+)", cookie)
            if m:
                self.sid = m.group(1)
            return resp.status, resp.read().decode("utf-8", "replace")

    def login(self, username: str, password: str) -> None:
        body = urllib.parse.urlencode({"username": username, "password": password}).encode()
        status, text = self._request(
            "/api/v2/auth/login", body, "application/x-www-form-urlencoded"
        )
        if status != 200 or text.strip() != "Ok.":
            raise RuntimeError(f"qBittorrent login failed (HTTP {status}): {text.strip()[:80]}")

    def add(self, magnets: list[str], savepath: str = "", category: str = "", paused: bool = False):
        fields = {"urls": "\n".join(magnets)}
        if savepath:
            fields["savepath"] = savepath
        if category:
            fields["category"] = category
        if paused:
            fields["paused"] = "true"
        body, ctype = multipart(fields)
        status, text = self._request("/api/v2/torrents/add", body, ctype)
        if status != 200 or text.strip().lower() not in ("ok.", "ok", ""):
            raise RuntimeError(f"torrents/add failed (HTTP {status}): {text.strip()[:80]}")
        return status


# ------------------------------------------------------------------- output


def render_table(magnets: list[Magnet]) -> str:
    if not magnets:
        return "no magnet links found"
    name_w = max([len("NAME")] + [min(len(m.name or "(unnamed)"), 60) for m in magnets])
    lines = [
        f"{'NAME':<{name_w}}  {'VER':<3} {'INFOHASH':<40}  SRC",
        "-" * (name_w + 3 + 40 + 8),
    ]
    for m in magnets:
        label = m.name or "(unnamed)"
        lines.append(
            f"{label[:60]:<{name_w}}  v{m.version:<2} {m.infohash:<40}  {m.sources[0]}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Extract magnet links from HTML and compile them for a torrent client.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="With no --plain/--json, prints a summary table. Use --plain for a paste-ready list.",
    )
    ap.add_argument("inputs", nargs="*", help="HTML files, directories, or - for stdin")
    ap.add_argument("--url", action="append", default=[], help="fetch this URL and extract from it")
    ap.add_argument("--plain", "-1", action="store_true", help="one magnet per line, no decoration")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--strip-trackers", action="store_true", help="drop tr= params (keep xt/dn)")
    ap.add_argument("--filter", metavar="REGEX", help="keep only magnets whose name matches")
    ap.add_argument("--no-dedupe", action="store_true", help="keep duplicates")

    push = ap.add_argument_group("push to qBittorrent")
    push.add_argument("--add", action="store_true", help="POST the magnets to the qBittorrent WebUI")
    push.add_argument("--host", default=os.environ.get("QBT_HOST", "http://localhost:8080"))
    push.add_argument("--username", default=os.environ.get("QBT_USER", ""))
    push.add_argument("--password", default=os.environ.get("QBT_PASS", ""))
    push.add_argument("--savepath", default="")
    push.add_argument("--category", default="")
    push.add_argument("--paused", action="store_true")
    ap.add_argument("--timeout", type=float, default=20.0)

    args = ap.parse_args(argv)

    if not args.inputs and not args.url:
        ap.error("give me at least one file, directory, --url, or - for stdin")

    magnets: list[Magnet] = []
    seen: set[str] = set()
    errors: list[str] = []

    def absorb(text: str, source: str) -> None:
        for m in extract(text, source, dedupe=not args.no_dedupe):
            if not args.no_dedupe:
                if m.infohash in seen:
                    continue
                seen.add(m.infohash)
            magnets.append(m)

    if "-" in args.inputs:
        absorb(sys.stdin.read(), "<stdin>")

    for path in collect_paths([p for p in args.inputs if p != "-"]):
        try:
            absorb(read_file(path), path)
        except OSError as exc:
            errors.append(f"{path}: {exc}")

    for url in args.url:
        try:
            absorb(fetch(url, args.timeout), url)
        except (urllib.error.URLError, OSError) as exc:
            errors.append(f"{url}: {exc}")

    if args.filter:
        try:
            rx = re.compile(args.filter, re.I)
        except re.error as exc:
            ap.error(f"invalid --filter regex: {exc}")
        magnets = [m for m in magnets if rx.search(m.name or m.uri)]

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "infohash": m.infohash,
                        "version": m.version,
                        "name": m.name,
                        "trackers": len(m.trackers),
                        "sources": m.sources,
                        "magnet": m.clean_uri if args.strip_trackers else m.uri,
                    }
                    for m in magnets
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if not errors else 1

    uris = [m.clean_uri if args.strip_trackers else m.uri for m in magnets]

    if args.add:
        if not uris:
            print("nothing to add", file=sys.stderr)
            return 1
        try:
            client = QBittorrent(args.host, args.username, args.password, args.timeout)
            client.add(uris, args.savepath, args.category, args.paused)
        except (urllib.error.URLError, OSError, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"added {len(uris)} magnet(s) to {args.host}", file=sys.stderr)
        return 0

    if args.plain:
        if uris:
            print("\n".join(uris))
    else:
        print(render_table(magnets))
        print(f"\n{len(magnets)} unique magnet link(s)", file=sys.stderr)
        if magnets:
            print("use --plain for a paste-ready list", file=sys.stderr)

    for err in errors:
        print(f"warning: {err}", file=sys.stderr)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
