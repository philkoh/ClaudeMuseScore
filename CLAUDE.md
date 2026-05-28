# ClaudeMuseScore

## Project
Customized MuseScore build managed with Claude Code.

## Default User
Phil Koh <pk14225@gmail.com>

## MuseScore Source
- Source: `MuseScore/` (cloned from https://github.com/musescore/MuseScore, submodule `muse` initialized)
- Version: MuseScore Studio 5.0.0 (development branch)
- Binary helper: `musescore_path.py` locates the built binary on any OS (use `from musescore_path import require_mscore`)
- Build artifacts directory `MuseScore/build/` is gitignored (each machine builds independently)

### Linux build
- Configure: `mkdir -p MuseScore/build && cd MuseScore/build && cmake .. -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=$(pwd)/install -DMUSE_COMPILE_BUILD_64=ON`
- Build: `cmake --build . --parallel $(nproc)`
- Install: `cmake --install . --config RelWithDebInfo`
- Binary: `MuseScore/build/install/bin/mscore`
- Dependencies: Qt 6.10.2, GCC 15, CMake 4.2.3, Ninja 1.13.2 (all from Ubuntu 26.04 repos)

### Windows build
- Prerequisites: Visual Studio 2022 with "Desktop development with C++", Qt 6.8+ (via Qt online installer, MSVC 2022 64-bit kit), CMake 3.28+, Git for Windows, Python 3.10+
- Set `QTDIR` env var to Qt install path (e.g., `C:\Qt\6.10.0\msvc2022_64`)
- Configure: `mkdir MuseScore\build && cd MuseScore\build && cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=%CD%\install -DMUSE_COMPILE_BUILD_64=ON`
- Build: `cmake --build . --config RelWithDebInfo --parallel`
- Install: `cmake --install . --config RelWithDebInfo`
- Binary: `MuseScore\build\install\bin\MuseScore5.exe`

## Chord Analysis Tools
- `analyze_chords.py` — whole-score harmonic analysis bridge
  - Linux/macOS: `venv/bin/python3 analyze_chords.py input.mid [output.musicxml] [--roman|--both] [--per-measure] [--open] [--key Am]`
  - Windows: `venv\Scripts\python.exe analyze_chords.py input.mid ...`
  - Auto-detects key, chordifies score, writes chord symbols/Roman numerals back as MusicXML
- `analyze_by_instrument.py` — per-instrument chord analysis (one analysis per part)
  - Same invocation patterns as above
  - Splits format-0 MIDI files by channel; produces side-by-side measure-vs-instrument table
  - Reports `avg_polyphony` per part — high values indicate chord-conveying instruments
  - Foundation for future structural section detection (chorus/verse identification)
- Setup (Linux/macOS): `python3 -m venv venv && venv/bin/pip install music21`
- Setup (Windows): `python -m venv venv && venv\Scripts\pip install music21`

## Customization Workflow
- Edit source files in `MuseScore/` directly
- Save patches:
  - Linux/macOS: `patches/save-patches.sh`
  - Windows: `patches\save-patches.ps1` (or use Git Bash to run the .sh version)
- Apply patches after fresh clone:
  - Linux/macOS: `patches/apply-patches.sh`
  - Windows: `patches\apply-patches.ps1`
- Patches are committed to this repo so changes flow between Linux and Windows machines
- Rebuild (Linux): `cd MuseScore/build && cmake --build . --parallel $(nproc) && cmake --install . --config RelWithDebInfo`
- Rebuild (Windows): `cd MuseScore\build && cmake --build . --config RelWithDebInfo --parallel && cmake --install . --config RelWithDebInfo`

## Git
- Remote: git@github-ClaudeMuseScore:philkoh/ClaudeMuseScore.git (uses deploy key)
- `MuseScore/` is a git submodule pointing to upstream musescore/MuseScore
- Always commit and push after a new feature is successfully added
- Commit after successful tests; avoid committing in a broken state
- The .claude/projects/ memory directory is tracked in git so work can resume after a fresh clone
- Before committing: run `patches/save-patches.sh` to capture any MuseScore source changes

## Deploy Key / Authentication
- Each machine should have its OWN deploy key (don't copy private keys between machines)
- The Ubuntu machine's deploy key lives at `deploy_key` (gitignored) and its public key is in `deploy_key.pub`
- To add a second machine (e.g., Windows):
  1. On the new machine: `ssh-keygen -t ed25519 -f deploy_key -C "deploy-key-ClaudeMuseScore-<machine>"`
  2. Add the new `.pub` to https://github.com/philkoh/ClaudeMuseScore/settings/keys (Allow write)
  3. Configure SSH alias `github-ClaudeMuseScore` to use that key
- Alternative: use HTTPS + Personal Access Token via Git Credential Manager (simpler, no SSH config)

## Fresh Clone Bootstrap (Linux or Windows)
1. `git clone <repo-url>` and `cd ClaudeMuseScore`
2. `git submodule update --init --recursive` (pulls MuseScore source + muse framework)
3. Apply customizations: `patches/apply-patches.sh` (or `.ps1` on Windows)
4. Set up auth (see "Deploy Key / Authentication" above)
5. Build MuseScore (see "Linux build" or "Windows build" above)
6. Create Python venv and install music21 (see "Chord Analysis Tools" above)

## Standing Orders
- Commit + push + save to memory whenever a new feature is successfully added (autonomously, without being asked)
- Track enough files so that cloning from GitHub allows continuing right where we left off, including memories
- The repo is co-developed on Ubuntu and Windows 11 — keep all code cross-platform (no hardcoded paths, use `musescore_path.py` to find the binary)
