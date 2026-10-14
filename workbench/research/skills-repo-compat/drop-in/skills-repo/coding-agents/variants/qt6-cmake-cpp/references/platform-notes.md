# Platform notes — Linux, Windows, macOS

Only the lane matching the target applies. Every item is a trap that has cost
someone a session.

## Linux (X11 and Wayland — both are real)

- The platform plugin is chosen at run time (`QT_QPA_PLATFORM=wayland|xcb|offscreen`).
  A bundle must ship **both** `qxcb` and `qwayland-*` plugins, plus the
  `wayland-shell-integration/` and `wayland-decoration-client/` plugin dirs
  for Wayland, or users on one or the other get "could not load the Qt
  platform plugin".
- Under Wayland: no global window positioning (`move()` is ignored), no
  `QCursor::setPos`, no screen-grab of other windows; client-side decorations
  are Qt-drawn unless the compositor provides them. Tiling compositors
  (Hyprland, sway) ignore minimum sizes and float dialogs — test the layout at
  unusual aspect ratios.
- `xcb` needs `libxcb-*`, `libxkbcommon-x11`; in a minimal container that is
  the first failure. `QT_DEBUG_PLUGINS=1` prints exactly which library is
  missing.
- Fonts: `fontconfig` must exist; an AppImage on a bare system needs a
  fallback font or renders boxes.
- Dark mode: follows the platform theme (`QT_QPA_PLATFORMTHEME=gtk3|qt6ct|kde`);
  do not hard-code colours — honour `QPalette`.
- File dialogs: `QFileDialog::DontUseNativeDialog` is the deterministic choice
  for tests; the native (portal) dialog is the right default for users.
- Headless CI: `QT_QPA_PLATFORM=offscreen` (preferred) or `xvfb-run -a`.
- Case-sensitive filesystem; path separators `/`; `~` is not expanded by Qt
  (`QDir::homePath()`).

## Windows (MinGW and MSVC — both are real)

- **Subsystem:** `qt_add_executable(app WIN32 …)`; otherwise a console appears.
  For a child engine process, pass `CREATE_NO_WINDOW` through
  `QProcess::setCreateProcessArgumentsModifier`.
- **Toolchain parity:** the Qt build must match the compiler ABI
  (`win64_mingw` with MinGW-w64 gcc; `win64_msvc2022_64` with MSVC). Mixing
  links fine and crashes at run time.
- **Runtime DLLs:** MinGW's `libstdc++-6.dll`, `libgcc_s_seh-1.dll`,
  `libwinpthread-1.dll` are not on a clean machine; statically link them for
  CLIs/tests, let `windeployqt` handle the GUI. MSVC: the VC++ redistributable
  or `vc_redist` merge module.
- **`long` is 4 bytes** (LLP64). `strtol`, `std::stol`, `QString::toLong`
  overflow where Linux does not. Use 64-bit types for sizes and counts.
- **Paths and Unicode:** the console and `argv` are code-page encoded; use
  `QCoreApplication::arguments()` (UTF-16 aware) or `CommandLineToArgvW`, and
  `std::filesystem::path` from `QString::toStdWString()`, never from `toStdString()`.
  Reserved names (`CON`, `NUL`, `COM1`…), trailing dots/spaces, and
  superscript digit aliases in device names must be rejected in output-name
  sanitization; max path 260 unless the long-path manifest is set.
- **Exit codes:** NTSTATUS on crash (see `crash-diagnosis.md` §3); batch files
  and `cmd` mask codes > 255 differently from PowerShell.
- **Line endings:** Git for Windows checks out CRLF unless `.gitattributes`
  pins LF; base64 fixtures, shell scripts and `SHA256SUMS` break on CR.
- **DPI:** per-monitor v2 is on by default in Qt 6; a mixed-DPI setup is where
  fixed pixel sizes show. `QT_SCALE_FACTOR` for testing.
- **Dark mode:** Qt ≥ 6.5 reads the system scheme; the `windows11` style honours
  it on Windows 11; Fusion is the portable fallback.
- **Defender/SmartScreen:** unsigned portable executables get a warning;
  signing is an owner step with a certificate. Antivirus can hold a freshly
  written output file open for a moment — a "verify immediately after rename"
  check should retry briefly before declaring failure.
- **OpenGL:** some VMs and old drivers lack a usable GL; `QT_OPENGL=software`
  or shipping `opengl32sw.dll` (what `windeployqt` adds) keeps the app usable.

## macOS (brief — only when it is a real target)

- `MACOSX_BUNDLE`, an `Info.plist` template, `macdeployqt`, signing +
  notarization for distribution outside the App Store.
- Retina is 2× by default; menus live in the global menu bar
  (`QMenuBar` without parent); `Cmd` instead of `Ctrl` in shortcuts via
  `QKeySequence::StandardKey`.
- Gatekeeper quarantines downloaded binaries; a portable zip is not a normal
  distribution shape here.

## All platforms

- Never hard-code the Qt location, a user's home, or a drive letter in CMake,
  presets, scripts or docs; use `CMAKE_PREFIX_PATH`/env vars and
  `QStandardPaths`.
- Settings: `QStandardPaths::AppConfigLocation` + an env override for tests
  and portable mode; atomic writes.
- Temp files: `QTemporaryDir`/`QTemporaryFile` in the output's directory when
  the final step is a rename (cross-device rename is not atomic).
- Timestamp granularity differs (NTFS 100 ns, ext4 ns, FAT 2 s): size+mtime
  "changed" checks are conservative, say so.
