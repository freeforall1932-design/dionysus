# Magnet Excavator

Pull every magnet link out of saved pages and hand them to a torrent client.
Stdlib only — no BeautifulSoup, no `requests`, nothing to install.

**New here?** Start with [WALKTHROUGH.md](WALKTHROUGH.md) — a raw messy file all
the way to a running download, with real output at every step.

Prefer clicking to typing? There is a GUI:

```bash
python3 magnet_excavator_gui.py        # opens http://127.0.0.1:8765
```

## GUI

A local web app — drag files onto the page, get a clean list, push it to
qBittorrent. Standard library only, same as the CLI, and it imports
`magnet_excavator.py` so the two cannot disagree about what a magnet is.

```bash
python3 magnet_excavator_gui.py                    # 127.0.0.1:8765, opens a browser
python3 magnet_excavator_gui.py --port 9000
python3 magnet_excavator_gui.py --host 0.0.0.0     # reachable from another machine
python3 magnet_excavator_gui.py --no-browser       # do not auto-open
```

**It needs a browser.** The GUI is a local web server plus one HTML page, so it
opens in whatever browser you already have. There is no native window and no
third-party toolkit — that is deliberate, because it keeps the whole tool in the
Python standard library with nothing to install on Windows, macOS or Linux. The
trade-off is that a browser has to be running; if you would rather not have one,
the CLI does everything the page does and more.

What it does:

- **Drag and drop** — multiple files, any format, dropped anywhere on the page
- **…or a path** — a file or directory on the same machine, so you never have to
  upload a large page
- **Options** — bare links, hints (xt + trackers), strip trackers, an optional
  tracker list file or URL, dedupe, name filter, min/max size
- **Results** — name, size, BitTorrent version, infohash, source, duplicates
  dropped, and a **Name from** column marking whether each name came from the
  URI (`uri`, trustworthy) or was scraped off the markup (`page`, a best guess)
- **Copy list / Copy bare / Copy hints** — into the qBittorrent dialog
- **Download .txt**, optionally **split into files of N links** for a client that
  balks at thousands at once
- **Add to qBittorrent** — host, credentials, category, save path, batch size,
  and **Max active**: the same queue-aware feeding as the CLI's `--max-active`.
  Set it and the page adds only into the free headroom, then waits and tops up,
  instead of dumping thousands in and starving the queue. Progress updates live
  while it runs
- **Test connection** — really logs in and reports the qBittorrent version and
  how many torrents are downloading now, so you know what headroom you have

Files never leave your machine: the page talks only to the local server, and the
local server only to the qBittorrent host you type in.

Two things to know:

- It binds `127.0.0.1` by default. `--host 0.0.0.0` exposes it on your network,
  and the add endpoint will then accept requests from anyone who can reach that
  port — only do that on a network you trust.
- The browser sends file contents to the local server as base64, so a very large
  page costs roughly 1.3× its size in transit. For big dumps, use the path field
  or the CLI instead.

```bash
./magnet_excavator.py page.html                 # what was found
./magnet_excavator.py pages/ --summary          # per-source counts, overlap, size totals
./magnet_excavator.py pages/ --out-dir lists/   # one paste-ready .txt per source
./magnet_excavator.py pages/ --plain > all.txt  # merged, deduped across every source
./magnet_excavator.py pages/ --add --batch 500  # POST straight to the qBittorrent WebUI
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

1. **Scrape it from the page**, which is what this does. Units are read as
   1024-based, because that is what index sites mean by MB/GB — reporting a
   "1 MB" torrent as "976.6 KiB" would be more confusing than useful.

   Pairing the size with the *right* link is the hard part, and it cannot be
   done by measuring characters. A listing that puts the size **above** its link
   and one that puts it **below** are mirror images of each other, so "nearest
   value wins" shifts the whole list by one in one of them — the first link gets
   nothing and every later link takes the previous entry's size. Instead the
   page's own structure decides: one tag-stack pass records the nesting around
   every magnet, and the search starts at the innermost element and walks
   outward until it finds a size. It stops at the first element that also
   contains a *different* magnet, and refuses a parent that spans more than one
   entry, so a size never travels across an entry boundary. A preceding sibling
   row is still used (a metadata row followed by a link row); a following one
   never is. Where the entry is genuinely ambiguous — one size, two links — it
   reports nothing rather than guess, because a wrong size corrupts the total.
   Pages with no usable markup fall back to a short window bounded by the
   neighbouring links. Sizes inside HTML comments are ignored throughout: a
   commented-out row is not a size the page is publishing, and counting one
   would quietly inflate the total.

   The same pass supplies the **name** when the URI has no `dn=`, skipping
   anchor captions so "Download" and "get" are not mistaken for titles.
   `.name_source` records whether a name came from `dn` or from the page.
2. **The legacy `xl=` parameter**, from the pre-BEP-9 magnet draft. Almost no
   site emits it, but when present it is authoritative, so it wins over scraping.

`SIZED` in the summary is the honest hit rate. On pages whose markup puts the
size somewhere unusual it will be low, and the total is then only partial —
the count tells you how much to trust it.

```bash
./magnet_excavator.py pages/ --min-size 5GB --max-size 20GB --plain   # filter first
./magnet_excavator.py pages/ --json | jq '.[].size'                   # pipe the sizes
```

## Why not just `grep -o 'magnet:...'`

A one-liner looks like it works and quietly loses links:

| Trap in real saved pages | Naive regex | Magnet Excavator |
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
- `--bare` / `--minimal` — only `magnet:?xt=urn:btih:HASH`, nothing else. No
  display name, no trackers, no `xl`. Everything in a magnet besides `xt` is
  decoration or a hint — the client resolves the name and finds peers itself —
  so this is the shortest string that still works. Longest line on the example
  file drops from 193 characters to 88. Dual v1+v2 links keep both hashes.
  Supersedes `--strip-trackers`
- `--out-dir DIR` — one paste-ready `.txt` per source, named after the source
- `--summary` — the per-source, cross-source and size report above
- `--json` — structured; each record carries `size_bytes`, `size` and `sources`
- `--hints` — keep `xt` and the `tr=` tracker hints, drop `dn` and everything
  else. The middle ground between `--bare` and the full link. A bare magnet has
  to find peers on the DHT alone, which is what leaves a torrent sitting at
  *Downloading metadata*; this keeps the hints that fix that without the name
- `--trackers-file FILE` / `--trackers-url URL` — append tracker hints to magnets
  that have **none** of their own, one tracker per line, `#` comments ignored.
  This is the ngosang/trackerslist format, so a downloaded `trackers_all.txt`
  can be pointed at directly. Pages that publish magnets with no `tr=` are
  common, and for those `--hints` alone is no better than `--bare`. Only
  trackerless magnets are touched: a page that supplied trackers knew which ones
  that torrent is on
