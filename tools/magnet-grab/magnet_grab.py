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
import time
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
class SourceStats:
    """Per-input-file tallies, so multi-source runs stay auditable."""

    path: str
    raw: int = 0
    unique: int = 0
    magnets: list["Magnet"] = field(default_factory=list)

    @property
    def label(self) -> str:
        return os.path.basename(self.path) or self.path


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
        query = self.uri.split("?", 1)[1] if "?" in self.uri else ""
        kept = [p for p in query.split("&") if p and not p.startswith("tr=")]
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


def rebuild_with_sources(m: Magnet, sources: list[str]) -> Magnet:
    """Re-derive a Magnet from its URI, carrying over the source list."""
    fresh = build(m.uri, m.infohash, m.version)
    fresh.sources = sources
    return fresh


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


def render_table(magnets: list[Magnet], limit: int = 50) -> str:
    if not magnets:
        return "no magnet links found"
    shown = magnets if limit <= 0 else magnets[:limit]
    name_w = max([len("NAME")] + [min(len(m.name or "(unnamed)"), 60) for m in shown])
    lines = [
        f"{'NAME':<{name_w}}  {'VER':<3} {'INFOHASH':<40}  SRC",
        "-" * (name_w + 3 + 40 + 8),
    ]
    for m in shown:
        label = m.name or "(unnamed)"
        src = m.sources[0] if m.sources else ""
        if len(m.sources) > 1:
            src += f" (+{len(m.sources) - 1})"
        lines.append(f"{label[:60]:<{name_w}}  v{m.version:<2} {m.infohash:<40}  {src}")
    if limit > 0 and len(magnets) > limit:
        lines.append(f"... {len(magnets) - limit} more (use --limit 0 to show all)")
    return "\n".join(lines)


