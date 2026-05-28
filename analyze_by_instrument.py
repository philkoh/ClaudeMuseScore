#!/usr/bin/env python3
"""
Per-instrument chord analysis.

For each instrument/part in a MIDI or MusicXML file, runs chord analysis
independently and produces:
  1. A per-instrument chord-per-measure sequence
  2. A side-by-side comparison table
  3. A JSON dump for later structural analysis (chord n-grams, section detection)

Usage:
    ./analyze_by_instrument.py input.mid [--per-beat] [--json out.json] [--csv out.csv]
"""

import argparse
import json
import sys
import os
from pathlib import Path
from collections import defaultdict


def analyze_per_instrument(input_path, per_beat=False, verbose=True):
    from music21 import converter, chord, harmony, roman, key

    if verbose:
        print(f"Loading {input_path}...")

    is_midi = str(input_path).lower().endswith(('.mid', '.midi', '.kar'))
    if is_midi:
        score = _load_midi_split_by_channel(input_path, verbose=verbose)
    else:
        score = converter.parse(str(input_path))

    detected_key = score.analyze('key')
    if verbose:
        alt = detected_key.alternateInterpretations[0] if detected_key.alternateInterpretations else None
        print(f"Detected key: {detected_key} (confidence: {detected_key.correlationCoefficient:.3f})")
        if alt:
            print(f"  Alternative: {alt} (confidence: {alt.correlationCoefficient:.3f})")

    if str(input_path).lower().endswith(('.mid', '.midi', '.kar')):
        _respell_midi_pitches(score, detected_key)

    parts_data = []
    for idx, part in enumerate(score.parts):
        inst_name = _get_instrument_name(part, idx)
        is_perc = _is_percussion(part)
        if verbose:
            print(f"\n[{idx}] {inst_name}{' (percussion)' if is_perc else ''}")
        if is_perc:
            parts_data.append({
                'index': idx,
                'name': inst_name,
                'percussion': True,
                'chords': [],
            })
            continue

        chord_events = _analyze_part(part, detected_key, per_beat)
        if verbose:
            polyphony = _avg_polyphony(chord_events)
            print(f"  {len(chord_events)} chord events, avg polyphony: {polyphony:.2f}")

        parts_data.append({
            'index': idx,
            'name': inst_name,
            'percussion': False,
            'avg_polyphony': _avg_polyphony(chord_events),
            'chords': chord_events,
        })

    return {
        'input': str(input_path),
        'key': str(detected_key),
        'key_confidence': detected_key.correlationCoefficient,
        'parts': parts_data,
    }


def _load_midi_split_by_channel(input_path, verbose=True):
    """Load MIDI, splitting each track by channel if necessary (format 0 support)."""
    from music21 import converter, midi
    from music21.midi import translate as midi_translate

    mf = midi.MidiFile()
    mf.open(str(input_path))
    mf.read()
    mf.close()

    needs_split = False
    if len(mf.tracks) <= 2:
        channels_seen = set()
        for trk in mf.tracks:
            for ev in trk.events:
                if ev.channel is not None:
                    channels_seen.add(ev.channel)
        if len(channels_seen) > 1:
            needs_split = True

    if needs_split:
        if verbose:
            print(f"  (Format 0 MIDI detected; splitting by channel)")
        new_tracks = _split_tracks_by_channel(mf.tracks)
        mf.tracks = new_tracks
        mf.format = 1

    score = midi_translate.midiFileToStream(mf)
    return score


def _split_tracks_by_channel(tracks):
    """Split each track into one track per MIDI channel, preserving timing."""
    from music21 import midi
    new_tracks = []
    next_index = 1

    for trk in tracks:
        timed_events = []
        timed_meta = []
        abs_time = 0
        i = 0
        events = trk.events
        while i < len(events):
            ev = events[i]
            if ev.isDeltaTime():
                abs_time += ev.time
                if i + 1 < len(events):
                    next_ev = events[i + 1]
                    if next_ev.channel is None:
                        timed_meta.append((abs_time, next_ev))
                    else:
                        timed_events.append((abs_time, next_ev))
                    i += 2
                else:
                    i += 1
            else:
                if ev.channel is None:
                    timed_meta.append((abs_time, ev))
                else:
                    timed_events.append((abs_time, ev))
                i += 1

        channels = sorted(set(ev.channel for _, ev in timed_events))

        if len(channels) <= 1:
            new_tracks.append(trk)
            continue

        for ch in channels:
            ch_events = [(t, ev) for t, ev in timed_events if ev.channel == ch]
            combined = sorted(timed_meta + ch_events, key=lambda x: x[0])

            new_trk = midi.MidiTrack(next_index)
            next_index += 1
            new_events = []
            prev_time = 0
            for abs_t, ev in combined:
                dt = midi.DeltaTime(new_trk)
                dt.time = abs_t - prev_time
                new_events.append(dt)
                new_events.append(ev)
                prev_time = abs_t
            new_trk.events = new_events
            new_tracks.append(new_trk)

    return new_tracks


def _get_instrument_name(part, idx):
    from music21 import instrument
    inst = part.getInstrument(returnDefault=False)
    if inst is None:
        for el in part.recurse().getElementsByClass(instrument.Instrument):
            inst = el
            break
    if inst is not None:
        name = inst.instrumentName or inst.partName or type(inst).__name__
        if name and name != 'Instrument':
            return name
    if part.partName:
        return part.partName
    return f"Part {idx}"


