"""Score the scanner against verse a prosodist marked by hand, in a printed book.

The gold corpora the benchmarks use are two: For Better For Verse, 88 poems, and Haider's gathering,
3,183 lines. That is the whole modern supply, and it is thin where this library is thickest, in the
verse before 1800. But the handbooks of a century ago did the same work, by hand, in print: Schipper
sets an acute accent on the vowel of every stressed syllable, 'For thóusandés his hóndes máden dýe',
and his 1910 history holds five hundred and sixty such lines of modern English. Where an edition kept
the accents through digitisation, that is a ruler nobody has used.

markedin.py reads each book in its own notation and writes marked/<source>.tsv: the plain line and a
mark string, + for a beat, - for a slack, x where the prosodist marked nothing. That is all this reads. The marks are read as follows:
an acute on a vowel is the beat; a grave is a half beat and is counted as one; a bar is the caesura
and is ignored. Everything else is unstressed.

    python3 marked.py               score every source
    python3 marked.py schipper      one source
    python3 marked.py --show 12     print the lines the scanner gets most wrong
"""
import collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scansion as S

SOURCES = {
    'schipper':   {'cite': 'Schipper 1910',   'full': 'Jakob Schipper, A History of English Versification (Oxford, 1910)'},
    'saintsbury': {'cite': 'Saintsbury 1910', 'full': 'George Saintsbury, Historical Manual of English Prosody (London, 1910), Gutenberg 56187'},
    'brown':      {'cite': 'Brown 1851',      'full': "Goold Brown, The Grammar of English Grammars (New York, 1851), Part IV, Gutenberg 11615"},
    'latham':     {'cite': 'Latham 1841',     'full': 'R. G. Latham, A Handbook of the English Language, Part VI Prosody, Gutenberg 28436'},
    'leigh':      {'cite': 'Leigh 1840',      'full': 'Percival Leigh, The Comic English Grammar, ch. II Of Versification, Gutenberg 43397'},
    'guest':      {'cite': 'Guest 1882',      'full': "Edwin Guest, A History of English Rhythms, ed. W. W. Skeat (London, 1882), the lines the library also holds"},
    'skeat':      {'cite': 'Skeat 1894',      'full': "W. W. Skeat, Chaucer's Works vol. VI, Introduction, Versification (Oxford, 1894), Gutenberg 43097"},
    'kirkham':    {'cite': 'Kirkham 1829',    'full': 'Samuel Kirkham, English Grammar in Familiar Lectures, Versification, Gutenberg 14070'},
}

ACUTE = set('áéíóúýÁÉÍÓÚÝ')
GRAVE = set('àèìòùỳÀÈÌÒÙỲ')

def foot_of(g):
    """The foot a marked line is in, read off the marks themselves.

    A specimen in a handbook comes without its poem, so the scanner has nothing to settle the foot
    with; on the page, the prosodist's own marks say. Rising or falling from where the first beat
    falls; duple or triple from the spacing of the beats. This is what bench.py does with the gold
    corpus's metre label, and it measures the same claim: the reading a reader is shown once the poem's
    metre is known.
    """
    beats = [i for i, c in enumerate(g) if c == '+']
    if len(beats) < 2: return None
    gaps = [b - a for a, b in zip(beats, beats[1:])]
    triple = sum(1 for x in gaps if x == 3) > sum(1 for x in gaps if x == 2)
    # Rising or falling is decided by where MOST beats fall, not by the first one. An iambic line that
    # opens with a trochee starts on a beat, and that is the commonest substitution in the language;
    # calling every such line trochaic handed the scanner the wrong foot for exactly the lines a
    # prosodist most wants marked.
    period = 3 if triple else 2
    on_first = sum(1 for i in beats if i % period == 0)
    falling = on_first > len(beats) / 2.0
    # A line that opens slack-then-beat is rising whatever the rest of it does. The majority rule
    # filed Schipper's shifted-accent specimens, 'Surprised with blind flame and to her mind', as
    # trochaic because a beat displaced by one lands the rest on even positions; Schipper cites them
    # as iambic, and no falling metre opens on an iamb (Halle and Keyser). A trochaic line with an
    # extra initial syllable has its beats on odd positions throughout and was rising already.
    if g[:2] == '-+': falling = False
    if triple: return 'dactylic' if falling else 'anapaestic'
    return 'trochaic' if falling else 'iambic'

def load(name):
    """(plain line, marks) pairs from marked/<name>.tsv, as markedin.py wrote them."""
    path = os.path.join(HERE, 'marked', name + '.tsv')
    rows = []
    for raw in open(path, encoding='utf-8'):
        if '\t' not in raw: continue
        plain, m = raw.rstrip('\n').split('\t', 1)
        if len(m) >= 4 and '+' in m: rows.append((plain, m))
    return rows

