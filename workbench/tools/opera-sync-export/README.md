# tools/opera-sync-export — get your data out of Opera Sync (sync.opera.com)

**Status (2026-11-10): research + guided-capture drop zone. No runnable decoder code yet.**
Opera gives no export button anywhere in Sync: the web panel at
`https://www.sync.opera.com` only *displays* counts and lists, and the browser's
built-in exports cover only some data types. This unit holds what we learned
about how that panel really works (from its own public JavaScript), a ranked
list of ways to get the data out, and a step-by-step capture plan that the
owner runs in their own logged-in browser. Captured files land in `inbox/`
(git-ignored). Decoder/converter scripts are planned as the next session's work,
once real captures exist to test against.

- Owner-facing capture guide: `inbox/README.md`
- Research audit trail (sources, candidates, scores): `RESEARCH.md`

## ⚠️ Read before touching this folder

1. **This repository is PUBLIC (it is a fork, so it cannot be made private).**
   `inbox/` is git-ignored, but the GitHub **web upload ignores `.gitignore`** —
   never upload captures through github.com. Attach them to the chat session
   instead, or keep them local. Nothing personal should ever be committed here.
2. **Never click "Reset Passphrase" on sync.opera.com.** It is destructive: it
   wipes *all* sync data on Opera's server (the local devices keep their copies
   and would re-upload, but anything no longer on a device is gone). It is not
   an export tool and not needed for any route in this folder.
3. **Captures contain live credentials.** A HAR holds session cookies and OAuth
   material; an IndexedDB dump holds your full synced data. After capturing,
   log out of the panel, keep the files out of Git, and share them only where
   you intend to (the chat session is the intended channel).

## What the target is (verified 2026-11-10 from public assets, logged out)

- `www.sync.opera.com` serves a React 16 / Create-React-App SPA (build
  `main.4f8b0e67.js`, dated 2023-09-12). It is **not** a thin view over a JSON
  API: the bundle ships the **Chromium sync protobuf** schema (protobufjs,
  `sync_pb.ClientToServerMessage`) and a **Dexie/IndexedDB** database, and the
  app speaks the Chromium sync protocol itself, in the browser.
- Endpoints (same-origin, `withCredentials`, session cookies from the OAuth
  login at `auth.opera.com`, `client_id=sync-ui`):
  - `POST https://sync.opera.com/ui_backend/proxy/sync/api/sync/command/`
    — binary protobuf `ClientToServerMessage` → `ClientToServerResponse`
    (`GetUpdates` with per-datatype progress-marker tokens).
  - `GET  https://sync.opera.com/ui_backend/proxy/auth/api/v1/me` — account check.
  - `GET/POST/DELETE .../ui_backend/oauth2/login|logout|empty/` — OAuth plumbing.
  - `DELETE .../ui_backend/proxy/sync/api/sync/purge_user_data/` — **the Reset
    Passphrase action. Destructive. Do not call it.**
- The browser's own sync protocol endpoint (`sync.opera.com/api/sync/`) is a
  different surface, User-Agent-sensitive, meant for the browser client.
- IndexedDB database **`SyncData`** (Dexie, 5 schema versions), stores:

  | store | schema (indexes) | content |
  |---|---|---|
  | `tabs` | `id, parentId` | one row per open tab of every synced device (`title`, `url`, `favicon`, `tabId`, `windowId`) |
  | `device_windows` | `id, parentId` | window headers per device (client name, platform, window/tab ids) |
  | `history` | `id, visited` | typed-URL history entries (`title`, `url`, `visited` as JS `Date`) |
  | `devices` | `id, platform` | device info (name, platform class) |
  | `preferences` | `id` | rows are `{id}` only — the panel never stores preference values |
  | `passwords` | `id` | rows are `{id}` only — the panel never stores password content |
  | `bookmarks` | `id, type, folder, [parent+folder]` | bookmark tree + special `type` rows `speeddial_bookmarks`, `pinboard_bookmarks`; folder types: bookmark bar, user root, trash, unsorted |

