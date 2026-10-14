# CMake for Qt 6 — cross-platform

Adapted in part from the `qt-cmake-project-generator` process in
`a5c-ai/babysitter` (MIT; `library/specializations/desktop-development/skills/`)
and from standard Qt 6 CMake practice. Machine paths are deliberately absent;
Qt's location comes from `CMAKE_PREFIX_PATH`, which a preset reads from an
environment variable.

## 1. Minimal correct skeleton

```cmake
cmake_minimum_required(VERSION 3.21)
project(MyApp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)              # Qt 6 floor; 20 is fine
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Qt6 6.4 REQUIRED COMPONENTS Core Widgets)   # pin a floor you test
qt_standard_project_setup()             # AUTOMOC/AUTORCC/AUTOUIC + sane defaults

qt_add_executable(MyApp WIN32 MACOSX_BUNDLE
    src/main.cpp
    src/MainWindow.cpp src/MainWindow.h   # list headers with Q_OBJECT so AUTOMOC sees them
)
target_link_libraries(MyApp PRIVATE Qt6::Widgets)
target_include_directories(MyApp PRIVATE src)
```

Why each line matters:

- `qt_add_executable` (not `add_executable`) performs Qt's target finalization
  (plugin import for static builds, deployment metadata, platform properties).
- `WIN32` sets the Windows GUI subsystem — without it MinGW/MSVC produce a
  console app and double-clicking the `.exe` opens a terminal window.
  `MACOSX_BUNDLE` produces an `.app` on macOS. Both are ignored elsewhere.
- Listing `.h` files containing `Q_OBJECT` in the target is what makes AUTOMOC
  reliable across generators; relying on header discovery through includes is
  slower and occasionally misses.

## 2. Single version source, build-tree-only generation

```cmake
file(READ "${CMAKE_SOURCE_DIR}/VERSION" _ver_raw)
string(STRIP "${_ver_raw}" APP_VERSION)
configure_file(cmake/version.h.in "${CMAKE_BINARY_DIR}/generated/version.h" @ONLY)
target_include_directories(MyApp PRIVATE "${CMAKE_BINARY_DIR}/generated")
```

Never `configure_file` into `${CMAKE_SOURCE_DIR}`: a read-only checkout fails,
parallel build trees race on one header, and `git status` is dirty after a mere
configure. If a committed fallback header must exist (for a secondary build
system), have **one** script sync it, and put the generated directory *first*
in the include order so the build tree copy always wins.

## 3. Shared core as a library, GUI and tests on top

```cmake
add_library(app_core STATIC src/core/Settings.cpp src/core/Command.cpp)
target_include_directories(app_core PUBLIC src)
target_link_libraries(app_core PUBLIC Qt6::Core)          # or no Qt at all — see below

qt_add_executable(MyApp WIN32 MACOSX_BUNDLE src/main.cpp src/ui/MainWindow.cpp src/ui/MainWindow.h)
target_link_libraries(MyApp PRIVATE app_core Qt6::Widgets)
```

Keep the core **Qt-free** when the app shells a CLI engine or has a CLI of its
own: a header-only or plain-C++ core (settings, validation, argv builder,
output planner) is testable on a runner with no Qt, and a GUI-only CI lane
cannot hide a logic regression. An `INTERFACE` library works for header-only
cores.

## 4. Tests — headless by construction

```cmake
enable_testing()

add_executable(test_core tests/test_core.cpp)
target_link_libraries(test_core PRIVATE app_core)
add_test(NAME core COMMAND test_core)

if(TARGET Qt6::Widgets)
  qt_add_executable(test_gui_offscreen tests/test_gui_offscreen.cpp src/ui/MainWindow.cpp src/ui/MainWindow.h)
  target_link_libraries(test_gui_offscreen PRIVATE app_core Qt6::Widgets)
  add_test(NAME gui_offscreen COMMAND test_gui_offscreen)
  set_tests_properties(gui_offscreen PROPERTIES
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen"
    TIMEOUT 600)
  # Every fixture binary the harness launches must be a dependency, or a
  # `--target test_gui_offscreen` build leaves it missing at run time.
  add_dependencies(test_gui_offscreen fake_engine_ok fake_engine_fail)
endif()
```

`QT_QPA_PLATFORM=offscreen` lets a real `QApplication` and real widgets run
without a display server. Linux runners also accept `xvfb-run`, but offscreen
is deterministic and works on Windows too. Qt Test (`Qt6::Test`,
`QTEST_MAIN`) is the framework option; a house-style `CHECK` counter with a
non-zero exit is equally valid and has no extra dependency — pick one per
project and do not mix.

## 5. Optional GUI, honest skip

```cmake
option(BUILD_GUI "Build the Qt 6 GUI" ON)
if(BUILD_GUI)
  find_package(Qt6 COMPONENTS Widgets QUIET)
  if(Qt6_FOUND)
    message(STATUS "Qt6 ${Qt6_VERSION} found -> building GUI")
    # … GUI targets …
  else()
    message(STATUS "Qt6 NOT found -> GUI skipped (install Qt 6 or pass -DCMAKE_PREFIX_PATH)")
  endif()
endif()
```

A skipped GUI must be visible in CI logs and must not let a "GUI tests passed"
claim through: the test step should fail if the harness binary does not exist
when the job was supposed to build it.

