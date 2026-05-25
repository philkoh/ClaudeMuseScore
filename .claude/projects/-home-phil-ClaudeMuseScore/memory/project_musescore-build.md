---
name: musescore-build
description: MuseScore 5.0.0-dev built from source on Ubuntu 26.04 with Qt 6.10.2, GCC 15, Ninja
metadata:
  type: project
---

MuseScore Studio 5.0.0 (development) built from source in `MuseScore/` subdirectory.
Binary at `MuseScore/build/install/bin/mscore`.

Build dependencies (all from Ubuntu 26.04 apt repos):
- Qt 6.10.2: qt6-base-dev, qt6-base-private-dev, qt6-declarative-dev, qt6-declarative-private-dev, qt6-tools-dev, qt6-5compat-dev, qt6-shadertools-dev, qt6-svg-dev, qt6-networkauth-dev, qt6-websockets-dev, qt6-l10n-tools, qt6-wayland-dev, qml6-module-* packages
- GCC 15.2.0 (system default)
- CMake 4.2.3, Ninja 1.13.2
- libasound2-dev, libcups2-dev, libsndfile1-dev, libvulkan-dev, ffmpeg, libavcodec-dev, libavformat-dev, libswscale-dev, libdbus-1-dev, libgl1-mesa-dev, libxkbcommon-dev, libxkbcommon-x11-dev

Configure command: `cmake .. -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=$(pwd)/install -DMUSE_COMPILE_BUILD_64=ON`
Build command: `cmake --build . --parallel $(nproc)`
Install command: `cmake --install . --config RelWithDebInfo`

**Why:** User wants to customize MuseScore source code for personal use.

**How to apply:** After source changes, rebuild with ninja (incremental). The `MuseScore/` source tree is tracked in our git repo; build artifacts in `MuseScore/build/` are gitignored.

Related: [[standing-orders]], [[repo-setup]]