- The panel's **"encrypted" mark** is per data type: if the server returns an
  entry whose specifics are encrypted (which happens when a sync passphrase is
  set), the app stores only `{id, encrypted: true}` rows, sets an `encrypted`
  flag, and **refuses to render that section** (the main page shows the count
  with an "Information is encrypted" mark instead of a link). Passwords are
  always in this state; with "encrypt all with passphrase" enabled, everything
  is. Encrypted content cannot be captured from the panel at all — the
  decryption key never reaches the browser. The honest alternatives then are
  the browser-side routes below.
- The app persists sync state in `localStorage`: `progressMarkers`
  (per-datatype GetUpdates tokens), `storeBirthday`, `dataWereInitiallyFetched`,
  `user_id`. It re-fetches GetUpdates every ~60 s while the tab is visible, and
  clears local data when the logged-in user id changes.

## Routes ranked (details and sources in RESEARCH.md)

| # | Route | Gets | Effort | Complete? |
|---|---|---|---|---|
| A1 | **IndexedDB dump** of `SyncData` from the panel's DevTools console (snippet in `inbox/README.md`) | bookmarks tree, speed dials, pinboards, all devices' open tabs, history — exactly what the panel can see | low | yes (panel scope) |
| B | **`opera://sync-internals` → "Dump Sync nodes to a file"** (Data tab, "Include node content") | raw sync nodes per data type, straight from the browser's sync engine | very low | broad; CSV, cryptic |
| C1 | **`opera://bookmarks` → Export bookmarks** (drop-down, bottom left) | full local bookmark tree incl. speed dials (no thumbnails) as HTML | trivial | local scope |
| C2 | **`opera://password-manager/settings` → Export passwords** (CSV) | passwords, plaintext CSV — handle with care | trivial | local scope |
| C3 | **Tab right-click → Save → "All tabs to a speed dial folder"**, then C1 | current window's open tabs as bookmarks | low | per workspace/window |
| D | **Local profile files** (path shown at `opera://about`): `Bookmarks`, `BookmarksExtras`, `History`, `Sessions/`, `Sync Data/` (LevelDB), `Login Data` | everything local, offline | medium; parsers exist (see RESEARCH.md) | local scope |
| A2 | **HAR with content** of a logged-in panel visit (Network tab → Export HAR) | raw protobuf GetUpdates bodies — complete but hardest to decode, and credential-laden | medium | protocol scope |
| A3 | **Saved HTML / MHTML / SingleFile** of each panel page | whatever is rendered | trivial | partial; per view |
| E | Direct sync-protocol client (reuse the panel's flow headlessly) | everything, automatable | high; no existing tool | yes |
| F | Tiny extension using `chrome.sessions.getDevices()` | other devices' tabs | low; Opera support unverified | partial |

**Recommended sequence: C1 + C2 (one minute each, zero risk) → B → A1 →
(optionally A3 per section; A2 only if a decoder is going to be built).**
If a section shows "encrypted" in the panel, A1/A3 capture nothing for it —
use B and C for those types, and do **not** "fix" it via Reset Passphrase.

## Drop zone

`inbox/` is the only place captures should ever land. It is git-ignored
(`*` with exceptions); name files `YYYY-MM-DD_<label>_<kind>.<ext>`, e.g.
`2026-11-10_syncdata_idb-dump.json`. `inbox/README.md` is the capture guide and
stays tracked so a fresh clone always carries it.

## Provenance & next steps

All protocol facts above were read on 2026-11-10 from the site's own public
assets (`/asset-manifest.json`, `/locales/en/translation.json`,
`/static/js/main.4f8b0e67.js` and its source map, via a text proxy because the
sandbox has no direct route to the site) plus Opera forum/Reddit threads by
volunteer `shadow2531`/`burnout426` and Opera help pages. The bundle was read
minified; function names are guessed from structure — the facts that matter
(endpoints, store schema, encrypted-flag behaviour) are strings and control
flow, which survive minification. Untested against a logged-in session: the
IndexedDB snippet in `inbox/README.md` is written for standard IndexedDB APIs
and needs one real run (it can first be exercised offline in Node with
`fake-indexeddb` + `dexie` from npm). Next session: test the snippet, build the
JSON→HTML/CSV converters, and only then consider the HAR/protobuf route.
