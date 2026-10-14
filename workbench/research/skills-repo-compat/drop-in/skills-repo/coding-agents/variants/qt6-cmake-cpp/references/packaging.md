# Packaging and deployment

A green build is not a working package. The package is the deliverable; test
it as one (v4 §7).

## 1. What must ship with a Qt 6 Widgets app

| Item | Why | Where it goes |
|---|---|---|
| `Qt6Core`, `Qt6Gui`, `Qt6Widgets` (+ `Svg`, `Network`… as linked) | the app does not start without them | beside the exe (Windows), `lib/` (Linux bundle), `Frameworks/` (macOS) |
| `platforms/` plugin: `qwindows`, `qxcb` **and** `qwayland*`, `qcocoa` | "could not find or load the Qt platform plugin" | `plugins/platforms/` or next to the exe on Windows |
| `imageformats/` the app actually loads (`qgif`, `qjpeg`, `qsvg`, `qico`) | previews silently blank otherwise | `plugins/imageformats/` |
| `styles/` (`qwindowsvistastyle`/`qmodernwindowsstyle`) on Windows | native look; otherwise falls back to Fusion | `plugins/styles/` |
| `tls/` plugins if networking with HTTPS | silent TLS failure | `plugins/tls/` |
| ICU / libstdc++ / libgcc / libwinpthread as applicable | start-up failure on a clean machine | beside the exe or statically linked |
| the engine executable + its own license text | the app is a shell | beside the exe; notices in the root |
| Qt LGPL notices (`LGPLv3`, companion `GPLv3`), a `QT_NOTICE.txt` naming the Qt version and how to relink | license obligation | package root |
| your own license | obviously | package root |
| `qt.conf` if plugins are not in the default relative layout | plugin discovery | beside the exe |

## 2. Tools

- **Windows:** `windeployqt --release --no-translations --no-system-d3d-compiler <app.exe>`
  (add `--no-opengl-sw` unless the software rasterizer is wanted). MinGW builds
  need the MinGW runtime DLLs too; statically link them for non-Qt executables.
  Verify with `dumpbin /dependents` or `objdump -p | grep DLL`.
- **Linux:** `linuxdeploy --appdir AppDir --plugin qt --output appimage`
  (needs `QMAKE`/`qmake6` on `PATH`), or `cqtdeployer`, or a distro package that
  depends on the system Qt. Check with `ldd` and `QT_DEBUG_PLUGINS=1` on a
  minimal container.
- **macOS:** `macdeployqt App.app -dmg`; code-sign and notarize for
  distribution — an owner-only step with credentials.
- **CMake:** `qt_generate_deploy_app_script` + `cmake --install` wires
  `windeployqt`/`macdeployqt` into the install step.

## 3. The packaging script contract (fail closed)

1. Stage into a **fresh, private** directory; never into a directory that may
   already contain a previous release.
2. Copy from a **manifest** (explicit list of required files). A missing or
   empty required file is an error, exit non-zero, no archive produced.
3. Record the source revision (`git rev-parse HEAD`) and the toolchain versions
   into the package (a `BUILD_INFO.txt`), so an artifact can be tied to its
   commit later.
4. Produce the archive and a `SHA256SUMS`.
5. Run the **negative tests**: remove one required file from a staging copy and
   assert the script fails; remove the engine and assert the app reports
   "engine missing" with a non-zero CLI exit — not a silent 0.

## 4. Proving the package

| Proof | How | Certifies |
|---|---|---|
| manifest assertion | script lists every required path, fails on absence/emptiness | the files exist |
| architecture check | `file`/`objdump -f`/`dumpbin /headers` on every binary | no 32/64-bit or wrong-OS mix |
| fresh-runner smoke | a second CI job downloads the artifact, unpacks, runs the CLI on a fixture, launches the GUI offscreen for one job | the package runs with no dev tree |
| clean-machine run | a person on a machine with no Qt/compiler, following a dated runsheet | the real thing — still not every machine |

Wine on Linux is a useful **signal** for Windows packages (missing DLL,
console subsystem, path handling), not Windows proof — label it as emulation.

## 5. Portable vs installed

A portable zip keeps settings beside the exe only if the app is told to
(`QSettings` user scope writes to `%AppData%`); decide explicitly and document.
A system package on Linux depends on the distro's Qt and ships no plugins; keep
both paths in one `package_common.sh` with mode flags rather than two scripts
that drift.

## 6. Releases

Cutting a tag/pre-release is a separate, deliberate step with its own
checklist: gates green on the exact SHA, artifact built by CI from that SHA,
notes that name the SHA and the evidence run, checksums published, and a
post-publish download + checksum verification. An artifact upload in a normal
run is not a release.
