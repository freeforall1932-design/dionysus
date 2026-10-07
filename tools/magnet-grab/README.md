# magnet-grab

Pull every magnet link out of saved HTML and hand it to a torrent client.
Stdlib only — no BeautifulSoup, no `requests`, nothing to install.

```bash
./magnet_grab.py page.html                # what was found
./magnet_grab.py page.html --plain        # one per line -> paste into qBittorrent
./magnet_grab.py saved_pages/ --plain > m.txt
cat page.html | ./magnet_grab.py -
./magnet_grab.py page.html --add          # POST straight to the qBittorrent WebUI
./magnet_grab.py --url https://site/list  # fetch and extract in one go
```

## Why not just `grep -o 'magnet:...'`

A one-liner looks like it works and quietly loses links:

| Trap in real saved HTML | Naive regex | magnet-grab |
|---|---|---|
| `&` is written as `&amp;`, so the URI is cut at the first tracker | truncated | unescaped, full URI kept |
| magnet inside `<script>var m = "..."` | often missed | found |
| magnet in a `data-*` attribute | often missed | found |
| `MAGNET:` uppercase | missed | found |
| v1 base32 or v2 `btmh` multihash hashes | missed | found, version reported |
| same torrent listed 3× on the page | 3 pastes | 1, deduped by infohash |
| page saved as gzip, or in cp1252 | garbage | transparent |

## Multiple sources, thousands of links each

Point it at several saved pages at once. It keeps per-source tallies and merges
across them by infohash.

```bash
./magnet_grab.py pages/ --summary              # what each source held, and the overlap
./magnet_grab.py pages/ --out-dir lists/       # one paste-ready .txt per source
./magnet_grab.py pages/ --plain > all.txt      # merged, deduped across every source
```

`--summary`:

```
SOURCE            RAW  UNIQUE  IN-SRC DUPES
-------------------------------------------
small.html        500     500             0
large.html       5500    5000           500
huge.html       55000   50000          5000

CROSS-SOURCE
------------------------------------------
unique across all sources    50000
in 2+ sources     5000
exclusive to huge.html    45000
```

`RAW` is every magnet URI matched; `UNIQUE` is after collapsing repeats within
that file; `IN-SRC DUPES` is how many the page listed more than once. The
cross-source block tells you how much your sources actually overlap.

When one hash appears in several sources, `--pick richest` (default) keeps the
URI carrying the most information — usually the fullest tracker list — and
records *every* source it was seen in. `--pick first` keeps the first seen.

## Output modes

- **default** — table of name, BitTorrent version, infohash, source. Capped at
  50 rows on purpose; `--limit 0` shows all
- `--plain` / `-1` — bare magnet URIs, one per line. This is what you paste into
  qBittorrent's *File → Add Torrent Link* (Ctrl+Shift+O), which accepts many at once
- `--out-dir DIR` — one paste-ready `.txt` per source file, named after the source
- `--summary` — the per-source and cross-source report above
- `--json` — structured; each record carries the full `sources` list
- `--strip-trackers` — drop `tr=` params, keep `xt`/`dn` (qBittorrent substitutes its own list)
- `--filter REGEX` — keep only magnets whose name matches (case-insensitive)
- `--no-dedupe` — keep every occurrence, within and across files

## Scale

Measured on this machine: 50,000 magnets out of an 18 MB page in ~2.5 s, ~190 MB
peak RSS. Four sources totalling 66,000 raw links in ~2.6 s. Stdlib only, single pass.

## Pushing straight to qBittorrent

```bash
export QBT_HOST=http://localhost:8080 QBT_USER=admin QBT_PASS=secret

# one source at a time, into its own category
./magnet_grab.py pages/source-a.html --add --category source-a --savepath /downloads/a
# or everything merged, 500 at a time so the client is not slammed
./magnet_grab.py pages/ --add --batch 500 --batch-delay 2
```

With thousands of links, use `--batch`: verified 500 magnets arrive as three
requests of 200/200/100 rather than one giant POST.

Logs in at `/api/v2/auth/login`, then POSTs the magnets as newline-separated `urls`
to `/api/v2/torrents/add` (multipart form-data), which is the same shape the WebUI
itself sends. Works against qBittorrent 4.1+ WebAPI v2.

## Validation

`magnet_grab.py` only emits links carrying a well-formed infohash — v1 40-hex,
v1 32-char base32, or v2 `urn:btmh:1220` + 64 hex. So `class="magnet-link"`,
`magnet:?xt=urn:ed2k:...`, truncated hashes and `magnet:?dn=nohash` are all rejected
rather than pasted into your client.

## Tests

```bash
python3 -m unittest test_magnet_grab -v
```

39 tests covering extraction, rejection, encodings, CLI behaviour and the
qBittorrent login + multipart add path and batch chunking (run against a mock WebUI, so no client needed).

## Alternatives worth knowing

- **FlexGet** — the `html` input with `links_re: [magnet]` plus a `qbittorrent:` output
  automates this end to end on a schedule. Note it fetches the page itself over HTTP;
  it cannot read a saved local HTML file.
- **Browser extensions** (`magnet-link-grabber`, Magnet Collector) — do this on live
  pages across open tabs, but not on saved files.
- **Jackett + qBittorrent RSS** — better fit if what you actually want is
  "search trackers and auto-add", not "parse pages I already saved".
