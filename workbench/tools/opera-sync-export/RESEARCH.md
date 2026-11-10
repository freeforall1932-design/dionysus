# RESEARCH — exporting data out of Opera Sync (sync.opera.com)

Dated survey per `skills/universal-agent-context/UNIVERSAL_AGENT_CONTEXT_v4.md` §11.6.
Research days: 2026-11-10 (session 2, this file) building on 2026-11-10 session 1
(GitHub landscape). The decision this research backs: **how the owner exports
their own synced data (bookmarks, speed dials, pinboards, open tabs of all
devices, history) out of Opera Sync, without a decryptable server-side copy and
with no export feature offered anywhere.**

## 1. Scope

Searched 2026-11-10:

- **github.com** (REST search API, authenticated): repositories — quoted
  `"opera sync"`, `"opera link"`, `"synced tabs"`, `"tabs from other devices"`,
  `"sync-internals"`, `SNSS`, `browser history export`, Chromium sync client /
  server queries; code — `"www.sync.opera.com"`, `"sync.opera.com"` (by
  language: Python/JavaScript/Go/TypeScript), `"ui_backend/proxy/sync"`,
  `"ui_backend/oauth2"`, `"speeddial_bookmarks"`,
  `"user_root_bookmarks" "trash_bookmarks"`; issues — `"sync.opera.com" is:issue`.
- **Web (search + page fetch):** Opera forums, Reddit r/operabrowser & r/OperaGX,
  help.opera.com, the sync.opera.com site itself (logged out).
- **sync.opera.com public assets, fetched and read:** `/` and `/bookmarks`
  (login redirect chain), `/asset-manifest.json`, `/locales/en/translation.json`,
  `/static/js/main.4f8b0e67.js.LICENSE.txt`, `/static/css/main.e2fbde48.css`,
  `/static/js/main.4f8b0e67.js.map` (`sources` list),
  `/static/js/main.4f8b0e67.js` (full 126-chunk read through the
  `https://r.jina.ai/<url>` text proxy, because the sandbox has no direct
  network route to the site and `fetch_page` mangles raw JS).

**Inaccessible / not verifiable here (disclosed per §11.6):**

- Every data-bearing page of the panel sits behind Opera account login. No
  logged-in session was available, so all panel behaviour is inferred from the
  public JS, not observed live. The IndexedDB schema below is from the app's
  own `db.js` code and is high-confidence, but **no real `SyncData` database
  has been opened yet**.
- `opera://sync-internals` exists (forum-confirmed with tab-by-tab
  instructions) but its exact dump format was not inspected here.
- Wayback Machine pages returned only the toolbar through the fetcher; not used.
- Sandbox shell egress is restricted to GitHub/npm/PyPI: site files cannot be
  downloaded into the workspace; the proxy was used read-only for one public
  static asset. No credentials were ever sent through it.

## 2. What the panel actually is (new findings, session 2)

Session 1 established: no existing project does this job; Opera's browser-side
sync endpoint is `sync.opera.com/api/sync/` (User-Agent-sensitive), auth at
`auth.opera.com`. Session 2 read the panel's own bundle
(`main.4f8b0e67.js`, build "Published Time: Tue, 12 Sep 2023 12:52:32 GMT")
end-to-end. The **inference from session 1 is confirmed in code**: the SPA is a
Chromium sync protocol client in the browser.

- Runtime config: `PUBLIC_URL https://www.sync.opera.com`,
  `REACT_APP_PROXY_HOST https://sync.opera.com/`, `REACT_APP_BASE_PATH /`,
  `REACT_APP_LOCALES https://www.sync.opera.com/locales/{{lng}}/{{ns}}.json`.
- Libraries (LICENSE.txt + bundle structure): React 16.14.0, protobufjs, Dexie,
  axios, redux + react-redux, @reach/router, i18next (+ http-backend),
  @sentry/browser, react-ga, react-infinite-scroll-component.