def render_summary(stats: list[SourceStats], merged: list[Magnet]) -> str:
    name_w = max([len("SOURCE")] + [len(s.label) for s in stats]) if stats else len("SOURCE")
    lines = [
        f"{'SOURCE':<{name_w}}  {'RAW':>7} {'UNIQUE':>7} {'IN-SRC DUPES':>13}",
        "-" * (name_w + 2 + 7 + 1 + 7 + 1 + 13),
    ]
    for s in stats:
        lines.append(f"{s.label:<{name_w}}  {s.raw:>7} {s.unique:>7} {s.raw - s.unique:>13}")

    if len(stats) > 1:
        seen_in: dict[str, int] = {}
        for s in stats:
            for m in s.magnets:
                seen_in[m.infohash] = seen_in.get(m.infohash, 0) + 1
        overlap = [h for h, n in seen_in.items() if n > 1]
        only = {s.label: sum(1 for m in s.magnets if seen_in[m.infohash] == 1) for s in stats}

        lines += ["", f"{'CROSS-SOURCE':<{name_w}}", "-" * (name_w + 30)]
        lines.append(f"{'unique across all sources':<{name_w}}  {len(merged):>7}")
        lines.append(f"{'in 2+ sources':<{name_w}}  {len(overlap):>7}")
        for label, count in only.items():
            lines.append(f"{('exclusive to ' + label):<{name_w}}  {count:>7}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Extract magnet links from HTML and compile them for a torrent client.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Handles pages with thousands of links across several source files.\n"
            "  --summary            per-source counts and cross-source overlap\n"
            "  --out-dir DIR        one paste-ready .txt per source file\n"
            "  --plain              merged, deduped list (default cross-source)"
        ),
    )
    ap.add_argument("inputs", nargs="*", help="HTML files, directories, or - for stdin")
    ap.add_argument("--url", action="append", default=[], help="fetch this URL and extract from it")
    ap.add_argument("--plain", "-1", action="store_true", help="one magnet per line, no decoration")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--summary", action="store_true", help="per-source stats and overlap report")
    ap.add_argument("--out-dir", metavar="DIR", help="write one .txt per source into DIR")
    ap.add_argument("--strip-trackers", action="store_true", help="drop tr= params (keep xt/dn)")
    ap.add_argument("--filter", metavar="REGEX", help="keep only magnets whose name matches")
    ap.add_argument("--no-dedupe", action="store_true", help="keep every occurrence, in and across files")
    ap.add_argument(
        "--pick",
        choices=("richest", "first"),
        default="richest",
        help="which URI to keep when a hash repeats across sources (default: richest)",
    )
    ap.add_argument("--limit", type=int, default=50, help="rows in the table; 0 = all (default 50)")

    push = ap.add_argument_group("push to qBittorrent")
    push.add_argument("--add", action="store_true", help="POST the magnets to the qBittorrent WebUI")
    push.add_argument("--host", default=os.environ.get("QBT_HOST", "http://localhost:8080"))
    push.add_argument("--username", default=os.environ.get("QBT_USER", ""))
    push.add_argument("--password", default=os.environ.get("QBT_PASS", ""))
    push.add_argument("--savepath", default="")
    push.add_argument("--category", default="")
    push.add_argument("--paused", action="store_true")
    push.add_argument("--batch", type=int, default=0, help="add at most N per request (0 = all)")
    push.add_argument("--batch-delay", type=float, default=0.0, help="seconds between batches")
    ap.add_argument("--timeout", type=float, default=20.0)

    args = ap.parse_args(argv)

    if not args.inputs and not args.url:
        ap.error("give me at least one file, directory, --url, or - for stdin")

    stats: list[SourceStats] = []
    index: dict[str, Magnet] = {}
    order: list[str] = []
    flat: list[Magnet] = []
    errors: list[str] = []

    def absorb(text: str, source: str) -> None:
        matches = extract(text, source, dedupe=False)
        entry = SourceStats(path=source, raw=len(matches))
        local: dict[str, Magnet] = {}
        local_order: list[str] = []

        for m in matches:
            if args.no_dedupe:
                flat.append(m)
            else:
                # within this source
                prev = local.get(m.infohash)
                if prev is None:
                    local[m.infohash] = m
                    local_order.append(m.infohash)
                elif len(m.uri) > len(prev.uri):
                    local[m.infohash] = m
                # across all sources
                known = index.get(m.infohash)
                if known is None:
                    index[m.infohash] = rebuild_with_sources(m, [source])
                    order.append(m.infohash)
                else:
                    if source not in known.sources:
                        known.sources.append(source)
                    # "richest": prefer the URI carrying the most information
                    # (usually the one with the fullest tracker list).
                    # "first": keep whatever was seen first, across all sources.
                    if args.pick == "richest" and len(m.uri) > len(known.uri):
                        index[m.infohash] = rebuild_with_sources(m, known.sources)

        entry.magnets = [local[h] for h in local_order]
        entry.unique = len(local)
        stats.append(entry)

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
        keep = lambda m: bool(rx.search(m.name or m.uri))  # noqa: E731
        for entry in stats:
            entry.magnets = [m for m in entry.magnets if keep(m)]
            entry.unique = len(entry.magnets)
        flat = [m for m in flat if keep(m)]
        order = [h for h in order if keep(index[h])]

    merged = flat if args.no_dedupe else [index[h] for h in order]
    uri_of = (lambda m: m.clean_uri) if args.strip_trackers else (lambda m: m.uri)  # noqa: E731

    if args.out_dir:
        try:
            os.makedirs(args.out_dir, exist_ok=True)
        except OSError as exc:
            ap.error(f"cannot create --out-dir: {exc}")
        written = 0
        for entry in stats:
            stem = os.path.splitext(os.path.basename(entry.path))[0] or "stdin"
            stem = re.sub(r"[^\w.\-]+", "_", stem) or "source"
            dest = os.path.join(args.out_dir, f"{stem}.txt")
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write("\n".join(uri_of(m) for m in entry.magnets))
                if entry.magnets:
                    fh.write("\n")
            print(f"{dest}  {entry.unique} magnet(s)", file=sys.stderr)
            written += 1
        if not written:
            print("no sources to write", file=sys.stderr)

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
                        "magnet": uri_of(m),
                    }
                    for m in merged
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if not errors else 1

    if args.summary:
        print(render_summary(stats, merged))
        for err in errors:
            print(f"warning: {err}", file=sys.stderr)
        return 0 if not errors else 1

    uris = [uri_of(m) for m in merged]

    if args.add:
        if not uris:
            print("nothing to add", file=sys.stderr)
            return 1
        try:
            client = QBittorrent(args.host, args.username, args.password, args.timeout)
            size = args.batch if args.batch > 0 else len(uris)
            sent = 0
            for start in range(0, len(uris), size):
                chunk = uris[start : start + size]
                client.add(chunk, args.savepath, args.category, args.paused)
                sent += len(chunk)
                print(f"  added {sent}/{len(uris)}", file=sys.stderr)
                if args.batch_delay and start + size < len(uris):
                    time.sleep(args.batch_delay)
        except (urllib.error.URLError, OSError, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"added {len(uris)} magnet(s) to {args.host}", file=sys.stderr)
        return 0

    if args.plain:
        if uris:
            print("\n".join(uris))
    elif not args.out_dir:
        print(render_table(merged, args.limit))
        print(f"\n{len(merged)} unique magnet link(s)", file=sys.stderr)
        if len(stats) > 1:
            print(f"from {len(stats)} source(s) — use --summary for the breakdown", file=sys.stderr)
    else:
        print(f"\n{len(merged)} unique magnet link(s) across {len(stats)} source(s)", file=sys.stderr)

    for err in errors:
        print(f"warning: {err}", file=sys.stderr)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
