---
name: chord-analysis
description: music21-based chord analysis bridge (analyze_chords.py) — detects key, chordifies, outputs chord symbols and Roman numerals
metadata:
  type: project
---

`analyze_chords.py` is a Python bridge that uses MIT's music21 library (v10.1, BSD) to perform harmonic analysis on MIDI or MusicXML files and write chord symbols back.

Features:
- Auto key detection (Krumhansl-Schmuckler algorithm)
- Chordify (salami-slice all parts into simultaneous chords)
- Chord symbol identification via `harmony.chordSymbolFromChord()`
- Roman numeral analysis via `roman.romanNumeralFromChord()`
- MIDI enharmonic respelling based on detected key
- Per-measure reduction mode
- MusicXML output with chord symbols that MuseScore can render

Setup: `python3 -m venv venv && venv/bin/pip install music21`

**Why:** User wants to import MIDI/karaoke files and automatically identify what chords are being played at each beat/measure.

**How to apply:** Use this as the primary analysis tool. Future improvements could include: better enharmonic handling, non-chord tone filtering, floating key detection for modulating pieces, integration as a MuseScore plugin via QProcess.

Related: [[musescore-build]], [[standing-orders]]