- Data flow (minified names are structural, not original):
  - Auth: `GET /ui_backend/proxy/auth/api/v1/me` with cookies; on 403 →
    `GET /ui_backend/oauth2/login/`. Login page itself is OAuth2 authorization
    code at `auth.opera.com`, `client_id=sync-ui`,
    `scope=https://sync.opera.com user:read`, redirect
    `https://sync.opera.com/ui_backend/oauth2/empty/`.
  - Sync: `POST /ui_backend/proxy/sync/api/sync/command/`, request body =
    protobuf `sync_pb.ClientToServerMessage` with
    `Contents.GET_UPDATES`, `getUpdates.fromProgressMarker[]`
    (`dataTypeId` + token from `localStorage.progressMarkers`),
    `getUpdatesOrigin = NEW_CLIENT | PERIODIC`, `storeBirthday`;
    response decoded as `ClientToServerResponse`; new per-type tokens written
    back to `localStorage`; entries classified by `specifics` field
    (session tab/window, typedUrl, deviceInfo, preference, password, bookmark)
    and tombstones (`deleted` + matching specifics) applied via Dexie
    `bulkPut`/`bulkDelete`. Auto-refresh ≈ 60 s while the tab is visible
    (`visibilitychange` aware).
  - Requested data types (Chromium `DataTypeTypeId` values in code):
    `DEVICE_INFO 154522, TYPED_URL 40781, BOOKMARK 32904, PASSWORD 45873,
    SESSION 50119, PREFERENCE 37702`.
  - Reset: `DELETE /ui_backend/proxy/sync/api/sync/purge_user_data/`
    (the Reset Passphrase button; wipes server-side sync data).
- IndexedDB: `new Dexie("SyncData")`, versions 1–5 → stores
  `tabs:"id, parentId"`, `device_windows:"id, parentId"`,
  `history:"id, visited"`, `devices:"id, platform"`, `preferences:"id"`,
  `passwords:"id"`, `bookmarks:"id, type, folder, [parent+folder]"`.
  History timestamps are Chromium µs: `new Date(usec/1e3 - 116444736e5)`.
  Preferences and passwords are stored **as `{id}` rows only**; passwords
  always carry `encrypted:true` (the panel can show only a count).
- Encryption behaviour: an entry whose specifics arrive encrypted is stored as
  `{id, encrypted:true}`; a data type with any such first row sets the type's
  `encrypted` flag; encrypted types render **no detail route** (main page card
  only, with "Information is encrypted" mark). The panel therefore cannot
  decrypt passphrase-protected content — its key never reaches the browser.
  This matches the 2016 forum finding that only passwords are encrypted by
  default and the help docs' "encrypt all synchronized data with your own sync
  passphrase" option.

## 3. Ranked candidates

Scores are the §11.6 heuristic (30 functional fit / 20 architecture / 15
toolchain / 15 platform / 10 engineering evidence / 10 adoption), judged from
READMEs and GitHub API metadata on 2026-11-10 — not benchmarks. "Functional"
is measured against **this job** (export *synced* data), which penalises
local-profile tools that are otherwise excellent.

