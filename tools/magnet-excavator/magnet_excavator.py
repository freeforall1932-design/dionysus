#!/usr/bin/env python3
"""
Magnet Excavator — dig every magnet link out of saved HTML and hand it to a torrent client.

Stdlib only. No BeautifulSoup, no requests.

    ./magnet_excavator.py page.html                 # table of what was found
    ./magnet_excavator.py page.html --plain         # one magnet per line -> paste into qBittorrent
    ./magnet_excavator.py dir/ *.html --plain > m.txt
    cat page.html | ./magnet_excavator.py -
    ./magnet_excavator.py page.html --add           # POST straight to the qBittorrent WebUI
    ./magnet_excavator.py --url https://site/list   # fetch + extract in one go

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

# A magnet URI is a scheme plus a query string, and per RFC 3986 every character
# in it is printable ASCII. Restricting to the allowed URI set means a magnet
# embedded in a binary file stops cleanly at the first null byte or non-ASCII
# byte instead of dragging garbage into the link.
_URI_CHARS = r"[0-9A-Za-z\-._~:/?#\[\]@!$&()*+,;=%]"
# No \b anchor: a magnet is often preceded by a word character ("url":"magnet:, xmagnet:)
# and \b would refuse to match there. False positives are prevented downstream by
# requiring a well-formed infohash, not by the anchor.
MAGNET_RE = re.compile(r"(?i)magnet:\?" + _URI_CHARS + r"+")

# Accepted infohash encodings:
#   v1  40 hex chars, or 32 chars of base32
#   v2  "1220" prefix + 64 hex chars (sha256 multihash, urn:btmh)
BTIH_V1_HEX = re.compile(r"(?i)xt=urn:btih:([0-9a-f]{40})\b")
BTIH_V1_B32 = re.compile(r"(?i)xt=urn:btih:([a-z2-7]{32})\b")
BTMH_V2 = re.compile(r"(?i)xt=urn:btmh:1220([0-9a-f]{64})\b")
ANY_XT = re.compile(r"(?i)[?&]xt=")

TRAILING_JUNK = ".,;:!?)'\""

# Files are read in chunks with an overlap so a link straddling a boundary is
# re-found whole. 16 MiB means any realistically saved page is a single pass and
# never touches the boundary path at all; it stays as a safety net for a huge
# dump. OVERLAP must exceed the longest magnet URI we expect — real magnets run
# a few hundred bytes to a few KB even with dozens of trackers.
CHUNK_BYTES = 16 << 20
OVERLAP = 1 << 16

# "1.4 GB", "700MB", "12,5 KiB", "4.2gb". Index pages put this next to the magnet
# and it is the only size available before metadata is resolved.
SIZE_RE = re.compile(
    r"(?<![0-9a-zA-Z])"
    r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?)"
    r"\s*"
    r"(KiB|MiB|GiB|TiB|PiB|KB|MB|GB|TB|PB|B)\b",
    re.I,
)

# Index sites write "MB"/"GB" but mean 1024-based units, so read every unit as
# binary. Treating MB as 10^6 would report a "1 MB" torrent as "976.6 KiB".
SIZE_UNITS = {"b": 1, "kb": 1 << 10, "kib": 1 << 10, "mb": 1 << 20, "mib": 1 << 20,
              "gb": 1 << 30, "gib": 1 << 30, "tb": 1 << 40, "tib": 1 << 40,
              "pb": 1 << 50, "pib": 1 << 50}


def parse_size(text: str) -> int | None:
    """Turn '1.4 GB' / '700MB' / '12,5 KiB' into a byte count."""
    m = SIZE_RE.search(text)
    if not m:
        return None
    raw, unit = m.group(1), m.group(2).lower()
    factor = SIZE_UNITS.get(unit)
    if factor is None:
        return None
    # Handle both "1,234.5" (en) and "1.234,5" (id/de) separators.
    if "," in raw and "." in raw:
        raw = raw.replace(",", "") if raw.rfind(".") > raw.rfind(",") else raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(",", ".") if "," in raw else raw
    try:
        return int(float(raw) * factor)
    except ValueError:
        return None


def human_size(n: int | None) -> str:
    if n is None:
        return "-"
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    value = float(n)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PiB"


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
    size: int | None = None  # bytes, from xl= if present or scraped from the page

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


def canonicalize(uri: str) -> str:
    """Lowercase the scheme, parameter names and URN prefix of a magnet URI.

    URI schemes are case-insensitive but query parameter *names* are not, so an
    all-uppercase link written as MAGNET:?XT=URN:BTIH:... would not be read by a
    strict parser looking for `xt`. Parameter *values* are left byte-for-byte
    alone — the display name is not ours to rewrite.
    """
    scheme, sep, query = uri.partition("?")
    if not sep:
        return scheme.lower()

    out = []
    for part in query.split("&"):
        if not part:
            continue
        key, eq, value = part.partition("=")
        key = key.lower()
        if eq and key == "xt":
            # urn:btih:<hash> / urn:btmh:<hash> — the namespace is case-insensitive
            value = re.sub(r"(?i)^urn:bt(ih|mh):", lambda m: "urn:bt" + m.group(1).lower() + ":", value)
        out.append(key + eq + value)
    return scheme.lower() + "?" + "&".join(out)


def _blank_uris(region: str) -> str:
    """Blank out magnet URIs so a size inside a dn= name is not taken as the row's."""
    for uri_match in MAGNET_RE.finditer(region):
        start, end = uri_match.span()
        region = region[:start] + " " * (end - start) + region[end:]
    return region