def _is_percussion(part):
    from music21 import instrument
    for inst in part.recurse().getElementsByClass(instrument.Instrument):
        if hasattr(inst, 'midiChannel') and inst.midiChannel == 9:
            return True
        if isinstance(inst, instrument.UnpitchedPercussion):
            return True
    for el in part.recurse():
        if type(el).__name__ == 'Unpitched':
            return True
    return False


def _analyze_part(part, detected_key, per_beat):
    from music21 import chord as m21chord, harmony, roman, stream

    try:
        chordified = part.chordify()
    except Exception:
        return []

    if not per_beat:
        chordified = _reduce_to_measure(chordified)

    events = []
    for c in chordified.recurse().getElementsByClass(m21chord.Chord):
        if len(c.pitches) == 0:
            continue
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

        try:
            rn = roman.romanNumeralFromChord(c_closed, detected_key)
            roman_fig = rn.figure
        except Exception:
            roman_fig = "?"

        events.append({
            'measure': c.measureNumber or 0,
            'beat': float(c.beat) if hasattr(c, 'beat') else 0.0,
            'symbol': symbol,
            'roman': roman_fig,
            'pitches': [str(p) for p in c.pitches],
            'pitch_classes': sorted(set(p.pitchClass for p in c.pitches)),
        })

    return events


def _reduce_to_measure(chordified):
    from music21 import stream, chord
    reduced = stream.Part()
    for m in chordified.getElementsByClass('Measure'):
        new_m = stream.Measure(number=m.number)
        new_m.offset = m.offset
        chords = list(m.getElementsByClass(chord.Chord))
        chords = [c for c in chords if len(c.pitches) > 0]
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


def _avg_polyphony(events):
    if not events:
        return 0.0
    return sum(len(e['pitch_classes']) for e in events) / len(events)


def _respell_midi_pitches(score, detected_key):
    from music21 import pitch
    key_sharps = detected_key.sharps
    for n in score.recurse().getElementsByClass('Note'):
        if n.pitch.accidental and abs(n.pitch.accidental.alter) > 0:
            try:
                if _should_respell(n.pitch, key_sharps):
                    n.pitch = pitch.Pitch(n.pitch.nameWithOctave).getEnharmonic()
            except Exception:
                pass


def _should_respell(p, key_sharps):
    natural_name = p.step
    acc = p.accidental
    if acc is None:
        return False
    if key_sharps >= 0 and acc.name == 'flat' and natural_name in 'BEADGCF'[:key_sharps]:
        return True
    if key_sharps < 0 and acc.name == 'sharp' and natural_name in 'FCGDAEB'[:abs(key_sharps)]:
        return True
    return False


def print_comparison_table(data, max_measures=None):
    """Print a side-by-side table of measure -> chord for each non-percussion instrument."""
    parts = [p for p in data['parts'] if not p['percussion']]
    if not parts:
        print("No non-percussion parts to compare.")
        return

    by_measure = defaultdict(dict)
    for p in parts:
        for e in p['chords']:
            m = e['measure']
            if m not in by_measure[p['name']]:
                by_measure[p['name']][m] = e['symbol']

    all_measures = sorted({m for p in parts for e in p['chords'] for m in [e['measure']] if m > 0})
    if max_measures:
        all_measures = all_measures[:max_measures]

    col_w = 18
    name_w = 6
    header = f"{'Meas':>{name_w}}  " + "  ".join(
        f"{_truncate(p['name'], col_w):<{col_w}}" for p in parts
    )
    print(f"\n{header}")
    print("-" * len(header))

    for m in all_measures:
        row = f"{m:>{name_w}}  " + "  ".join(
            f"{_truncate(by_measure[p['name']].get(m, '-'), col_w):<{col_w}}"
            for p in parts
        )
        print(row)


def _truncate(s, n):
    s = str(s)
    if len(s) <= n:
        return s
    return s[:n-1] + '…'


def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Wrote {path}")


def save_csv(data, path):
    parts = [p for p in data['parts'] if not p['percussion']]
    by_measure = defaultdict(dict)
    for p in parts:
        for e in p['chords']:
            m = e['measure']
            if m not in by_measure[p['name']]:
                by_measure[p['name']][m] = e['symbol']

    all_measures = sorted({m for p in parts for e in p['chords'] for m in [e['measure']] if m > 0})
    headers = ['measure'] + [p['name'] for p in parts]
    with open(path, 'w') as f:
        f.write(','.join(_csv_escape(h) for h in headers) + '\n')
        for m in all_measures:
            row = [str(m)] + [_csv_escape(by_measure[p['name']].get(m, '')) for p in parts]
            f.write(','.join(row) + '\n')
    print(f"Wrote {path}")


def _csv_escape(s):
    s = str(s)
    if ',' in s or '"' in s or '\n' in s:
        return '"' + s.replace('"', '""') + '"'
    return s


def main():
    parser = argparse.ArgumentParser(
        description="Per-instrument chord analysis for structural section detection")
    parser.add_argument("input", help="Input MIDI or MusicXML file")
    parser.add_argument("--per-beat", action="store_true",
                        help="One chord per beat (default: one per measure)")
    parser.add_argument("--json", help="Save full results as JSON")
    parser.add_argument("--csv", help="Save measure-vs-instrument matrix as CSV")
    parser.add_argument("--max-measures", type=int, default=None,
                        help="Limit table output to N measures")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    data = analyze_per_instrument(args.input, per_beat=args.per_beat,
                                  verbose=not args.quiet)

    if not args.quiet:
        print_comparison_table(data, max_measures=args.max_measures)

    if args.json:
        save_json(data, args.json)
    if args.csv:
        save_csv(data, args.csv)


if __name__ == "__main__":
    main()