## 6. Warnings and sanitizers

```cmake
if(MSVC)
  target_compile_options(MyApp PRIVATE /W4 /permissive-)
else()
  target_compile_options(MyApp PRIVATE -Wall -Wextra -Wpedantic -Wshadow -Wconversion)
endif()

option(ENABLE_ASAN  "AddressSanitizer" OFF)
option(ENABLE_UBSAN "UndefinedBehaviorSanitizer" OFF)
if(ENABLE_ASAN AND NOT MSVC)
  add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
  add_link_options(-fsanitize=address)
elseif(ENABLE_ASAN AND MSVC)
  add_compile_options(/fsanitize=address)
  add_link_options(/INCREMENTAL:NO)
endif()
if(ENABLE_UBSAN AND NOT MSVC)
  add_compile_options(-fsanitize=undefined -fno-omit-frame-pointer)
  add_link_options(-fsanitize=undefined)
endif()
```

Run the ASan/UBSan preset in CI on Linux at least; it is where most Qt
use-after-free bugs are first seen. ThreadSanitizer is Linux/macOS only and
conflicts with ASan — a separate preset. Treat `-Werror` as a CI-only flag
(`if(DEFINED ENV{CI})`) so a new compiler does not block local work.

## 7. Resources and UI files

```cmake
qt_add_resources(MyApp "app_res" PREFIX "/" FILES icons/app.svg style/app.qss)
# or a classic .qrc: qt_add_resources(MyApp "res" FILES resources/app.qrc)
```

Access with `QIcon(":/icons/app.svg")`. SVG icons require the `Qt6::Svg`
module **and** the `imageformats/qsvg` plugin at deploy time (§8 / packaging).

## 8. Deployment hook

```cmake
install(TARGETS MyApp BUNDLE DESTINATION . RUNTIME DESTINATION bin)
qt_generate_deploy_app_script(TARGET MyApp OUTPUT_SCRIPT deploy_script NO_UNSUPPORTED_PLATFORM_ERROR)
install(SCRIPT ${deploy_script})
```

This runs `windeployqt`/`macdeployqt` logic at `cmake --install`. Linux has no
official equivalent inside Qt's CMake; use `linuxdeploy` + its Qt plugin, or a
system-package path (see `packaging.md`). Whatever the path, **assert the
manifest** (platform plugin, image formats, notices, engine binary) in a script
that fails on a missing file.

## 9. Presets — one file, every platform

See `templates/CMakePresets.json`. Rules:

- `version: 6` (needs CMake 3.25 for all features; 3.23 reads v4). If the
  project pins an older CMake, lower the preset version accordingly.
- Qt location via `"CMAKE_PREFIX_PATH": "$env{QT_PREFIX}"` — never a literal
  `C:/Qt/...` or `/opt/Qt/...` (machine-specific example). Document `QT_PREFIX` in the README.
- Single-config generator (`Ninja`) + `CMAKE_BUILD_TYPE` on Linux/MinGW;
  `Ninja Multi-Config` or Visual Studio on MSVC where `--config` selects.
- A `condition` on `hostSystemName` so `cmake --list-presets` shows only what
  can run here.
- Separate `asan` preset inheriting the Linux one.

## 10. MinGW specifics (Windows without MSVC)

- Static C++ runtime for non-Qt executables so they run without
  `libstdc++-6.dll`/`libgcc_s_seh-1.dll`/`libwinpthread-1.dll`:
  `target_link_options(cli PRIVATE -static)`; for Qt targets use
  `-static-libgcc -static-libstdc++` and let `windeployqt` ship Qt's DLLs.
- `long` is 32-bit (LLP64). Any code that parses or compares integers with
  `long` behaves differently from Linux; use `long long`/`int64_t` and test
  on a 4-byte-`long` target (a `zig cc -target x86_64-windows-gnu` or
  `-m32`-class build in CI catches this class without a Windows runner).
- The exit code of a crashed child is an NTSTATUS (e.g. `0xC0000005`); masking
  with `& 0xff` turns a crash into "success". See `subprocess-engine.md`.

## 11. Package managers

- **vcpkg:** `CMAKE_TOOLCHAIN_FILE=<vcpkg>/scripts/buildsystems/vcpkg.cmake`
  plus Qt via `CMAKE_PREFIX_PATH`. Do not install Qt itself through vcpkg for
  desktop apps unless the project already does — the official installer/aqt
  builds are what `windeployqt` and the docs assume.
- **Conan 2:** `requires = "qt/6.x"` with `CMakeToolchain` + `CMakeDeps`
  generators; heavy first build. Usually unnecessary when the only large
  dependency is Qt.
- **System packages (Linux):** `qt6-base-dev` (Debian/Ubuntu), `qt6-base`
  (Arch), `qt6-qtbase-devel` (Fedora). Fine for CI and for a system package;
  not for a portable bundle.

## 12. Checklist before merging a CMake change

- configure from a *fresh* build directory succeeds (cached variables hide errors)
- `git status` clean after configure (no source-tree writes)
- `ctest --output-on-failure` runs the tests you think it runs — read the list
- the GUI target still has `WIN32`/`MACOSX_BUNDLE`
- presets still contain no literal machine path (`qt_lint.py` rule QL015)
- CI and any mirrored workflow copy changed together