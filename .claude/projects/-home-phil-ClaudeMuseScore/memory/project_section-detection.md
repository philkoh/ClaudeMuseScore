---
name: section-detection
description: Larger goal — identify repeated sections (chorus/verse) across MIDI variations using multiple strategies, starting with per-instrument chord n-grams
metadata:
  type: project
---

User wants to identify structurally repeated sections (e.g., "measures 24-34 = chorus, measures 74-84 = same chorus") in MIDI/MuseScore files, even when bassist/guitarist/etc. vary their parts between iterations.

Plan: build multiple strategies, run each, compare where they agree/disagree per measure.

**Strategies discussed:**
- Harmonic: chord n-grams (chosen first), Roman numeral, bass-line root
- Melodic: top-voice contour, melodic n-grams
- Rhythmic: per-measure onset patterns, drum-track hash
- Texture: active-track signature, velocity envelope
- MIR-style: self-similarity matrix (SSM), lyric matching (karaoke)

**Currently built (2026-05-28):** `analyze_by_instrument.py` — per-instrument chord analysis. Foundation for chord n-gram strategy. Handles format 0 MIDI by splitting on channel. Reports `avg_polyphony` per instrument as natural hint for which parts best convey chord content.

**Next steps:**
- Build chord n-gram matching across measures
- User wants to rank instruments by how reliably they convey chords (TBD; polyphony is a starting hint)
- Then add other strategies and a comparison runner

**Why:** Long-term goal of repository — understand and manipulate song structure semantically.

**How to apply:** When extending, keep per-instrument analysis separate from cross-instrument aggregation. Don't lock in an instrument-ranking heuristic yet — user wants to develop this carefully.

Related: [[chord-analysis]], [[standing-orders]]
