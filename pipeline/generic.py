"""Generic parser for Project Gutenberg poetry collections.

Given a Gutenberg text, finds the poems: a title line (short, capitalised, standing alone) followed by
verse blocks (blank-line separated, short lines, mostly capital initials). Front matter, contents,
prefaces, notes and prose are skipped by heuristics. Output matches ingest.py's work JSON.

    from generic import parse_gutenberg
    work = parse_gutenberg(gid, slug, meta)   # meta: title, author, author_sort, born, died, published, blurb
"""
import re, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
from ingest import load, clean, source

SKIP_TITLES = re.compile(r'^(END OF.*|VOL\.? [IVX\d]+.*|VOLUME [IVX\d]+.*|A NOTE ON.*|FROM .*HOMES AND HAUNTS.*|BY [A-Z]\. ?[A-Z]\..*|BY [A-Z][A-Z]+ [A-Z][A-Z]+|PRONOUNCING INDEX.*|IN (TWO|THREE|FOUR) VOLUMES.*|THE POETIC PRINCIPLE|[A-Z]\. ?[A-Z]\. ?[A-Z]\.?|LONDON[:,;] .*|LONDON \d.*|.*ERRORS?( IN .*)?|NOTE ON.*|ABBREVIATIONS.*|LIST OF.*|PRINTER.*|EDITOR.*|TEXTUAL.*|WARRANTY|MAIN COMPONENTS|COPYRIGHT.*|TABLE OF CONTENTS.*|INTRODUCTORY MATTER|CONTENTS?( .*)?|INDEX( OF (FIRST LINES|TITLES))?|PREFACE|AUTHOR.?S PREFACE|.*CONTEMPORARY EVENTS.*|INTRODUCTION (TO|BY) .*|INTRODUCTORY (NOTE|MATTER|ESSAY|MEMOIR).*|NOTES?( (TO|ON|FOR|UPON) .*)?|EXPLANATORY NOTES.*|TEXTUAL NOTES.*|VARIANTS?.*|ERRATA.*|FOOTNOTES:?|GLOSSARY|APPENDIX.*|BIBLIOGRAPH.*|ADVERTISEMENT|DEDICATION|ILLUSTRATIONS|LIST OF ILLUSTRATIONS|TRANSCRIBER.?S? NOTES?|BIOGRAPHICAL.*|MEMOIR.*|LIFE OF.*|CHRONOLOG.*|ERRATA|THE END|FINIS)\.?$', re.I)
ROMAN = re.compile(r'^[\(\[]?[IVXLC]+[\)\]\.]?$|^[IVXLC]+\.\s*\d\.?$')
NUMBER = re.compile(r'^\d{1,3}\.?$')

def is_title(block, meta=None, flush=None):
    # Some editions set every poem title hard against the left margin and indent everything else: verse,
    # subtitles, part labels and all. Where that holds, indentation settles the question on its own, and
    # nothing indented may be read as a heading. `flush` is read off the raw block, before clean() strips it.
    if meta and meta.get('flush_titles') and flush is False: return False
    if meta and meta.get('titlere'):
        # a scene heading, possibly preceded by its number on the line before
        if len(block) == 2 and ROMAN.match(block[0].strip()): block = block[1:]
        return len(block) == 1 and re.match(meta['titlere'], re.sub(r'[\*_]+', '', block[0]).strip()) is not None
    if 3 < len(block) <= 5 and all(re.sub(r'[^A-Za-z]', '', l) and re.sub(r'[^A-Za-z]', '', l).isupper() and len(l.strip()) <= 40 for l in block): return True
    if len(block) > 3 or (len(block) == 3 and len(' '.join(block)) > 60): return False
    if len(block) == 1 and re.match(r'^(fit|canto|book|part|chapter|runo) the \w+\.?$', block[0].strip(), re.I): return True
    if len(block) == 2 and ROMAN.match(block[0].strip()) and 3 < len(block[1].strip()) < 70 and not re.search(r'[.;,!?]$', block[1].strip().rstrip('.')):
        ws = block[1].strip().split(); tc = sum(1 for w in ws if w[:1].isupper() or w.lower() in ('a', 'an', 'the', 'of', 'to', 'in', 'on', 'and', 'or', 'for', 'at', 'by', 'from', 'with')) / len(ws)
        if tc >= 0.8 or (meta and meta.get('numbered_titles')): return True
    t = re.sub(r'[\*_]+', '', ' '.join(block)).strip(); t = re.sub(r'[\s.…]+$', '', t)
    if not t or len(t) > 70: return False
    # A title that runs on into its subtitle keeps the comma: "A GRAMMARIAN'S FUNERAL," then, indented,
    # "SHORTLY AFTER THE REVIVAL OF LEARNING IN EUROPE". At the margin and in capitals, it is still a title.
    margin_caps = flush and meta and meta.get('flush_titles') and re.sub(r'[^A-Za-z]', '', t).isupper()
    if t.endswith((',', ';')) and not margin_caps: return False
    if margin_caps: return True
    t = t.rstrip('.')
    if ROMAN.match(t) or NUMBER.match(t): return False
    letters = re.sub(r'[^A-Za-z]', '', t)
    if not letters: return False
    upper = sum(1 for c in letters if c.isupper()) / len(letters)
    words = t.split()
    titlecase = sum(1 for w in words if w[:1].isupper() or w.lower() in ('a', 'an', 'the', 'of', 'to', 'in', 'on', 'and', 'or', 'for', 'at', 'by', 'from', 'with')) / len(words)
    return upper > 0.8 or (titlecase >= 0.9 and len(words) <= 9)

def is_verse(block):
    if len(block) < 2: return False
    block = [l.strip() for l in block]
    lens = [len(l) for l in block]
    if max(lens) > 100: return False
    if sum(lens) / len(lens) > 78: return False
    caps = sum(1 for l in block if l[:1].isupper() or l[:1] in '\'"“‘(') / len(block)
    if caps >= 0.6: return True
    # lower-case line starts (Gummere's Beowulf, some moderns): accept short, even lines
    return len(block) >= 4 and max(lens) <= 70 and sum(lens) / len(lens) <= 50 and sum(1 for l in block if l.rstrip().endswith('.')) <= len(block) / 2

# A backstop against a runaway parse swallowing a whole file of prose, not a length limit on poetry.
# At 12,000 it was silently truncating ten real books — Burns lost Tam o' Shanter and A Red, Red Rose,
# Donne lost The Sun Rising and Batter my heart, Whitman lost half of Leaves of Grass — and nothing said
# so. It is now well above the longest thing anyone has published in verse, and it complains when it bites.
MAX_LINES = 60000
ORD = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, 'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10, 'eleventh': 11, 'twelfth': 12, 'thirteenth': 13, 'fourteenth': 14, 'fifteenth': 15, 'sixteenth': 16, 'seventeenth': 17, 'eighteenth': 18, 'nineteenth': 19, 'twentieth': 20, 'twenty-first': 21, 'twenty-second': 22, 'twenty-third': 23, 'twenty-fourth': 24}
def tmkey(t): return re.sub(r'[\*\s]+', ' ', t).strip(' .:*').upper()
def norm_roman(p):
    m = re.match(r'^([IVXLC]+)$', p or '')
    if not m: return p
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}; n = 0
    for i, ch in enumerate(p):
        v = vals[ch]; n += -v if i + 1 < len(p) and vals[p[i + 1]] > v else v
    return to_roman(n) if 0 < n < 400 else p
def roman_to_int(p):
    vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}; n = 0
    for i, ch in enumerate(p):
        v = vals[ch]; n += -v if i + 1 < len(p) and vals[p[i + 1]] > v else v
    return n
