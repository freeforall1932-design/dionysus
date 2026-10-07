# magnet-grab

Pull every magnet link out of saved pages and hand them to a torrent client.
Stdlib only — no BeautifulSoup, no `requests`, nothing to install.

```bash
./magnet_grab.py page.html                 # what was found
./magnet_grab.py pages/ --summary          # per-source counts, overlap, size totals
./magnet_grab.py pages/ --out-dir lists/   # one paste-ready .txt per source
./magnet_grab.py pages/ --plain > all.txt  # merged, deduped across every source
./magnet_grab.py pages/ --add --batch 500  # POST straight to the qBittorrent WebUI
```

## Any file, not just HTML

Every file is scanned as raw text — no extension filter. `.txt`, `.mhtml`, a
log, a JSON dump, a weird `.xyz123`, or a binary blob with a magnet embedded all
work. Matching is restricted to the printable-ASCII characters a URI may contain,
so a link inside binary data stops cleanly at the first null byte instead of
dragging garbage with it. Gzip is transparent.

Files stream in 1 MiB chunks, so a huge dump costs ~130 MB rather than the size
of the file. A link straddling a chunk boundary is re-found whole on the next
pass. `--ext html` restricts a directory walk if you want that; a file you name
explicitly is always attempted, so a typo is an error rather than a silent skip.

## Multiple sources, thousands of links each

```
SOURCE            RAW  UNIQUE  DUPES  SIZED  EST. TOTAL
-------------------------------------------------------
index_a.html      400     400      0    400   791.3 GiB
index_b.html      350     350      0    350   784.9 GiB

CROSS-SOURCE
unique across all sources      750
in 2+ sources        0
exclusive to index_a.html      400

ESTIMATED TOTAL (merged, deduped)
links with a size                       750 / 750
total (human)                       1.5 TiB
largest single link                 9.0 GiB  Ubuntu.24.04.Desktop.230
```

`RAW` is every magnet URI matched; `UNIQUE` is after collapsing repeats within
that file; `DUPES` is how many the page itself listed twice; `SIZED` is how many
got a size scraped. The cross-source block shows how much your sources overlap.

When one hash appears in several sources, `--pick richest` (default) keeps the
URI carrying the most information — usually the fullest tracker list — and
records *every* source it was seen in. `--pick first` keeps the first seen.

## Estimating total size

A magnet URI carries **no file size**. BEP 9 defines only
`xt` (the hash), `dn` (display name), `tr` (trackers) and `x.pe` (peer hint).
Size only becomes known once the client fetches the info dictionary from a peer
via `ut_metadata` — which is why qBittorrent shows "downloading metadata" first.

So there are exactly two ways to know the size *before* adding anything:

1. **Scrape it from the page**, which is what this does. Index pages list the
   size beside each link; the text following each magnet is read up to the end of
   the enclosing `<tr>`, so a size in the next row is never misattributed. Units
   are read as 1024-based, because that is what index sites mean by MB/GB —
   reporting a "1 MB" torrent as "976.6 KiB" would be more confusing than useful.
2. **The legacy `xl=` parameter**, from the pre-BEP-9 magnet draft. Almost no
   site emits it, but when present it is authoritative, so it wins over scraping.

`SIZED` in the summary is the honest hit rate. On pages whose markup puts the
size somewhere unusual it will be low, and the total is then only partial —
the count tells you how much to trust it.

```bash
./magnet_grab.py pages/ --min-size 5GB --max-size 20GB --plain   # filter first
./magnet_grab.py pages/ --json | jq '.[].size'                   # pipe the sizes
```

## Why not just `grep -o 'magnet:...'`

A one-liner looks like it works and quietly loses links:

| Trap in real saved pages | Naive regex | magnet-grab |
|---|---|---|
| `&` written as `&amp;`, so the URI is cut at the first tracker | truncated | unescaped, full URI kept |
| magnet inside `<script>` or a JSON string | often missed | found |
| magnet preceded by a letter (`"url":"magnet:`) | often missed | found |
| `MAGNET:` uppercase | missed | found |
| v1 base32 or v2 `btmh` multihash hashes | missed | found, version reported |
| magnet inside a binary file | garbage appended | stops at the null byte |
| same torrent listed 3× on the page | 3 pastes | 1, deduped by infohash |
| page saved as gzip, or in cp1252 | garbage | transparent |
| link split across a read buffer | lost | re-found whole |

## Output modes

- **default** — table of name, size, BitTorrent version, infohash, source.
  Capped at 50 rows; `--limit 0` shows all
- `--plain` / `-1` — bare magnet URIs, one per line. This is what you paste into
  qBittorrent's *File → Add Torrent Link* (Ctrl+Shift+O), which accepts many at once
- `--out-dir DIR` — one paste-ready `.txt` per source, named after the source
- `--summary` — the per-source, cross-source and size report above
- `--json` — structured; each record carries `size_bytes`, `size` and `sources`
- `--strip-trackers` — drop `tr=` params, keep `xt`/`dn` (qBittorrent substitutes its own list)
- `--filter REGEX` — keep only magnets whose name matches (case-insensitive)
- `--no-dedupe` — keep every occurrence, within and across files

## Pushing to qBittorrent

```bash
export QBT_HOST=http://localhost:8080 QBT_USER=admin QBT_PASS=secret

./magnet_grab.py pages/index-a.html --add --category index-a --savepath /downloads/a
./magnet_grab.py pages/ --add --batch 500 --batch-delay 2
```

Logs in at `/api/v2/auth/login`, then POSTs newline-separated `urls` to
`/api/v2/torrents/add` (multipart form-data), the same shape the WebUI sends.
qBittorrent 4.1+ WebAPI v2. Use `--batch` for thousands of links.

## Validation

Only links carrying a well-formed infohash are emitted — v1 40-hex, v1 32-char
base32, or v2 `urn:btmh:1220` + 64 hex. So `class="magnet-link"`,
`magnet:?xt=urn:ed2k:...`, truncated hashes and `magnet:?dn=nohash` are rejected
rather than pasted into your client.

## Scale

Measured here: 50,000 magnets from an 18 MB page in ~2.9 s, ~137 MB peak RSS.
Two sources totalling 750 links with sizes in well under a second.

## Tests

```bash
python3 -m unittest test_magnet_grab -v
```

52 tests covering extraction, rejection, encodings, chunk-boundary streaming,
any-extension scanning, binary safety, size parsing and filters, CLI behaviour,
and the qBittorrent login + multipart add path with batch chunking (against a
mock WebUI, so no client is needed).

## Alternatives worth knowing

- **FlexGet** — the `html` input with `links_re: [magnet]` plus a `qbittorrent:`
  output automates this end to end on a schedule. Note it fetches the page itself
  over HTTP; it cannot read a saved local file, and it only looks at `<a href>`,
  so magnets in scripts or `data-*` attributes are missed.
- **Browser extensions** (Magnet Link Grabber, Magnet Collector) — live pages and
  open tabs, not saved files.
- **Jackett + qBittorrent RSS** — better fit if what you want is "search trackers
  and auto-add", not "parse pages I already saved".