def scrape_size(text: str, match: "re.Match", window: int = 400) -> int | None:
    """Find the file size belonging to one magnet link.

    Listings disagree about where the size sits: some put it before the link
    (Name | Size | Seeds | Magnet), some after. So when the link is genuinely
    inside a table row, read the whole row. When it is not — a link in a JSON
    blob, a comment, plain prose — only look forward a short way, and never
    reach back into a row the link does not belong to. Getting this wrong is
    worse than reporting no size at all.
    """
    row_start = text.rfind("<tr", 0, match.start())
    if row_start != -1:
        # The link is inside that row only if no other </tr> closed it first.
        if text.find("</tr>", row_start, match.start()) == -1:
            row_close = text.find("</tr>", match.end())
            if row_close != -1:
                return parse_size(_blank_uris(text[row_start : row_close + 5]))

    end = min(len(text), match.end() + window)
    next_row = text.find("<tr", match.end(), end)
    if next_row != -1:
        end = next_row
    return parse_size(_blank_uris(text[match.end() : end]))


def build(uri: str, infohash: str, version: int, size: int | None = None) -> Magnet:
    params = parse_query(uri)
    # `xl` (exact length) predates BEP 9 and index sites rarely emit it, but when
    # present it is authoritative, so it beats anything scraped from the page.
    if size is None:
        for candidate in params.get("xl", []):
            try:
                size = int(candidate)
                break
            except ValueError:
                continue
    return Magnet(
        uri=canonicalize(uri),
        infohash=infohash,
        version=version,
        name=decode_name(params.get("dn", [])),
        trackers=[unquote_smart(t) for t in params.get("tr", [])],
        size=size,
    )


def rebuild_with_sources(m: Magnet, sources: list[str]) -> Magnet:
    """Re-derive a Magnet from its URI, carrying over source list and scraped size."""
    fresh = build(m.uri, m.infohash, m.version)
    fresh.sources = sources
    if fresh.size is None:
        fresh.size = m.size
    return fresh


def detect_encoding(sample: bytes) -> str:
    """Pick a decoder from a leading <meta charset>, else fall back to utf-8."""
    head = sample[:4096].decode("ascii", "ignore").lower()
    m = re.search(r'charset=["\']?\s*([a-z0-9_\-]+)', head)
    if m:
        try:
            "".encode(m.group(1))
            return m.group(1)
        except LookupError:
            pass
    return "utf-8"


def iter_text_chunks(path: str, chunk_bytes: int = CHUNK_BYTES):
    """Yield decoded text for any file on disk, gunzipping transparently.

    No extension filter and no assumption about format: the bytes are decoded
    with errors='replace' so a .txt, an .mhtml, a log, or a binary that happens
    to contain a magnet all work.
    """
    with open(path, "rb") as fh:
        magic = fh.read(2)
        fh.seek(0)
        raw = gzip.GzipFile(fileobj=fh) if magic == b"\x1f\x8b" else fh
        first = raw.read(chunk_bytes)
        if not first:
            return
        encoding = detect_encoding(first)
        yield first.decode(encoding, "replace")
        while True:
            buf = raw.read(chunk_bytes)
            if not buf:
                break
            yield buf.decode(encoding, "replace")