| Rank | Candidate | Purpose | Lang / license | ★ / last push | Score | Verdict for this job |
|---|---|---|---|---|---|---|
| 1 | [cclgroupltd/ccl_chromium_reader](https://github.com/cclgroupltd/ccl_chromium_reader) | Python re-implementations of Chromium store readers (LevelDB incl. `Sync Data`, cookies, histories) | Python / MIT | 261 / 2026-11-09 | **91** | Best dependency candidate for route D decoders (offline profile). No README mention of Opera specifics — assume "Chromium-esque, verify on a real profile". |
| 2 | [RyanDFIR/hindsight](https://github.com/RyanDFIR/hindsight) | Chromium-family forensics: history, sessions, cache → XLSX/JSON | Python / Apache-2.0 | 1554 / 2026-11-04 | **80** | Strong testing oracle for route D (compare its history/session output with ours). README names no Opera paths — verify. |
| 3 | [moonD4rk/HackBrowserData](https://github.com/moonD4rk/HackBrowserData) | One-shot decrypt+export (passwords, cookies, history, bookmarks) for 20 browsers — Opera + OperaGX supported | Go / MIT | 14694 / 2026-11-10 | **79** | Fastest zero-code route for local passwords/history on a live machine; not a library; no session/sync scope. |
| 4 | [herreio/browsewake](https://github.com/herreio/browsewake) | Exports tabs + per-tab history from Firefox/Chrome/Brave/Safari session files | Rust / MIT | 2 / 2026-04-06 | **62** | Architecture model for our converter's output semantics; no Opera paths. |
| 5 | [cclgroupltd/ccl-ssns](https://github.com/cclgroupltd/ccl-ssns) | SNSS session-file parser | Python / none | 49 / 2023-05-11 | **58** | Fine-grained route-D session parsing reference; stale, unlicensed (read-only use). |
| 6 | [brave/go-sync](https://github.com/brave/go-sync) | Brave's Chromium sync v2 server | Go / MPL-2.0 | 375 / 2026-11-10 | **55** | Protocol reference for route E only; heavy. |
| 7 | [lachlanallison/chrome-session-viewer](https://github.com/lachlanallison/chrome-session-viewer) | Web viewer for SNSS files | JS / MIT | 43 / 2026-05-21 | **54** | UX reference for rendering sessions; not a pipeline component. |
| 8 | [jaidhyani/chromium-sync-mcp](https://github.com/jaidhyani/chromium-sync-mcp) | MCP server reading a local Chromium profile incl. `Sync Data/LevelDB` sessions (`device_info-dt-*`, `sessions-dt-*`) | Python / Apache-2.0 | 0 / 2026-01-11 | **52** | Proof that synced-tabs data sits in the local LevelDB (route D); parsing is regex-over-bytes, no titles — idea only. |
| 9 | [cirotron/bookmarksexport](https://github.com/cirotron/bookmarksexport) | Bookmarks of many browsers incl. Opera → CSV/JSON/HTML | Python / none | 0 / 2026-06-21 | **45** | Marginal: local `Bookmarks` JSON is trivial without a tool. |
| 10 | [valurhrafn/chrome-sync-server](https://github.com/valurhrafn/chrome-sync-server) | Chromium sync server (C++) | C++ / MIT | 95 / 2020 | **40** | Protocol reference only. |
| 11 | [jlopezr/brave-remote-tabs](https://github.com/jlopezr/brave-remote-tabs) | MV3 extension listing other-device tabs via `chrome.sessions.getDevices()` → Markdown | JS / none | 0 / 2025-01-13 | **38** | Route F seed; whether Opera exposes that API is unverified. No README. |

Not in the table: legacy Opera Link API clients (2010–2015, service retired);
`step-/opera-bookmarks.awk` and `wagnerc4/opera_bookmarks.py` (old
`bookmarks.adr` format); Kubernetes "sync operator" noise; `kitt-browser/chrome-sync`,
`marleyjaffe/ChromeSyncParser`, `bluecat1999/chrome-sync`, `quack-io/chrome-sync`
(checked in session 1, reference-only); `prefix325/opera-sync-gateway` (ticketing,
false positive).

## 4. Source-backed observations

Community experience (dates matter; UI wording has changed over the years):

- Panel shows only counts/lists; no export anywhere — Opera threads
  [86139](https://forums.opera.com/topic/86139) (2025-09-03),
  [71223](https://forums.opera.com/topic/71223) (2024-05-16),
  [60645](https://forums.opera.com/topic/60645) (2025-07-04); "How can i access
  my synchronized content??" [76071](https://forums.opera.com/topic/76071)
  (2025-02-07): passphrase-enabled accounts see only "encrypted" on the panel.
- **Reset Passphrase wipes server sync data** — stated by volunteers in
  [Bookmarks gone](https://forums.opera.com/topic/61073/bookmarks-gone)
  (2025-08-06), [Sync not working](https://www.reddit.com/r/operabrowser/comments/1gwljzn/sync_not_working/)
  (2024-11-21), [Delete bookmarks in Opera Sync's Bookmark Trash folder](https://forums.opera.com/topic/87392/delete-bookmarks-in-opera-sync-s-bookmark-trash-folder)
  (2025-12-11).
- **`opera://sync-internals` "Dump Sync nodes to a file"** — Data tab, per-type
  checkboxes, "Include node content", CSV output:
  [r/OperaGX 1f4xp5c](https://www.reddit.com/r/OperaGX/comments/1f4xp5c/how_do_i_permanently_delete_something_from_my/)
  (2024-08-30); same page recommended for encryption status in
  [Sync passphrase does nothing?](https://forums.opera.com/topic/15317/sync-passphrase-does-nothing)
  (2016-10-17 — also: default encryption covers passwords only; all-data
  encryption is opt-in; the wording bug was fixed in Opera 39).
- Built-in exports: bookmarks HTML from `opera://bookmarks` (bottom-left
  drop-down), password CSV from `opera://password-manager/settings`,
  "Save all tabs to a speed dial folder" via tab right-click, other devices'
  tabs at `opera://activity` — volunteer `shadow2531`/`burnout426` guidance in
  the threads above plus [passwords thread](https://www.reddit.com/r/OperaGX/comments/1kw06d5/how_does_synchronization_work/)
  (2025-05-26). Opera help confirms the passphrase option
  ([Features](https://help.opera.com/en/latest/features/), 2026-08-31) and that
  passwords are credential-encrypted by default.
- Profile files: `Bookmarks`, `BookmarksExtras` (speed-dial thumbnails),
  `Sync Data/` folder, path shown at `opera://about` —
  [Bookmarks gone](https://forums.opera.com/topic/61073/bookmarks-gone) and
  [Bookmarks Sync still a problem](https://forums.opera.com/topic/37104/bookmarks-sync-still-a-problem)
  (2019-12-25, which also shows devices re-upload local state after a server
  reset — another reason Reset is not an export).
- Protocol facts: sync endpoint `sync.opera.com/api/sync/`, UA sensitivity and
  auth host — [AdguardTeam/AdguardFilters#1202](https://github.com/AdguardTeam/AdguardFilters/issues/1202)
  (2015-12-28); Opera account OAuth2 shape (token endpoint
  `auth.opera.com/oauth2/v1/token/`, clients `opera_desktop-client` /
  `opera_desktop`, per-service scopes incl. `https://sync.opera.com`) —
  `FOSWLY/translate` `src/providers/operaaria.ts` (MIT). The panel's own
  `client_id=sync-ui` flow is visible in its login redirect (fetched 2026-11-10).

## 5. Recommendation

Nothing existing does the job; the practical pipeline is **capture from the
surfaces Opera already exposes**, in this order:

1. **C1 + C2 now:** browser-native bookmarks HTML and password CSV (zero risk,
   local scope, one minute each).
2. **B next:** `opera://sync-internals` node dump — the only browser-side view
   that includes passphrase-encrypted types (as ciphertext) and per-type
   progress state.
3. **A1 primary for panel-visible data:** the Dexie `SyncData` dump via the
   console snippet in `inbox/README.md` — complete, already-decoded, structured
   JSON of bookmarks/speed dials/pinboards/tabs/history/devices.
4. **A3 as human-readable redundancy** (saved HTML/MHTML per section).
5. **A2/E/F deferred:** HAR+protobuf decoding or a headless protocol client is
   the completeness ceiling but needs real captures first; route F needs an
   Opera `chrome.sessions` check.

`ccl_chromium_reader` is the dependency candidate for any route-D (local
LevelDB) follow-up; HackBrowserData/hindsight are cross-check oracles.

## 6. Transfer plan

- **From the panel's bundle (already transferred):** endpoint paths, protobuf
  message flow, `SyncData` Dexie schema, Chromium-epoch date conversion,
  encrypted-flag semantics. Adapt: original identifiers, React/Dexie runtime —
  not copied. Proof before trusting: open a real `SyncData` dump and check it
  against this schema.
- **From `ccl_chromium_reader` (route D, later):** its LevelDB wrapper and
  Chromium record decoding; adapt licensing (MIT, keep attribution); proof:
  parse the owner's `Sync Data/LevelDB` and match against the A1 dump.
- **From HackBrowserData/hindsight:** only expected-output shapes for
  cross-checking; do not import code across languages.
- **From forum guidance:** treat volunteer instructions as experience, verify
  each menu path against the current Opera version during capture.
- **Must not be copied:** any OAuth client secret (one leaked in session-1 tool
  output — never written to this repo, never reused), captured credentials into
  Git, or the Reset-Passphrase endpoint into any script surface.
