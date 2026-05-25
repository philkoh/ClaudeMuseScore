# ClaudeMuseScore

## Project
Customized MuseScore build managed with Claude Code.

## Default User
Phil Koh <pk14225@gmail.com>

## MuseScore Source
- Source: `MuseScore/` (cloned from https://github.com/musescore/MuseScore, submodule `muse` initialized)
- Version: MuseScore Studio 5.0.0 (development branch)
- Build: `cd MuseScore/build && cmake --build . --parallel $(nproc)`
- Binary: `MuseScore/build/install/bin/mscore`
- Configure: `mkdir -p MuseScore/build && cd MuseScore/build && cmake .. -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=$(pwd)/install -DMUSE_COMPILE_BUILD_64=ON`
- Install: `cmake --install . --config RelWithDebInfo`
- Dependencies: Qt 6.10.2, GCC 15, CMake 4.2.3, Ninja 1.13.2 (all from Ubuntu 26.04 repos)

## Chord Analysis Tool
- `analyze_chords.py` — music21-based harmonic analysis bridge
- Requires: `python3 -m venv venv && venv/bin/pip install music21`
- Usage: `venv/bin/python3 analyze_chords.py input.mid [output.musicxml] [--roman|--both] [--per-measure] [--open] [--key Am]`
- Auto-detects key, chordifies score, identifies chord symbols and Roman numerals
- Handles MIDI enharmonic respelling for the detected key
- Writes chord symbols back into MusicXML for MuseScore import

## Customization Workflow
- Edit source files in `MuseScore/` directly
- Run `patches/save-patches.sh` to export changes as patch files
- Patches are committed to this repo and applied after a fresh clone with `patches/apply-patches.sh`
- Rebuild: `cd MuseScore/build && cmake --build . --parallel $(nproc) && cmake --install . --config RelWithDebInfo`

## Git
- Remote: git@github-ClaudeMuseScore:philkoh/ClaudeMuseScore.git (uses deploy key)
- `MuseScore/` is a git submodule pointing to upstream musescore/MuseScore
- Always commit and push after a new feature is successfully added
- Commit after successful tests; avoid committing in a broken state
- The .claude/projects/ memory directory is tracked in git so work can resume after a fresh clone
- Before committing: run `patches/save-patches.sh` to capture any MuseScore source changes

## Deploy Key
- Private key: `deploy_key` (gitignored, keep safe)
- Public key: `deploy_key.pub` (tracked)
- SSH config alias: `github-ClaudeMuseScore` (configured in ~/.ssh/config)

## Standing Orders
- Commit + push + save to memory whenever a new feature is successfully added (autonomously, without being asked)
- Track enough files so that cloning from GitHub allows continuing right where we left off, including memories