def to_roman(n):
    out = ''
    for v, r in ((1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')):
        while n >= v: out += r; n -= v
    return out
def _ordinal_book(t):
    m = re.match(r'^the (\w+) (book|canto|part)\.?$', t.strip(), re.I)
    return f"{m.group(2).title()} {to_roman(ORD[m.group(1).lower()])}" if m and m.group(1).lower() in ORD else t
def polish_title(t):
    t = _ordinal_book(t)
    r = _polish(t)
    return re.sub(r"'S\b", "'s", r).replace('’S', '’s')

LATIN_ORD = {'primus': 1, 'primvs': 1, 'secundus': 2, 'secvndvs': 2, 'tertius': 3, 'tertivs': 3, 'quartus': 4, 'qvartvs': 4, 'quintus': 5, 'qvintvs': 5, 'sextus': 6, 'sextvs': 6, 'septimus': 7, 'septimvs': 7, 'octavus': 8, 'octavvs': 8, 'nonus': 9, 'nonvs': 9, 'decimus': 10, 'decimvs': 10, 'undecimus': 11, 'vndecimvs': 11, 'duodecimus': 12, 'dvodecimvs': 12}
def _polish(t):
    m0 = re.match(r'^liber (\w+)\.?$', re.sub(r'[\*_]+', '', t).strip().lower())
    if m0 and m0.group(1) in LATIN_ORD: return f'Liber {to_roman(LATIN_ORD[m0.group(1)])}'
    """Normalise section headings: strip markup, 'THE *Second Book* OF THE METAMORPHOSES' -> 'Book II', 'BOOK THE FIRST' -> 'Book I', 'RUNO I.--BIRTH OF X' -> 'Runo I: Birth of X'."""
    t = re.sub(r'[\*_]+', '', t).strip(' .:;-–—')
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'^[IVXLC]+\.\s+(?=[A-Z][a-z]|[A-Z]{2})', '', t)   # "I. BED IN SUMMER" -> "BED IN SUMMER"
    low = t.lower()
    m = re.match(r'^the (\w[\w-]*) (book|canto|part|fit|runo)( of .*)?$', low)
    if m and m.group(1) in ORD: return f"{m.group(2).title()} {to_roman(ORD[m.group(1)])}"
    m = re.match(r'^(book|canto|part|fit|runo|chapter) the (\w[\w-]*)\b(.*)$', low)
    if m and m.group(2) in ORD: return f"{m.group(1).title()} {to_roman(ORD[m.group(2)])}" + (': ' + t[m.end(2):].strip(' .:;-–—').title() if t[m.end(2):].strip(' .:;-–—') else '')
    m = re.match(r'^(book|canto|part|fit|runo|chapter|section) ([ivxlc]+|\d+)\b[\.\s:;\-–—]*(.*)$', low)
    if m:
        n = m.group(2).upper() if not m.group(2).isdigit() else to_roman(int(m.group(2)))
        rest = t[m.end(2):].strip(' .:;-–—')
        rest = rest.title() if rest.isupper() else rest
        return f"{m.group(1).title()} {n}" + (': ' + rest if rest else '')
    if t.isupper(): t = t.title()
    t = ' '.join(w.upper() if re.match(r'^[ivxlc]+[\.:]?$', w, re.I) and len(w) <= 6 else w for w in t.split())
    t = re.sub(r"'S\b", "'s", t)
    return t

PUBLISHER = re.compile(r'\b(printed|reprinted|edition|impression|copyright|company|co\.|ltd|press|publishers?|street|square|row|museum|new york|london|boston|chicago|edited|introduction by|preface by|illustrated by|all rights)\b', re.I)
APPARATUS = re.compile(r'^\[|\b1[5-9]\d\d\b,\s*[A-Z]|\bMS\.|\bl\. \d+|\bll\. \d+|\b1[5-9]\d\d-\d\d\b|^(?:[A-Z][A-Za-z0-9\']{0,3},\s*){2,}|\]$|^\d{1,4}\.\s+[A-Z][^.]{2,60}\.\s+(Cf\.|See|That is|An? |The |I\.e\.|Gray|Scott)|^Page \d+\.|^\d{1,4}\.\s+[A-Z][A-Z ,\'\u2019]{4,}\.|\b[Cc]f\.\s|--Ed\.$|\b1[56]\d\d:|\b[A-Z]\d{2}\b|\bMSS?\.|^\d{1,4}\.\s+[A-Z].{0,80}\b(quotes|Printed in|Cp\.|Var\.|om\.)|^\d{1,4}\.\s+[A-Z][^.]{2,60}\.\s+(Printed|See|Var)')

GLOSS = re.compile(r'^(.*?\S)\s{2,}\*(.+?)\*?\s*$')
def strip_gloss(l, notes):
    l = re.sub(r'\s*<\d+>', '', l)
    m = GLOSS.match(l)
    if m:
        text, g = m.group(1), m.group(2).strip('* ')
        starred = re.findall(r'\*([^*]{2,60})\*', text) or re.findall(r'([A-Za-z’\'-]+)\*', text)
        text = text.replace('*', '')
        if starred: notes.append(f"{starred[-1]}: {g}")
        else: notes.append(g)
        return text
    return l.replace('*', '') if '*' in l else l
GLOSS_LINE = re.compile(r'^_([^_]{1,40})_,\s+(.{2,80})$')
def clean_stanza(st, notes=None):
    out = []
    if st and re.match(r'^[\(\[]?([IVXLC]+|\d{1,4})[\)\]\.]?$', st[0].strip()): st = st[1:]
    if st and re.match(r'^\d{1,3}\.\s+[A-Z“"‘\'(]', st[0]) and not re.search(r'\b(Cf|See|cf|Snorri|editors|stanza|line|MS)\b', st[0]): st = [re.sub(r'^\d{1,3}\.\s+', '', st[0])] + st[1:]   # "1.  Hearing I ask": a stanza number on the first line
    for l in st:
        if notes is not None: l = strip_gloss(l, notes)
        l = re.sub(r'^\d{1,4}\s+(?=[A-Za-z"\'])', '', l)          # leading line numbers
        l = re.sub(r'(?<=[\.,;:!\?\'"”’])\s+\d{2,4}$', '', l)   # trailing line numbers after punctuation
        if len(l) > 12 and l.upper() == l and re.search(r'[A-Z]{3}', l): continue   # shouting headers, publisher lines
        if re.match(r'^[A-Z][A-Z .\-\']{2,30}\.?$', l.strip()) and l.strip().upper() == l.strip() and not re.match(r'^[IVXLC]+\.?$', l.strip()): continue   # speaker tags
        if APPARATUS.search(l): continue
        if re.match(r'^[\W\d_]+$', l): continue
        out.append(l)
    if 2 <= len(out) <= 12 and sum(1 for l in out if PUBLISHER.search(l) and re.search(r'\d{4}|\b(ltd|co\.|company|press)\b', l, re.I)) >= 2: return []   # a title page, not a poem that mentions a press
    return out

def parse_gutenberg(gid, slug, meta, min_lines=4):
    min_lines = meta.get('min_lines', min_lines)
    lines = load(gid)
    for g in meta.get('append_gids', []): lines = lines + [''] + load(g)   # a work printed in two volumes
    if meta.get('stop_at'):
        hits = [i for i, l in enumerate(lines) if re.match(meta['stop_at'], l.strip())]
        k = meta.get('stop_occurrence', 1)
        if len(hits) >= k: lines = lines[:hits[k - 1]]
    if meta.get('start_at'):
        hits = [i for i, l in enumerate(lines) if re.match(meta['start_at'], l.strip())]
        k = meta.get('start_occurrence', 1)
        if len(hits) >= k: lines = lines[hits[k - 1] + (0 if meta.get('start_inclusive') else 1):]
    # raw blocks keeping original indentation info for prose detection
    blocks, cur = [], []
    for l in lines:
        if l.strip(): cur.append(l)
        else:
            if cur: blocks.append(cur); cur = []
    if cur: blocks.append(cur)
    orig_sections = []
    if meta.get('dual_numbered'):
        # Burton's Catullus: each numbered poem is printed twice, the original first, then the English under the same numeral.
        # The first block of verse under a numeral is kept aside as the original text; the prose paraphrase that follows the English is dropped.
        kept, cur_num, seen_second, orig_buf = [], None, False, []
        for b in blocks:
            cb0 = [clean(l) for l in b]; cb0 = [l for l in cb0 if l]
            if len(cb0) == 1 and ROMAN.match(cb0[0].strip()):
                n = cb0[0].strip().strip('()[].')
                if n == cur_num and not seen_second: seen_second = True; kept.append(b); continue
                if orig_buf: orig_sections.append({'title': f"{meta.get('partlabel', 'Poem')} {norm_roman(cur_num)}", 'stanzas': orig_buf}); orig_buf = []
                cur_num, seen_second = n, False; kept.append(b); continue
            if cur_num and not seen_second:
                if is_verse(cb0) or (len(cb0) >= 1 and all(l.startswith(' ') for l in b)): orig_buf.append([l.strip() for l in cb0 if not re.match(r'^[\*\s]+$', l)])
                continue
            if cur_num and seen_second and not all(l.startswith(' ') for l in b) and not is_title(cb0, meta): continue   # the prose paraphrase
            kept.append(b)
        if orig_buf: orig_sections.append({'title': f"{meta.get('partlabel', 'Poem')} {norm_roman(cur_num)}", 'stanzas': orig_buf})
        blocks = kept
    sections, title, stanzas, skipping, base, part = [], None, [], True, None, None
    glosses = {}; base_has_verse = set(); major_title = None; prev_title = None
    pending_heading = [None]; book_ctx = [None]
    def flush():
        nonlocal stanzas
        if title and not SKIP_TITLES.match(title) and sum(len(s) for s in stanzas) < min_lines and not part and not skipping: pending_heading[0] = title
        if title and not SKIP_TITLES.match(title) and sum(len(s) for s in stanzas) >= min_lines:
            base = meta.get('titlemap', {}).get(tmkey(title), title)
            pt = norm_roman(part) if part else part
            if pt and meta.get('partlabel'): shown = f"{meta['partlabel']} {pt}"
            elif pt and re.search(r'\bsonnets?\b', base, re.I) and len(base) < 40: shown = f"Sonnet {pt}"
            elif pt and base.strip().lower() == meta['title'].strip().lower(): shown = f"Poem {pt}"
            elif pt and (title in base_has_verse or meta.get('number_parts')) and not meta.get('epic'): shown = f"Poem {pt}"
            else: shown = polish_title(base) + (f' {pt}' if pt else '')
            if meta.get('first_line_titles') and re.match(r'^Poem [IVXLC\d]+$', shown) and stanzas and stanzas[0]:
                fl = re.sub(r'[\s,;:.!?]+$', '', stanzas[0][0].strip()); fl = re.sub(r'^([A-Z])([A-Z]+)(?=\b)', lambda m: m.group(1) + m.group(2).lower(), fl); shown = fl if len(fl) <= 60 else fl[:57].rsplit(' ', 1)[0] + '…'
            sid = re.sub(r'[^a-z0-9]+', '-', shown.lower()).strip('-')[:60] or f'poem-{len(sections)+1}'
            if any(s['id'] == sid for s in sections): sid += f'-{len(sections)+1}'
            if not part: base_has_verse.add(title); pending_heading[0] = None
            if os.environ.get('PARSE_TRACE'): print('FLUSH', repr(shown[:50]), sum(len(x) for x in stanzas))
            sections.append({'id': sid, 'title': shown, 'short': (part if part else shown)[:18], 'stanzas': stanzas, '_base': title, '_part': part, '_heading': pending_heading[0], '_book': book_ctx[0], '_gl': {ti: g for (si, ti), g in glosses.items() if si == len(sections)}})
        stanzas = []
    skip_blocks = set()
    for bi, b in enumerate(blocks):
        if len(b) >= 4 and sum(1 for l in b if re.search(r'(\.{3,}|\s{2,})\s*([ivxlc\d]+|_?ib\._?)\s*$', l.strip())) >= 0.4 * len(b): continue   # contents page
        if bi in skip_blocks: continue
        if meta.get('longs'): b = [re.sub(r'(?<=[A-Za-z])/(?=[A-Za-z])|(?<=\s)/(?=[A-Za-z])|^/(?=[A-Za-z])', 's', l) for l in b]
        if meta.get('caesura_gap'): b = ['     ' + re.sub(r'\s{3,}', '   |   ', re.sub(r'^\s*\d+\s+', '', l).strip()) if not re.match(r'^\s*\d+\s*$', l) else '' for l in b]; b = [l for l in b if l.strip()]
        if b and re.match(r'^\s*<\d+\.\d+>', b[0]): continue   # an editor's note block (Hazlitt's Lovelace)
        b = [re.sub(r'<\d+\.\d+>', '', l) for l in b if not re.match(r'^\s*<\d+\.\d+>', l)]
        cb = [clean(l) for l in b]; cb = [l for l in cb if l and not l.startswith('[Illustration') and not l.startswith('[Picture')]
        at_margin = not b[0][:1].isspace() if b else None
        if not cb: continue
        if b[0].lstrip().startswith('[Illustration') and len(cb) == 1 and is_title(cb, meta) and bi + 1 < len(blocks):
            nb = [clean(l) for l in blocks[bi + 1]]; nb = [l for l in nb if l]
            if len(nb) == 1 and re.match(r'^\(.*\)$', nb[0].strip()): skip_blocks.add(bi + 1); continue
        if meta.get('ignore_heading') and len(cb) <= 2 and re.match(meta['ignore_heading'], ' '.join(cb).strip(), re.I): continue
        if meta.get('drop_block') and len(cb) > 3 and re.match(meta['drop_block'], cb[0].strip()): continue   # a dramatis personae under a title
        if len(cb) == 2 and NUMBER.match(cb[0].strip()) and 3 < len(cb[1].strip()) < 70 and (meta.get('number_parts') or is_title([cb[1]], meta)):
            part = None; cb = [cb[1]]   # "14 / Hurrahing in Harvest": a numbered, titled poem
        if os.environ.get('PARSE_DEBUG') and any('Oxenford' in l or l.strip() == 'THE TALE.' for l in cb): print('BLK', cb[:1], 'title=', title, 'skipping=', skipping, 'is_title=', is_title(cb, meta), 'verse=', is_verse(cb))
        if os.environ.get('PARSE_DEBUG') and any(l.strip() in ('III', 'IV') for l in cb): print('BLOCK', cb[:2], '...', cb[-1:], 'title=', title, 'skipping=', skipping, 'is_title=', is_title(cb, meta))
        if len(cb) == 1 and re.match(r'^_?(the )?argument_?\.?$', cb[0], re.I): continue
        if sum(len(st) for sec in sections for st in sec['stanzas']) > meta.get('max_lines', MAX_LINES):
            print('   !! %s stopped at the %s-line cap with %d of %d blocks left; the text is being truncated'
                  % (slug, format(meta.get('max_lines', MAX_LINES), ','), len(blocks) - bi, len(blocks)))
            break
        if (is_title(cb, meta, at_margin) or (meta.get('headre') and len(cb) == 1 and len(cb[0]) < 60 and re.search(meta['headre'], cb[0], re.I) and re.search(r'\b([ivxlc]+|\d+|\w+)\b', cb[0]))) and not (len(cb) == 1 and ROMAN.match(cb[0])):
            hl = cb[1:] if meta.get('titlere') and len(cb) == 2 else cb
            if len(hl) > 2: hl = [x for x in hl if not re.match(r'^\s*(A |AN )?(SONG|SONNET|ODE|SET BY|TUNE|AIR)\b', x)] or hl[:1]; hl = [hl[0].strip(' .')] + [', ' + x.strip(' .') for x in hl[1:]] if len(hl) > 1 else hl
            newt = re.sub(r'^\(\d+\)\s*', '', re.sub(r'\s+', ' ', ''.join(hl) if len(hl) > 1 and hl[1].startswith(', ') else ' '.join(hl)).strip(' .'))
            if meta.get('title_sub'): newt = re.sub(meta['title_sub'][0], meta['title_sub'][1], newt).strip(' .')
            newt = re.sub(r'\s*<\d+\.\d+>', '', newt); newt = newt.replace(' ,', ',')
            newt = re.sub(r'^_?(the )?argument_?[.:]?\s+(?=\S)', '', newt, flags=re.I)   # "ARGUMENT. MINERVA'S DESCENT TO ITHACA" is the title without its label
            if skipping and meta.get('resume_only') and title and re.match(meta['resume_only'][0], title, re.I) and not re.match(meta['resume_only'][1], newt, re.I): continue   # inside the notes: only a named heading ends the skip
            if meta.get('book_prefix') and re.match(r'^(BOOK|Book) [IVXLC]+\.?$', newt.strip()): book_ctx[0] = polish_title(newt.strip(' .'))
            if meta.get('numbered_titles') and part and not stanzas: newt = f"{meta.get('partlabel', 'Part')} {norm_roman(part)}: {newt}"; part = None
            if title and not stanzas and not skipping and re.match(r'^(book|canto|part|runo|fit|chapter)( the)? ([ivxlc]+|\d+|\w+)\.?$', re.sub(r'[\*_]+', '', title), re.I) and not re.match(r'^(book|canto|part|runo|fit|chapter)\b', newt, re.I) and not SKIP_TITLES.match(newt):
                title = polish_title(title) + ': ' + polish_title(newt); continue
            if title and not stanzas and not skipping and re.match(r'^\(.*\)$', newt.strip()) and not re.match(r'^\(.*\)$', title.strip()):
                title = title + ' ' + newt.strip(); continue
            if title and not stanzas and not skipping and re.match(r'^(Tune|Air)\b', newt.strip(), re.I): continue   # a tune line under a song title
            if meta.get('subtitle_join') and title and not stanzas and not skipping and not SKIP_TITLES.match(newt.strip().rstrip(': ')) and ':' not in title: title = title.strip() + ': ' + newt.strip(); continue
            if title and not stanzas and not skipping and title.rstrip().endswith(':'): title = title.rstrip(': ') + ': ' + newt.strip(); continue
            if title and not stanzas and not skipping and title.rstrip().endswith(',') and not SKIP_TITLES.match(newt.strip()): title = title.rstrip(', ') + ', ' + newt.strip(); continue
            if os.environ.get('PARSE_DEBUG') and meta.get('carry_title') and newt.startswith('THALABA'): print('CARRY?', repr(title), len(stanzas), skipping, repr(newt))
            if meta.get('carry_title') and title and not stanzas and not skipping and re.match(meta['carry_title'], polish_title(meta.get('titlemap', {}).get(tmkey(title), title)), re.I): continue   # a speaker heading right under the work's title: the title stays
            elif meta.get('number_parts') and part and not stanzas: part = None
            elif meta.get('numbered_titles') and re.match(r'^([IVXLC]+)\.\s+(.+)$', newt): m2 = re.match(r'^([IVXLC]+)\.\s+(.+)$', newt); newt = f"{meta.get('partlabel', 'Part')} {m2.group(1)}: {m2.group(2)}"
            if meta.get('subparts'):
                tclean = re.sub(r'\s*<[^>]*>', '', newt).strip(' .')
                if re.match(r'^the (prologue|tale)$', tclean, re.I) and major_title: newt = f"{major_title}: {'Prologue' if 'rologue' in tclean.lower() else 'The Tale'}"
                elif re.match(r'^(the \w+ fit|fit\b)', tclean, re.I) and major_title: newt = f"{major_title}: {tclean}"
                elif re.match(r'^pars \w+', tclean, re.I) and major_title:
                    _rest = re.sub(r'^pars \w+\.?\s*', '', tclean, flags=re.I).title() or tclean
                    newt = f"{major_title}: {_rest}"
                elif re.search(r'\btale\b', tclean, re.I) and not SKIP_TITLES.match(tclean) and not re.match(r'^notes', tclean, re.I): major_title = tclean
            flush()
            if title and not (SKIP_TITLES.match(title.rstrip(': ')) or skipping): prev_title = title
            title = newt; part = None; skipping = bool(SKIP_TITLES.match(title.rstrip(': '))) or bool(meta.get('skipre') and re.match(meta['skipre'], title, re.I))
            if os.environ.get('PARSE_TRACE'): print('TITLE', repr(newt[:50]), 'skip' if skipping else '')
            continue
        if len(cb) == 1 and ROMAN.match(cb[0]) and (skipping or title is None) and not (title and meta.get('skipre') and re.match(meta['skipre'], title, re.I)):
            title = meta['title']; skipping = False
        if skipping and meta.get('resume_after_note') and prev_title and len(cb) >= 2 and is_verse(cb) and not is_title(cb, meta):
            title = prev_title; skipping = False
        if skipping or title is None: continue
        if len(cb) > 1 and ROMAN.match(cb[0].strip()) and not meta.get('titlere') and not is_title(cb, meta, at_margin):
            # "III" glued to the first line of its part: split it off as the part marker
            if stanzas: flush()
            part = cb[0].strip().strip('()[].'); cb = cb[1:]
        if len(cb) == 1 and ROMAN.match(cb[0]) and meta.get('titlere'): continue   # scene numbers in a play
        if len(cb) == 1 and ROMAN.match(cb[0]):
            # numbered part or sonnet: becomes its own section under the current title
            if stanzas: flush()
            part = cb[0].strip('()[].'); continue
        if len(cb) == 1 and NUMBER.match(cb[0]) and meta.get('number_parts'):
            if stanzas: flush()
            part = cb[0].strip('()[].'); continue
        if len(cb) == 1 and NUMBER.match(cb[0]): continue   # stanza number
        trailing_part = None
        if len(cb) > 1 and ROMAN.match(cb[-1].strip()) and not meta.get('titlere'): trailing_part = cb[-1].strip().strip('()[].'); cb = cb[:-1]
        if meta.get('split_lines') and cb and not skipping:
            # an unheaded poem inside a work: a new section begins at a known first line
            for pat, name in meta['split_lines']:
                if re.match(pat, cb[0].strip()): flush(); title = name; part = None; break
        if os.environ.get('PARSE_TRACE') and not is_verse(cb) and not skipping: print('BLOCKREJ', len(cb), repr(cb[0][:60]))
        if is_verse(cb) or (meta.get('headre') and len(cb) >= 2 and max(len(l) for l in cb) <= 90 and sum(len(l) for l in cb) / len(cb) <= 60):
            notes = [] if meta.get('inline_gloss') else None
            if meta.get('gloss_lines'):
                # Pollard's Herrick: "_Tiffanies_, gauzes." lines after a poem are word-glosses, kept as notes
                gl = [m for l in b if (m := GLOSS_LINE.match(l.strip()))]
                if gl and len(gl) >= len(cb) - 1:
                    if stanzas: glosses[(len(sections), len(stanzas) - 1)] = ' · '.join(f"{m.group(1)}: {m.group(2).rstrip('.')}" for m in gl)
                    continue
            cb = clean_stanza(cb, notes)
            if len(cb) >= 1:
                stanzas.append(cb)
                if notes: glosses[(len(sections), len(stanzas) - 1)] = ' · '.join(notes)
            if trailing_part:
                if os.environ.get('PARSE_DEBUG'): print('trailing part', trailing_part, 'title', title, 'stanzas', len(stanzas))
                flush(); part = trailing_part
    flush()
    if os.environ.get('PARSE_DEBUG'): print('after loop:', len(sections), [x['title'] for x in sections][:10])
    # drop obvious junk sections (contents lists parse as many one-line stanzas)
    good = []
    for s in sections:
        st = s['stanzas']; one = sum(1 for x in st if len(x) == 1)
        if one > len(st) / 2 and len(st) > 6: continue
        if sum(len(x) for x in st) < min_lines: continue
        good.append(s)
    # roman numerals that mark single stanzas (Spenser, Byron's Childe Harold): fold the parts back under their base title
    parts = [s for s in sections if s.get('_part')]
    sonnets = meta.get('scheme') in ('ABABCDCDEFEFGG', 'ABBAABBACDCDCD')
    if meta.get('epic') and not meta.get('headre') and parts and sum(1 for s in parts if len(s['stanzas']) == 1) >= 0.7 * len(parts):
        foldbases = {s['_base'] for s in parts}
    elif parts and not sonnets and not meta.get('headre') and not meta.get('no_fold'):
        # a poem whose roman numerals mark stanzas (Childe Roland, The Shrine) is one section, not thirty
        from collections import Counter
        nparts = Counter(s['_base'] for s in parts); single = Counter(s['_base'] for s in parts if len(s['stanzas']) <= 1)
        foldbases = {b for b, n in nparts.items() if n >= 3 and single[b] >= 0.7 * n and b.strip().lower() != meta['title'].strip().lower() and b in base_has_verse}
    else: foldbases = set()
    if foldbases:
        folded, bybase = [], {}
        for s in sections:
            if s.get('_part') and s['_base'] not in foldbases: folded.append(s); continue
            if s.get('_part') and s['_base'] in bybase:
                bybase[s['_base']]['stanzas'].extend(s['stanzas']); continue
            if s.get('_part'):
                s = dict(s); s['title'] = polish_title(meta.get('titlemap', {}).get(tmkey(s['_base']), s['_base'])); s['short'] = s['title'][:18]; s['id'] = re.sub(r'[^a-z0-9]+', '-', s['title'].lower()).strip('-')[:60]
                bybase[s['_base']] = s
            folded.append(s)
        sections = folded
    if meta.get('book_prefix'):
        for s in sections:
            if s.get('_book') and not re.match(r'^(Book|Carmen Saeculare)\b', s['title']): s['title'] = f"{s['_book']}: {s['title']}"; s['id'] = re.sub(r'[^a-z0-9]+', '-', s['title'].lower()).strip('-')[:60]
    for s in sections: s.pop('_base', None); s.pop('_part', None); s.pop('_book', None)
    good = [s for s in sections if not (sum(1 for x in s['stanzas'] if len(x) == 1) > len(s['stanzas']) / 2 and len(s['stanzas']) > 6) and sum(len(x) for x in s['stanzas']) >= min_lines]
    # epics: drop anything before the first canto/book
    if meta.get('epic'):
        k = next((i for i, s in enumerate(good) if re.search(r'\b(canto|book|runo|fit|part|inferno|purgatorio|paradiso|adventure|lay|prelude)\b', s['title'], re.I)), None)
        if k and k <= 8: good = good[k:]
    # merge consecutive sections with the same title (argument quatrain + canto); fix roman numerals in title case
    def fixcase(t): return ' '.join(w.upper() if re.match(r'^[ivxlc]+[\.:]?$', w, re.I) and len(w) <= 6 else w for w in t.split())
    merged2 = []
    for s in good:
        s['title'] = fixcase(s['title']); s['short'] = fixcase(s['short'])
        if merged2 and merged2[-1]['title'] == s['title']: merged2[-1]['stanzas'].extend(s['stanzas'])
        else: merged2.append(s)
    good = merged2
    # epics with numbered books: fold sub-headings (The Catalogue of the Ships) into the book they belong to
    if meta.get('epic') or meta.get('foldsub'):
        NUM = re.compile(r'^(Book|Canto|Part|Runo|Fit|Chapter|Inferno|Purgatorio|Paradiso|Liber|Ode|Satire|Carmen)\b', re.I)
        folded = []
        for s in good:
            if folded and not NUM.match(s['title']) and NUM.match(folded[-1]['title']): folded[-1]['stanzas'].extend(s['stanzas'])
            else: folded.append(s)
        good = folded
    # Drop front matter — but by what it IS, not by how short it is. The old rule dropped every leading
    # section until one reached thirty lines, which threw away the opening poem of any book that starts
    # with a short one: Frost's "The Road Not Taken" is twenty lines and is the first poem in Mountain
    # Interval, so the site had the book without the poem it is famous for. Hemans's "Casabianca" went
    # the same way. Front matter is recognised by its title, which is what SKIP_TITLES is for.
    FRONT = re.compile(r'^(dedication|to the reader|preface|proem|advertisement|introduction|'
                       r'prefatory|foreword|inscription|to [A-Z][a-z]+ [A-Z]|publisher|imprimatur|'
                       r'contents|note|errata)\b', re.I)
    while good and FRONT.match(good[0]['title'].strip()) and sum(len(st) for st in good[0]['stanzas']) < 30:
        good = good[1:]
    good = [s for s in good if not s['title'].startswith(('=>', 'Note', 'Footnote'))]
    # ...and front matter that cannot be recognised by its title, because its title is the publisher's
    # name. 'Dodd, Mead and Company 1922', 'New York The Macmillan Company', 'With Illustrations' all
    # matched nothing above and were read as poems: Dunbar's book opened with six lines of copyright
    # dates, numbered and scanned like verse. A page that is mostly imprint and copyright is a page from
    # the front of the book whatever it calls itself, and no poem is mostly 'Copyright 1898'.
    IMPRINT = re.compile(r'copyright|all rights reserved|entered according to act of congress|'
                         r'printed in the united states|first printing|distributed proofreade|'
                         r'set up and electrotyped|published .{0,20}\b(19|18)\d\d', re.I)
    def imprint_page(sec):
        ls = [l for st in sec['stanzas'] for l in st if l.strip()]
        if not ls or len(ls) > 14: return False
        # a real poem may mention a date; a copyright page is made of them
        return sum(1 for l in ls if IMPRINT.search(l)) >= max(2, 0.4 * len(ls))
    good = [s for s in good if not imprint_page(s)]
    # A title page is short, carries an imprint, and is at the FRONT. Requiring all three lets the rule
    # be loose enough to catch 'New York B. W. Huebsch / Copyright, 1916, by D. H. Lawrence' -- only one
    # of its four lines says copyright -- without touching a poem later in the book that happens to
    # mention a date. Only the first few are examined, because that is where the front of a book is.
    def title_page(sec):
        ls = [l for st in sec['stanzas'] for l in st if l.strip()]
        return bool(ls) and len(ls) <= 12 and any(IMPRINT.search(l) for l in ls)
    while good and len(good) > 3 and title_page(good[0]): good = good[1:]
    if len(good) > 3 and title_page(good[1]) if len(good) > 1 else False: good = good[:1] + good[2:]

    # A publisher's trade catalogue is not front matter in the usual sense -- it is a list of other
    # books, bound in at either end -- and its headings are short, capitalised and alone on a line,
    # which is indistinguishable from a poem's title. Gutenberg 70950 opens with eleven thousand
    # characters of Edward Moxon's 1850 list, and six of its headings were published as poems of
    # Tennyson's: 'Lamb's Works', 'Dyce's Beaumont and Fletcher', 'Dramatic Library'.
    #
    # What gives it away is not the words but the shape of the lines. Verse keeps an EVEN line, because
    # the poet chose where each one ends; a booklist does not, because its entries are as long as they
    # happen to be. Three tests together, because no two of them are enough: the vocabulary of the book
    # trade, lines too long for verse, and lines too ragged for verse.
    #
    # The third test is there because the first two would have deleted a poem. Douglas Hyde's 'Have you
    # been at Carrack' is a real song in long lines that happens to say 'guineas' and 'price', and it
    # was caught. Its lines vary by 7% about their mean; a booklist's by 19% to 28%. Publishing an
    # advertisement as a poem is an embarrassment, but deleting a poem is worse, so the rule is set to
    # miss rather than to overreach: across the whole library it drops six sections, and every one of
    # them was read and confirmed to be a list of other people's books.
    TRADE = re.compile(r'\b(price|cloth|vols?\.|8vo|12mo|fcap|post free|published by|sold by|bookseller|'
                       r'second edition|third edition|now ready|in the press|shillings|guineas|'
                       r'edited, with|crown 8vo|demy)\b', re.I)
    def catalogue_page(sec):
        ls = [l.strip() for st in sec['stanzas'] for l in st if l.strip()]
        if not ls or len(ls) > 60: return False
        if len(TRADE.findall(' '.join(ls))) < 2: return False
        lens = [len(l) for l in ls]
        avg = sum(lens) / len(lens)
        if avg < 52: return False
        import statistics
        return statistics.pstdev(lens) / avg >= 0.19
    good = [s for s in good if not catalogue_page(s)]
    good = [s for s in good if sum(1 for st in s['stanzas'] for l in st if re.match(r'^\d{1,4}\.\s', l)) < 0.3 * max(1, sum(len(st) for st in s['stanzas'])) or sum(len(st) for st in s['stanzas']) < 6]
    good = [s for s in good if not re.search(r'\]$|^(?:[A-Z][A-Za-z0-9\']{0,3},\s*){2,}', s['title'])]
    def prosey(sec):
        ls = [l for st in sec['stanzas'] for l in st]
        if len(ls) < 6: return False
        med = sorted(len(l) for l in ls)[len(ls) // 2]; caps = sum(1 for l in ls if l[:1].isupper()) / len(ls)
        return med > 58 and caps < 0.6
    good = [s for s in good if not prosey(s)]
    if meta.get('each_stanza'):
        label = meta['each_stanza']; split = []; k = 0; song = 0
        for sec in good:
            mo = re.match(r'^(?:the )?(\w+) sonnets?$', sec['title'].strip(' ._'), re.I)
            if mo and ORD.get(mo.group(1).lower()):
                song = ORD[mo.group(1).lower()]; split.append({'id': f'song-{song}', 'title': f'Song {song}', 'short': f'Song {song}', 'stanzas': list(sec['stanzas'])}); continue
            for st in sec['stanzas']:
                if 13 <= len(st) <= 15: k += 1; split.append({'id': f'{label.lower()}-{k}', 'title': f'{label} {k}', 'short': f'{label} {k}'[:18], 'stanzas': [st]})
                elif not split: continue
                else: split[-1]['stanzas'].append(st)
        good = split
    good = tidy_titles(good, meta)
    # Some editions print a prose note on each poem straight after it, in the same measure as the verse, so the
    # parser reads it as verse. Split it off: the poem keeps its lines, and the note becomes that poem's
    # introduction in the commentary file, which is where a reader expects to find it.
    note_com = {}
    if meta.get('note_block'):
        rx = re.compile(meta['note_block'])
        for sec in good:
            cut = next((i for i, st in enumerate(sec['stanzas']) if st and rx.match(st[0].strip())), None)
            if cut is None: continue
            tail = [l for st in sec['stanzas'][cut:] for l in st]
            tail = tail[1:] if rx.match((tail[0] if tail else '').strip()) else tail
            sec['stanzas'] = sec['stanzas'][:cut]
            body = ' '.join(x.strip() for x in tail if x.strip())
            body = re.sub(r'\s{2,}', ' ', body).strip()
            if body:
                esc = body.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                note_com[sec['id']] = {'source': meta.get('note_block_source') or 'The editor\u2019s note to this poem.',
                                       'intro': '<p>' + esc + '</p>', 'stanzas': {}}
        good = [x for x in good if x['stanzas']]
    if note_com:
        cp = os.path.join(HERE, '..', 'site', 'data', 'works', slug + '.commentary.json')
        cur = json.load(open(cp, encoding='utf-8')) if os.path.exists(cp) else {}
        for k, v in note_com.items():
            d = cur.setdefault(k, {'source': v['source'], 'intro': None, 'stanzas': {}})
            d['intro'] = v['intro']
            if not d.get('source'): d['source'] = v['source']
        json.dump(cur, open(cp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    if meta.get('inline_gloss') or meta.get('gloss_lines'):
        com = {}
        for sec in good:
            gl = sec.pop('_gl', None) or {}
            # one shape for every commentary file: a stanza holds a list of notes, each with a line or None
            if gl: com[sec['id']] = {'source': meta.get('inline_gloss') or meta.get('gloss_lines'), 'intro': None,
                                     'stanzas': {str(k): ([{'line': None, 'html': v}] if isinstance(v, str) else v) for k, v in gl.items()}}
        json.dump(com, open(os.path.join(HERE, '..', 'site', 'data', 'works', slug + '.commentary.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    for sec in good: sec.pop('_gl', None)
    w = dict(meta); w.update({'slug': slug, 'source': source(gid, meta.get('title_as_published', meta['title'])), 'sections': good})
    if orig_sections: w['orig_sections'] = orig_sections
    return w


# Documented metres. For a famous poem the answer is settled and published, so it is stated from here
# rather than inferred, and everywhere else these serve as the scoring set the detector is measured
# against. Sources: the standard handbooks and each poem's own scholarship; every one of these is
# uncontroversial. Where a work is a COLLECTION it is left out on purpose: a book of many metres has no
# single answer, and asking for one is what produced the wrong labels in the first place.
DOCUMENTED = {
    'ancient-mariner':           'common measure',
    'barrett-browning-sonnets':  'iambic pentameter',
    'byron-childe-harold':       'iambic pentameter',
    'canterbury-tales':          'iambic pentameter',
    'carroll-snark':             'anapaestic tetrameter',
    'clough-amours':             'dactylic hexameter',
    'cowper-task':               'iambic pentameter',
    'crabbe-village':            'iambic pentameter',
    'don-juan':                  'iambic pentameter',
    'faerie-queene':             'iambic pentameter',
    'keats-endymion':            'iambic pentameter',
    'longfellow-evangeline':     'dactylic hexameter',
    'longfellow-hiawatha':       'trochaic tetrameter',
    'marlowe-hero-leander':      'iambic pentameter',
    'milton-paradise-lost':      'iambic pentameter',
    'paradise-regained':         'iambic pentameter',
    'patmore-angel':             'iambic tetrameter',
    'pope-rape-of-the-lock':     'iambic pentameter',
    'scott-lady-of-the-lake':    'iambic tetrameter',
    'shakespeare-sonnets':       'iambic pentameter',
    'tennyson-idylls':           'iambic pentameter',
    'the-raven':                 'trochaic octameter',
    'young-night-thoughts':      'iambic pentameter',
}
# ---------------------------------------------------------------- what kind of foot
# A metre named from line length alone cannot tell an anapaestic tetrameter from an alexandrine: both are
# twelve syllables. But the stress the words themselves fix says which it is. Measure the gap between one
# fixed stress and the next: duple verse puts them two apart (and four, where a beat goes unmarked), triple
# verse three. The Hunting of the Snark comes out 87% threes; every iambic work in the library sits near
# zero there. Whether the foot rises or falls is the position of the first stress in the line.
FOOT_NAMES = {('duple', 'rising'): 'iambic', ('duple', 'falling'): 'trochaic',
              ('triple', 'rising'): 'anapaestic', ('triple', 'falling'): 'dactylic'}
LENGTH_NAMES = {2: 'dimeter', 3: 'trimeter', 4: 'tetrameter', 5: 'pentameter', 6: 'hexameter',
                7: 'heptameter', 8: 'octameter'}
def foot_shape(rows):
    """rows: the [.., stressString, ..] records of a work or a section.
    Returns (kind, lean, confidence) or (None, None, 0) when the verse does not settle."""
    gaps = collections.Counter(); firsts = collections.Counter(); n = 0
    for r in rows:
        pat = r[7] if len(r) > 7 else None
        if not pat: continue
        pos = [i for i, c in enumerate(pat) if c == 'S']
        if not pos: continue
        n += 1
        firsts[min(pos[0], 2)] += 1
        for a, b in zip(pos, pos[1:]):
            if b - a <= 4: gaps[b - a] += 1
    tot = sum(gaps.values())
    if tot < 14: return None, None, 0.0
    triple = gaps[3] / tot
    duple = (gaps[2] + gaps[4]) / tot
    if triple < 0.5 and duple < 0.5: return None, None, 0.0
    kind = 'triple' if triple > duple else 'duple'
    conf = max(triple, duple)
    even = odd = 0
    for r in rows:
        pat = r[7] if len(r) > 7 else None
        if not pat: continue
        for i, c in enumerate(pat):
            if c != 'S': continue
            if kind == 'triple':
                if i % 3 == 0: even += 1
                elif i % 3 == 2: odd += 1
            else:
                if i % 2 == 0: even += 1
                else: odd += 1
    lean = 'falling' if even > odd else 'rising'
    return kind, lean, round(conf, 3)
def meter_name(rows, syl_mode):
    """The metre a work or section may be said to be in, or None when the evidence will not carry one."""
    kind, lean, conf = foot_shape(rows)
    if not kind or conf < 0.55: return None, conf
    per = 3 if kind == 'triple' else 2
    if syl_mode is None: return None, conf
    feet = round(syl_mode / per)
    if feet < 2 or feet > 8: return None, conf
    length = LENGTH_NAMES.get(feet)
    if not length: return None, conf
    return '%s %s' % (FOOT_NAMES[(kind, lean)], length), conf

# A metre named from the commonest line length only means something when that length is actually common.
# Hopkins came out as "iambic pentameter" on a mode holding 18% of his lines, which is close to saying
# nothing at all about a poet who invented sprung rhythm against iambic metre; Skelton 16%, Toomer 17%,
# Lear's nonsense songs 17%. Works whose metre is not in doubt sit far higher: Shakespeare's sonnets 78%,
# Paradise Lost 75%, Keats 1820 67%, Don Juan 57%. A floor of 0.40 separates the two groups cleanly.
METER_FLOOR = 0.40
def meter_share(work):
    """(label, share of lines at the commonest length). The label is a guess whatever the share."""
    from analyze import line_syls
    counts = collections.Counter()
    for s in work['sections']:
        for st in s['stanzas']:
            for l in st[:40]: counts[len(line_syls(l))] += 1
    if not counts: return None, 0.0
    mode, n = counts.most_common(1)[0]
    label = {10: 'iambic pentameter', 8: 'iambic tetrameter', 11: 'iambic pentameter',
             12: 'alexandrines', 6: 'iambic trimeter', 7: 'ballad meter'}.get(mode)
    return label, n / sum(counts.values())
def meter_guess(work, floor=None):
    """The metre to PUBLISH: the label only when the evidence carries it, else None. analyze.py wants the
    working hint whatever its confidence, and passes floor=0 to get it."""
    label, share = meter_share(work)
    return label if label and share >= (METER_FLOOR if floor is None else floor) else None


SMALL = {'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but', 'nor', 'by', 'with', 'from', 'as', 'o', 'upon', 'into', 'unto', 'than'}
def smart_case(t):
    """Title case that leaves small words lower except at the start, after a number, or after a colon or quote mark."""
    words = t.split(' '); out = []
    for i, w in enumerate(words):
        core = w.strip('"“”\'‘’(')
        lw = core.lower()
        first = i == 0 or (i == 1 and re.match(r'^\d+\.$', words[0]))
        if not first and lw in SMALL and not re.search(r'[:—–]$', words[i - 1]) and not re.match(r'^["“‘(]', w): out.append(w.replace(core, lw, 1))
        elif first and lw in SMALL: out.append(w.replace(core, core[:1].upper() + core[1:], 1))
        else: out.append(w)
    return ' '.join(out)
def _cap_after_numeral(t): return re.sub(r'^([IVXLC]+\.\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), t)
def final_title(t):
    t = re.sub(r'<[^>]{0,12}>', '', t)                       # <1>, <l> markers
    t = re.sub(r'\s+deg\.?$', '', t)                          # degree-sign residue
    t = re.sub(r'^Song[—–-]\s*', '', t)                        # Burns: Song—Mary Morison
    if any(len(re.sub(r'[^A-Za-z]', '', w)) >= 4 and re.sub(r'[^A-Za-z]', '', w).isupper() and not re.match(r'^[IVXLC]+$', re.sub(r'[^A-Za-z]', '', w)) for w in t.split(' ')):
        t = ' '.join(w if re.match(r'^[IVXLC]+[.:]?$', w) else w.title() for w in t.split(' '))   # shouting words: re-case the whole title
    t = re.sub(r'^(.*), (the|a|an)$', lambda m: m.group(2).title() + ' ' + m.group(1), t, flags=re.I)   # index-style "Lasses, the"
    t = re.sub(r'^\(\d+\)\s*', '', t)                       # "(7) Early Poems"
    t = re.sub(r'^\d{1,2}\s+(?=[A-Za-z]{2})', '', t)             # "4 the Wreck" (a stray number without its period)
    t = re.sub(r'\^\{([^}]*)\}', r'\1', t)                    # M^{ris} superscripts
    t = re.sub(r'\s*\[[A-Za-z0-9]{1,3}\]', '', t)              # footnote letters
    t = re.sub(r'\s+to\b[\s—–-]*$', '', t.rstrip(' .'), flags=re.I)          # a dedication line cut in half
    if len(re.findall(r'\b[A-Za-z]\b', t)) >= 4 and re.search(r'(\b[A-Za-z]\b\s+){3,}', t): t = re.sub(r'((?:\b[A-Za-z]\b\s*){3,})', lambda m: m.group(1).replace(' ', '') + ' ', t).strip()   # M A E C E N A S
    t = re.sub(r'^(Part [IVXLC]+) ([IVXLC]+)$', r'\1, Section \2', t)   # Evangeline: Part I I
    t = t.replace('----', '—').replace('--', '—')
    t = re.sub(r'([’\'])(S|T|Ll|Ve|Re|D|M)\b', lambda m: m.group(1) + m.group(2).lower(), t)   # Hunt’S, Don’T
    t = re.sub(r'\.(["”’\'])$', r'\1', t)                    # "Blessed Are They That Mourn." -> ..."
    if re.search(r'(?:^|[\s.])[A-Z](?:\.[A-Z])*$', t) and re.search(r'\b[A-Z]\.[A-Z]$|\b[A-Z]$', t) and re.search(r'[A-Z]\.[A-Z]$|\s[A-Z]\.[A-Z]', t): t += '.'   # J.W -> J.W.
    t = smart_case(t)
    return t.strip()
def strip_numbering(good):
    num = re.compile(r'^([IVXLC]+)\s+(?=[A-Z])')
    if sum(1 for s in good if (m := num.match(s['title'])) and m.group(1) != 'I') >= 3:
        for s in good: s['title'] = num.sub('', s['title'])
    return good
def canto_key_of(t):
    # the innermost numbering wins: "Book I: Ode V" is keyed by the ode, not the book
    ms = list(re.finditer(r'\b(Canto|Book|Part|Runo|Fit|Chapter|Ode|Satire|Carmen) ([IVXLC]+|\d+)\b', t))
    return (ms[-1].group(1), ms[-1].group(2)) if ms else None
def tidy_titles(good, meta):
    good = strip_numbering(good)
    NUMT = re.compile(r'^(Book|Canto|Part|Runo|Idyll|Liber|Fit|Chapter) ([IVXLC]+|\d+): (.+)$')
    # continuation headings (a bracketed apparatus line, a parenthetical note) belong to the section before
    out = []
    major = None; numbered = re.compile(r'^(Canto|Book|Part|Epistle|Section|Chapter|Ode|Satire) [IVXLC\d]+\b')
    nnum = sum(1 for s in good if numbered.match(s['title'])); nother = len(good) - nnum
    if not meta.get('epic') and nother >= 2 and nnum and nnum < nother:
        heading = None; first_run = True
        for s in good:
            if numbered.match(s['title']):
                h = s.get('_heading') or heading
                if h: s['title'] = f"{polish_title(h)}: {s['title']}"; heading = h
                elif first_run: s['title'] = f"{meta['title']}: {s['title']}"
            else: heading = None; first_run = False
    for s in good:
        t = s['title'].strip()
        if out and (re.match(r'^[\[\{]', t) or re.match(r'^\(.*\)$', t) or re.match(r'^(Enter|Exit|Exeunt|Re-enter|ROME\.|SCENE\b|Scene\b)', t) or re.match(r'^(Chorus|Semi-Chorus|Recitative|Air|Duet|Trio|Strophe|Antistrophe|Epode|Strophe [IVX]+|Antistrophe [IVX]+|Epode [IVX]+)$', t, re.I) or re.match(r'^[A-Z][a-z]+\.\s+[A-Z]', t) or re.match(r'^[A-Z][a-z]+, \d{2}$', t) or re.search(r'\bVOICE\b|^THE VALLEY\b', t) or re.match(r'^[a-z]', t) or len(re.sub(r'[^A-Za-z]', '', t)) <= 2):
            out[-1]['stanzas'].extend(s['stanzas']); continue
        out.append(s)
    # a dialogue poem parsed by speaker: a run of four or more short titles drawn from two or three names folds into the section before it
    merged = []; i = 0
    while i < len(out):
        j = i
        while j < len(out) and len(out[j]['title'].split()) <= 3 and not numbered.match(out[j]['title']) and not re.search(r'\b(the|of|and|to|a|an)\b', out[j]['title'], re.I): j += 1
        run = out[i:j]; names = {x['title'] for x in run}
        if merged and all(len(x['stanzas']) <= 25 for x in run) and ((len(run) >= 4 and len(names) <= 3) or (len(run) >= 3 and len(names) <= 2) or (len(run) >= 6 and len(names) <= len(run) // 2)):
            for x in run: merged[-1]['stanzas'].extend(x['stanzas'])
            i = j; continue
        if j == i: merged.append(out[i]); i += 1
        else: merged.extend(run); i = j
    out = merged
    # an epigraph printed before the poem, its author's name taken for a title: "“Italia, Italia!…” / FILICAJA / Land of departed fame…"
    ep = []
    for k, s in enumerate(out):
        nxt = out[k + 1] if k + 1 < len(out) else None
        ln = [l for st in s['stanzas'] for l in st]
        if nxt and len(ln) <= 8 and re.match(r'^[“"‘\']', ln[0]) and re.search(r'[”"’\'][.,!?]?$|[.,!?][”"’\']$', ln[-1]) and len(nxt['title'].split()) <= 3 and not re.match(r'^(the|a|an|on|to|in)\b', nxt['title'], re.I):
            nxt['stanzas'] = s['stanzas'] + nxt['stanzas']; nxt['title'] = s['title']; nxt['short'] = s['short']; nxt['id'] = s['id']; continue
        ep.append(s)
    out = ep
    # A motto in another alphabet is not a poem in it. Longfellow heads Voices of the Night with six
    # lines of Euripides, and the parser made them a section titled 'Voices of the Night' -- so a
    # reader who clicked that division got a page of Ancient Greek and no Longfellow. The motto is
    # his and stays, at the head of the poem it introduces, under that poem's own title.
    motto = []
    for k, s in enumerate(out):
        nxt = out[k + 1] if k + 1 < len(out) else None
        ln = [l for st in s['stanzas'] for l in st]
        if nxt and ln and len(ln) <= 12 and not meta.get('lang') \
           and not any(re.search(r'[A-Za-z]', l) for l in ln) \
           and any(re.search(r'[\u0370-\u03ff\u1f00-\u1fff\u0400-\u04ff\u0590-\u05ff\u0600-\u06ff]', l) for l in ln):
            nxt['stanzas'] = s['stanzas'] + nxt['stanzas']; continue
        motto.append(s)
    out = motto
    bases = {}
    for s in out:
        m = re.match(r'^(.+?) ([IVXLC]+)$', s['title'])
        if m: bases.setdefault(m.group(1), []).append(s)
    alone = {s['title'] for s in out}
    if os.environ.get('PARSE_DEBUG'): print('bases', {b: len(r) for b, r in bases.items() if len(r) >= 3}, 'alone-hits', [b for b in bases if b in alone])
    for b, run in bases.items():
        if len(run) >= 3 and b not in alone and sum(1 for x in run if len(x['stanzas']) <= 3 or sum(len(st) for st in x['stanzas']) <= 24) >= 0.8 * len(run) and not numbered.match(run[0]['title']) and not meta.get('epic') and not meta.get('headre'):
            k = out.index(run[0]); first_num = re.match(r'^(.+?) ([IVXLC]+)$', run[0]['title']).group(2)
            if first_num == 'I':
                # a poem in numbered parts (Innocence I, II, III): one section under the base title
                head = run[0]; head['title'] = b; head['short'] = b[:18]; head['id'] = re.sub(r'[^a-z0-9]+', '-', b.lower()).strip('-')[:60]
                for x in run[1:]: head['stanzas'].extend(x['stanzas'])
                out = [x for x in out if x is head or x not in run]
            elif k > 0 and not re.match(r'^(.+?) ([IVXLC]+)$', out[k - 1]['title']):
                for x in run: out[k - 1]['stanzas'].extend(x['stanzas'])
                out = [x for x in out if x not in run]
    if meta.get('fold_into_prev'):
        fp = []
        for s in out:
            if fp and re.match(meta['fold_into_prev'], s['title'], re.I): fp[-1]['stanzas'].extend(s['stanzas'])
            else: fp.append(s)
        out = fp
    # a short section whose number the next section repeats (an epigraph printed before its canto) joins it
    joined = []
    for k, s in enumerate(out):
        nxt = out[k + 1] if k + 1 < len(out) else None
        if nxt and canto_key_of(s['title']) and canto_key_of(s['title']) == canto_key_of(nxt['title']) and sum(len(st) for st in s['stanzas']) < 20:
            nxt['stanzas'] = s['stanzas'] + nxt['stanzas']; continue
        joined.append(s)
    out = joined
    if out and re.match(r'^Poem [IVXLC]+$', out[0]['title']) and len(out) > 3 and not re.match(r'^Poem ', out[1]['title']): out[1]['stanzas'] = out[0]['stanzas'] + out[1]['stanzas']; out = out[1:]
    # a first section with no real title
    if out and len(re.sub(r'[^A-Za-z]', '', out[0]['title'])) <= 2 and len(out) > 1: out[1]['stanzas'] = out[0]['stanzas'] + out[1]['stanzas']; out = out[1:]
    # a work that is one poem takes the work's own title
    if len(out) == 1 and meta.get('title') and not numbered.match(out[0]['title']): out[0]['title'] = meta['title']
    # a subtitle repeated across numbered books (Book I: Proem, Book II: Proem) is not a title
    from collections import Counter
    subs = Counter(m.group(3) for s in out for m in [NUMT.match(s['title'])] if m)
    for s in out:
        m = NUMT.match(s['title'])
        if m and subs[m.group(3)] >= 2: s['title'] = f"{m.group(1)} {m.group(2)}"
        s['title'] = _cap_after_numeral(final_title(s['title'])); s['short'] = final_title(s['short']) if s.get('short') else s['title'][:18]
        s['id'] = re.sub(r'[^a-z0-9]+', '-', s['title'].lower()).strip('-')[:60] or s['id']
    # ids must stay unique
    seen = {}
    for s in out:
        if s['id'] in seen: seen[s['id']] += 1; s['id'] = f"{s['id']}-{seen[s['id']]}"
        else: seen[s['id']] = 1
    return out
