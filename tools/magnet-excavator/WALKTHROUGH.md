# From a raw file to a running download

A walkthrough against `examples/raw_dump.txt` — a deliberately messy file:
HTML with escaped entities, a JSON blob in a `<script>`, plain prose, a CSS class
named `magnet-link`, an `ed2k` link, a broken hash, a `data-*` attribute, a
duplicate, a BitTorrent v2 link, base64 noise, and a magnet buried in binary.

Every command and number below is copied from a real run.

## 0. Get the tool

Nothing to install — standard library only, Python 3.9+.

```bash
cd tools/magnet-excavator
python3 magnet_excavator.py --help
```

## 1. Look at what it found

```bash
python3 magnet_excavator.py examples/raw_dump.txt
```

```
NAME                             SIZE  VER INFOHASH                                  SRC
-------------------------------------------------------------------------------------------
(unnamed)                           -  v1  0000000000000000000000000000000000000008  examples/raw_dump.txt
Ubuntu 24.04 Desktop amd64    4.7 GiB  v1  0000000000000000000000000000000000000001  examples/raw_dump.txt
Fedora Workstation 41         2.3 GiB  v1  0000000000000000000000000000000000000002  examples/raw_dump.txt
Blender 4.2 LTS             340.0 MiB  v1  0000000000000000000000000000000000000003  examples/raw_dump.txt
Hidden In Data Attribute            -  v1  0000000000000000000000000000000000000004  examples/raw_dump.txt
Inside A JSON Blob                  -  v1  0000000000000000000000000000000000000005  examples/raw_dump.txt
Also In JSON                        -  v1  0000000000000000000000000000000000000006  examples/raw_dump.txt
Buried In Binary                    -  v1  0000000000000000000000000000000000000007  examples/raw_dump.txt
BitTorrent v2                       -  v2  caf1e1c30e81cb361b9ee167c4aa64228a7fa4fa9f6105232b28ad099f3a302e  examples/raw_dump.txt
```

Nine links, from nine different hiding places. The CSS class, the `ed2k` link,
the truncated hash, the ordinary `https://` link and the base64 noise are all
absent — they never had a valid BitTorrent infohash.

## 2. Get the clean list

```bash
python3 magnet_excavator.py examples/raw_dump.txt --plain > magnets.txt
```

One magnet per line, nothing else. Schemes and parameter names are normalised to
lowercase (a link written `MAGNET:?XT=URN:BTIH:` becomes `magnet:?xt=urn:btih:`,
because parameter *names* are case-sensitive even though schemes are not), and
display names are left exactly as written.

### How much of the link do you want?

```bash
python3 magnet_excavator.py examples/raw_dump.txt --plain                 # full
python3 magnet_excavator.py examples/raw_dump.txt --plain --strip-trackers
python3 magnet_excavator.py examples/raw_dump.txt --plain --hints
python3 magnet_excavator.py examples/raw_dump.txt --plain --bare
```

Taking the Ubuntu line (the fixture's first link is a bare hash buried in prose,
so it looks the same in every mode):

```
default            magnet:?xt=urn:btih:0000…0001&dn=Ubuntu+24.04+Desktop+amd64&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce
--strip-trackers   magnet:?xt=urn:btih:0000…0001&dn=Ubuntu+24.04+Desktop+amd64
--hints            magnet:?xt=urn:btih:0000…0001&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce
--bare             magnet:?xt=urn:btih:0000000000000000000000000000000000000001
```

Longest line across the file: **193 → 105 → 163 → 88 characters**. Note that
`--hints` is *longer* than `--strip-trackers` here — a tracker URL outweighs a
display name. The modes differ in what they keep, not in how short they are.

`--bare` keeps only `xt`, which is the part that actually identifies the
torrent. Everything else is a hint the client re-derives anyway — the name comes
back from the metadata, and trackers are found via DHT. Use it when you want the
smallest, cleanest list to paste, pipe, or diff. Dual v1+v2 links keep both
hashes. It works with `--add` and `--out-dir` too, and supersedes
`--strip-trackers`.

### If bare links sit at "Downloading metadata"

That is the trade-off showing up. A bare link gives the client no tracker hints,
so it has to find peers on the DHT alone. For anything dead or obscure that can
take a very long time, or never finish — qBittorrent has no timeout on metadata
resolution, so those torrents keep holding a download slot.

`--hints` is the middle option: it keeps `xt` and the `tr=` tracker hints and
drops only `dn`. You lose the pretty name (which the client recovers from the
metadata anyway) but keep the part that actually gets peers.

Some pages publish magnets with **no** `tr=` at all. For those `--hints` is no
better than `--bare`, so add a tracker list:

```bash
# one tracker per line, # comments ignored - the ngosang/trackerslist format
python3 magnet_excavator.py pages/ --hints --plain \
  --trackers-url https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt

# or a file you already have
python3 magnet_excavator.py pages/ --hints --plain --trackers-file trackers_all.txt
```

Only magnets with no tracker of their own are touched — a page that supplied
trackers knew which ones that torrent is on — and `--max-trackers` (default 5)
caps how many are added so the list stays pasteable.

| mode | keeps | use it when |
|---|---|---|
| `--bare` | `xt` | you want the shortest list and the torrents are healthy |
| `--hints` | `xt` + `tr` | bare links stall at *Downloading metadata* |
| `--strip-trackers` | `xt` + `dn` | you want names in the client and qBittorrent substitutes its own tracker list |
| default | everything | you want exactly what the page published |

## 3. Check it before you trust it

