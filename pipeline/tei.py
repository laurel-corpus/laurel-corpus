"""TEI P5 for every work: the text, its scansion, its rhyme, and the reference each line answers to.

The form a classicist expects, and the form another project can build on. Everything Laurel knows about
a line travels with the line rather than sitting in a database beside it: which syllables the words
themselves stress, which the metre asks for, how the stanza rhymes, and the canonical URN.

The stress notation follows For Better For Verse, the University of Virginia's hand-scansion corpus,
because interoperating with the one existing scholarly corpus of English scansion is worth more than
inventing a better alphabet:

    +   a stressed syllable        -   an unstressed syllable
    x   a syllable the dictionary does not settle, which the metre may take either way

@met on a line is the pattern the poem's metre asks for; @real is what the words themselves insist on.
Where they differ is where the interest is: a trochaic first foot, a missing first syllable, a
monosyllable the metre leans on that speech would not.

    python3 tei.py              write site/tei/<slug>.xml for every work
    python3 tei.py <slug ...>   only those
"""
import html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _paths import DATA, WORKS, TEI as OUT

LICENCE = 'https://creativecommons.org/licenses/by-sa/4.0/'

def load(p, d=None):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d

import re
CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

def esc(s): return html.escape(str(s if s is not None else ''), quote=True)

def real_of(stress):
    """What the words settle, in the Virginia notation: + stressed, - unstressed, x left open."""
    return ''.join('+' if c == 'S' else '-' if c == 'U' else 'x' for c in (stress or ''))

def met_of(nsyl, foot, feet):
    """What the metre asks for, built from the poem's own foot and length."""
    try:
        from scansion import FEET, by_length
        if not foot or not feet or foot not in FEET: return ''
        # @met is the metre the line is written in, not the reading of it -- TEI keeps what the words
        # actually do in @real. So take the PLAINEST template of this length, the one that needs no
        # substitution: cost 0 is the pure foot repeated. Taking whichever came first stopped being
        # safe when substitution took iambic pentameter from thirty templates to twelve hundred, and
        # would have published a line's ideal pattern with a trochaic inversion already in it.
        pool = by_length(foot).get(nsyl, ())
        for want in (True, False):
            best = min((t for t in pool if not want or t[1] == feet),
                       key=lambda t: (t[2], t[0]), default=None)
            if best: return best[0].replace('1', '+').replace('0', '-')
    except Exception:
        pass
    return ''

