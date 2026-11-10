# inbox — capture drop zone + capture guide (owner-run)

This folder receives the files you capture from your own Opera Sync account.
It is **git-ignored**: everything except this README and `.gitignore` stays on
your machine and in the chat session. **Do not upload captures through the
GitHub web UI** — web uploads ignore `.gitignore` and this repository is
public. Attach files to the chat session instead.

Naming: `YYYY-MM-DD_<label>_<kind>.<ext>` — e.g.
`2026-11-10_syncdata_idb-dump.json`, `2026-11-10_bookmarks.html`.

**Before anything else, three warnings:**

1. **Never click "Reset Passphrase"** on sync.opera.com while capturing (or in
   general). It wipes all sync data on Opera's server. It is not needed for any
   step below.
2. Captures contain private data (history, tabs, passwords CSV) and the HAR
   additionally contains **live session cookies**. Log out of the panel after
   capturing; keep the files off Git and out of shared folders.
3. Do this from a device that already has your data (your daily Opera), so a
   mistake cannot lose anything: every route here is read-only except Reset.

Run the steps in a desktop browser (Chrome/Edge/Opera all work) — you need its
DevTools. Steps 1–2 are pure Opera UI. Steps 3–5 are on
`https://www.sync.opera.com` after **Login**.

---

## Step 1 — Bookmarks HTML (Opera UI, ~1 minute)

In Opera: open `opera://bookmarks` → drop-down at the bottom-left →
**Export bookmarks**. Saves the full local bookmark tree (Speed Dials included,
without thumbnails) as an HTML file → `inbox/…_bookmarks.html`.

## Step 2 — Passwords CSV (Opera UI, ~1 minute, sensitive)

`opera://password-manager/settings` → **Export passwords** (confirm with your
OS login). Plaintext CSV → `inbox/…_passwords.csv`. Handle with the same care
as a password manager unzip.

## Step 3 — sync-internals node dump (browser engine view)

In Opera: open `opera://sync-internals/` → **Data** tab → tick the data types
you care about (Bookmarks, Sessions, Typed URLs, Device Info, …) → tick
**"Include node content"** (bottom of the page) → **"Dump Sync nodes to a
file"** → save the CSV into `inbox/`. This is the only capture that includes
passphrase-encrypted types (as ciphertext) and it comes straight from the sync
engine rather than the panel.

## Step 4 — IndexedDB dump of the panel (`SyncData`) — the main capture

Open `https://www.sync.opera.com`, **Login**, and let the page finish loading
the section counts. Then press `F12` → **Console**, paste **one** of the
snippets below, press Enter.

Quick sanity check first (shows the database and per-store row counts):

```js
(async () => {
  const rq = indexedDB.open("SyncData");
  const db = await new Promise((res, rej) => { rq.onsuccess = () => res(rq.result); rq.onerror = () => rej(rq.error); });
  const counts = {};
  for (const s of db.objectStoreNames)
    counts[s] = await new Promise((r) => { const q = db.transaction(s).objectStore(s).count(); q.onsuccess = () => r(q.result); });
  console.table(counts); db.close();
})();
```

Expected stores: `tabs, device_windows, history, devices, preferences,
passwords, bookmarks` (schema in `../README.md`). If the browser says the
database does not exist, the panel stores under a prefix/origin variant — run
the full dumper anyway, it enumerates every database of the origin.

Full dump (every IndexedDB database of this origin → one JSON download;
binary values become `{__bin:"base64", b64:"…"}`):

```js
(async () => {
  const enc = (v) => {
    if (v instanceof ArrayBuffer) {
      let s = ""; const b = new Uint8Array(v);
      for (let i = 0; i < b.length; i += 0x8000)
        s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000));
      return { __bin: "base64", b64: btoa(s) };
    }
    if (v instanceof Uint8Array) return enc(v.buffer.slice(v.byteOffset, v.byteOffset + v.byteLength));
    return v;
  };
  const dumpStore = (db, store) => new Promise((res, rej) => {
    const out = []; const req = db.transaction(store, "readonly").objectStore(store).openCursor();
    req.onsuccess = () => { const c = req.result;
      if (!c) return res(out);
      out.push({ key: enc(c.key), value: enc(c.value) }); c.continue(); };
    req.onerror = () => rej(req.error);
  });
  const listDbs = () => new Promise((res, rej) => {
    if (indexedDB.databases) return indexedDB.databases().then((l) => res(l.map((d) => d.name)), rej);
    const r = indexedDB.webkitGetDatabaseNames();
    r.onsuccess = () => res([...r.result]); r.onerror = () => rej(r.error);
  });
  const names = await listDbs(); const dump = {};
  for (const name of names) {
    const rq = indexedDB.open(name);
    rq.onupgradeneeded = () => rq.transaction.abort();   // never create/upgrade
    const db = await new Promise((res, rej) => { rq.onsuccess = () => res(rq.result); rq.onerror = () => rej(rq.error); });
    dump[name] = { version: db.version, stores: {} };
    for (const store of db.objectStoreNames) dump[name].stores[store] = await dumpStore(db, store);
    db.close();
  }
  const blob = new Blob([JSON.stringify({ origin: location.origin, captured: new Date().toISOString(), databases: dump }, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "sync-opera-com-idb-" + new Date().toISOString().replace(/:/g, "-") + ".json";
  a.click();
  console.log("Saved", a.download, "— databases:", names.join(", "));
})().catch((e) => console.error("Dump failed:", e));
```

Then also save the panel's small localStorage state (holds the sync progress
tokens, useful if we ever replay the protocol) — Console:

```js
copy(JSON.stringify(Object.fromEntries(["storeBirthday","progressMarkers","dataWereInitiallyFetched","user_id","i18nextLng"].map(k => [k, localStorage.getItem(k)])), null, 2))
```

`copy()` puts it on the clipboard — paste into a file
`…_localstorage.json`. (Leave `user_id` in if asked for; it is not a secret.)

**Note:** if the main page shows an **"encrypted"** mark on a section, that
section's detail rows are `{id, encrypted: true}` placeholders — the panel
never received decodable content. Capture it anyway (completeness), rely on
Step 3 for that type, and **do not** Reset Passphrase to "fix" it.

## Step 5 — Human-readable copies of the panel (optional, cheap)

Still logged in: visit each section (Bookmarks, Speed Dials, Open tabs,
History, Devices, Pinboards), and per page either `Ctrl+S` → "Web page,
Complete" into `inbox/`, or use the browser's "Save as MHTML"/SingleFile. Do
sections with many items in scrollable chunks if your saver truncates.

## Step 6 — HAR (only if asked; credential-laden)

F12 → **Network** tab → tick **Preserve log** → reload the panel, click through
every section → right-click the request list → **Save all as HAR with content**
→ `inbox/…_panel.har`. The responses are protobuf (`application/octet-stream`);
this is raw material for a decoder, and it contains your session cookies —
after saving, **log out of the panel** (`Logout` icon, top right), and never
commit or share the HAR casually.

---

## After capturing

- Keep everything out of Git (this folder is ignored — leave it that way).
- Attach the files to the chat session; say which steps you ran and on which
  Opera/browser version.
- Next session builds the converters (JSON → bookmarks HTML / CSV, and
  optionally HAR → protobuf JSON) and validates them against these captures.

*Untested disclaimer: the snippets above use standard IndexedDB APIs and were
written against the panel's verified schema (see `../README.md`), but have not
yet been run against the live site — if a snippet errors, capture the error
text and the sanity-check output anyway; both are diagnostic gold.*
