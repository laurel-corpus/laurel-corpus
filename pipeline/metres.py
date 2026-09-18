"""The metre of every poem, per poem, with the evidence that settled it.

Metre was recorded once per book. A Poetical Works holding two hundred poems in a dozen metres carried
a single guess for all of them, so every page under it repeated the same claim and most of those claims
were wrong. A section is where the evidence actually lives: one poem has a settled line length, a whole
book does not.

Four sources, in this order. Where somebody who knew has written down what a poem's metre is, that is
the answer, and measuring is what you do when nobody has:
  1. an authority, named and dated -- Alden 1903 and the other prosody handbooks, via authorities.py;
  2. the documented metre, where the poem is famous enough that the answer is published and settled;
  3. the scanner in scansion.py, which proposes each metre in turn and tests the words against it;
  4. nothing. A poem whose verse will not settle is left without a metre rather than given a guess.

Writes site/data/metres.json:  {slug: {"work": [name, confidence, source],
                                      "sections": {sectionId: [name, confidence, source]}}}

    python3 metres.py           -> build it, then readings.py, which stores each line's reading in it
    python3 metres.py --score   -> score the scanner against the documented metres and stop
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from generic import DOCUMENTED
from scansion import describe, analyse, FLOOR
from authorities import build as authorities
from scansion import evidence, best_line
from teiread import load_work

from _paths import SITE
DATA = os.path.join(SITE, 'data')
WORKS = os.path.join(DATA, 'works')

# Enough lines to settle a metre, few enough that Paradise Lost does not take a minute by itself. A
# hundred lines of a poem say everything about its measure that ten thousand would.
SAMPLE = 200

def load(p, d=None):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d

def section_lines(sec):
    """(lines, stanza sizes) for a poem, capped, and never cutting a stanza in half -- a half stanza
    would report a shape the poet did not write, and the shape is what names a common measure."""
    lines, sizes = [], []
    for st in sec.get('stanzas', []):
        if len(lines) >= SAMPLE: break
        lines.extend(st); sizes.append(len(st))
    return lines, sizes

def published():
    """The metre of a poem as an article on that poem states it: pipeline/poem-metres.json, from
    poemmetres.py. {slug: {section: record}}, records with a foot only; free verse and sprung rhythm
    carry a name and no foot, and are kept so the page can say so."""
    d = load(os.path.join(HERE, 'poem-metres.json'), {}) or {}
    return d.get('poems', {})

def agreement(lines, foot, feet):
    """How far the scanner agrees with a metre somebody published: the mean agreement of the lines
    read in that foot at that length, on the same scale as a measured confidence."""
    evs = [evidence(t) for t in lines]
    evs = [e for e in evs if e]
    if not evs: return 0.0
    return round(sum(best_line(e, foot, prefer=feet)[0] for e in evs) / len(evs), 3)

AUTH, PUB = {}, {}

def one(w):
    """Everything decided about one work: what a pool worker does, with the authorities and the
    published metres already loaded in the parent before it forked."""
    slug = w['slug']
    wk = load_work(slug)
    if not wk: return None
    disagree, scored = [], None
    named = sections_named = sections_total = 0
    secs = {}
    book_lines, book_sizes = [], []
    for s in wk.get('sections', []):
        if s.get('prose'): continue          # the edition prints it as prose; there is no metre to settle
        sections_total += 1
        lines, sizes = section_lines(s)
        if len(book_lines) < SAMPLE * 2:
            book_lines.extend(lines[:40]); book_sizes.extend(sizes)
        if len(lines) < 6: continue
        name, conf, foot, feet = analyse(lines, sizes)
        # An authority outranks the measurement. The measured foot and length are kept beside it,
        # because the reader tapping a line still needs a template to mark it against -- but the
        # name, and the confidence, come from the person who signed their work.
        # An authority outranks the measurement -- but only where it is talking about the same
        # thing. Alden prints SPECIMENS: he quotes the four short lines of Pope's Ode on Solitude
        # to illustrate two-stress iambic, and the poem itself is tetrameter. Reading his label as
        # the poem's metre published 'iambic dimeter' over a poem in tetrameter, and 'trochaic
        # trimeter' over To a Skylark, whose stanza is three trochaic trimeters and an alexandrine.
        #
        # So his judgement is taken where it and the measurement are describing the same verse --
        # the foot agrees -- and is otherwise kept as what it is: a citation, recorded beside the
        # poem, saying which line of it he quoted and for what.
        # A published statement about THIS poem outranks the measurement, whether or not the two
        # agree: 'The Raven is written in trochaic octameter' is about the whole poem, where Alden
        # quotes specimens. The measured name and confidence stay beside it, and the confidence
        # recorded is the scanner's agreement read in the published metre, so the page can say
        # who named it and how far the scanner goes along.
        pub = PUB.get(slug, {}).get(s['id'])
        if pub:
            cite = 'Wikipedia: ' + pub['article']
            if pub.get('foot') and pub['foot'] in ('iambic', 'trochaic', 'anapaestic', 'dactylic') and pub.get('feet'):
                agree = agreement(lines, pub['foot'], pub['feet'])
                secs[s['id']] = [pub['metre'], agree, cite, pub['foot'], pub['feet'], name, round(conf, 3), pub.get('url')]
            else:
                secs[s['id']] = [pub['metre'], 0.0, cite, None, None, name, round(conf, 3), pub.get('url')]
            sections_named += 1
            if name and name != pub['metre']: disagree.append((slug, s['id'], pub['metre'], name, cite, bool(name.split()[0] == pub['metre'].split()[0])))
            continue
        auth = AUTH.get(slug, {}).get(s['id'])
        if auth:
            # An authority still outranks the measurement when the measurement declines to name
            # anything. analyse() now withholds a name from a poem whose lines are not lengths the
            # metre can make, and it returns the foot regardless, so the two can still be compared:
            # a scholar who says trochaic and a measurement that reads trochaic agree, whether or
            # not the measurement was willing to publish a length of its own.
            same = (name.split()[0] if name else foot) == auth['metre'].split()[0]
            if name and name != auth['metre']:
                disagree.append((slug, s['id'], auth['metre'], name, auth['cite'], bool(same)))
            if same:
                secs[s['id']] = [auth['metre'], 1.0, auth['cite'], foot, feet]
                sections_named += 1
                continue
        if name:
            # The foot and the count travel with the name so a reader tapping a line can be shown
            # that line read against this poem's own metre, rather than against an assumption that
            # every poem alternates.
            secs[s['id']] = [name, round(conf, 3), 'measured', foot, feet]
            sections_named += 1

    # A book of many metres has no metre. Dickinson's collected poems came out 'iambic trimeter'
    # -- one label stamped across four hundred poems in common measure, short measure, tetrameter
    # and hymn stanzas alike, which is the very claim this file exists to stop making. Where the
    # poems have their own answers and those answers disagree, the book is left without one.
    doc = DOCUMENTED.get(slug)
    wname, wconf = describe(book_lines, book_sizes) if book_lines else (None, 0.0)
    # A book of many metres has no metre -- but the test has to be on the FOOT, not on the whole name.
    # Evangeline is eleven sections of dactyls whose lines run six feet in some and five in others,
    # and comparing full names read that as a disagreement and withdrew the metre from the most famous
    # hexameter poem in English. What makes a book metrically mixed is walking in different feet.
    own = collections.Counter(v[0].split()[0] for v in secs.values())
    if len(secs) >= 5 and own and own.most_common(1)[0][1] / len(secs) < 0.6:
        wname, wconf = None, 0.0
    if doc:
        scored = (slug, doc, wname, wconf)
        work_entry = [doc, 1.0, 'documented']
    elif wname:
        work_entry = [wname, round(wconf, 3), 'measured']
    else:
        work_entry = [None, round(wconf, 3), 'unsettled']
    if work_entry[0]: named += 1
    return {'slug': slug, 'entry': {'work': work_entry, 'sections': secs}, 'disagree': disagree, 'scored': scored,
            'named': named, 'sections_total': sections_total, 'sections_named': sections_named}

def build(score_only=False):
    lib = load(os.path.join(DATA, 'library.json'), []) or []
    global AUTH, PUB
    AUTH = authorities(); PUB = published()
    disagree = []
    out, scored = {}, []
    named = sections_named = sections_total = 0
    # One core did every poem in turn and took an hour. The works are independent, so they go to a
    # pool of workers, forked so each already holds the authorities and the published metres.
    import multiprocessing as mp
    with mp.get_context('fork').Pool(max(1, mp.cpu_count() - 2)) as pool:
        results = pool.map(one, lib, chunksize=1)
    for r in results:
        if not r: continue
        out[r['slug']] = r['entry']; disagree.extend(r['disagree'])
        if r['scored']: scored.append(r['scored'])
        named += r['named']; sections_total += r['sections_total']; sections_named += r['sections_named']

    if score_only:
        # The one test the scanner's design never saw: these labels come from published scholarship and
        # were written down before the scanner existed. Small, but genuinely held out.
        ok = sum(1 for _, d, g, _ in scored if d == g)
        近 = sum(1 for _, d, g, _ in scored if g and d.split()[0] == g.split()[0])
        print('%-28s %-24s %s' % ('work', 'documented', 'scanner'))
        for slug, d, g, c in scored:
            print('  %s %-26s %-24s %-24s %s' % ('ok ' if d == g else 'NO ', slug, d, g or '(unsettled)',
                                                 ('%.0f%%' % (c * 100)) if c else ''))
        print('\n%d of %d agree exactly; %d of %d agree on the foot' % (ok, len(scored), 近, len(scored)))
        return

    # Never write an empty file over a full one. Run this where the poems cannot be found -- a checkout
    # without them, a path that resolved somewhere unexpected -- and the alternative is to replace the
    # published metres.json with two bytes and report success.
    if not out:
        print('no works could be read from %s -- nothing written' % DATA)
        return 1
    json.dump(out, open(os.path.join(DATA, 'metres.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    kinds = collections.Counter()
    for v in out.values():
        for e in v['sections'].values(): kinds[e[0]] += 1
    print('%d works, %d with a metre; %s of %s poems get one of their own'
          % (len(out), named, format(sections_named, ','), format(sections_total, ',')))
    print('metres found across the library:')
    for k, n in kinds.most_common(20): print('   %6s  %s' % (format(n, ','), k))
    if disagree:
        print('\nwhere an authority and the measurement disagree:')
        for slug, sid, said, measured, cite, same in disagree:
            print('   %-3s %-24s %-20s %s says %-22s we measured %s'
                  % ('foot' if same else 'FOOT', slug[:24], sid[:20], cite, said, measured))
        print('   (FOOT = the foot itself differs, which is a real disagreement; foot = only the length,')
        print('    which usually means the authority was quoting part of the poem, not all of it)')
    print('written to %s' % os.path.join(DATA, 'metres.json'))

if __name__ == '__main__':
    sys.exit(build('--score' in sys.argv) or 0)
