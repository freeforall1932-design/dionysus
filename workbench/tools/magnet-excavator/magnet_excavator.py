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
import bisect
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
    rejected: int = 0   # looked like a magnet, failed validation
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
    name_source: str = ""    # "dn" if from the URI, "page" if scraped, "" if unknown

    @property
    def clean_uri(self) -> str:
        """Magnet with the tracker list stripped off (xt + dn only)."""
        query = self.uri.split("?", 1)[1] if "?" in self.uri else ""
        kept = [p for p in query.split("&") if p and not p.startswith("tr=")]
        return "magnet:?" + "&".join(kept)

    @property
    def hints_uri(self) -> str:
        """xt plus tracker hints, and nothing else - the middle option.

        ``--bare`` leans entirely on the DHT, which is why those torrents can sit
        at "Downloading metadata" for a long time or forever if no DHT peer has
        the info dict. ``--strip-trackers`` keeps the name but drops exactly the
        hints that fix that. This keeps the hints and drops the name, so the
        client can still find peers without the URI carrying decoration.
        """
        query = self.uri.split("?", 1)[1] if "?" in self.uri else ""
        kept = [
            p for p in query.split("&")
            if p and (p.lower().startswith("xt=") or p.lower().startswith("tr="))
        ]
        if not any(p.lower().startswith("xt=") for p in kept):
            kept.insert(0, "xt=urn:btih:" + self.infohash)
        return "magnet:?" + "&".join(kept)

    @property
    def bare_uri(self) -> str:
        """The minimum that still identifies the torrent: xt and nothing else.

        Everything else in a magnet is decoration or a hint. The client resolves
        the name and finds peers on its own, so for pasting or piping this is the
        shortest string that still works.
        """
        query = self.uri.split("?", 1)[1] if "?" in self.uri else ""
        xts = [p for p in query.split("&") if p.lower().startswith("xt=")]
        if not xts:
            return "magnet:?xt=urn:btih:" + self.infohash
        return "magnet:?" + "&".join(xts)


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


# How far, in characters, to look either side of a link when the page's
# structure gives no usable container (plain-text dumps, minified markup).
# Single source of truth for iter_matches_with_size's default.
META_WINDOW = 400

TAG_RE = re.compile(r"<[^>]*>")

# Tags that never contain anything, so they are never pushed on the stack.
_VOID = {"br", "hr", "img", "input", "link", "meta", "source", "track", "wbr",
         "area", "base", "col", "embed", "param"}

# Closing tags that end an *entry*. Counting these between a candidate value and
# a link is what tells us whether they belong to the same listing item — raw
# character distance cannot, because markup padding varies wildly.
ENTRY_CLOSE_RE = re.compile(
    r"(?i)</(tr|li|div|article|section|p|dl|dd|table|ul|ol|h[1-6]|figure|details)\b"
)

# Elements that end a whole *entry*. Walking up out of a <td> into its <tr> is
# safe; walking up out of a <tr> into the <table> is not, because the table also
# holds every other row's size. </div> is deliberately absent: nested divs are
# normal inside one entry.
ENTRY_BOUNDARY_RE = re.compile(r"</(?:tr|li|article|table|ul|ol|dl|dd)\b", re.I)

_NOT_A_NAME = re.compile(r"^[\s\d.,:;%/\\|+*#()\[\]{}<>=~-]*$")


def rebuild_with_sources(m: Magnet, sources: list[str]) -> Magnet:
    """Re-derive a Magnet from its URI, carrying over what the page told us.

    Everything scraped has to be copied across by hand, because `build()` only
    knows what is in the URI. The size was always carried; the scraped name was
    not, so any magnet that went through dedupe - the default - came out
    "(unnamed)" even though the page had a title for it.
    """
    fresh = build(m.uri, m.infohash, m.version)
    fresh.sources = sources
    if fresh.size is None:
        fresh.size = m.size
    if not fresh.name and m.name:
        fresh.name = m.name
        fresh.name_source = m.name_source
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


