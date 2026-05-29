---
name: version-alignment
description: align_versions.py — chord-sequence Needleman-Wunsch alignment of multiple MIDI versions with transposition search
metadata:
  type: project
---

`align_versions.py` aligns multiple MIDI/MusicXML versions of the same song using their chord progressions. Built 2026-05-28 after the per-instrument analyzer.

**Pipeline:**
1. For each file: chordify whole score → one chord per measure → classify as (root_pc, quality) tuples
2. For each pair (reference vs each other): try all 12 transpositions of B, run Needleman-Wunsch with custom scoring
3. Report best transposition + alignment + structural diff classified as intro/middle/outro

**Scoring:**
- MATCH (exact root+quality): +2
- ROOT_MATCH (same root, different quality): +1
- RELATED (relative major/minor 3rd away): 0
- MISMATCH: -2
- GAP: -1

**Tested on 5 versions of Doobie Brothers "Listen To The Music":**
- 01 karaoke (A maj) vs 02 studio (A maj): score 252, 126/126 exact match — confirmed same arrangement
- 04 v1_guitar (G maj) vs 05 v2_drumsplit (A maj): score 89, -2 semitones, 95%/95% coverage — same arrangement transposed
- 04 vs 01 (A maj): score 27, +2 semitones — correctly detects G→A transposition needed
- 03 incognito (e min) vs 01: score -26 — flagged as different arrangement (radical reharmonization)

**Output sections:**
- Section-level summary: coverage %, intro/middle/outro classification of differences
- Detailed structural diff: MATCH/EXTRA segments with measure ranges
- `--full-table` flag for measure-by-measure pair listing

**Known limitations / future work:**
- Single global transposition only — doesn't detect mid-song key changes (would need windowed alignment or segment-level transposition search)
- Chord identification noise causes many short matches with gaps when arrangements differ slightly
- "Score" threshold for "same song?" decision not formalized — currently inspect manually
- Alignment is one-to-one; can't yet detect "verse 1 = verse 2" structural repetition within ONE file (that's the larger section-detection problem)

**Why:** User asked to align multiple versions and identify (a) key transpositions, (b) intro length differences, (c) outro differences, (d) middle repetition count differences, (e) new ending material. All five are now detectable.

**How to apply:** This is the cross-version alignment tool. For within-file structural repetition (chorus/verse detection), see [[section-detection]] memory — that's a related but distinct problem.

Related: [[chord-analysis]], [[section-detection]], [[analysis-gotchas]]