```bash
wc -l magnets.txt                                  # 9   lines out
grep -c '^magnet:?' magnets.txt                    # 9   all well-formed
grep -oP 'bt(ih|mh):\K[0-9a-f]+' magnets.txt | sort -u | wc -l   # 9 unique hashes
grep -c '&amp;' magnets.txt                        # 0   no unescaped entities left
grep -c '^[A-Z]' magnets.txt                       # 0   no uppercase schemes left
```

All three counts agree at 9. If lines and unique hashes ever disagree, a
duplicate slipped through; if the `&amp;` or uppercase counts are non-zero,
something was not normalised. Longest line here is 193 characters — normal for a
link carrying a couple of trackers.

## 4. See what it will cost you

```bash
python3 magnet_excavator.py examples/raw_dump.txt --summary
```

```
SOURCE            RAW  UNIQUE  DUPES  SIZED  EST. TOTAL
-------------------------------------------------------
raw_dump.txt       11       9      2      3       7.3 GiB

ESTIMATED TOTAL (merged, deduped)
links with a size                         3 / 9
links with no size found                  6
total (human)                       7.3 GiB
largest single link                 4.7 GiB  Ubuntu 24.04 Desktop amd64
```

`RAW 11` means 11 magnet URIs were physically present; `DUPES 2` is the page
listing two of them twice. `SIZED 3 / 9` is the honest scrape rate — only the
three links sitting in a table row with a size column got one. A magnet URI
carries no size, so a link in a JSON blob or in prose simply has none, and the
tool says so rather than guessing.

## 5. Narrow it down

```bash
python3 magnet_excavator.py examples/raw_dump.txt --filter 'ubuntu|fedora' --plain
python3 magnet_excavator.py examples/raw_dump.txt --min-size 1GB --plain
```

`--filter` matches the display name, case-insensitively. Size filters need a
scraped size; add `--keep-unknown-size` to retain links whose size is unknown.

## 6a. Feed it straight into qBittorrent

Turn on the WebUI first: **Tools → Options → Web User Interface → enable**, set a
username and password, note the port (default 8080).

```bash
export QBT_HOST=http://localhost:8080 QBT_USER=admin QBT_PASS=yourpassword

python3 magnet_excavator.py examples/raw_dump.txt --add \
    --category excavated --savepath /downloads/from-html \
    --max-active 4 --batch 3
```

```
added 3/9 (6 left)
  added 6/9 (3 left)
  added 9/9 (0 left)
added 9 magnet(s) to http://127.0.0.1:38709
```

It logs in, then adds only into the space the client actually has. `--max-active`
polls `torrents/info?filter=downloading` and tops up as torrents start and
finish, so you can point it at 50,000 links and walk away. Ctrl+C reports what
went in and what did not.

For a one-shot dump with no pacing, drop `--max-active` and use
`--batch 500 --batch-delay 5`.

## 6b. Or paste it yourself

```bash
python3 magnet_excavator.py examples/raw_dump.txt --out-dir lists/ --split 100
```

Writes part files of 100 links each, sized to paste into *File → Add Torrent
Link* (Ctrl+Shift+O) one at a time.

## 6c. Or write the list, then feed that file back

The `.txt` files are plain magnet lists, and the tool reads plain text — so the
output of one run is valid input to the next. Useful when you want to eyeball or
edit the list before committing it, or keep it as a record of what you added.

```bash
# step 1: extract to one .txt per source
python3 magnet_excavator.py ~/saved-pages/ --out-dir lists/
#   lists/site_alpha.txt   3 magnet(s)
#   lists/site_beta.txt    2 magnet(s)

# step 2: feed those files back into qBittorrent
python3 magnet_excavator.py lists/ --add --category excavated --max-active 4
```

Verified end to end: step 1 wrote 3 + 2 links across two files, every line
starting `magnet:?xt=urn:btih:` with no stray carriage returns, and step 2 read
them back and added all 5. Step 2 does not need the original HTML at all.

Editing the file between the two steps works too — delete lines you do not want,
or paste in magnets from elsewhere. Comments, prose and anything that is not a
magnet are ignored. A string that *starts* `magnet:?` but does not hold a valid
infohash is not added, and `--summary` reports how many of those there were in a
`BAD` column, so a typo cannot quietly cost you a link:

```
SOURCE          RAW  UNIQUE  DUPES  SIZED  EST. TOTAL   BAD
-----------------------------------------------------------
edited.txt        2       2      0      0           -     1

BAD 1: string(s) starting magnet:? that did not hold a valid BitTorrent
infohash, so they were not added.
```

The column only appears when something was actually rejected.

## 7. Several sources at once

```bash
python3 magnet_excavator.py ~/saved-pages/ --summary
python3 magnet_excavator.py ~/saved-pages/ --out-dir lists/
python3 magnet_excavator.py ~/saved-pages/ --plain > everything.txt
```

Directories are walked and every file is scanned as raw text — `.html`, `.txt`,
`.mhtml`, a log, a `.xyz123`, or a binary blob. The summary adds a cross-source
block showing how much your sources overlap and what is exclusive to each.

## What it ignores, and why

| In the file | Result |
|---|---|
| `.magnet-link` CSS class | ignored — no infohash |
| `magnet:?xt=urn:btih:tooshort` | ignored — malformed hash |
| `magnet:?xt=urn:ed2k:...` | ignored — not BitTorrent |
| `https://example.com/download.php?id=99` | ignored — not a magnet |
| 40 hex chars with no `magnet:` scheme | ignored |
| The same magnet listed twice | kept once |

Accepted: v1 40-hex, v1 32-char base32, and v2 `urn:btmh:1220…` hashes, in
`href`, `data-*`, JSON, comments, prose, or binary.

## Run the tests

```bash
python3 -m unittest test_magnet_excavator -v    # 102 tests
```
