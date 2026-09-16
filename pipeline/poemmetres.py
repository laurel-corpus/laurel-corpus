"""The metre of a poem as somebody has published it, poem by poem.

metres.py names a poem from an authority where one has been matched, from the documented metre of a
work famous enough to have one, and otherwise by measuring. Twenty-three works and nine poems were all
the first two sources gave. But a poem with a Wikipedia article of its own usually has its metre in
the lead ('The Raven ... is written in trochaic octameter'), and Wikidata knows which poems those are.
This asks Wikidata for every poem by each poet in the library that has an English article, reads the
article, keeps the sentence that names the metre, and writes pipeline/poem-metres.json for metres.py
to take as a source that outranks measurement. Facts, with the sentence they came from and the
article they came from, under the same attribution as the biographies (CC BY-SA).

    python3 poemmetres.py             every poet with a biography
    python3 poemmetres.py "John Keats" ...   only these

A statement is trusted from the article's lead, or from a sentence that says the poem is written or
composed in the metre; a metre merely mentioned elsewhere in the article is kept under 'doubts' for a
person to look at, and metres.py ignores it.
"""
import io, json, os, re, sys, time
import requests
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wikibios import S, API, fetch, is_disambiguation
from _paths import DATA

OUT = os.path.join(HERE, 'poem-metres.json')
SPARQL = 'https://query.wikidata.org/sparql'
H = {'User-Agent': 'laurelpoetry.com (garrett.dome1@gmail.com) poem metre survey'}
# poem, sonnet, ode, elegy, ballad, literary work, epic poem, hymn, narrative poem
CLASSES = 'wd:Q5185279 wd:Q80056 wd:Q7366 wd:Q3298013 wd:Q1093397 wd:Q7725634 wd:Q37707 wd:Q182659 wd:Q3554702'

TERM = re.compile(r"\b((?:iambic|trochaic|anap(?:a)?estic|dactylic|amphibrachic)\s+(?:mono|di|tri|tetra|penta|hexa|hepta|octa)meters?"
                  r"|heroic couplets?|blank verse|ballad (?:stanza|metre|meter)s?|common (?:metre|meter)|hymn (?:metre|meter)|Spenserian stanzas?"
                  r"|ottava rima|rhyme royal|terza rima|(?:Petrarchan|Shakespearean|Italian|English|Miltonic) sonnets?|alexandrines?|fourteeners?"
                  r"|sprung rhythm|free verse"
                  # the looser phrases articles actually use; each maps to a metre by form, or to a foot alone
                  r"|octosyllabic couplets?|(?<!Petrarchan )(?<!Shakespearean )(?<!Italian )(?<!English )(?<!Miltonic )sonnets?(?! sequence)|iambic pentameters?|in pentameters?|elegiac stanzas?|In Memoriam stanzas?|Burns stanzas?|limericks?)\b", re.I)
FEET = {'mono': 1, 'di': 2, 'tri': 3, 'tetra': 4, 'penta': 5, 'hexa': 6, 'hepta': 7, 'octa': 8}

def to_metre(term):
    """(name, foot, feet) in the site's own vocabulary, for a term the article used."""
    t = term.lower().rstrip('s')
    m = re.match(r'(iambic|trochaic|anap(?:a)?estic|dactylic|amphibrachic)\s+(\w+?)meter', t)
    if m:
        foot = {'anapestic': 'anapaestic'}.get(m.group(1), m.group(1))
        return ('%s %smeter' % (foot, m.group(2)), foot, FEET.get(m.group(2)))
    if t in ('heroic couplet', 'blank verse', 'ottava rima', 'rhyme royal', 'terza rima', 'spenserian stanza') or t.endswith('sonnet'):
        return ('iambic pentameter', 'iambic', 5)
    if t.startswith(('ballad', 'common', 'hymn')): return ('common measure', 'iambic', 4)
    if t.startswith('alexandrine'): return ('iambic hexameter', 'iambic', 6)
    if t.startswith('fourteener'): return ('iambic heptameter', 'iambic', 7)
    if t in ('sprung rhythm', 'free verse'): return (t, None, None)
    if t in ('sonnet', 'in pentameter', 'elegiac stanza'): return ('iambic pentameter', 'iambic', 5)
    if t in ('octosyllabic couplet', 'in memoriam stanza', 'burns stanza'): return ('iambic tetrameter', 'iambic', 4)
    if t == 'limerick': return ('anapaestic trimeter', 'anapaestic', 3)
    return None

