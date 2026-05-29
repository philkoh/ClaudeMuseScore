#!/usr/bin/env python3
"""
Align multiple MIDI/MusicXML versions of the same song using chord sequences.

For each file, extracts a primary chord-per-measure sequence, then runs
pairwise alignment (Needleman-Wunsch) with key-transposition search.

Detects:
  - Whole-song or section key transpositions
  - Extra/missing pickup (intro) measures
  - Extra/missing outro measures
  - Different repetition counts in the middle
  - New ending material

Usage:
    ./align_versions.py file1.mid file2.mid [file3.mid ...]
    ./align_versions.py file1.mid file2.mid --reference 0 --output alignment.txt
"""

import argparse
import sys
import os
import json
from pathlib import Path
from collections import defaultdict


# -------- Step 1: Extract per-measure chord sequence --------

def get_chord_sequence(input_path, verbose=True):
    """Return a list of (measure_number, root_pc, quality) tuples.
    root_pc is 0-11 (C=0, ...); quality is 'maj', 'min', 'dom7', etc.
    Returns (sequence, detected_key)."""
    from music21 import converter, chord as m21chord, harmony, key

    if verbose:
        print(f"  Loading {input_path}...")

    is_midi = str(input_path).lower().endswith(('.mid', '.midi', '.kar'))
    if is_midi:
        from analyze_by_instrument import _load_midi_split_by_channel
        score = _load_midi_split_by_channel(input_path, verbose=False)
    else:
        score = converter.parse(str(input_path))

    detected_key = score.analyze('key')

    chordified = score.chordify()
    measure_chords = {}

    for c in chordified.recurse().getElementsByClass(m21chord.Chord):
        if len(c.pitches) == 0:
            continue
        m = c.measureNumber
        if not m:
            continue
        if m not in measure_chords:
            measure_chords[m] = []
        measure_chords[m].append(c)

    sequence = []
    for m in sorted(measure_chords.keys()):
        best = max(measure_chords[m], key=lambda c: (
            len(set(p.pitchClass for p in c.pitches)),
            c.quarterLength
        ))
        root_pc, quality = _classify_chord(best)
        sequence.append((m, root_pc, quality))

    if verbose:
        print(f"  Key: {detected_key} (conf {detected_key.correlationCoefficient:.3f})")
        print(f"  Extracted {len(sequence)} chord events (measures {sequence[0][0] if sequence else '?'}-{sequence[-1][0] if sequence else '?'})")

    return sequence, detected_key


def _classify_chord(c):
    """Return (root_pc, quality) where quality is one of:
    'maj', 'min', 'dim', 'aug', 'dom7', 'maj7', 'min7', 'dim7', 'hdim7',
    'sus', 'pow' (power chord), 'mono' (single note), 'other'"""
    try:
        root = c.root()
        root_pc = root.pitchClass
    except Exception:
        if c.pitches:
            return (c.pitches[0].pitchClass, 'mono')
        return (-1, 'other')

    pcs = set(p.pitchClass for p in c.pitches)
    if len(pcs) == 1:
        return (root_pc, 'mono')

    intervals = sorted((p - root_pc) % 12 for p in pcs)

    has_3 = 3 in intervals
    has_4 = 4 in intervals
    has_5 = 7 in intervals
    has_b5 = 6 in intervals
    has_a5 = 8 in intervals
    has_b7 = 10 in intervals
    has_7 = 11 in intervals
    has_2 = 2 in intervals
    has_4th = 5 in intervals

    if not has_3 and not has_4:
        if has_5 and not has_b7:
            return (root_pc, 'pow')
        if has_b7:
            return (root_pc, 'dom7' if has_5 or has_b5 else 'pow')
        if has_2 or has_4th:
            return (root_pc, 'sus')
        return (root_pc, 'pow')

    if has_4 and has_5 and has_b7:
        return (root_pc, 'dom7')
    if has_3 and has_5 and has_b7:
        return (root_pc, 'min7')
    if has_3 and has_b5 and 9 in intervals:
        return (root_pc, 'dim7')
    if has_3 and has_b5 and has_b7:
        return (root_pc, 'hdim7')
    if has_4 and has_5 and has_7:
        return (root_pc, 'maj7')

    if has_4 and has_5:
        return (root_pc, 'maj')
    if has_3 and has_5:
        return (root_pc, 'min')
    if has_3 and has_b5:
        return (root_pc, 'dim')
    if has_4 and has_a5:
        return (root_pc, 'aug')

    return (root_pc, 'other')


