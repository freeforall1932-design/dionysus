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

## Output modes

- **default** — a table of name, BitTorrent version, infohash, source file
- `--plain` / `-1` — bare magnet URIs, one per line. This is what you paste into
  qBittorrent's *File → Add Torrent Link* (Ctrl+Shift+O), which accepts many at once
- `--json` — structured, good for piping elsewhere
- `--strip-trackers` — drop `tr=` params, keep `xt`/`dn` (qBittorrent substitutes its own list)
- `--filter REGEX` — keep only magnets whose name matches (case-insensitive)
- `--no-dedupe` — keep every occurrence instead of collapsing by infohash

## Pushing straight to qBittorrent

```bash
export QBT_HOST=http://localhost:8080 QBT_USER=admin QBT_PASS=secret
./magnet_grab.py page.html --add --savepath /downloads/tv --category tv --paused
```

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

31 tests covering extraction, rejection, encodings, CLI behaviour and the
qBittorrent login + multipart add path (run against a mock WebUI, so no client needed).

## Alternatives worth knowing

- **FlexGet** — the `html` input with `links_re: [magnet]` plus a `qbittorrent:` output
  automates this end to end on a schedule. Note it fetches the page itself over HTTP;
  it cannot read a saved local HTML file.
- **Browser extensions** (`magnet-link-grabber`, Magnet Collector) — do this on live
  pages across open tabs, but not on saved files.
- **Jackett + qBittorrent RSS** — better fit if what you actually want is
  "search trackers and auto-add", not "parse pages I already saved".