def qid_of(titles):
    """Wikidata ids for Wikipedia article titles, fifty at a time."""
    out = {}
    for i in range(0, len(titles), 50):
        r = S.get(API, params={'action': 'query', 'prop': 'pageprops', 'ppprop': 'wikibase_item', 'redirects': 1, 'titles': '|'.join(titles[i:i + 50]), 'format': 'json'}, timeout=30).json()
        back = {}
        for x in r['query'].get('redirects', []): back[x['to']] = x['from']
        for x in r['query'].get('normalized', []): back[x['to']] = x['from']
        for p in r['query']['pages'].values():
            q = (p.get('pageprops') or {}).get('wikibase_item')
            if q: out[back.get(p['title'], p['title'])] = q
    return out

def poems_in_category(article):
    """Article titles in Wikipedia's 'Poetry by <poet>' category (and 'Poems by'), which is what the
    encyclopedia keeps for every poet with poem articles. The query service was tried first and
    answered one batch in three; the ordinary API answers at once."""
    out = set()
    for cat in ('Category:Poetry by ' + article, 'Category:Poems by ' + article):
        cont = {}
        while True:
            r = None
            for wait in (0, 5, 20, 60):      # the API refuses a burst now and then; wait it out rather than read nothing
                time.sleep(wait)
                try:
                    resp = S.get(API, params=dict({'action': 'query', 'list': 'categorymembers', 'cmtitle': cat, 'cmnamespace': 0, 'cmlimit': 500, 'format': 'json'}, **cont), timeout=30)
                    if resp.status_code == 200:
                        r = resp.json()
                        if 'error' not in r: break
                except Exception:
                    pass
                r = None
            if r is None: print('  category lookup failed: %s' % cat, flush=True); break
            for m in r.get('query', {}).get('categorymembers', []): out.add(m['title'])
            cont = r.get('continue') or {}
            if not cont: break
        time.sleep(0.2)
    return sorted(out)

# Read and rejected: the sentence the pattern caught is not a statement of this poem's metre. A re-run
# must not bring them back, so they are listed here with the reason, and the review stands.
REJECTED = {
    ('donne-poems', 'the-canonization'): "the article compares the poem's imagery to a Petrarchan sonnet",
    ('frost-north-of-boston', 'after-apple-picking'): 'the article describes the first line only; the poem is irregular',
    ('hughes-weary-blues', 'mother-to-son'): 'two lines of pentameter in a free-verse poem',
    ('whitman-leaves', 'o-captain-my-captain'): 'the early draft was free verse; the poem is rhymed and metrical',
    ('shelley-later-poems', 'mutability-2'): "the article is about the other poem called Mutability ('We are as clouds')",
    ('keats-1820', 'ode-to-psyche'): "the sentence is about Keats expanding the sonnet form, not the ode's metre",
}
# Read and corrected: what the article says, in the site's own terms, where the pattern misread it.
OVERRIDES = {
    ('kipling-verses', 'the-ballad-of-east-and-west'): ('iambic heptameter', 'iambic', 7, 'rhyming heptameters'),
    ('hopkins-poems', 'the-windhover'): ('sprung rhythm', None, None, 'a sonnet in sprung rhythm'),
}

key = lambda t: re.sub(r'[^a-z0-9]', '', re.sub(r'\s*\([^)]*\)\s*$', '', t).lower())