def load_trackers(path: str | None = None, url: str | None = None,
                  timeout: float = 20.0) -> list[str]:
    """Read a tracker list - one per line, blanks and # comments ignored.

    This is the format published by ngosang/trackerslist and friends, so a
    downloaded trackers_all.txt can be pointed at directly.
    """
    if not path and not url:
        return []
    if url:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            blob = resp.read()
    else:
        with open(path, "rb") as fh:
            blob = fh.read()
    seen: set[str] = set()
    out: list[str] = []
    for line in decode_bytes(blob).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line in seen:
            continue
        seen.add(line)
        out.append(line)
    return out


def augment_trackers(magnets: list[Magnet], trackers: list[str], cap: int = 5) -> int:
    """Give trackerless magnets some hints, and say how many were touched.

    Only magnets with no tr= of their own are touched: a page that supplied
    trackers knew which ones that torrent is on, and overwriting that with a
    generic list would be worse than leaving it alone.
    """
    if not trackers:
        return 0
    pool = trackers if cap <= 0 else trackers[:cap]
    if not pool:
        return 0
    suffix = "&" + "&".join("tr=" + urllib.parse.quote(t, safe="") for t in pool)
    touched = 0
    for m in magnets:
        if m.trackers:
            continue
        m.uri = m.uri + suffix
        m.trackers = list(pool)
        touched += 1
    return touched


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
    name = decode_name(params.get("dn", []))
    return Magnet(
        uri=canonicalize(uri),
        infohash=infohash,
        version=version,
        name=name,
        trackers=[unquote_smart(t) for t in params.get("tr", [])],
        size=size,
        name_source="dn" if name else "",
    )


_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def _blank_comments(text: str) -> str:
    """Blank out HTML comments without shifting any offsets.

    Saved pages often carry commented-out rows, and a size in one of those is not
    a size the page is publishing. Replacing each comment with the same number of
    spaces keeps every other position valid, so callers can still trust offsets.
    """
    return _COMMENT_RE.sub(lambda m: " " * len(m.group(0)), text)


def _clean_text(fragment: str) -> str:
    text = TAG_RE.sub(" ", fragment)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


_ENTITY_RE = re.compile(r"&(?:nbsp|mdash|ndash|middot|bull|amp|lt|gt|#\d+|#x[0-9a-fA-F]+);")
_TRAILING_SEP = " \t\r\n—–-|,;:·•»»/"


def _clean_name(value: str) -> str:
    """Tidy a name scraped out of the page.

    Drops HTML entities and any size that got glued to the end, so a listing
    cell reading ``Ubuntu 24.04 &mdash; 4.7 GB`` yields ``Ubuntu 24.04``.
    """
    stripped = _ENTITY_RE.sub(" ", value)
    for _ in range(3):
        m = SIZE_RE.search(stripped)
        if not m or m.end() < len(stripped.rstrip()) - 2:
            break
        stripped = stripped[: m.start()]
    stripped = stripped.strip(_TRAILING_SEP)
    return stripped or value.strip()


def _candidates(segment: str, base: int, link_edge: int, side: str):
    """Yield (entry_closes, distance, kind, value) for sizes and text in a segment."""
    cleaned = _blank_comments(segment)
    for uri in MAGNET_RE.finditer(cleaned):
        a, b = uri.span()
        cleaned = cleaned[:a] + " " * (b - a) + cleaned[b:]

    out = []
    for sm in SIZE_RE.finditer(cleaned):
        value = parse_size(sm.group(0))
        if value is None:
            continue
        gap = cleaned[: sm.start()] if side == "before" else cleaned[sm.end() :]
        closes = len(ENTRY_CLOSE_RE.findall(gap))
        dist = abs((base + sm.start()) - link_edge)
        out.append((closes, dist, "size", value))

    pos = 0
    for piece in re.split(r"(<[^>]*>)", cleaned):
        if piece.startswith("<"):
            pos += len(piece)
            continue
        stripped = _clean_text(piece)
        advance = piece.find(stripped[:1]) if stripped else 0
        abs_pos = base + pos + max(advance, 0)
        pos += len(piece)
        if not stripped or len(stripped) > 80 or _NOT_A_NAME.match(stripped):
            continue
        if SIZE_RE.fullmatch(stripped):
            continue
        cleaned_name = _clean_name(stripped)
        if not cleaned_name:
            continue
        gap = cleaned[: abs_pos - base] if side == "before" else cleaned[abs_pos - base :]
        closes = len(ENTRY_CLOSE_RE.findall(gap))
        out.append((closes, abs(abs_pos - link_edge), "name", cleaned_name))
    return out


