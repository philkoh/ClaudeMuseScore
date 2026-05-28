---
name: cross-platform
description: Repo is co-developed on Ubuntu and Windows 11 — code must stay portable (use musescore_path.py, no hardcoded paths)
metadata:
  type: project
---

The project is co-developed on:
- Ubuntu 26.04 (primary, where MuseScore was first built)
- Windows 11 (secondary)

**Rules for staying cross-platform:**
- No hardcoded paths in Python code. Use `from musescore_path import require_mscore` to locate the MuseScore binary.
- Build artifacts (`MuseScore/build/`, `venv/`) are gitignored — each machine builds independently.
- Customizations to MuseScore source are tracked as patch files in `patches/` (run `save-patches.sh` or `save-patches.ps1` before committing, and `apply-patches.sh`/`.ps1` after a fresh clone).
- Both `.sh` and `.ps1` versions of the patch scripts exist.
- `.gitattributes` normalizes line endings (LF for source, CRLF for `.bat`/`.ps1`, binary for MIDI/PNG/etc.).
- Each machine gets its OWN deploy key (don't copy private keys). GitHub allows multiple deploy keys per repo.

**Windows build differs from Linux:**
- Generator: `"Visual Studio 17 2022"` instead of Ninja
- Build command: `cmake --build . --config RelWithDebInfo --parallel` (no `-j N`)
- Binary name: `MuseScore5.exe` (Windows) vs `mscore` (Linux)
- Toolchain: MSVC 2022 + Qt 6.8+ from Qt online installer

**Why:** User wants to work on this project from either machine and have the customized MuseScore app build/run on both.

**How to apply:** When adding new code, always consider Windows compatibility. Test path handling, line endings, and shell command invocations. The `musescore_path.py` helper handles binary location; extend it (rather than hardcoding) if you need other tool paths.

Related: [[repo-setup]], [[musescore-build]], [[standing-orders]]