def score(name, show=0):
    rows = load(name)
    src = SOURCES[name]
    n = syl = 0
    fixed_ok = fixed_n = 0
    met_ok = met_n = 0
    whole_ok = whole_n = 0
    inf_ok = inf_n = 0
    inwhole_ok = inwhole_n = 0
    kinds = collections.Counter()
    worst = []
    for plain, g in rows:
        n += 1
        ev = S.asked(plain, len(g))
        if len(ev) != len(g): continue
        syl += 1
        # what the words alone fix, before any metre is chosen
        words = ''.join('+' if k == '1' and w >= 1.0 else '-' if k == '0' and w >= 1.0 else 'x' for k, w in ev)
        pairs = [(o, c) for o, c in zip(words, g) if o in '+-' and c in '+-']
        fixed_n += len(pairs); fixed_ok += sum(1 for o, c in pairs if o == c)
        # what the reader is shown: the best reading in whichever foot fits this line best
        best = None
        for foot in S.FEET:
            a, w, feet = S.best_line(ev, foot)
            if best is None or a > best[0]: best = (a, foot, feet)
        if best and best[1]:
            pool = S.by_length(best[1]).get(len(ev), ())
            tpl = min((t for t in pool if t[1] == best[2]), key=lambda t: (t[2], t[0]), default=None)
            if tpl:
                read = tpl[0].replace('1', '+').replace('0', '-')
                wrong = sum(1 for r, c in zip(read, g) if c in '+-' and r != c)
                met_n += len(g); met_ok += len(g) - wrong
                whole_n += 1; whole_ok += (wrong == 0)
                if wrong: worst.append((wrong, plain, g, read))
        # and read in the foot the marks imply, which is what the poem would have told the scanner
        foot = foot_of(g)
        if foot:
            # The reading the scanner would actually choose in that foot, substitutions charged for,
            # which is what bench.py scores. The plainest template is the metre, not the reading, and a
            # prosodist's marks record the reading.
            from bench import best as _best
            tpl = _best(ev, [S.FEET[foot]])
            if tpl:
                read = tpl.replace('1', '+').replace('0', '-')
                bad = [i for i, (r, c) in enumerate(zip(read, g)) if c in '+-' and r != c]
                inf_n += len(g); inf_ok += len(g) - len(bad)
                inwhole_n += 1; inwhole_ok += (not bad)
                if bad:
                    # what kind of wrong: the whole line slid, or one foot bent
                    slid = any((k > 0 and read[k:] == g[:-k]) or (k < 0 and read[:k] == g[-k:]) for k in (1, -1, 2, -2))
                    if slid: kinds['the line slid by a syllable or a foot'] += 1
                    elif len(bad) <= 2 and all(g[i] == '-' for i in bad): kinds['a pyrrhic the scanner did not take'] += 1
                    elif len(bad) <= 2 and all(g[i] == '+' for i in bad): kinds['a spondee the scanner did not take'] += 1
                    elif len(bad) <= 2: kinds['one foot inverted'] += 1
                    else: kinds['scattered'] += 1
    pc = lambda a, b: 100.0 * a / b if b else 0.0
    print('%s: %d marked lines\n' % (src['cite'], n))
    print('  syllable count agrees                 %5.1f%%   (%d of %d)' % (pc(syl, n), syl, n))
    print('  stress, words only, where they fix    %5.1f%%   (%s syllables)' % (pc(fixed_ok, fixed_n), format(fixed_n, ',')))
    print('  stress, read in the best-fitting foot %5.1f%%   (%s syllables)' % (pc(met_ok, met_n), format(met_n, ',')))
    print('  lines every mark right                %5.1f%%   (%d of %d)' % (pc(whole_ok, whole_n), whole_ok, whole_n))
    print()
    print("  read in the foot the marks imply, as the poem would supply it:")
    print('    stress                              %5.1f%%   (%s syllables)' % (pc(inf_ok, inf_n), format(inf_n, ',')))
    print('    lines every mark right              %5.1f%%   (%d of %d)' % (pc(inwhole_ok, inwhole_n), inwhole_ok, inwhole_n))
    if kinds:
        print('    what kind of wrong, when wrong:')
        for k, v in kinds.most_common():
            print('      %-42s %4d' % (k, v))
    if show:
        print('\n  the worst of them:')
        for wrong, plain, g, read in sorted(worst, reverse=True)[:show]:
            print('\n     %s   (%d wrong)' % (plain[:70], wrong))
            print('     %-8s %s' % (src['cite'].split()[0], g))
            print('     %-8s %s' % ('ours', read))
            print('              %s' % ''.join('^' if r != c else ' ' for r, c in zip(read, g)))

if __name__ == '__main__':
    show = int(sys.argv[sys.argv.index('--show') + 1]) if '--show' in sys.argv else 0
    names = [a for a in sys.argv[1:] if a in SOURCES] or list(SOURCES)
    for i, name in enumerate(names):
        if i: print()
        score(name, show)
