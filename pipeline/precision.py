"""What the scanner calls a poem whose metre nobody needs to measure.

bench.py scores against hand-annotated lines, and those corpora are deliberately balanced: Haider's
gathering is 44% non-iambic, because a corpus meant to test whether a scanner can tell a trochee from an
iamb would be useless if it were all iambs. Real English verse is not like that. This library is about
nine tenths iambic, and a scanner tuned until it finds every trochee on a balanced corpus will start
seeing trochees everywhere on an unbalanced one -- and the benchmark cannot show it, because the
benchmark has no opinion about how often a wrong answer is offered to a poem that was never in doubt.

That is not a hypothetical. Per-foot substitution took trochaic recall from 16% to 60% on the control
and, at the same time, took Shakespeare's sonnets from 4 wrong to 12, and every sonnet in the library
from 2.4% wrong to 14.5%.

So: a class of poem where the answer is known in advance and no annotation is needed. A sonnet is
fourteen lines of iambic pentameter; that is most of what the word means. Anything else the scanner says
about one is a false positive, and counting them is the precision this project was missing.

    python3 precision.py            score the sonnets
    python3 precision.py --sample N how many to read (default all)
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scansion import analyse
from teiread import load_work
from _paths import SITE
WORKS = os.path.join(SITE, 'data', 'works')

# Enough lines of a long poem to settle its measure, and no more. Paradise Lost does not become more
# obviously iambic pentameter at ten thousand lines than it is at two hundred.
SAMPLE = 200

def sonnets(limit=None):
    """Sections that are certainly sonnets: the word in the id, and fourteen lines."""
    lib = json.load(open(os.path.join(SITE, 'data', 'library.json'), encoding='utf-8'))
    for w in lib:
        wk = load_work(w['slug'])
        if not wk: continue
        for s in wk.get('sections', []):
            if 'sonnet' not in (s.get('id','') + ' ' + (s.get('title') or '')).lower(): continue
            lines, sizes = [], []
            for st in s.get('stanzas', []):
                lines.extend(st); sizes.append(len(st))
            # A 'sonnet' of ninety lines is a sequence under one heading, not a sonnet.
            if len(lines) != 14: continue
            yield w['slug'], s['id'], lines, sizes
            if limit and limit <= 0: return

def by_stated_metre(limit=None):
    """Sections of works whose EDITION says what the metre is.

    library.json carries a metre for the book, written from the edition's own front matter rather than
    measured here: eleven books of blank verse, twelve of heroic couplets. Both mean iambic pentameter
    in every section, so they are a second and much larger class where a wrong answer is visibly wrong.
    Only the unambiguous labels are used -- 'mixed' and 'mostly iambic pentameter' say the opposite of
    what a test needs, and free verse has no answer to be right about.
    """
    lib = json.load(open(os.path.join(SITE, 'data', 'library.json'), encoding='utf-8'))
    for w in lib:
        m = (w.get('meter') or '').strip().lower()
        if m not in ('blank verse', 'heroic couplets'): continue
        wk = load_work(w['slug'])
        if not wk: continue
        for s in wk.get('sections', []):
            lines, sizes = [], []
            for st in s.get('stanzas', []):
                if len(lines) >= SAMPLE: break
                lines.extend(st); sizes.append(len(st))
            if len(lines) < 8: continue      # too short to settle anything
            yield w['slug'], s['id'], lines, sizes

# What share of a class whose answer is known may be called something else before the build stops.
# Not zero: a few of these poems really are irregular, and a handful of the 'sonnets' are sonnets in
# name only. Set well above what a healthy scanner produces (0.5% and 1.5%) and well below the state
# that prompted writing this file at all, when per-foot substitution took the sonnets to 14.5%.
CEILING = 5.0

def score(label, rows, expect='iambic'):
    got = collections.Counter(); wrong = []; n = 0
    for slug, sid, lines, sizes in rows:
        name, conf, foot, feet = analyse(lines, sizes)
        got[name or '(unsettled)'] += 1; n += 1
        if name and not name.startswith(expect): wrong.append((slug, sid, name, conf))
    if not n: print('%s: nothing to score' % label); return 0
    print('\n%s -- %s poems, every one of them %s' % (label, format(n, ','), expect))
    print('   right foot            %5.1f%%' % (100*sum(v for k,v in got.items() if k.startswith(expect))/n))
    print('   WRONG foot            %5.1f%%   (%s)' % (100*len(wrong)/n, format(len(wrong), ',')))
    print('   left unsettled        %5.1f%%' % (100*got['(unsettled)']/n))
    if wrong:
        for k, v in collections.Counter(x[2] for x in wrong).most_common(6):
            print('      %5s  %s' % (format(v, ','), k))
    pct = 100 * len(wrong) / n
    if pct > CEILING:
        print('   !! %.1f%% is above the %.1f%% ceiling -- the scanner is calling too many of these' % (pct, CEILING))
        return 1
    return 0

def main(limit):
    got = collections.Counter()
    wrong = []
    n = 0
    for slug, sid, lines, sizes in sonnets():
        name, conf, foot, feet = analyse(lines, sizes)
        got[name or '(unsettled)'] += 1
        n += 1
        if name and not name.startswith('iambic'): wrong.append((slug, sid, name, conf))
        if limit and n >= limit: break
    named = sum(v for k, v in got.items() if k != '(unsettled)')
    right = got['iambic pentameter']
    print('%s sonnets read (fourteen lines each)' % format(n, ','))
    print('  iambic pentameter      %5.1f%%   (%s)' % (100*right/max(1,n), format(right, ',')))
    print('  some other iambic      %5.1f%%' % (100*sum(v for k,v in got.items() if k.startswith('iambic') and k!='iambic pentameter')/max(1,n)))
    print('  NOT iambic at all      %5.1f%%   <- every one of these is wrong' % (100*len(wrong)/max(1,n)))
    print('  left unsettled         %5.1f%%' % (100*got['(unsettled)']/max(1,n)))
    print('\nwhat it said instead:')
    for k, v in collections.Counter(x[2] for x in wrong).most_common(10):
        print('   %5s  %s' % (format(v, ','), k))
    print('\na few of them:')
    for slug, sid, name, conf in wrong[:8]:
        print('   %-26s %-22s %-22s %.2f' % (slug[:26], sid[:22], name, conf))
    pct = 100 * len(wrong) / max(1, n)
    if pct > CEILING:
        print('\n!! %.1f%% of sonnets called non-iambic, above the %.1f%% ceiling' % (pct, CEILING))
        return 1
    return 0

if __name__ == '__main__':
    lim = None
    if '--sample' in sys.argv: lim = int(sys.argv[sys.argv.index('--sample')+1])
    bad = main(lim) or 0
    bad += score('BLANK VERSE AND HEROIC COUPLETS', by_stated_metre(lim)) or 0
    sys.exit(1 if bad else 0)
