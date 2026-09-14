"""The three numbers a scholar would ask for, measured on data never used to build anything.

    syllables   does the line have the number of syllables the annotators counted
    stress      of the syllables, how many carry the beat they marked
    foot        is the line read in the foot the poem is actually in

Scored on the control half of the gathered gold corpora (Haider 2021: For Better For Verse, EPG64 and
the prosodic corpus), which monostress.py and everything else were forbidden to look at.

Three ways of marking the stress are reported, because they are three different claims:

    words only   what the lexicon insists on, before any metre is considered
    free         the best template for this line, choosing foot and length per line
    in metre     the poem's own foot and length, which is what the reader actually shows

    python3 bench.py           the three numbers
    python3 bench.py --train   the development half instead, for tuning against
"""
import collections, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from goldsplit import load_one
from goldscore import words_of
import scansion as S

COARSE = {'iambic': 'iambic', 'troch': 'trochaic', 'anapaest': 'anapaestic', 'daktyl': 'dactylic'}

def best(ev, feet, want_len=None):
    """The reading the scanner would actually choose -- which means charging for substitutions.

    variants() returns {template: what it costs}, and iterating it gives only the keys. Scoring those
    without the cost let an iambic template bend two feet to imitate a trochaic line for nothing, so
    every falling metre read as iambic and the benchmark reported 0% on trochaic while the scanner
    itself was fine. A benchmark that does not charge what the scanner charges is measuring a different
    program.
    """
    b = (-1.0, None)
    for pat in feet:
        for n in range(1, 9):
            for tpl, c in S.variants(pat, n).items():
                if len(tpl) != len(ev): continue
                if want_len and len(tpl) != want_len: continue
                v = S.fit(ev, tpl); v = v[0] if isinstance(v, tuple) else v
                v -= S.SUB_COST * c
                if v > b[0]: b = (v, tpl)
    return b[1]

def run(split):
    gold = load_one(split)
    n_lines = syl_ok = 0
    raw = [0, 0]; free = [0, 0]; inmet = [0, 0]
    foot_ok = foot_n = 0
    by_metre = collections.defaultdict(lambda: [0, 0])
    for line in gold:
        n_lines += 1
        try: ev = S.evidence(' '.join(words_of(line)))
        except Exception: continue
        if len(ev) != len(line): continue
        syl_ok += 1
        want = COARSE.get(line[0][6])
        g = ''.join('1' if f[2] == '+' else '0' for f in line)

        for (w, wt), c in zip(ev, g):
            if w is None: continue
            raw[1] += 1; raw[0] += (w == '1') == (c == '1')
        a = best(ev, list(S.FEET.values()))
        if a:
            for x, c in zip(a, g): free[1] += 1; free[0] += x == c
        if want:
            # which foot does the line read as, unaided?
            pick, pv = None, -1.0
            for name, pat in S.FEET.items():
                bb = (-1.0, None)
                for n in range(1, 9):
                    for tpl, c in S.variants(pat, n).items():
                        if len(tpl) != len(ev): continue
                        v = S.fit(ev, tpl); v = v[0] if isinstance(v, tuple) else v
                        v -= S.SUB_COST * c
                        if v > bb[0]: bb = (v, tpl)
                if bb[1] is not None and bb[0] > pv: pick, pv = name, bb[0]
            if pick:
                foot_n += 1; foot_ok += pick == want
                by_metre[want][1] += 1; by_metre[want][0] += pick == want
            b = best(ev, [S.FEET[want]])
            if b:
                for x, c in zip(b, g): inmet[1] += 1; inmet[0] += x == c
    pc = lambda p: 100.0 * p[0] / p[1] if p[1] else 0.0
    print('%s: %s lines' % (split.replace('.txt', '').upper(), format(n_lines, ',')))
    print()
    print('  syllable count agrees      %5.1f%%   (%s of %s lines)'
          % (100.0*syl_ok/n_lines, format(syl_ok, ','), format(n_lines, ',')))
    print('  the foot the line reads in %5.1f%%   (%s lines)' % (100.0*foot_ok/foot_n if foot_n else 0, format(foot_n, ',')))
    print()
    print('  stress, words only         %5.1f%%   (%s syllables)' % (pc(raw), format(raw[1], ',')))
    print('  stress, free choice        %5.1f%%' % pc(free))
    print("  stress, in the poem's metre %5.1f%%   <- what the reader shows" % pc(inmet))
    print()
    print('  the foot, by what it really is:')
    for m, p in sorted(by_metre.items(), key=lambda kv: -kv[1][1]):
        print('     %-12s %5.1f%%  of %s' % (m, 100.0*p[0]/p[1], format(p[1], ',')))

if __name__ == '__main__':
    run('train.txt' if '--train' in sys.argv else 'test.txt')