def _after_anchor(text: str, edge: int, limit: int) -> int:
    """Move past a link's own </a>, so its anchor text is not taken for its name."""
    close = text.find("</a>", edge)
    if close != -1 and close - edge < 200:
        return min(close + 4, limit)
    gt = text.find(">", edge)
    return min(gt + 1, limit) if gt != -1 else edge


# An <a> element holds nothing but the link and its caption, so it is useless as
# a container to read metadata from. Ignoring it makes the innermost block the
# real entry: the <div>, <td> or <p> the listing actually built.
_TRANSPARENT = {"a", "span", "font", "b", "i", "em", "strong", "small", "code"}


def analyze_blocks(
    text: str, positions: list[int]
) -> tuple[list[list[tuple[int, int, int]]], list[list[tuple[int, int]]]]:
    """One pass over the tags -> the nesting chain each position sits in.

    Returns ``(chains, by_depth)``:
      * ``chains[i]`` — the enclosing elements around ``positions[i]``,
        innermost first, as ``(start, end, depth)``.
      * ``by_depth[d]`` — the ``(start, end)`` pairs at depth ``d``, sorted and
        non-overlapping, so the sibling beside an entry is a binary search.

    This is a tag stack, not an HTML parser: unclosed elements simply run to the
    end of the text, and the bounded-window fallback below takes over from there.
    Positions must already be sorted.
    """
    all_blocks: list[tuple[int, int, int]] = []
    stack: list[tuple[int, str]] = []
    pending: list[list[int]] = [[] for _ in positions]
    pi = 0
    length = len(text)

    def answer(up_to: int):
        nonlocal pi
        snapshot = [start for start, _name in stack]
        while pi < len(positions) and positions[pi] <= up_to:
            pending[pi] = snapshot
            pi += 1

    pos = text.find("<")
    while pos != -1:
        answer(pos)
        gt = text.find(">", pos)
        if gt == -1:
            break
        tag = text[pos + 1 : gt]
        if tag.startswith("!--"):
            close = text.find("-->", pos)
            pos = text.find("<", pos + 1 if close == -1 else close + 3)
            continue
        closing = tag.startswith("/")
        name = (tag[1:] if closing else tag).split(None, 1)[0].lower().rstrip("/")
        self_closing = tag.endswith("/") or name in _VOID
        if name and name not in _TRANSPARENT:
            if closing:
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i][1] == name:
                        for k in range(len(stack) - 1, i - 1, -1):
                            all_blocks.append((stack[k][0], gt + 1, k))
                        del stack[i:]
                        break
            elif not self_closing:
                stack.append((pos, name))
        pos = text.find("<", gt + 1)

    answer(length)
    for k in range(len(stack) - 1, -1, -1):
        all_blocks.append((stack[k][0], length, k))

    ends = {b_start: (b_end, depth) for b_start, b_end, depth in all_blocks}
    chains: list[list[tuple[int, int, int]]] = []
    for snapshot in pending:
        chain = []
        for b_start in reversed(snapshot):
            if b_start in ends:
                b_end, depth = ends[b_start]
                chain.append((b_start, b_end, depth))
        chains.append(chain)

    all_blocks.sort()
    by_depth: list[list[tuple[int, int]]] = []
    for b_start, b_end, depth in all_blocks:
        while len(by_depth) <= depth:
            by_depth.append([])
        by_depth[depth].append((b_start, b_end))
    return chains, by_depth


