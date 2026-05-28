#!/usr/bin/env python3
"""
Harmonic analysis bridge: analyzes a MIDI or MusicXML file using music21,
detects chords and key, and writes chord symbols back into a MusicXML file
that MuseScore can open.

Usage:
    ./analyze_chords.py input.mid [output.musicxml]
    ./analyze_chords.py input.mid --roman          # Roman numeral analysis
    ./analyze_chords.py input.mid --both           # chord symbols + Roman numerals
    ./analyze_chords.py input.mid --open           # open result in MuseScore
    ./analyze_chords.py input.mid --key Am          # override detected key
    ./analyze_chords.py input.mid --per-measure    # one chord per measure (simplified)
"""

import argparse
import sys
import os
from pathlib import Path


def _respell_midi_pitches(score, detected_key):
    """Fix enharmonic spellings from MIDI import using the detected key context."""
    from music21 import pitch

    key_sig_sharps = detected_key.sharps

    for n in score.recurse().getElementsByClass('Note'):
        if n.pitch.accidental and abs(n.pitch.accidental.alter) > 0:
            try:
                n.pitch.getEnharmonic()
                n.pitch = pitch.Pitch(n.pitch.nameWithOctave).getEnharmonic() \
                    if _should_respell(n.pitch, key_sig_sharps) else n.pitch
            except Exception:
                pass


def _should_respell(p, key_sharps):
    """Heuristic: respell if the current spelling uses accidentals foreign to the key."""
    from music21 import pitch
    natural_name = p.step
    acc = p.accidental
    if acc is None:
        return False
    if key_sharps >= 0 and acc.name == 'flat' and natural_name in 'BEADGCF'[:key_sharps]:
        return True
    if key_sharps < 0 and acc.name == 'sharp' and natural_name in 'FCGDAEB'[:abs(key_sharps)]:
        return True
    return False


def analyze(input_path, output_path=None, mode="symbols", key_override=None,
            per_measure=False, open_in_musescore=False, verbose=True):
    from music21 import converter, chord, harmony, roman, key, stream, meter, note

    if verbose:
        print(f"Loading {input_path}...")
    score = converter.parse(str(input_path))

    if key_override:
        detected_key = key.Key(key_override)
        if verbose:
            print(f"Using specified key: {detected_key}")
    else:
        detected_key = score.analyze('key')
        alt_key = detected_key.alternateInterpretations[0] if detected_key.alternateInterpretations else None
        if verbose:
            print(f"Detected key: {detected_key} (confidence: {detected_key.correlationCoefficient:.3f})")
            if alt_key:
                print(f"  Alternative: {alt_key} (confidence: {alt_key.correlationCoefficient:.3f})")

    is_midi = str(input_path).lower().endswith(('.mid', '.midi', '.kar'))
    if is_midi:
        if verbose:
            print("Respelling MIDI pitches for key context...")
        _respell_midi_pitches(score, detected_key)

    if verbose:
        print("Chordifying score...")
    chordified = score.chordify()

    if per_measure:
        chordified = _reduce_to_measure(chordified)

    results = []
    unidentified = 0

    for c in chordified.recurse().getElementsByClass(chord.Chord):
        c_closed = c.closedPosition(forceOctave=4, inPlace=False)

        symbol = None
        try:
            cs = harmony.chordSymbolFromChord(c_closed)
            fig = cs.figure if cs.figure else ""
            if "Cannot Be Identified" not in fig and fig:
                symbol = fig
        except Exception:
            pass
        if symbol is None:
            symbol = c_closed.pitchedCommonName
            unidentified += 1

        try:
            rn = roman.romanNumeralFromChord(c_closed, detected_key)
            roman_fig = rn.figure
        except Exception:
            roman_fig = "?"

        measure_num = c.measureNumber if c.measureNumber else 0
        beat = c.beat if hasattr(c, 'beat') else 0

        results.append({
            'measure': measure_num,
            'beat': beat,
            'offset': c.offset,
            'symbol': symbol,
            'roman': roman_fig,
            'pitches': ' '.join(str(p) for p in c.pitches),
            'common_name': c_closed.commonName,
        })

    if verbose:
        print(f"\nKey: {detected_key}")
        print(f"Chords identified: {len(results) - unidentified}/{len(results)}"
              f" ({unidentified} fell back to common name)")
        print(f"\n{'Meas':>4} {'Beat':>5}  {'Symbol':<14} {'Roman':<10} {'Name':<28} Pitches")
        print("-" * 95)
        for r in results:
            print(f"{r['measure']:4d} {r['beat']:5.1f}  {r['symbol']:<14} {r['roman']:<10} "
                  f"{r['common_name']:<28} {r['pitches']}")

    if verbose:
        print(f"\nWriting chord symbols into score...")
    _write_symbols_to_score(score, chordified, results, mode, detected_key)

    if output_path is None:
        stem = Path(input_path).stem
        output_path = str(Path(input_path).parent / f"{stem}_analyzed.musicxml")

    try:
        score.write('musicxml', fp=output_path)
    except Exception as e:
        if verbose:
            print(f"Export failed ({e}), retrying without percussion parts...")
        _remove_percussion_parts(score)
        score.write('musicxml', fp=output_path)
    if verbose:
        print(f"Saved: {output_path}")

    if open_in_musescore:
        _open_in_musescore(output_path)

    return results, detected_key, output_path