def iter_matches_with_size(chunks, source: str = "<input>", window: int = 400,
                           want_size: bool = True):
    """Yield every Magnet in a stream of text chunks, safe across chunk edges.

    A match is held back when it *starts* inside the trailing OVERLAP, and carry
    is exactly OVERLAP long — so any held-back match is guaranteed to be present
    in full on the next pass. Keying off the start matters: a match can begin
    before the carry window and still run past the cut, and testing its end
    would drop it permanently.

    When want_size is on, a file size is scraped from the text following each
    magnet (up to the end of the enclosing table row).
    """
    carry = ""
    pending = None

    def scan(text: str, final: bool):
        limit_start = len(text) if final else len(text) - OVERLAP
        for m in MAGNET_RE.finditer(text):
            if m.start() >= limit_start:
                break
            uri = normalize(m.group(0))
            info = classify(uri)
            if info is None:
                continue
            infohash, version = info
            magnet = build(uri, infohash, version)
            magnet.sources = [source]
            if want_size and magnet.size is None:
                magnet.size = scrape_size(text, m, window)
            yield magnet

    for chunk in chunks:
        if pending is None:
            pending = chunk
            continue
        text = carry + pending
        yield from scan(text, False)
        carry = text[-OVERLAP:]
        pending = chunk
    if pending is not None:
        yield from scan(carry + pending, True)


def iter_matches(chunks, source: str = "<input>"):
    """Same traversal without the size scrape."""
    return iter_matches_with_size(chunks, source, want_size=False)


def extract(text: str, source: str = "<input>", dedupe: bool = True,
            with_size: bool = True) -> list[Magnet]:
    """Find every magnet URI in `text`.

    With dedupe=True (default) each infohash appears once, keeping the richest URI.
    With dedupe=False every occurrence is returned, in document order.
    """
    found: dict[str, Magnet] = {}
    order: list[str] = []
    all_matches: list[Magnet] = []

    for magnet in iter_matches_with_size([text], source, want_size=with_size):
        if not dedupe:
            all_matches.append(magnet)
            continue
        known = found.get(magnet.infohash)
        if known is None:
            found[magnet.infohash] = magnet
            order.append(magnet.infohash)
        elif len(magnet.uri) > len(known.uri):
            found[magnet.infohash] = rebuild_with_sources(magnet, known.sources)

    return all_matches if not dedupe else [found[h] for h in order]