def statement(text):
    """(term, sentence, where) for the metre an article states, or None."""
    lead = text.split('\n==')[0]
    for where, part in (('lead', lead), ('body', text)):
        for sent in re.split(r'(?<=[.!?])\s+', part):
            m = TERM.search(sent)
            if not m: continue
            # in the body, only a sentence that is about this poem's own form
            if m.group(1).lower().rstrip('s') == 'sonnet' and not re.search(r'\b(is|as) an? (?:\w+ )?sonnet\b|\bthe sonnet\b|\bsonnet form\b', sent, re.I): continue
            if where == 'body' and not re.search(r'\b(written|composed|is in|are in|uses|employs|consists of|the (?:poem|metre|meter|stanzas?|lines?|verse)\b|in the (?:form|metre|meter) of|its (?:metre|meter|form))\b', sent, re.I): continue
            return m.group(1), re.sub(r'\s+', ' ', sent).strip()[:300], where
    # a metre mentioned anywhere, for a person to look at
    m = TERM.search(text)
    if m:
        i = text.rfind('.', 0, m.start()) + 1; j = text.find('.', m.end()) + 1
        return m.group(1), re.sub(r'\s+', ' ', text[i:j or None]).strip()[:300], 'doubt'
    return None

def main(only):
    lib = json.load(open(os.path.join(DATA, 'library.json'), encoding='utf-8'))
    bios = json.load(open(os.path.join(DATA, 'bios.json'), encoding='utf-8'))
    poets = sorted({w['author'] for w in lib if (w.get('lang') or 'en') == 'en' and not w.get('translator') and w['author'] in bios})
    if only: poets = [p for p in poets if p in only]
    # a run for named poets merges into what is there; a full run starts over
    out = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) and only else {'poems': {}, 'doubts': []}
    n_art = n_match = n_kept = 0
    for name in poets:
      try:
        titles = poems_in_category(bios[name]['title'])
        if not titles: continue
        secs = {}
        for w in lib:
            if w['author'] != name: continue
            for s in w['sections']: secs.setdefault(key(s['title']), []).append((w['slug'], s['id']))
        found = []
        for t in titles:
            n_art += 1
            hit = secs.get(key(t)) or secs.get(key(re.sub(r'^(The|A|An)\s+', '', re.sub(r'\s*\([^)]*\)\s*$', '', t))))
            if not hit: continue
            n_match += 1
            page = fetch(t)
            if not page or is_disambiguation(page): continue
            st = statement(page.get('extract') or '')
            if not st: continue
            term, sent, where = st
            mt = to_metre(term)
            if not mt: continue
            rec = {'metre': mt[0], 'foot': mt[1], 'feet': mt[2], 'term': term, 'quote': sent, 'article': page['title'], 'url': page.get('fullurl'), 'where': where}
            for slug, sid in hit:
                if where == 'doubt': out['doubts'].append(dict(rec, work=slug, section=sid))
                else: out['poems'].setdefault(slug, {})[sid] = rec; n_kept += 1
            found.append('%s: %s' % (t[:30], mt[0]))
            time.sleep(0.15)
        print('%-28s articles %3d  matched %3d  kept %2d   %s' % (name, len(titles), sum(1 for t in titles if secs.get(key(t))), len(found), '; '.join(found[:3])), flush=True)
      except Exception as e:
        print('%-28s failed: %s' % (name, str(e)[:120]), flush=True)
    for (slug, sid), why in REJECTED.items():
        r = out['poems'].get(slug, {}).pop(sid, None)
        if r: out['doubts'].append(dict(r, work=slug, section=sid, why='rejected on review: ' + why))
    for (slug, sid), (metre, foot, feet, term) in OVERRIDES.items():
        r = out['poems'].get(slug, {}).get(sid)
        if r: r.update({'metre': metre, 'foot': foot, 'feet': feet, 'term': term})
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    kinds = {}
    for slug in out['poems']:
        for sid, r in out['poems'][slug].items(): kinds[r['metre']] = kinds.get(r['metre'], 0) + 1
    print('\n%d poem articles, %d matched a poem in the library, %d metres kept, %d doubts -> %s' % (n_art, n_match, sum(len(v) for v in out['poems'].values()), len(out['doubts']), os.path.relpath(OUT, HERE)))
    print('by metre:', sorted(kinds.items(), key=lambda x: -x[1]))

if __name__ == '__main__':
    main(set(sys.argv[1:]))