- `--max-trackers N` — cap how many are added per magnet (default 5, `0` = no cap)
- `--strip-trackers` — drop `tr=` params, keep `xt`/`dn` (qBittorrent substitutes its own list)
- `--filter REGEX` — keep only magnets whose name matches (case-insensitive)
- `--no-dedupe` — keep every occurrence, within and across files

## Getting thousands of links into a client

Pasting is the easy part. qBittorrent's *File → Add Torrent Link* (Ctrl+Shift+O)
takes many URLs at once, one per line — hundreds is fine. The problem is what
happens next: every magnet sits at **"Downloading metadata"** until a peer
answers, and qBittorrent counts those against its active-download limit. Paste
thousands and the GUI locks up while it resolves them, and dead magnets can sit
there indefinitely holding queue slots.

So the bottleneck is resolution, not the paste. Three ways to handle it:

### 1. Feed the queue (recommended)

`--max-active` adds only into the space the client actually has, then polls and
tops up as torrents start and finish:

```bash
./magnet_excavator.py pages/ --add --max-active 40 --batch 10 --poll-interval 60
```

```
  38 downloading, holding at --max-active 40; retrying in 60s (4960 queued)
  added 512/5000 (4488 left)
```

This runs unattended. Ctrl+C reports how many went in and how many did not.

### 2. Split into paste-sized files

```bash
./magnet_excavator.py pages/ --out-dir lists/ --split 100
```

Writes `index_a.part01.txt`, `index_a.part02.txt`, … each holding 100 links —
small enough to paste into the dialog by hand and let the queue absorb.

### 3. Plain batching

```bash
./magnet_excavator.py pages/ --add --batch 500 --batch-delay 5
```

Verified: 500 magnets arrive as three requests of 200/200/100 rather than one
giant POST.

### Other clients

- **Transmission** — no bulk add, and its watch folder ignores magnets. Loop
  `transmission-remote --add` over a `--plain` list:
  `./magnet_excavator.py pages/ --plain | while read -r l; do transmission-remote -a "$l"; done`
- **Deluge** — the watch folder *does* pick up `.magnet` files, so split a list
  into one-magnet-per-file and drop them in
- **ruTorrent** — still has no bulk import ([issue #1966](https://github.com/Novik/ruTorrent/issues/1966),
  open since 2019); use its RPC or the API path instead

Whichever client: set its active-download limit low and let the queue do the
pacing. Adding everything at once is never faster than adding it steadily.

## Pushing to qBittorrent

```bash
export QBT_HOST=http://localhost:8080 QBT_USER=admin QBT_PASS=secret

./magnet_excavator.py pages/index-a.html --add --category index-a --savepath /downloads/a
```

Logs in at `/api/v2/auth/login`, then POSTs newline-separated `urls` to
`/api/v2/torrents/add` (multipart form-data), the same shape the WebUI sends.
qBittorrent 4.1+ WebAPI v2. `--max-active` polls
`/api/v2/torrents/info?filter=downloading`.

## Validation

Only links carrying a well-formed infohash are emitted — v1 40-hex, v1 32-char
base32, or v2 `urn:btmh:1220` + 64 hex. So `class="magnet-link"`,
`magnet:?xt=urn:ed2k:...`, truncated hashes and `magnet:?dn=nohash` are rejected
rather than pasted into your client.

## Scale

Tuned for 1-10 MB saved pages, which is what you actually deal with. Files read
in 16 MiB chunks, so anything that size is a single pass and never touches the
chunk-boundary logic at all — that code stays only as a safety net for an
oversized dump. Measured anyway: 50,000 magnets from an 18 MB page in ~2.9 s,
~137 MB peak RSS.

## Tests

```bash
python3 -m unittest discover -s . -p 'test_*.py' -v
```

132 tests — 102 for the CLI and 30 for the GUI backend — covering extraction, rejection, encodings, chunk-boundary streaming,
any-extension scanning, binary safety, size parsing and filters, CLI behaviour,
and the qBittorrent login + multipart add path with batch chunking and
queue-aware feeding, and the GUI's extract/add endpoints and batching
(against a mock WebUI, so no client is needed).

## Alternatives worth knowing

- **FlexGet** — the `html` input with `links_re: [magnet]` plus a `qbittorrent:`
  output automates this end to end on a schedule. Note it fetches the page itself
  over HTTP; it cannot read a saved local file, and it only looks at `<a href>`,
  so magnets in scripts or `data-*` attributes are missed.
- **Browser extensions** (Magnet Link Grabber, Magnet Collector) — live pages and
  open tabs, not saved files.
- **Jackett + qBittorrent RSS** — better fit if what you want is "search trackers
  and auto-add", not "parse pages I already saved".