def chord_to_str(root_pc, quality):
    names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    if root_pc < 0:
        return '?'
    suffix = {'maj':'', 'min':'m', 'dim':'°', 'aug':'+', 'dom7':'7',
              'maj7':'M7', 'min7':'m7', 'dim7':'°7', 'hdim7':'ø7',
              'sus':'sus', 'pow':'5', 'mono':'.', 'other':'?'}
    return names[root_pc] + suffix.get(quality, '?')


def transpose(seq, semitones):
    """Transpose a chord sequence by `semitones`."""
    return [(m, (pc + semitones) % 12 if pc >= 0 else pc, q) for m, pc, q in seq]


# -------- Step 2: Needleman-Wunsch alignment --------

# Scoring
MATCH_SCORE = 2          # exact chord match (root + quality)
ROOT_MATCH_SCORE = 1     # same root, different quality (e.g., G vs G7)
RELATED_SCORE = 0        # related (e.g., G vs Em — relative minor/major)
MISMATCH_SCORE = -2      # different chord
GAP_PENALTY = -1         # insertion or deletion


def _pair_score(a, b):
    """Score for matching chord a against chord b. Each is (pc, quality)."""
    _, pc_a, q_a = a
    _, pc_b, q_b = b
    if pc_a == pc_b and q_a == q_b:
        return MATCH_SCORE
    if pc_a == pc_b:
        return ROOT_MATCH_SCORE
    if (pc_b - pc_a) % 12 in (3, 9) and {q_a, q_b} <= {'maj', 'min', 'maj7', 'min7'}:
        return RELATED_SCORE
    return MISMATCH_SCORE