def work_tei(slug, lib, cite, stable, metres):
    wk = load(os.path.join(WORKS, slug + '.json'))
    ann = load(os.path.join(WORKS, slug + '.lines.json')) or {}
    if not wk: return None
    meta = lib.get(slug) or {}
    ce = (cite or {}).get(slug) or {}
    ids = ((stable or {}).get('ids') or {}).get(slug) or {}
    me = (metres or {}).get(slug) or {}
    src = wk.get('source') or {}

    rows = {}
    for r in (ann.get('lines') or []):
        rows[(r[0], r[1], r[2])] = r
    schemes = ann.get('schemes') or []

    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:lang="%s">' % esc(meta.get('lang') or 'en'),
         '  <teiHeader>', '    <fileDesc>',
         '      <titleStmt><title>%s</title><author>%s</author></titleStmt>' % (esc(wk.get('title')), esc(meta.get('author'))),
         '      <publicationStmt>',
         '        <publisher>Laurel</publisher>',
         '        <distributor><ref target="https://laurelpoetry.com/">laurelpoetry.com</ref></distributor>',
         '        <availability status="free"><licence target="%s">The text is in the public domain. '
         'The scansion, rhyme lettering and references added here are published under CC BY-SA 4.0: '
         'use them freely, credit Laurel, and keep derivatives as open.</licence></availability>' % LICENCE,
         '      </publicationStmt>',
         '      <sourceDesc><bibl>%s%s%s</bibl></sourceDesc>' % (
             esc(src.get('title_as_published') or wk.get('title')),
             '. %s' % esc(ce.get('editionName')) if ce.get('editionName') else '',
             '. <ref target="%s">source</ref>' % esc(src.get('url')) if src.get('url') else ''),
         '    </fileDesc>',
         '    <encodingDesc>',
         '      <metDecl xml:id="laurel-stress" type="met real" pattern="[+\\-x]+">',
         '        <metSym value="+">a stressed syllable</metSym>',
         '        <metSym value="-">an unstressed syllable</metSym>',
         '        <metSym value="x">a syllable the dictionary does not settle; the metre may take it either way</metSym>',
         '      </metDecl>',
         '      <p>@met is the pattern this poem\'s metre asks for; @real is what the words themselves insist on. '
         'Notation after For Better For Verse (University of Virginia).</p>',
         '    </encodingDesc>',
         '  </teiHeader>',
         '  <text><body>']

    off = 0
    for si, sec in enumerate(wk.get('sections', [])):
        sid = sec['id']
        pid = ids.get(sid) or ''
        ref = (ce.get('sections') or {}).get(sid, {}).get('ref') or sid
        urn = 'urn:laurel:eng:%s.%s.%s:%s' % (ce.get('author') or '', slug, ce.get('edition') or 'text', ref) if ce else ''
        m = (me.get('sections') or {}).get(sid) or []
        mname, foot, feet = (m[0] if m else ''), (m[3] if len(m) > 3 else ''), (m[4] if len(m) > 4 else 0)
        o.append('    <div type="poem" xml:id="%s"%s>' % (esc(sid), ' n="%s"' % esc(pid) if pid else ''))
        o.append('      <head>%s</head>' % esc(sec.get('title')))
        bits = []
        if urn: bits.append('<idno type="URN">%s</idno>' % esc(urn))
        if pid: bits.append('<idno type="laurel-id">%s</idno>' % esc(pid))
        if mname: bits.append('<note type="metre">%s</note>' % esc(mname))
        if bits: o.append('      ' + ''.join(bits))
        n = 0
        for ti, st in enumerate(sec.get('stanzas', [])):
            scheme = schemes[off + ti] if off + ti < len(schemes) else ''
            attrs = ' n="%d"' % (ti + 1)
            if scheme and any(c.isalpha() for c in scheme): attrs += ' rhyme="%s"' % esc(scheme.lower())
            o.append('      <lg type="stanza"%s>' % attrs)
            for li, text in enumerate(st):
                n += 1
                r = rows.get((si, ti, li))
                a = ' n="%d"' % n
                if r:
                    real = real_of(r[7])
                    if real: a += ' real="%s"' % real
                    met = met_of(len(real), foot, feet)
                    if met: a += ' met="%s"' % met
                o.append('        <l%s>%s</l>' % (a, esc(text)))
            o.append('      </lg>')
        off += len(sec.get('stanzas', []))
        o.append('    </div>')
    o += ['  </body></text>', '</TEI>', '']
    return '\n'.join(o)

def main():
    os.makedirs(OUT, exist_ok=True)
    lib = {w['slug']: w for w in (load(os.path.join(DATA, 'library.json'), []) or [])}
    cite = load(os.path.join(DATA, 'cite.json'), {})
    stable = load(os.path.join(DATA, 'stable.json'), {})
    metres = load(os.path.join(DATA, 'metres.json'), {})
    want = [a for a in sys.argv[1:] if not a.startswith('-')] or sorted(lib)
    n = bytes_ = 0
    for slug in want:
        x = work_tei(slug, lib, cite, stable, metres)
        if not x: continue
        # XML 1.0 admits no control character but tab, newline and carriage return, so a stray one in a
        # source text makes a file no parser will open. One did: Project Gutenberg 38520 carries U+001A
        # where the 'a' of 'chamber' belongs, and the Lowell TEI was unreadable for months without
        # anything saying so. Refuse to write rather than publish it, and name the line so the reading
        # can be settled and recorded in corrections.json.
        m = CONTROL.search(x)
        if m:
            raise SystemExit('%s: U+%04X at character %d, which XML does not allow\n  ...%s...\n'
                             'Settle the reading and add it to corrections.json.'
                             % (slug, ord(m.group()), m.start(),
                                x[max(0, m.start() - 60):m.start() + 40].replace('\n', ' ')))
        p = os.path.join(OUT, slug + '.xml')
        open(p, 'w', encoding='utf-8').write(x)
        n += 1; bytes_ += len(x.encode('utf-8'))
    if not n:
        # Either the library is empty or the parsed works are not here. The second is the usual case in
        # the published corpus, which ships the TEI this script wrote rather than the JSON it reads.
        raise SystemExit('nothing written: no parsed works found under %s\n'
                         'The published corpus carries the TEI, not the JSON these are built from.' % WORKS)
    print('%d works written to %s (%.1f MB)' % (n, OUT, bytes_ / 1e6))

if __name__ == '__main__':
    main()
