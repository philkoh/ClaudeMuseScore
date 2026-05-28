---
name: session-resume
description: Where we paused on 2026-05-28 — current state, next planned step, and how to resume
metadata:
  type: project
---

**Last session ended:** 2026-05-28, on commit `46a3ab0`. Everything pushed to GitHub.

**Recent commits:**
1. `4f82498` — Initial repo setup with deploy key, Claude memory, standing orders
2. `58ce692` — Add MuseScore 5.0.0-dev as submodule with patch-based customization workflow
3. `723f9de` — Add music21-based chord analysis bridge (analyze_chords.py)
4. `b651c2a` — Fix chord analysis for real-world MIDI files (percussion handling, etc.)
5. `46a3ab0` — Add per-instrument chord analysis (analyze_by_instrument.py)

**State of work:**
- MuseScore 5.0.0-dev built from source, working binary at `MuseScore/build/install/bin/mscore`
- Python venv at `venv/` with music21 10.1 installed
- Two analysis scripts working and tested on Bach + 5 rock MIDIs:
  - `analyze_chords.py` — whole-score chord symbols + Roman numerals
  - `analyze_by_instrument.py` — per-instrument chord sequences (foundation for section detection)

**Next planned step (chosen but not started):** Build the chord n-gram matcher for structural section detection. User selected this as Strategy #1 of several. Goal: identify that, e.g., "measures 24-34 = chorus" and "measures 74-84 = same chorus" even when bassist/guitarist vary their parts.

**Open design questions for next session:**
- Window size for n-grams (4 measures? 8? variable?)
- Fuzzy matching tolerance (allow substitutions? how many?)
- Instrument ranking — user explicitly wants to develop this carefully, NOT just use polyphony heuristic. For first cut, run the matcher per-instrument and show results separately.
- Output format — user previously rejected a 3-question form asking about output format and SSM strategy (interrupted to redirect work to per-instrument analysis). Don't re-ask the same set; if needed, ask one focused question.

**To resume after fresh clone:**
1. `git submodule update --init --recursive` (initializes MuseScore source)
2. `patches/apply-patches.sh` (applies any customizations)
3. Restore `deploy_key` private key and `~/.ssh/config` entry (or push via HTTPS)
4. Rebuild MuseScore: `cd MuseScore/build && cmake --build . --parallel $(nproc) && cmake --install . --config RelWithDebInfo`
5. Recreate Python env: `python3 -m venv venv && venv/bin/pip install music21`

**Why this memory exists:** User stops Claude Code between sessions; needs ability to resume from exact same place without losing context.

Related: [[chord-analysis]], [[section-detection]], [[analysis-gotchas]], [[standing-orders]], [[repo-setup]]
