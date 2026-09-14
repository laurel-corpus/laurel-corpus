"""Score this scanner against hand-annotated poetry that is not For Better For Verse.

Why: accuracy.md has had to say that trochaic and dactylic detection is "essentially untested", because
the only corpus available was For Better For Verse, and 62 of its 88 poems are iambic. A high score
there mostly measures whether the scanner can count feet, not whether it can tell a trochee from an iamb.

Thomas Haider's Metrical Tagging in the Wild (EACL 2021) gathers three English gold corpora into one
format -- For Better For Verse, EPG64, and the prosodic corpus -- 3,183 lines with a stress on every
syllable, and 44% of them are not iambic: 417 trochaic lines, 256 anapaestic, 219 amphibrachic, 209
dactylic. That is the blind spot, filled.

    https://github.com/tnhaider/metrical-tagging-in-the-wild

The data carries no licence, so it is used here the way For Better For Verse is: as a ruler, never as a
source. Nothing from it is copied into the corpus, and it lives in cache/, which is not in the
repository.

    python3 goldscore.py            score, and break the result down by metre
    python3 goldscore.py --errors   also print lines where the scanner and the gold disagree most
"""
import collections, io, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CACHE = os.path.join(HERE, 'cache', 'gold')
BASE = ('https://raw.githubusercontent.com/tnhaider/metrical-tagging-in-the-wild/'
        'master/data/English/SmallGold/eng_meter_3fold/')

def fetch(name):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name)
    if not os.path.exists(p): urllib.request.urlretrieve(BASE + name, p)
    return p

def load():
    """Each row is one syllable: index, text, stress, ., POS, position-in-word, metre, fine metre, line.

    Words are rebuilt from the position-in-word column: 0 marks a word of one syllable and anything
    above 1 continues the word before it. The column is not perfectly regular -- 'harbinger' comes
    through as har/bing/er numbered 0/1/2, so it rebuilds as two words -- which is why the dictionary
    hit rate is reported below rather than assumed.
    """
    out = []
    for name in ('train.txt', 'test.txt'):
        cur = []
        for row in io.open(fetch(name), encoding='utf-8'):
            row = row.rstrip('\n')
            if not row.strip():
                if cur: out.append(cur)
                cur = []; continue
            f = row.split('\t')
            if len(f) >= 9: cur.append(f)
        if cur: out.append(cur)
    return out

def words_of(line):
    """Rebuild the line's words from its syllables.

    The position-in-word column is the obvious guide and it is not reliable: 'harbinger' arrives numbered
    0/1/2 and 'morning' 1/2, so grouping on it alone produced 'Fan cyand' for 'Fancy and', 'hon our' for
    'honour', 'gar dens' for 'gardens'. Every one of those then counted against the scanner as a syllable
    it had miscounted, when the fault was here.

    So the column proposes and the dictionary disposes: choose the segmentation that leaves the fewest
    pieces the dictionary has never heard of, breaking ties towards the boundaries the column suggests.
    """
    syl = [f[1] for f in line]
    starts = [i for i, f in enumerate(line) if f[5] in ('0', '1')]
    n = len(syl)
    if not n: return []
    from analyze import CMU, norm
    import re as _re
    def known(a, b):
        """A join is only credible if the dictionary agrees the word has exactly the syllables that were
        joined into it. Without that test the segmentation happily made words out of the right letters
        and the wrong number of beats, and every one of those then read as a miscount."""
        w = _re.sub(r"[^a-z']", '', norm(''.join(syl[a:b])))
        if not w: return False
        ph = CMU.get(w) or CMU.get(w.replace("'", ''))
        if not ph: return False
        return sum(1 for x in ph[0] if x[-1].isdigit()) == (b - a)
    INF = float('inf')
    best = [INF] * (n + 1); back = [0] * (n + 1); best[0] = 0
    for j in range(1, n + 1):
        for i in range(max(0, j - 5), j):
            if best[i] == INF: continue
            cost = best[i] + (0 if known(i, j) else 1.6)
            if i not in starts: cost += 0.35          # the column said this was not a word boundary
            cost += 0.01 * (j - i)                     # all else equal, prefer shorter words
            if cost < best[j]: best[j], back[j] = cost, i
    out, j = [], n
    while j > 0:
        i = back[j]; out.append(''.join(syl[i:j])); j = i
    return out[::-1]

def main(show_errors=False):
    from analyze import CMU, norm
    from scansion import evidence
    gold = load()
    print('gold lines: %s   syllables: %s' % (format(len(gold), ','), format(sum(len(l) for l in gold), ',')))

    # How trustworthy is the rebuilt text? If the words are not words, nothing below means anything.
    seen = good = 0
    for line in gold:
        for w in words_of(line):
            core = re.sub(r"[^a-z']", '', norm(w))
            if core: seen += 1; good += core in CMU
    print('rebuilt words found in the pronouncing dictionary: %.1f%% of %s' % (100.0*good/seen, format(seen, ',')))

    agree = collections.Counter(); total = collections.Counter()
    hit = collections.Counter(); opin = collections.Counter(); counted = collections.Counter()
    misses = []
    for line in gold:
        metre = line[0][6]
        total[metre] += 1
        text = ' '.join(words_of(line))
        try: ev = evidence(text)
        except Exception: continue
        if len(ev) != len(line):        # his syllabifier and theirs disagree: not comparable
            continue
        counted[metre] += 1
        right = 0; n = 0
        for (wants, _), f in zip(ev, line):
            if wants is None: continue   # the words have no opinion; the metre decides
            n += 1; opin[metre] += 1
            ok = (wants == '1') == (f[2] == '+')
            right += ok; hit[metre] += ok
        if n and right / n < 0.6 and len(misses) < 12:
            misses.append((metre, text, ''.join(f[2] for f in line),
                           ''.join('1' if w == '1' else '0' if w == '0' else 'x' for w, _ in ev)))
        agree[metre] += 0

    print('\n%-12s %7s %8s %9s %9s' % ('metre', 'lines', 'usable', 'syllables', 'agree'))
    for m, t in total.most_common():
        u, o, h = counted[m], opin[m], hit[m]
        print('%-12s %7d %7d%% %9s %8.1f%%' % (m, t, round(100.0*u/t) if t else 0,
              format(o, ','), 100.0*h/o if o else 0))
    O, H = sum(opin.values()), sum(hit.values())
    C, T = sum(counted.values()), sum(total.values())
    print('%-12s %7d %7d%% %9s %8.1f%%' % ('ALL', T, round(100.0*C/T), format(O, ','), 100.0*H/O))
    print('\nusable = lines where this syllabifier and the gold agree on how many syllables there are.')
    print('agree  = of the syllables where the words themselves have an opinion, how often it matches.')
    if show_errors:
        print('\nlines where they disagree most:')
        for m, t, g, p in misses:
            print('  [%s] %s' % (m, t[:70])); print('     gold %s' % g); print('     ours %s' % p)

if __name__ == '__main__':
    main('--errors' in sys.argv)
