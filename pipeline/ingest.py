"""Turn Project Gutenberg plain-text sources into clean work JSON.

Output: site/data/works/<slug>.json
  {slug, title, author, born, died, source:{...}, sections:[{id,title,stanzas:[[line,...],...]}]}

Only the poem text is kept. Gutenberg headers, footers and license text are
stripped, so the output carries no Project Gutenberg trademark boilerplate.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'sources')
from _paths import WORKS as OUT

def load(gid):
    raw = open(os.path.join(SRC, f'pg{gid}.txt'), encoding='utf-8').read().replace('\r\n', '\n')
    s = raw.index('*** START OF THE PROJECT GUTENBERG EBOOK')
    s = raw.index('\n', s) + 1
    e = raw.index('*** END OF THE PROJECT GUTENBERG EBOOK')
    return raw[s:e].split('\n')

def clean(line):
    line = line.replace('<<', '').replace('>>', '')
    t = line.rstrip()
    t = re.sub(r'\s{2,}\d+$', '', t)          # trailing line numbers (Keats edition)
    t = t.replace('_', '')                    # italics markers
    t = re.sub(r'\{[)=~^.:]?([A-Za-z])\}', r'\1', t)          # diacritic markup: Cyb{)e}l{=e} -> Cybele
    t = re.sub(r'\^\{([^}]*)\}', r'\1', t)                     # superscripts: 6^{th} -> 6th
    t = re.sub(r'(?<=[A-Za-z0-9])\^([a-z]{1,2})\b', r'\1', t)     # S^r, 2^d
    t = re.sub(r'\[([a-z]{1,3})\]', r'\1', t)                     # editorial letters: Fate[s] -> Fates
    t = re.sub(r'(?<=[A-Za-z,])\*(?=\s(?!\s)|$|[,.;:])', '', t)     # lone asterisks after a word (no gloss follows)
    t = re.sub(r'\[\d+(:[A-Z])?\]|\[[A-Z\*]\]|\^\d+|\{\d+[a-z]?\}|\{P\.\s*\d+\}|\(\*\)', '', t)     # footnote and page markers, {0a}, (*)
    t = re.sub(r'\(\d{1,3}\)\s*$', '', t)                      # trailing note numbers: cold.(2)
    if t != line.rstrip(): t = re.sub(r'(?<=\S) {2,}(?=[a-z])', ' ', t)   # close the gap a removed marker left (glosses keep their wide gap before a capital or *)
    t = re.sub(r'\[[^\]]{1,40}\]\.?\s*$', '', t)                # trailing stage directions [musing]
    t = re.sub(r'(\s+\*)+\s*$', '', t)         # trailing asterisk rows
    return t.strip()

def blocks(lines, skip=lambda l: False):
    """Split lines into blank-line separated blocks, cleaning each line."""
    out, cur = [], []
    for l in lines:
        if skip(l):
            continue
        c = clean(l)
        if not c:
            if cur: out.append(cur); cur = []
        else:
            cur.append(c)
    if cur: out.append(cur)
    return out

CORR_PATH = os.path.join(HERE, 'corrections.json')
def apply_corrections(w):
    """Textual corrections confirmed by a person (pipeline/corrections.json): exact substring replacements
    on one line, each with a note and a source. Applied when the work JSON is written; a correction that
    no longer matches is reported so the list stays honest."""
    if not os.path.exists(CORR_PATH): return w
    rules = [c for c in json.load(open(CORR_PATH)) if c.get('work') == w['slug']]
    if not rules: return w
    for c in rules:
        hit = False
        for sec in w['sections']:
            if c.get('section') and sec['id'] != c['section']: continue
            for st in sec['stanzas']:
                for i, l in enumerate(st):
                    if c['from'] in l and (not c.get('line_starts') or l.startswith(c['line_starts'])):
                        st[i] = l.replace(c['from'], c['to'], 1); hit = True; break
                if hit: break
            if hit: break
        if not hit: print(f"  ! correction not applied in {w['slug']}: {c['from']!r} -> {c['to']!r}")
    w['corrections'] = len(rules)
    return w

def source(gid, title):
    return {
        'provider': 'Project Gutenberg',
        'ebook': gid,
        'url': f'https://www.gutenberg.org/ebooks/{gid}',
        'title_as_published': title,
        'rights': 'Public domain in the United States. Project Gutenberg header, footer and license text removed; the poem text itself carries no Gutenberg restrictions.',
    }

# ---------------------------------------------------------------- Don Juan
def don_juan():
    lines = load(21700)
    i = next(k for k, l in enumerate(lines) if l.strip() == 'DEDICATION' and lines[k+1].strip() == '' and 'Bob Southey' in ''.join(lines[k:k+6]))
    lines = lines[i:]
    roman = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII']
    sections, cur = [], None
    hdr = re.compile(r'^(DEDICATION|CANTO THE [A-Z]+)\.?\s*$')
    buf = []
    def flush():
        if cur is not None:
            cur['stanzas'] = blocks(buf, skip=lambda l: l.strip().startswith('[Illustration'))
            sections.append(cur)
    n = 0
    for l in lines:
        m = hdr.match(l.strip())
        if m:
            flush(); buf = []
            name = m.group(1)
            if name == 'DEDICATION':
                cur = {'id': 'dedication', 'title': 'Dedication', 'short': 'Ded.'}
            else:
                cur = {'id': f'canto-{n+1}', 'title': f'Canto {roman[n]}', 'short': roman[n]}; n += 1
        else:
            buf.append(l)
    flush()
    return {
        'slug': 'don-juan', 'title': 'Don Juan', 'author': 'Lord Byron', 'author_sort': 'Byron, George Gordon',
        'born': 1788, 'died': 1824, 'published': '1819–1824',
        'form': 'Ottava rima: eight lines of iambic pentameter rhyming ABABABCC',
        'scheme': 'ABABABCC', 'meter': 'iambic pentameter',
        'blurb': 'Byron\'s unfinished comic epic. Sixteen cantos and a fragment of a seventeenth, nearly two thousand stanzas, and a narrator who interrupts the story whenever a better joke occurs to him.',
        'source': source(21700, 'Don Juan'), 'sections': sections,
    }

# ---------------------------------------------------------------- In Memoriam
def in_memoriam():
    """Tennyson's elegy, in its prologue, hundred and thirty-one sections, and epilogue.

    The generic parser could not read this book at all. Gutenberg 70950 opens with eleven thousand
    characters of Edward Moxon's 1850 trade catalogue -- Haydn's Dictionary of Dates, Lamb's Letters,
    Dyce's Beaumont and Fletcher -- whose headings are short, capitalised and alone on a line, which is
    exactly what a poem title looks like. Six advertisements were published as poems. Then the whole
    elegy went under the one heading that followed, so a poem in a hundred and thirty-one sections
    appeared as a single section of 2,823 lines and no section of it could be cited.

    Both faults are fixed here by finding the poem rather than guessing at it: the catalogue is
    everything before the title block, and the sections are numbered in Roman on their own line.
    """
    lines = load(70950)
    # The book proper begins at the dedication block 'IN MEMORIAM / A. H. H. / OBIIT MDCCCXXXIII.'.
    # Everything before it is Moxon's catalogue and the title page; the prologue is the verse that
    # stands between the printer's imprint and that block, and is untitled in the book.
    obiit = next(k for k, l in enumerate(lines) if l.strip().startswith('OBIIT MDCCCXXXIII'))
    imprint = max(k for k, l in enumerate(lines[:obiit]) if 'PRINTERS' in l.upper())
    rom = re.compile(r'^([IVXLC]+)\.$')

    sections = []
    def add(sid, title, short, buf):
        st = blocks([l for l in buf if l.strip() != '1849.'])
        if st:
            sections.append({'id': sid, 'title': title, 'short': short, 'stanzas': st})

    add('prologue', 'Strong Son of God, immortal Love', 'Pro.', lines[imprint + 1:obiit - 2])

    # The epilogue, the marriage song for Tennyson's sister, carries no heading in this edition: it
    # simply follows the last section after a stanza break. It is split off by its first line, which is
    # the only thing on the page that marks it.
    EPILOGUE = 'O true and tried, so well and long,'

    cur, buf, n = None, [], 0
    for l in lines[obiit + 1:]:
        m = rom.match(l.strip())
        if m:
            if cur: add(cur[0], cur[1], cur[2], buf)
            n += 1
            cur, buf = ('section-%d' % n, m.group(1), m.group(1)), []
        elif cur:
            buf.append(l)
    if cur:
        cut = next((k for k, l in enumerate(buf) if l.strip() == EPILOGUE), None)
        if cut is None:
            raise SystemExit('in_memoriam: the epilogue no longer begins where it did')
        add(cur[0], cur[1], cur[2], buf[:cut])
        add('epilogue', 'O true and tried, so well and long', 'Epi.', buf[cut:])

    return {
        'slug': 'tennyson-in-memoriam', 'title': 'In Memoriam A.H.H.', 'author': 'Alfred Tennyson',
        # The name has to match the form the rest of the library uses, or the poet splits in two and
        # the new half has no portrait, no biography and no author page.
        'author_sort': 'Tennyson, Alfred Tennyson, Baron', 'born': 1809, 'died': 1892, 'published': '1850',
        'form': 'The In Memoriam stanza: four lines of iambic tetrameter rhyming ABBA',
        'scheme': 'ABBA', 'meter': 'iambic tetrameter',
        'blurb': "Tennyson's elegy for Arthur Hallam, written over seventeen years. This is the first "
                 "edition of 1850, which has a prologue, a hundred and twenty-nine sections, and an "
                 "epilogue for his sister's wedding; the two further sections everyone quotes were added "
                 "to later editions.",
        'source': source(70950, 'In memoriam'), 'sections': sections,
    }

# ---------------------------------------------------------------- Sonnets
def sonnets():
    lines = load(1041)
    rom = re.compile(r'^[IVXLC]+$')
    sections, cur, buf = [], None, []
    def flush():
        if cur is not None:
            b = blocks(buf)
            cur['stanzas'] = [sum(b, [])] if b else []
            sections.append(cur)
    for l in lines:
        s = l.strip()
        if rom.match(s):
            flush(); buf = []
            cur = {'id': f'sonnet-{len(sections)+1}', 'title': f'Sonnet {s}', 'short': s}
        elif cur is not None:
            if s.startswith('*** ') or s.upper() == 'THE END': continue
            buf.append(l)
    flush()
    sections = [s for s in sections if s['stanzas'] and 12 <= len(s['stanzas'][0]) <= 15]
    return {
        'slug': 'shakespeare-sonnets', 'title': 'The Sonnets', 'author': 'William Shakespeare', 'author_sort': 'Shakespeare, William',
        'born': 1564, 'died': 1616, 'published': '1609',
        'form': 'English sonnet: fourteen lines of iambic pentameter, three quatrains and a couplet, rhyming ABAB CDCD EFEF GG',
        'scheme': 'ABABCDCDEFEFGG', 'meter': 'iambic pentameter',
        'blurb': 'The 154 sonnets of the 1609 quarto: the fair youth, the rival poet, the dark lady, and the couplet that turns each poem at the end.',
        'source': source(1041, "Shakespeare's Sonnets"), 'sections': sections,
    }

# ---------------------------------------------------------------- The Raven
def raven():
    lines = load(1065)
    i = next(k for k, l in enumerate(lines) if l.strip().startswith('Once upon a midnight'))
    b = blocks(lines[i:])
    b = [s for s in b if len(s) >= 4]
    return {
        'slug': 'the-raven', 'title': 'The Raven', 'author': 'Edgar Allan Poe', 'author_sort': 'Poe, Edgar Allan',
        'born': 1809, 'died': 1849, 'published': '1845',
        'form': 'Eighteen six-line stanzas of trochaic octameter with internal rhyme, rhyming ABCBBB on a single refrain sound',
        'scheme': 'ABCBBB', 'meter': 'trochaic octameter',
        'blurb': 'A December night, a tapping at the chamber door, and one word repeated until it becomes unbearable.',
        'source': source(1065, 'The Raven'), 'sections': [{'id': 'poem', 'title': 'The Raven', 'short': '—', 'stanzas': b}],
    }

# ---------------------------------------------------------------- Ancient Mariner
def mariner():
    lines = load(151)
    hdr = re.compile(r'^PART THE ([A-Z]+)\.?$')
    words = {'FIRST':'I','SECOND':'II','THIRD':'III','FOURTH':'IV','FIFTH':'V','SIXTH':'VI','SEVENTH':'VII'}
    sections, cur, buf = [], None, []
    def flush():
        if cur is not None:
            cur['stanzas'] = blocks(buf, skip=lambda l: re.match(r'^[A-Z ]+\.$', l.strip()) is not None); sections.append(cur)
    for l in lines:
        m = hdr.match(l.strip())
        if m:
            flush(); buf = []
            r = words[m.group(1)]
            cur = {'id': f'part-{len(sections)+1}', 'title': f'Part {r}', 'short': r}
        elif cur is not None:
            buf.append(l)
    flush()
    return {
        'slug': 'ancient-mariner', 'title': 'The Rime of the Ancient Mariner', 'author': 'Samuel Taylor Coleridge', 'author_sort': 'Coleridge, Samuel Taylor',
        'born': 1772, 'died': 1834, 'published': '1798, text of 1834',
        'form': 'Ballad stanzas, mostly quatrains of alternating iambic tetrameter and trimeter rhyming ABCB, with five- and six-line stanzas where the story needs them',
        'scheme': 'ABCB', 'meter': 'ballad meter',
        'blurb': 'The final 1834 text: a wedding guest is stopped by an old sailor who shot an albatross and has been paying for it ever since.',
        'source': source(151, 'The Rime of the Ancient Mariner'), 'sections': sections,
    }

# ---------------------------------------------------------------- Keats 1820
def keats():
    lines = load(23684)
    # poems run from the first "LAMIA." heading (after the contents) to "INTRODUCTION TO LAMIA."
    starts = [k for k, l in enumerate(lines) if l.strip() == 'LAMIA.']
    start = starts[0]
    end = next(k for k, l in enumerate(lines) if l.strip() == 'INTRODUCTION TO LAMIA.')
    body = lines[start:end]
    titles = {
        'LAMIA.': 'Lamia', 'ISABELLA;': 'Isabella; or, The Pot of Basil', 'THE EVE OF ST. AGNES.': 'The Eve of St. Agnes',
        'ODE TO A NIGHTINGALE.': 'Ode to a Nightingale', 'ODE ON A GRECIAN URN.': 'Ode on a Grecian Urn', 'ODE TO PSYCHE.': 'Ode to Psyche',
        'FANCY.': 'Fancy', 'ODE.': 'Ode (Bards of Passion and of Mirth)', 'LINES ON THE MERMAID TAVERN.': 'Lines on the Mermaid Tavern',
        'ROBIN HOOD.': 'Robin Hood', 'THE MERMAID TAVERN.': 'Lines on the Mermaid Tavern', 'TO AUTUMN.': 'To Autumn', 'ODE ON MELANCHOLY.': 'Ode on Melancholy', 'HYPERION.': 'Hyperion',
    }
    sub = re.compile(r'^(PART|BOOK) ([IVX]+)\.$')
    sections, cur, buf, poem = [], None, [], None
    def flush():
        if cur is not None:
            st = blocks(buf, skip=lambda l: re.match(r'^\s*\d+\.\s*$', l) is not None or l.strip().upper() in ('A FRAGMENT.', 'TO A FRIEND.', 'OR, THE POT OF BASIL.', 'A STORY FROM BOCCACCIO.'))
            st = [s for s in st if not (len(s) == 1 and s[0].isupper())]
            st = [[l for l in s if not re.match(r'^[\*\s]+$', l)] for s in st if not any('Anatomy of Melancholy' in l for l in s)]
            st = [s for s in st if s]
            if st:
                cur['stanzas'] = st; sections.append(cur)
    for l in body:
        s = l.strip()
        if s in titles:
            flush(); buf = []
            poem = titles[s]
            cur = {'id': re.sub(r'[^a-z0-9]+', '-', poem.lower()).strip('-'), 'title': poem, 'short': poem.split(' (')[0][:18]}
        elif sub.match(s) and not l.startswith(' '):
            m = sub.match(s)
            flush(); buf = []
            cur = {'id': re.sub(r'[^a-z0-9]+', '-', f'{poem} {m.group(1)} {m.group(2)}'.lower()).strip('-'), 'title': f'{poem}, {m.group(1).title()} {m.group(2)}', 'short': f'{poem.split(" ")[0]} {m.group(2)}'}
        elif cur is not None:
            if l.startswith(' ') or not l.strip():
                buf.append(l)
    flush()
    return {
        'slug': 'keats-1820', 'title': 'Lamia, Isabella, The Eve of St. Agnes, and Other Poems', 'author': 'John Keats', 'author_sort': 'Keats, John',
        'born': 1795, 'died': 1821, 'published': '1820',
        'form': 'Mixed: heroic couplets (Lamia), ottava rima (Isabella), Spenserian stanzas (St. Agnes), odes in ten-line stanzas, blank verse (Hyperion)',
        'scheme': None, 'meter': 'mostly iambic pentameter',
        'blurb': 'Keats\'s last and greatest volume, published a year before his death: the six great odes, three narrative poems, and the unfinished Hyperion.',
        'source': source(23684, 'Keats: Poems Published in 1820 (Clarendon Press, 1909, ed. M. Robertson)'), 'sections': sections,
    }

WORKS = [don_juan, sonnets, raven, mariner, keats, in_memoriam]

if __name__ == '__main__':
    # The Gutenberg texts are not shipped with the corpus, so say which folder they go in rather than
    # raising on whichever one happens to be read first.
    if not os.path.isdir(SRC):
        sys.exit('no sources at %s\n'
                 'This reads Project Gutenberg plain-text files, which the corpus does not ship. Put\n'
                 'them there as pg<number>.txt; every work names its own source in the TEI header.' % SRC)
    os.makedirs(OUT, exist_ok=True)
    index = []
    for fn in WORKS:
        w = fn()
        nst = sum(len(s['stanzas']) for s in w['sections'])
        nl = sum(len(st) for s in w['sections'] for st in s['stanzas'])
        w['stats'] = {'sections': len(w['sections']), 'stanzas': nst, 'lines': nl}
        w = apply_corrections(w)
        json.dump(w, open(os.path.join(OUT, w['slug'] + '.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
        index.append({k: w[k] for k in ('slug', 'title', 'author', 'author_sort', 'born', 'died', 'published', 'form', 'scheme', 'meter', 'blurb', 'stats')})
        print(f"{w['slug']:22s} sections={len(w['sections']):3d} stanzas={nst:5d} lines={nl:6d}")
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w'), ensure_ascii=False, indent=1)