def sibling_before(
    start: int, depth: int, by_depth: list[list[tuple[int, int]]]
) -> tuple[int, int] | None:
    """The element at ``depth`` that ends immediately before ``start``."""
    if depth >= len(by_depth):
        return None
    pairs = by_depth[depth]
    i = bisect.bisect_left(pairs, (start, start))
    for j in range(i - 1, max(-1, i - 8), -1):
        b_start, b_end = pairs[j]
        if b_end <= start:
            return (b_start, b_end)
    return None


def _holds_other(spans: list[tuple[int, int]], starts: list[int],
                 lo: int, hi: int, mine: tuple[int, int]) -> bool:
    """True if ``[lo, hi)`` overlaps any magnet span other than ``mine``.

    Spans are sorted and never overlap each other, so this is a binary search
    plus the handful of spans that actually intersect - not a scan of every
    link on the page, which is what made large files quadratic.
    """
    i = bisect.bisect_left(starts, lo)
    if i > 0 and spans[i - 1][1] > lo:
        i -= 1
    while i < len(spans) and spans[i][0] < hi:
        if spans[i] != mine and spans[i][0] < hi and spans[i][1] > lo:
            return True
        i += 1
    return False


def _search(text: str, start: int, end: int):
    """First size and first usable name inside ``text[start:end]``.

    The window is *sliced* rather than passed to ``finditer`` as pos/endpos.
    That is not a micro-optimisation: with pos/endpos the scanner's cost tracks
    the distance to the end of the string, not the window, so reading a 150-byte
    cell near the top of a 10 MB page measured ~8.5 ms against ~9 us for the
    same cell sliced. Across 50,000 links that is the difference between seconds
    and minutes.
    """
    if start >= end:
        return None, None
    window = _blank_comments(text[start:end])
    size = None
    name = None
    for m in SIZE_RE.finditer(window):
        size = parse_size(m.group(0))
        if size is not None:
            break
    for m in TAG_RE.finditer(window):
        tag_name = m.group(0)[1:].split(None, 1)[0].lower().rstrip("/")
        if tag_name in ("a", "button"):
            continue
        inner = window[m.end() : window.find("<", m.end())]
        inner = inner.replace("&nbsp;", " ").strip()
        if (2 <= len(inner) <= 200 and not _NOT_A_NAME.search(inner)
                and not SIZE_RE.fullmatch(inner)):
            name = _clean_name(inner)
            break
    return size, name


def scrape_meta(
    text: str,
    chain: list[tuple[int, int, int]],
    by_depth: list[list[tuple[int, int]]],
    spans: list[tuple[int, int]],
    starts: list[int],
    match: "re.Match[str]",
    prev_end: int,
    next_start: int,
    window: int,
) -> tuple[int | None, str | None]:
    """The size and name for one magnet.

    Metadata is usually in the same entry as the link — above it, below it, or in
    a cell beside it — so the search starts at the innermost element around the
    link and walks outward, one level at a time. It stops at the first element
    that also contains a *different* magnet: past that point any size found
    would belong to another torrent, and a wrong size is worse than no size.

    If the whole entry is bare, the sibling entry just before it is tried, which
    is how a "metadata row, then link row" listing still pairs up. A following
    sibling is never used.
    """
    size = None
    name = None
    last_safe: tuple[int, int, int] | None = None

    mine = (match.start(), match.end())
    child: tuple[int, int, int] | None = None
    for b_start, b_end, depth in chain:
        if _holds_other(spans, starts, b_start, b_end, mine):
            if child is None:
                # The very element around the link already holds another magnet,
                # so any size nearby is shared and could belong to either link.
                # Guessing would corrupt the estimated total, so report nothing.
                return None, None
            break
        if child is not None:
            # Refuse a parent that spans more than one entry: the part of it
            # outside the child we came from belongs to other rows. The parent's
            # own closing tag is trimmed first, or every parent would look like
            # it ends an entry.
            head = text[b_start:child[0]]
            tail = text[child[1]:b_end]
            cut = tail.rfind("<")
            if cut != -1:
                tail = tail[:cut]
            if ENTRY_BOUNDARY_RE.search(head + tail):
                break
        last_safe = (b_start, b_end, depth)
        b_size, b_name = _search(text, b_start, b_end)
        if b_size is not None:
            return b_size, b_name or name
        if b_name and not name:
            name = b_name
        child = (b_start, b_end, depth)

    if last_safe is not None:
        sibling = sibling_before(last_safe[0], last_safe[2], by_depth)
        if sibling is not None:
            s_start, s_end = sibling
            if not _holds_other(spans, starts, s_start, s_end, (0, 0)):
                s_size, s_name = _search(text, s_start, s_end)
                if s_size is not None:
                    return s_size, s_name or name

    if chain:
        # There was markup and it did not yield a safe region. Trusting a raw
        # character window here is how one entry's size leaks into the next.
        return None, name

    # --- bounded window: no usable markup (plain text, minified dumps) ---
    before_start = max(prev_end, match.start() - window)
    before_start = _after_anchor(text, before_start, match.start()) if prev_end else before_start
    after_limit = min(next_start, match.end() + window)
    after_start = _after_anchor(text, match.end(), after_limit)
    # Never reach past the end of the current entry: a size in a following row
    # belongs to whatever link that row is for, not to this one.
    stop = ENTRY_CLOSE_RE.search(text[after_start:after_limit])
    if stop:
        after_limit = after_start + stop.start()

    def collect(start: int, end: int, side: str):
        if start >= end:
            return []
        edge = match.start() if side == "before" else match.end()
        return _candidates(text[start:end], start, edge, side)

    size = None
    for _closes, _dist, kind, value in sorted(collect(before_start, match.start(), "before")):
        if size is None and kind == "size":
            size = value
        elif name is None and kind == "name":
            name = value
        if size is not None and name:
            break
    if size is None or name is None:
        for _closes, _dist, kind, value in sorted(collect(after_start, after_limit, "after")):
            if size is None and kind == "size":
                size = value
            elif name is None and kind == "name":
                name = value
            if size is not None and name:
                break
    return size, name


