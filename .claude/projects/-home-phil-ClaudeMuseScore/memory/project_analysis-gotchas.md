---
name: analysis-gotchas
description: Practical gotchas learned from testing chord analysis on real MIDI files (Bach + 5 rock songs) — saves debugging time
metadata:
  type: project
---

Observations from testing analyze_chords.py and analyze_by_instrument.py on real MIDI files. Encoded as warnings for future work.

**MIDI file formats matter:**
- Format 0 MIDI = single track, channels distinguish instruments. music21 collapses everything into one part by default. `analyze_by_instrument.py` handles this by splitting on channel while preserving event timing (rebuilds DeltaTime events from absolute times).
- Format 1 MIDI = separate tracks per instrument. Works out of the box.
- Use `file *.mid` to identify format.

**Key detection ambiguities:**
- Relative major/minor confidence is often nearly tied (e.g., Yesterday: D minor 0.798 vs F major 0.787). Yesterday is actually F major. music21 reports the alternative — show it.
- Songs that modulate (Bohemian Rhapsody) get one summary key; this is a known limitation. Floating key detection via `analysis.floatingKey.KeyAnalyzer` is a future improvement.
- Confidences seen on tested rock songs: 0.80–0.90 range is normal for clean MIDIs.

**MusicXML export pitfalls:**
- Drum/percussion parts crash export with `Instrument instance ... not found in instrumentStream`. Workaround: catch the exception, remove percussion parts, retry. Already implemented in `analyze_chords.py`.
- RomanNumeral objects (Chord subclass with pitches) also crash export. Workaround: use `TextExpression` instead. Already implemented.
- "Cannot Be Identified" chord strings will crash `ChordSymbol()` constructor — filter them out before writing back.

**MIDI enharmonic spelling:**
- MIDI loses spelling (only stores pitch numbers). After import, F# minor pieces get spelled with Bb instead of A#, Eb instead of D#, etc.
- `_respell_midi_pitches()` heuristically respells based on detected key signature. Helps but not perfect.

**Per-instrument polyphony as chord-content signal:**
- Polyphonic instruments (piano, acoustic guitar): avg_polyphony 2.5–3.5
- Monophonic instruments (bass, vocals, lead clarinet): avg_polyphony ≈1.0
- This is just a hint; user wants a more sophisticated ranking later — don't lock in polyphony alone as the deciding factor.

**MIDI sources for testing:**
- bitmidi.com has direct .mid downloads (no registration). URLs like https://bitmidi.com/uploads/NNNNN.mid
- Tested songs: Hotel California (101107), Let It Be (100821), Yesterday (100895), Nothing Else Matters (73573), Bohemian Rhapsody (87216)
- Also: music21's own corpus (`corpus.parse('bwv66.6')` etc.) is good for testing

Related: [[chord-analysis]], [[section-detection]]
