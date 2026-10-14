# Qt 6 / CMake skeleton — cross-platform (Linux gcc/clang, Windows MinGW/MSVC, macOS).
#
# Shape:
#   app_core            Qt-free (or Qt Core only) library: settings, validation,
#                       argv builder, planners, verifiers — testable without a GUI.
#   MyApp               the Qt Widgets GUI (WIN32 + MACOSX_BUNDLE so no console
#                       window appears and macOS gets an .app).
#   test_core           plain C++ test executable for app_core.
#   test_gui_offscreen  real widgets under QT_QPA_PLATFORM=offscreen.
#   fake_engine_*       tiny fixture executables the GUI harness launches.
#
# Qt is located through CMAKE_PREFIX_PATH (see CMakePresets.json: it reads the
# QT_PREFIX environment variable). No machine path lives in this file.
#
# STATUS: written 2026-10-13 without a Qt 6 or CMake installation at hand —
# NOT compiled yet. First use: configure from a fresh build dir, fix what the
# real toolchain reports, and record the result in the project overlay.

cmake_minimum_required(VERSION 3.21)

# ---- single version source: VERSION file, generated header in the BUILD tree only
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" _app_version_raw)
string(STRIP "${_app_version_raw}" APP_VERSION)
if(NOT APP_VERSION MATCHES "^[0-9]+\\.[0-9]+\\.[0-9]+")
  message(FATAL_ERROR "VERSION must contain MAJOR.MINOR.PATCH, got '${APP_VERSION}'")
endif()

project(MyApp VERSION ${APP_VERSION} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(BUILD_GUI    "Build the Qt 6 Widgets GUI"             ON)
option(ENABLE_ASAN  "AddressSanitizer (gcc/clang/MSVC)"      OFF)
option(ENABLE_UBSAN "UndefinedBehaviorSanitizer (gcc/clang)" OFF)
option(WARNINGS_AS_ERRORS "Treat warnings as errors (CI)"    OFF)

configure_file(cmake/version.h.in "${CMAKE_BINARY_DIR}/generated/app/version.h" @ONLY)

# ---- diagnostics flags (applied to every target below via an INTERFACE lib)
add_library(app_flags INTERFACE)
if(MSVC)
  target_compile_options(app_flags INTERFACE /W4 /permissive- /utf-8)
  if(WARNINGS_AS_ERRORS)
    target_compile_options(app_flags INTERFACE /WX)
  endif()
  if(ENABLE_ASAN)
    target_compile_options(app_flags INTERFACE /fsanitize=address)
    target_link_options(app_flags INTERFACE /INCREMENTAL:NO)
  endif()
else()
  target_compile_options(app_flags INTERFACE -Wall -Wextra -Wpedantic -Wshadow)
  if(WARNINGS_AS_ERRORS)
    target_compile_options(app_flags INTERFACE -Werror)
  endif()
  if(ENABLE_ASAN)
    target_compile_options(app_flags INTERFACE -fsanitize=address -fno-omit-frame-pointer)
    target_link_options(app_flags INTERFACE -fsanitize=address)
  endif()
  if(ENABLE_UBSAN)
    target_compile_options(app_flags INTERFACE -fsanitize=undefined -fno-omit-frame-pointer)
    target_link_options(app_flags INTERFACE -fsanitize=undefined)
  endif()
endif()

# ---- core library: no Qt dependency so a Qt-less runner still pins the logic
add_library(app_core STATIC
  src/core/Settings.cpp
  src/core/Command.cpp
)
target_include_directories(app_core PUBLIC
  "${CMAKE_BINARY_DIR}/generated"   # generated FIRST so a committed fallback never wins
  src
)
target_link_libraries(app_core PUBLIC app_flags)

# ---- tests (always built; the GUI harness is added below when Qt exists)
enable_testing()

add_executable(test_core tests/test_core.cpp)
target_link_libraries(test_core PRIVATE app_core)
add_test(NAME core COMMAND test_core)

# Fixture engines the GUI harness launches for real (see subprocess-engine.md §10).
add_executable(fake_engine_ok   tests/fake_engine_ok.cpp)
add_executable(fake_engine_fail tests/fake_engine_fail.cpp)
target_link_libraries(fake_engine_ok   PRIVATE app_flags)
target_link_libraries(fake_engine_fail PRIVATE app_flags)

# ---- GUI (optional, honest skip)
if(BUILD_GUI)
  find_package(Qt6 6.4 COMPONENTS Widgets QUIET)
  if(Qt6_FOUND)
    message(STATUS "Qt6 ${Qt6_VERSION} found -> building GUI")
    qt_standard_project_setup()

    qt_add_executable(MyApp WIN32 MACOSX_BUNDLE
      src/main.cpp
      src/ui/MainWindow.cpp
      src/ui/MainWindow.h
    )
    target_link_libraries(MyApp PRIVATE app_core Qt6::Widgets)

    qt_add_executable(test_gui_offscreen
      tests/test_gui_offscreen.cpp
      src/ui/MainWindow.cpp
      src/ui/MainWindow.h
    )
    target_link_libraries(test_gui_offscreen PRIVATE app_core Qt6::Widgets)
    # Every fixture the harness launches must be a dependency, or a
    # `--target test_gui_offscreen` build leaves it missing at run time.
    add_dependencies(test_gui_offscreen fake_engine_ok fake_engine_fail)
    add_test(NAME gui_offscreen COMMAND test_gui_offscreen)
    set_tests_properties(gui_offscreen PROPERTIES
      ENVIRONMENT "QT_QPA_PLATFORM=offscreen"
      TIMEOUT 600)

    # Deployment hook: `cmake --install` runs windeployqt/macdeployqt logic.
    install(TARGETS MyApp BUNDLE DESTINATION . RUNTIME DESTINATION bin)
    qt_generate_deploy_app_script(TARGET MyApp OUTPUT_SCRIPT _deploy_script
                                  NO_UNSUPPORTED_PLATFORM_ERROR)
    install(SCRIPT ${_deploy_script})
  else()
    message(STATUS "Qt6 NOT found -> GUI skipped. Set CMAKE_PREFIX_PATH (or QT_PREFIX for the presets).")
  endif()
endif()

# ---- MinGW: self-contained non-Qt executables (no libstdc++-6.dll etc. on a clean machine)
if(MINGW)
  foreach(t test_core fake_engine_ok fake_engine_fail)
    target_link_options(${t} PRIVATE -static)
  endforeach()
  foreach(t MyApp test_gui_offscreen)
    if(TARGET ${t})
      target_link_options(${t} PRIVATE -static-libgcc -static-libstdc++)
    endif()
  endforeach()
endif()