def iter_matches_with_size(chunks, source: str = "<input>", window: int = META_WINDOW,
                           want_size: bool = True, counters: dict | None = None):
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
        # Collect first so each link knows where its neighbours are: that is what
        # keeps one entry's metadata from being attributed to the next one.
        found = []
        for m in MAGNET_RE.finditer(text):
            if m.start() >= limit_start:
                break
            found.append(m)

        by_depth: list[list[tuple[int, int]]] = []
        chains: list[list[tuple[int, int, int]]] = [[] for _ in found]
        spans: list[tuple[int, int]] = []
        starts: list[int] = []
        if want_size and found:
            spans = [(x.start(), x.end()) for x in found]
            starts = [a for a, _b in spans]
            chains, by_depth = analyze_blocks(text, starts)

        for i, m in enumerate(found):
            uri = normalize(m.group(0))
            info = classify(uri)
            if info is None:
                # Looked like a magnet but did not validate. Silent dropping is
                # how a hand-edited list loses a link nobody notices, so count it.
                if counters is not None:
                    counters["rejected"] = counters.get("rejected", 0) + 1
                continue
            infohash, version = info
            magnet = build(uri, infohash, version)
            magnet.sources = [source]
            if want_size:
                prev_end = found[i - 1].end() if i > 0 else 0
                next_start = found[i + 1].start() if i + 1 < len(found) else len(text)
                size, name = scrape_meta(
                    text,
                    chains[i],
                    by_depth,
                    spans,
                    starts,
                    m,
                    prev_end,
                    next_start,
                    window,
                )
                if magnet.size is None:
                    magnet.size = size
                if not magnet.name and name:
                    magnet.name = name
                    magnet.name_source = "page"
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
    # Only widen the table when there is something to report, so a clean run
    # reads the same as it always has.
    any_rejected = any(getattr(s, "rejected", 0) for s in stats)
    rej_head = f" {'BAD':>5}" if any_rejected else ""
    lines = [
        f"{'SOURCE':<{name_w}}  {'RAW':>7} {'UNIQUE':>7} {'DUPES':>6} {'SIZED':>6} "
        f"{'EST. TOTAL':>11}{rej_head}",
        "-" * (name_w + 2 + 7 + 1 + 7 + 1 + 6 + 1 + 6 + 1 + 11 + (6 if any_rejected else 0)),
    ]
    for s in stats:
        total = sum(m.size for m in s.magnets if m.size is not None)
        sized = sum(1 for m in s.magnets if m.size is not None)
        rej_cell = f" {getattr(s, 'rejected', 0):>5}" if any_rejected else ""
        lines.append(
            f"{s.label:<{name_w}}  {s.raw:>7} {s.unique:>7} {s.raw - s.unique:>6} "
            f"{sized:>6} {human_size(total) if sized else '-':>11}{rej_cell}"
        )
    if any_rejected:
        bad = sum(getattr(s, "rejected", 0) for s in stats)
        lines.append(
            f"\nBAD {bad}: string(s) starting magnet:? that did not hold a valid "
            "BitTorrent infohash, so they were not added."
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
    ap.add_argument(
        "--hints",
        action="store_true",
        help="keep xt and the tr= tracker hints, drop dn and everything else. "
        "The middle ground between --bare and the full link: bare links have to "
        "find peers on the DHT alone, which is what leaves a torrent sitting at "
        "\"Downloading metadata\"",
    )
    ap.add_argument(
        "--trackers-file",
        metavar="FILE",
        help="append tracker hints from FILE (one tracker per line, # comments ok) "
        "to magnets that have none. Use with --hints for pages whose links carry no tr=",
    )
    ap.add_argument(
        "--trackers-url",
        metavar="URL",
        help="same as --trackers-file but fetched over HTTP, e.g. the ngosang "
        "trackerslist trackers_all.txt",
    )
    ap.add_argument(
        "--max-trackers",
        type=int,
        default=5,
        metavar="N",
        help="cap trackers per magnet when using --trackers-file/--trackers-url "
        "(default 5, 0 = no cap)",
    )
    ap.add_argument(
        "--bare",
        "--minimal",
        dest="bare",
        action="store_true",
        help="emit only magnet:?xt=urn:btih:HASH — no dn, no trackers, nothing added. "
        "Supersedes --strip-trackers",
    )
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
        counters: dict[str, int] = {}

        for m in iter_matches_with_size(chunks, source, counters=counters):
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
        entry.rejected = counters.get("rejected", 0)
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

    augmented = 0
    if args.trackers_file or args.trackers_url:
        try:
            trackers = load_trackers(args.trackers_file, args.trackers_url, args.timeout)
        except (OSError, ValueError, urllib.error.URLError) as exc:
            print(f"warning: could not load tracker list: {exc}", file=sys.stderr)
            trackers = []
        if trackers:
            augmented = augment_trackers(merged, trackers, args.max_trackers)
            # --out-dir writes from the per-source magnets, which rebuild_with_sources
            # made into separate objects. Visit those too, or the written files
            # silently disagree with what --plain prints. Skipped for anything already
            # handled, so the flat (--no-dedupe) path is not counted twice.
            seen = {id(m) for m in merged}
            extra = [m for entry in stats for m in entry.magnets if id(m) not in seen]
            if extra:
                augment_trackers(extra, trackers, args.max_trackers)
    if args.bare:
        uri_of = lambda m: m.bare_uri  # noqa: E731
    elif args.hints:
        uri_of = lambda m: m.hints_uri  # noqa: E731
    elif args.strip_trackers:
        uri_of = lambda m: m.clean_uri  # noqa: E731
    else:
        uri_of = lambda m: m.uri  # noqa: E731

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
                    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
                        fh.write("\n".join(chunk) + "\n")
                    print(f"{dest}  {len(chunk)} magnet(s)", file=sys.stderr)
                    written += 1
            else:
                dest = os.path.join(args.out_dir, f"{stem}.txt")
                with open(dest, "w", encoding="utf-8", newline="\n") as fh:
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

    if augmented:
        # stderr, so --plain stdout stays a clean list to paste or pipe
        print(f"tracker hints added to {augmented} of {len(merged)} magnet(s)", file=sys.stderr)

    for err in errors:
        print(f"warning: {err}", file=sys.stderr)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