def align(seq_a, seq_b):
    """Needleman-Wunsch global alignment.
    Returns (score, alignment) where alignment is a list of (a_idx, b_idx)
    with None for gaps."""
    n, m = len(seq_a), len(seq_b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    bt = [[None] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        dp[i][0] = dp[i-1][0] + GAP_PENALTY
        bt[i][0] = 'up'
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j-1] + GAP_PENALTY
        bt[0][j] = 'left'

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = dp[i-1][j-1] + _pair_score(seq_a[i-1], seq_b[j-1])
            up = dp[i-1][j] + GAP_PENALTY
            left = dp[i][j-1] + GAP_PENALTY
            best = max(diag, up, left)
            dp[i][j] = best
            if best == diag:
                bt[i][j] = 'diag'
            elif best == up:
                bt[i][j] = 'up'
            else:
                bt[i][j] = 'left'

    alignment = []
    i, j = n, m
    while i > 0 or j > 0:
        d = bt[i][j]
        if d == 'diag':
            alignment.append((i-1, j-1))
            i -= 1; j -= 1
        elif d == 'up':
            alignment.append((i-1, None))
            i -= 1
        else:
            alignment.append((None, j-1))
            j -= 1
    alignment.reverse()
    return dp[n][m], alignment


def best_alignment_with_transposition(seq_a, seq_b):
    """Try all 12 transpositions of seq_b; return best (transpose_semitones, score, alignment).
    Transposition is reported in the range -5..+6 (closest to 0)."""
    best = (0, float('-inf'), None)
    for t in range(12):
        seq_b_t = transpose(seq_b, t)
        score, al = align(seq_a, seq_b_t)
        if score > best[1]:
            display_t = t if t <= 6 else t - 12
            best = (display_t, score, al, t)
    return best[0], best[1], best[2]


# -------- Step 3: Report --------

def find_segments(alignment):
    """Classify regions of the alignment into:
       - 'match': consecutive aligned pairs
       - 'gap_a': measures only in B (insertion in B / missing in A)
       - 'gap_b': measures only in A (deletion from B / extra in A)
    Returns list of (type, start_a_idx, end_a_idx, start_b_idx, end_b_idx)."""
    segments = []
    current = None
    for a_idx, b_idx in alignment:
        if a_idx is not None and b_idx is not None:
            kind = 'match'
        elif a_idx is None:
            kind = 'gap_a'
        else:
            kind = 'gap_b'
        if current and current['kind'] == kind:
            current['pairs'].append((a_idx, b_idx))
        else:
            if current:
                segments.append(current)
            current = {'kind': kind, 'pairs': [(a_idx, b_idx)]}
    if current:
        segments.append(current)
    return segments


def report_alignment(name_a, seq_a, key_a, name_b, seq_b, key_b, transpose_st, score, alignment):
    print(f"\n{'='*70}")
    print(f"  {name_a}  vs  {name_b}")
    print(f"  Key A: {key_a}    Key B: {key_b}    Detected transposition: {transpose_st:+d} semitones")
    print(f"  Alignment score: {score}")
    print(f"{'='*70}")

    seq_b_t = transpose(seq_b, transpose_st)

    segments = find_segments(alignment)

    print(f"\nStructural diff:")
    diff_lines = []
    for seg in segments:
        if seg['kind'] == 'match':
            n = len(seg['pairs'])
            a_first = seq_a[seg['pairs'][0][0]][0]
            a_last = seq_a[seg['pairs'][-1][0]][0]
            b_first = seq_b[seg['pairs'][0][1]][0]
            b_last = seq_b[seg['pairs'][-1][1]][0]
            exact = sum(1 for ai, bi in seg['pairs']
                        if (seq_a[ai][1], seq_a[ai][2]) == (seq_b_t[bi][1], seq_b_t[bi][2]))
            diff_lines.append(
                f"  MATCH  A m.{a_first:>3}-{a_last:<3} ~ B m.{b_first:>3}-{b_last:<3}  ({n} measures, {exact}/{n} exact)"
            )
        elif seg['kind'] == 'gap_a':
            indices = [bi for _, bi in seg['pairs']]
            b_first = seq_b[indices[0]][0]
            b_last = seq_b[indices[-1]][0]
            diff_lines.append(
                f"  EXTRA in B   B m.{b_first:>3}-{b_last:<3}  ({len(indices)} measures absent from A)"
            )
        else:
            indices = [ai for ai, _ in seg['pairs']]
            a_first = seq_a[indices[0]][0]
            a_last = seq_a[indices[-1]][0]
            diff_lines.append(
                f"  EXTRA in A   A m.{a_first:>3}-{a_last:<3}  ({len(indices)} measures absent from B)"
            )

    for line in diff_lines:
        print(line)

    print(f"\nMeasure-by-measure (showing chord pairs; transposition {transpose_st:+d} applied to B):")
    print(f"  {'A meas':>7}  {'A chord':<10}    {'B meas':>7}  {'B chord (transposed)':<22}  match?")
    print(f"  {'-'*7}  {'-'*10}    {'-'*7}  {'-'*22}  {'-'*6}")
    for a_idx, b_idx in alignment:
        a_meas = str(seq_a[a_idx][0]) if a_idx is not None else '-'
        a_chord = chord_to_str(*seq_a[a_idx][1:]) if a_idx is not None else '-'
        b_meas = str(seq_b[b_idx][0]) if b_idx is not None else '-'
        if b_idx is not None:
            b_chord_orig = chord_to_str(*seq_b[b_idx][1:])
            b_chord_t = chord_to_str(*seq_b_t[b_idx][1:])
            b_chord_str = f"{b_chord_orig}→{b_chord_t}" if transpose_st != 0 else b_chord_orig
        else:
            b_chord_str = '-'
        match = ''
        if a_idx is not None and b_idx is not None:
            if (seq_a[a_idx][1], seq_a[a_idx][2]) == (seq_b_t[b_idx][1], seq_b_t[b_idx][2]):
                match = '✓'
            elif seq_a[a_idx][1] == seq_b_t[b_idx][1]:
                match = '~root'
            else:
                match = '✗'
        print(f"  {a_meas:>7}  {a_chord:<10}    {b_meas:>7}  {b_chord_str:<22}  {match}")


def main():
    parser = argparse.ArgumentParser(
        description="Align multiple versions of a song via chord-sequence comparison")
    parser.add_argument("files", nargs="+", help="MIDI or MusicXML files")
    parser.add_argument("--reference", type=int, default=0,
                        help="Index of the reference file (default: 0)")
    parser.add_argument("--full-table", action="store_true",
                        help="Print the full measure-by-measure table (default: structural diff only)")
    parser.add_argument("--quiet", action="store_true")

    args = parser.parse_args()

    if len(args.files) < 2:
        print("Need at least 2 files to align.", file=sys.stderr)
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).resolve().parent))

    print("Extracting chord sequences...\n")
    sequences = []
    for path in args.files:
        print(f"[{path}]")
        seq, k = get_chord_sequence(path, verbose=not args.quiet)
        sequences.append((path, seq, k))

    ref_idx = args.reference
    ref_path, ref_seq, ref_key = sequences[ref_idx]

    for i, (path, seq, k) in enumerate(sequences):
        if i == ref_idx:
            continue
        transpose_st, score, alignment = best_alignment_with_transposition(ref_seq, seq)
        if args.full_table:
            report_alignment(ref_path, ref_seq, ref_key, path, seq, k,
                             transpose_st, score, alignment)
        else:
            _report_summary_only(ref_path, ref_seq, ref_key, path, seq, k,
                                 transpose_st, score, alignment)


