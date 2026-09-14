"""Metres named by a scholar, with the scholar named.

Where somebody who knew has written down what a poem's metre is, that is the answer, and the measurement
here is a fallback. So the order of resort is

    1. an authority, named and dated       -- 'trochaic tetrameter, after Alden 1903'
    2. the documented table in generic.py  -- settled scholarship, no single citation
    3. the scanner in scansion.py          -- measured, with a confidence
    4. nothing at all                      -- said plainly, rather than guessed

This file is step 1. It reads the specimens harvested from the old prosody handbooks and keeps only
those that can be tied to a poem actually in the library, matched on the poet AND the title -- matching
on the title alone put Shelley's To a Skylark against Meredith's, and Swinburne's The Birds against
William Carlos Williams's, which is exactly the sort of confident error this file exists to avoid.

    python3 authorities.py            what it would claim, and on whose authority
    python3 authorities.py --write    write site/data/authorities.json
"""
import json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
from _paths import SITE

SOURCES = {
    'alden-matched.json': {
        'cite': 'Alden 1903',
        'full': ('Raymond MacDonald Alden, English Verse: Specimens Illustrating its Principles '
                 'and History (New York: Henry Holt, 1903)'),
        'url': 'https://www.gutenberg.org/ebooks/32262',
    },
}

# 'four-stress trochaic' is how Alden counts; 'trochaic tetrameter' is how this site names it.
LEN = {'one': 'monometer', 'two': 'dimeter', 'three': 'trimeter', 'four': 'tetrameter',
       'five': 'pentameter', 'six': 'hexameter', 'seven': 'heptameter', 'eight': 'octameter'}
FOOT = {'iambic': 'iambic', 'trochaic': 'trochaic', 'anapestic': 'anapaestic',
        'anapaestic': 'anapaestic', 'dactylic': 'dactylic'}

def our_name(metre):
    m = re.match(r'(\w+)-stress\s+(\w+)', metre.strip().lower())
    if not m: return None
    n, foot = LEN.get(m.group(1)), FOOT.get(m.group(2))
    return '%s %s' % (foot, n) if n and foot else None

def build():
    out = {}
    for fname, src in SOURCES.items():
        p = os.path.join(HERE, fname)
        if not os.path.exists(p): continue
        for x in json.load(open(p, encoding='utf-8')):
            name = our_name(x['metre'])
            if not name: continue
            out.setdefault(x['slug'], {})[x['section']] = {
                'metre': name, 'as_printed': x['metre'],
                'cite': src['cite'], 'full': src['full'], 'url': src['url'],
                'poet': x['poet'], 'title': x['title'],
            }
    return out

if __name__ == '__main__':
    a = build()
    n = sum(len(v) for v in a.values())
    print('%d poems in %d works carry a metre named by an authority' % (n, len(a)))
    for slug, secs in sorted(a.items()):
        for sid, e in secs.items():
            print('   %-30s %-22s %-24s %s' % (slug[:30], sid[:22], e['metre'], e['cite']))
    if '--write' in sys.argv:
        p = os.path.join(SITE, 'data', 'authorities.json')
        json.dump(a, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print('\nwritten to %s' % p)