def fetch_chunks(url: str, timeout: float):
    """Stream a URL as decoded text chunks."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) magnet-excavator",
            "Accept-Encoding": "identity",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        first = resp.read(CHUNK_BYTES)
        if not first:
            return
        encoding = detect_encoding(first)
        yield first.decode(encoding, "replace")
        while True:
            buf = resp.read(CHUNK_BYTES)
            if not buf:
                break
            yield buf.decode(encoding, "replace")


def decode_bytes(blob: bytes) -> str:
    """Decode a whole in-memory payload (kept for tests and small buffers)."""
    if blob[:2] == b"\x1f\x8b":
        blob = gzip.decompress(blob)
    return blob.decode(detect_encoding(blob), "replace")


def collect_paths(inputs: list[str], only_ext: set[str] | None = None,
                  max_bytes: int | None = None):
    """Expand inputs into a file list. Every file is a candidate unless filtered.

    --ext and --max-file-size prune a *directory walk* only. A file named
    explicitly is always attempted, so a typo surfaces as an error instead of
    being silently dropped.
    """
    paths: list[str] = []

    def walk_ok(path: str) -> bool:
        if only_ext and not path.lower().endswith(tuple(only_ext)):
            return False
        if max_bytes is not None:
            try:
                if os.path.getsize(path) > max_bytes:
                    return False
            except OSError:
                return False
        return True

    for item in inputs:
        if item == "-":
            paths.append(item)
            continue
        if os.path.isdir(item):
            for root, _dirs, files in os.walk(item):
                for name in sorted(files):
                    full = os.path.join(root, name)
                    if walk_ok(full):
                        paths.append(full)
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
        req.add_header("User-Agent", "magnet-excavator")
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

    def get_json(self, path: str):
        status, text = self._request(path)
        if status != 200:
            raise RuntimeError(f"{path} failed (HTTP {status})")
        return json.loads(text)

    def active_count(self, state: str = "downloading") -> int:
        """How many torrents are currently in `state` (see /torrents/info filter)."""
        return len(self.get_json(f"/api/v2/torrents/info?filter={state}"))

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
        f"{'NAME':<{name_w}}  {'SIZE':>9}  {'VER':<3} {'INFOHASH':<40}  SRC",
        "-" * (name_w + 2 + 9 + 2 + 3 + 1 + 40 + 8),
    ]
    for m in shown:
        label = m.name or "(unnamed)"
        src = m.sources[0] if m.sources else ""
        if len(m.sources) > 1:
            src += f" (+{len(m.sources) - 1})"
        size = human_size(m.size)
        lines.append(f"{label[:60]:<{name_w}}  {size:>9}  v{m.version:<2} {m.infohash:<40}  {src}")
    if limit > 0 and len(magnets) > limit:
        lines.append(f"... {len(magnets) - limit} more (use --limit 0 to show all)")
    return "\n".join(lines)


def render_summary(stats: list[SourceStats], merged: list[Magnet]) -> str:
    name_w = max([len("SOURCE")] + [len(s.label) for s in stats]) if stats else len("SOURCE")
    lines = [
        f"{'SOURCE':<{name_w}}  {'RAW':>7} {'UNIQUE':>7} {'DUPES':>6} {'SIZED':>6} {'EST. TOTAL':>11}",
        "-" * (name_w + 2 + 7 + 1 + 7 + 1 + 6 + 1 + 6 + 1 + 11),
    ]
    for s in stats:
        total = sum(m.size for m in s.magnets if m.size is not None)
        sized = sum(1 for m in s.magnets if m.size is not None)
        lines.append(
            f"{s.label:<{name_w}}  {s.raw:>7} {s.unique:>7} {s.raw - s.unique:>6} "
            f"{sized:>6} {human_size(total) if sized else '-':>11}"
        )

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

    sized = [m for m in merged if m.size is not None]
    lines += ["", "ESTIMATED TOTAL (merged, deduped)", "-" * 46]
    lines.append(f"{'links with a size':<34}  {len(sized):>7} / {len(merged)}")
    lines.append(f"{'links with no size found':<34}  {len(merged) - len(sized):>7}")
    if sized:
        lines.append(f"{'total bytes':<34}  {sum(m.size for m in sized):>7}")
        lines.append(f"{'total (human)':<34}  {human_size(sum(m.size for m in sized)):>7}")
        biggest = max(sized, key=lambda m: m.size)
        lines.append(f"{'largest single link':<34}  {human_size(biggest.size):>7}  {biggest.name[:40]}")
    else:
        lines.append(
            "no sizes could be scraped — sizes come from the page markup, and a "
            "magnet URI carries none"
        )
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
    ap.add_argument(
        "--split",
        type=int,
        metavar="N",
        help="with --out-dir, break each source into part files of N links for manual pasting",
    )
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
    ap.add_argument(
        "--ext",
        action="append",
        metavar="EXT",
        help="only scan these extensions (repeatable). Default: scan every file",
    )
    ap.add_argument(
        "--max-file-size",
        type=int,
        default=512 * 1024 * 1024,
        help="skip files larger than N bytes in a directory walk (default 512 MiB, 0 = no limit)",
    )

    sizes = ap.add_argument_group("size filtering (scraped from the page)")
    sizes.add_argument("--min-size", metavar="SIZE", help='e.g. "500MB", "1.5GB"')
    sizes.add_argument("--max-size", metavar="SIZE", help='e.g. "20GB"')
    sizes.add_argument(
        "--keep-unknown-size",
        action="store_true",
        help="with --min-size/--max-size, keep links whose size could not be scraped",
    )

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
    push.add_argument(
        "--max-active",
        type=int,
        default=0,
        help="keep at most N torrents downloading: add into the headroom, then wait "
        "and top up. This is how you feed in thousands without wedging the client",
    )
    push.add_argument(
        "--poll-interval", type=float, default=30.0, help="seconds between queue polls (default 30)"
    )
    ap.add_argument("--timeout", type=float, default=20.0)

    args = ap.parse_args(argv)

    if not args.inputs and not args.url:
        ap.error("give me at least one file, directory, --url, or - for stdin")

    stats: list[SourceStats] = []
    index: dict[str, Magnet] = {}
    order: list[str] = []
    flat: list[Magnet] = []
    errors: list[str] = []

    def absorb(chunks, source: str) -> None:
        entry = SourceStats(path=source)
        local: dict[str, Magnet] = {}
        local_order: list[str] = []

        for m in iter_matches_with_size(chunks, source):
            entry.raw += 1
            if args.no_dedupe:
                flat.append(m)
                continue
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
                if known.size is None and m.size is not None:
                    known.size = m.size
                # "richest": prefer the URI carrying the most information
                # (usually the one with the fullest tracker list).
                # "first": keep whatever was seen first, across all sources.
                if args.pick == "richest" and len(m.uri) > len(known.uri):
                    index[m.infohash] = rebuild_with_sources(m, known.sources)

        entry.magnets = [local[h] for h in local_order]
        entry.unique = len(local)
        stats.append(entry)

    if "-" in args.inputs:
        absorb([sys.stdin.read()], "<stdin>")

    only_ext = None
    if args.ext:
        only_ext = {("." + e.lstrip(".").lower()) for e in args.ext}

    cap = args.max_file_size or None
    for path in collect_paths([p for p in args.inputs if p != "-"], only_ext, cap):
        try:
            absorb(iter_text_chunks(path), path)
        except OSError as exc:
            errors.append(f"{path}: {exc}")

    for url in args.url:
        try:
            absorb(fetch_chunks(url, args.timeout), url)
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

    lo = parse_size(args.min_size) if args.min_size else None
    hi = parse_size(args.max_size) if args.max_size else None
    if lo is not None or hi is not None:
        def sized(m: Magnet) -> bool:
            if m.size is None:
                return args.keep_unknown_size
            return (lo is None or m.size >= lo) and (hi is None or m.size <= hi)

        for entry in stats:
            entry.magnets = [m for m in entry.magnets if sized(m)]
            entry.unique = len(entry.magnets)
        flat = [m for m in flat if sized(m)]
        order = [h for h in order if sized(index[h])]

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
            items = [uri_of(m) for m in entry.magnets]

            if args.split and args.split > 0:
                parts = (len(items) + args.split - 1) // args.split
                width = max(2, len(str(parts)))
                for i in range(parts):
                    chunk = items[i * args.split : (i + 1) * args.split]
                    dest = os.path.join(args.out_dir, f"{stem}.part{i + 1:0{width}d}.txt")
                    with open(dest, "w", encoding="utf-8") as fh:
                        fh.write("\n".join(chunk) + "\n")
                    print(f"{dest}  {len(chunk)} magnet(s)", file=sys.stderr)
                    written += 1
            else:
                dest = os.path.join(args.out_dir, f"{stem}.txt")
                with open(dest, "w", encoding="utf-8") as fh:
                    if items:
                        fh.write("\n".join(items) + "\n")
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
                        "size_bytes": m.size,
                        "size": human_size(m.size),
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
            sent = 0
            queue = list(uris)

            if args.max_active > 0:
                # Queue-aware feeding. Magnets are cheap to add but expensive to
                # resolve: each one sits at "Downloading metadata" until a peer
                # answers, and qBittorrent counts those towards its active
                # download limit. Dumping thousands in at once locks the GUI and
                # starves the queue, so add only into the available headroom.
                while queue:
                    active = client.active_count("downloading")
                    headroom = args.max_active - active
                    if headroom <= 0:
                        print(
                            f"  {active} downloading, holding at --max-active "
                            f"{args.max_active}; retrying in {args.poll_interval:g}s "
                            f"({len(queue)} queued)",
                            file=sys.stderr,
                        )
                        time.sleep(args.poll_interval)
                        continue
                    take = min(headroom, args.batch if args.batch > 0 else headroom)
                    chunk = queue[:take]
                    client.add(chunk, args.savepath, args.category, args.paused)
                    queue = queue[take:]
                    sent += len(chunk)
                    print(f"  added {sent}/{len(uris)} ({len(queue)} left)", file=sys.stderr)
                    if args.batch_delay and queue:
                        time.sleep(args.batch_delay)
            else:
                size = args.batch if args.batch > 0 else len(queue)
                for start in range(0, len(queue), size):
                    chunk = queue[start : start + size]
                    client.add(chunk, args.savepath, args.category, args.paused)
                    sent += len(chunk)
                    print(f"  added {sent}/{len(uris)}", file=sys.stderr)
                    if args.batch_delay and start + size < len(queue):
                        time.sleep(args.batch_delay)
        except KeyboardInterrupt:
            print(f"\ninterrupted; {sent} added, {len(queue)} not yet sent", file=sys.stderr)
            return 130
        except (urllib.error.URLError, OSError, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"added {sent} magnet(s) to {args.host}", file=sys.stderr)
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