def _print_section_classification(segments, seq_a, seq_b):
    """Classify gaps as intro / middle / outro relative to match positions."""
    match_segments = [s for s in segments if s['kind'] == 'match']
    if not match_segments:
        print(f"\nNo significant matches found — likely different arrangements.")
        return

    first_match_idx = segments.index(match_segments[0])
    last_match_idx = segments.index(match_segments[-1])

    intro_gaps = segments[:first_match_idx]
    outro_gaps = segments[last_match_idx + 1:]
    middle_gaps = [s for s in segments[first_match_idx + 1:last_match_idx]
                   if s['kind'] != 'match']

    total_matched = sum(len(s['pairs']) for s in match_segments)
    total_a = len(seq_a)
    total_b = len(seq_b)
    pct_a = 100 * total_matched / total_a if total_a else 0
    pct_b = 100 * total_matched / total_b if total_b else 0

    print(f"\nSection-level summary:")
    print(f"  Coverage: {total_matched} measures matched ({pct_a:.0f}% of A, {pct_b:.0f}% of B)")

    if intro_gaps:
        a_extra = sum(len(s['pairs']) for s in intro_gaps if s['kind'] == 'gap_b')
        b_extra = sum(len(s['pairs']) for s in intro_gaps if s['kind'] == 'gap_a')
        if a_extra:
            print(f"  Intro:  A has {a_extra} extra pickup/intro measures before main body starts")
        if b_extra:
            print(f"  Intro:  B has {b_extra} extra pickup/intro measures before main body starts")
    else:
        print(f"  Intro:  aligned from the start")

    if middle_gaps:
        n_inserts = sum(1 for s in middle_gaps)
        a_extra = sum(len(s['pairs']) for s in middle_gaps if s['kind'] == 'gap_b')
        b_extra = sum(len(s['pairs']) for s in middle_gaps if s['kind'] == 'gap_a')
        descr = []
        if a_extra:
            descr.append(f"A has {a_extra} extra measures inserted")
        if b_extra:
            descr.append(f"B has {b_extra} extra measures inserted")
        print(f"  Middle: {n_inserts} insertion segments — {'; '.join(descr)}")
        print(f"          (possibly different repetition counts, solos, or fills)")
    else:
        print(f"  Middle: no insertions — repetition structure matches")

    if outro_gaps:
        a_extra = sum(len(s['pairs']) for s in outro_gaps if s['kind'] == 'gap_b')
        b_extra = sum(len(s['pairs']) for s in outro_gaps if s['kind'] == 'gap_a')
        if a_extra:
            print(f"  Outro:  A has {a_extra} extra outro measures (possibly different ending or fade-out replacement)")
        if b_extra:
            print(f"  Outro:  B has {b_extra} extra outro measures (possibly different ending or fade-out replacement)")
    else:
        print(f"  Outro:  endings align")


def _report_summary_only(name_a, seq_a, key_a, name_b, seq_b, key_b,
                         transpose_st, score, alignment):
    print(f"\n{'='*70}")
    print(f"  {Path(name_a).name}  vs  {Path(name_b).name}")
    print(f"  Key A: {key_a}    Key B: {key_b}    Best transposition: {transpose_st:+d} semitones")
    print(f"  Alignment score: {score}")
    print(f"{'='*70}")

    seq_b_t = transpose(seq_b, transpose_st)
    segments = find_segments(alignment)

    _print_section_classification(segments, seq_a, seq_b)

    print(f"\nDetailed structural diff:")
    for seg in segments:
        if seg['kind'] == 'match':
            n = len(seg['pairs'])
            a_first = seq_a[seg['pairs'][0][0]][0]
            a_last = seq_a[seg['pairs'][-1][0]][0]
            b_first = seq_b[seg['pairs'][0][1]][0]
            b_last = seq_b[seg['pairs'][-1][1]][0]
            exact = sum(1 for ai, bi in seg['pairs']
                        if (seq_a[ai][1], seq_a[ai][2]) == (seq_b_t[bi][1], seq_b_t[bi][2]))
            print(f"  MATCH  A m.{a_first:>3}-{a_last:<3} ~ B m.{b_first:>3}-{b_last:<3}  ({n} measures, {exact}/{n} exact)")
        elif seg['kind'] == 'gap_a':
            indices = [bi for _, bi in seg['pairs']]
            b_first = seq_b[indices[0]][0]
            b_last = seq_b[indices[-1]][0]
            print(f"  EXTRA in B   B m.{b_first:>3}-{b_last:<3}  ({len(indices)} measures absent from A)")
        else:
            indices = [ai for ai, _ in seg['pairs']]
            a_first = seq_a[indices[0]][0]
            a_last = seq_a[indices[-1]][0]
            print(f"  EXTRA in A   A m.{a_first:>3}-{a_last:<3}  ({len(indices)} measures absent from B)")


if __name__ == "__main__":
    main()