def _reduce_to_measure(chordified):
    from music21 import stream, chord
    reduced = stream.Part()
    for m in chordified.getElementsByClass('Measure'):
        new_m = stream.Measure(number=m.number)
        new_m.offset = m.offset
        chords = list(m.getElementsByClass(chord.Chord))
        if chords:
            best = max(chords, key=lambda c: (
                len(set(p.pitchClass for p in c.pitches)),
                c.quarterLength
            ))
            best.offset = 0
            best.quarterLength = m.barDuration.quarterLength
            new_m.append(best)
        reduced.append(new_m)
    return reduced


def _is_valid_chord_symbol(sym):
    skip = ("Cannot Be Identified", "triad", "chord", "trichord",
            "tetrachord", "tetramirror", "Minor Third", "Perfect Fourth",
            "Perfect Fifth", "incomplete", "enharmonic")
    return not any(s in sym for s in skip)


def _write_symbols_to_score(score, chordified, results, mode, detected_key):
    from music21 import harmony, expressions

    part = score.parts[0] if score.parts else score

    for r in results:
        measure_num = r['measure']
        offset = r['offset']

        m = None
        for candidate in part.getElementsByClass('Measure'):
            if candidate.number == measure_num:
                m = candidate
                break
        if m is None:
            continue

        local_offset = offset - m.offset
        sym = r['symbol']
        roman_fig = r['roman']

        if not _is_valid_chord_symbol(sym):
            continue

        if mode in ("symbols", "both"):
            try:
                cs = harmony.ChordSymbol(sym)
                m.insert(local_offset, cs)
            except Exception:
                pass

        if mode in ("roman", "both") and roman_fig != "?":
            try:
                te = expressions.TextExpression(roman_fig)
                te.style.fontSize = 10
                te.placement = 'below'
                m.insert(local_offset, te)
            except Exception:
                pass


def _remove_percussion_parts(score):
    """Remove percussion/drum parts that cause MusicXML export errors."""
    if not hasattr(score, 'parts'):
        return
    to_remove = []
    for p in score.parts:
        dominated_by_unpitched = False
        for inst in p.recurse().getElementsByClass('Instrument'):
            if hasattr(inst, 'midiChannel') and inst.midiChannel == 9:
                dominated_by_unpitched = True
                break
        for el in p.recurse():
            if type(el).__name__ == 'Unpitched':
                dominated_by_unpitched = True
                break
        if dominated_by_unpitched:
            to_remove.append(p)
    for p in to_remove:
        score.remove(p)


def _open_in_musescore(path):
    import subprocess
    from musescore_path import require_mscore
    mscore = require_mscore()
    subprocess.Popen([mscore, path],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Opened in MuseScore: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze chords in a MIDI or MusicXML file using music21")
    parser.add_argument("input", help="Input MIDI (.mid/.kar) or MusicXML file")
    parser.add_argument("output", nargs="?", help="Output MusicXML path (default: <input>_analyzed.musicxml)")
    parser.add_argument("--roman", action="store_const", const="roman", dest="mode",
                        help="Add Roman numeral analysis instead of chord symbols")
    parser.add_argument("--both", action="store_const", const="both", dest="mode",
                        help="Add both chord symbols and Roman numerals")
    parser.add_argument("--key", type=str, default=None,
                        help="Override key detection (e.g., 'Am', 'C#', 'Eb minor')")
    parser.add_argument("--per-measure", action="store_true",
                        help="Reduce to one chord per measure")
    parser.add_argument("--open", action="store_true",
                        help="Open result in MuseScore after analysis")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress verbose output")
    parser.set_defaults(mode="symbols")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    analyze(args.input, args.output, mode=args.mode, key_override=args.key,
            per_measure=args.per_measure, open_in_musescore=args.open,
            verbose=not args.quiet)


if __name__ == "__main__":
    main()
