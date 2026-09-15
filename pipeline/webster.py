"""Parse Webster's Unabridged Dictionary (1913), Project Gutenberg eBook 29765,
into a compact JSON: { headword: [ {pos, defn, flags}, ... ] }.

Output: pipeline/cache/webster.json  (not shipped; analyze.py cuts per-work glossaries from it)
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'sources', 'pg29765.txt')
CACHE = os.path.join(HERE, 'cache')
os.makedirs(CACHE, exist_ok=True)

if not os.path.exists(SRC):
    raise SystemExit('no %s\n'
                     'This builds the glossary dictionary from Project Gutenberg eBook 29765, which the\n'
                     'corpus does not ship. Download it to that path and run this again. Nothing else in\n'
                     'the pipeline needs it: without it the scansion is unchanged and no glossaries are cut.' % SRC)

raw = open(SRC, encoding='utf-8', errors='replace').read().replace('\r\n', '\n')
s = raw.index('*** START OF THE PROJECT GUTENBERG EBOOK'); s = raw.index('\n', s) + 1
e = raw.index('*** END OF THE PROJECT GUTENBERG EBOOK')
lines = raw[s:e].split('\n')

HEAD = re.compile(r"^[A-Z][A-Z'\-\.]*(?:(?:[;,]\s|\s)[A-Z][A-Z'\-\.]*)*$")
POS = re.compile(r"\b(n\.|v\. t\.|v\. i\.|v\.|a\.|adv\.|prep\.|conj\.|interj\.|pron\.|p\. p\.|p\. a\.|superl\.|compar\.)")
FLAG = re.compile(r"\[((?:Obs|Archaic|Poetic|Poet|Rare|R|Colloq|Scot|Prov\. Eng|Slang|Written also [a-z]+)[A-Za-z\. &,]{0,20})\]")

entries = {}
i, n = 0, len(lines)
def add(head, pos, defn, flags, etym=''):
    defn = re.sub(r'\s+', ' ', defn).strip()
    if not defn: return
    defn = re.sub(r'^Defn:\s*', '', defn)
    # trim quotations and attributions that follow the definition sentence
    defn = re.split(r'\s"', defn)[0].strip()
    defn = re.sub(r'\s+(Shak|Chaucer|Milton|Spenser|Dryden|Pope|Tennyson|Longfellow|Wordsworth|Byron|Bacon|Macaulay|Cowper|Addison|Locke|Swift|Sir W\. Scott|Shakespeare)\.$', '', defn)
    if len(defn) > 220: defn = defn[:217].rsplit(' ', 1)[0] + '…'
    for h in re.split(r'[;,] ', head):
        h = h.strip().lower()
        if not h or ' ' in h: continue
        entries.setdefault(h, []).append({'pos': pos, 'defn': defn, 'flags': sorted(set(flags)), 'etym': etym[:200]})

while i < n:
    l = lines[i]
    if HEAD.match(l) and i + 1 < n and lines[i+1][:1].isalpha() and lines[i+1].split(' ')[0].replace('*','').replace('"','').replace('`','').lower().startswith(l.split(';')[0].split(',')[0].strip("'-.").lower()[:3]):
        head = l
        i += 1
        info = []
        while i < n and lines[i].strip():
            info.append(lines[i]); i += 1
        info = ' '.join(info)
        m = POS.search(info)
        pos = m.group(1) if m else ''
        flags = FLAG.findall(info)
        em = re.search(r'Etym:\s*\[(.*?)\]', info)
        etym = re.sub(r'\s+', ' ', em.group(1)).strip() if em else ''
        body = []
        while i < n and not (HEAD.match(lines[i]) and i + 1 < n and lines[i+1][:1].isalpha() and not lines[i+1].startswith('Defn') and lines[i+1][:2] != ' -'):
            body.append(lines[i]); i += 1
        # First definition paragraph: "Defn: ..." or "1. ...", keeping lines until one ends a sentence.
        # A numbered sense often opens on a bare subject label -- HEMLOCK begins "1. (Bot.)" on its own
        # line, with the wording in a "Defn:" paragraph below it -- and taking that first start alone left
        # nothing once the number and the label were stripped, so the word was dropped from the dictionary
        # altogether. Hemlock and nightingale both went that way. Try each start until one yields wording.
        starts = [j for j, b in enumerate(body) if b.startswith('Defn:') or re.match(r'^\d+\. ', b)]
        for k0 in starts:
            k = k0; dl = []
            while k < len(body) and body[k].strip():
                dl.append(body[k])
                if re.search(r'[\.\]!?]$', body[k].strip()): break
                k += 1
            d = ' '.join(dl)
            d = re.sub(r'^(Defn:|\d+\.)\s*', '', d)
            f2 = list(flags) + FLAG.findall(d)
            d = FLAG.sub('', d)
            d = re.sub(r'^\(\w[\w\. &]*\)\s*', '', d).strip()
            if d:
                add(head, pos, d, f2, etym)
                break
    else:
        i += 1

json.dump(entries, open(os.path.join(CACHE, 'webster.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('headwords:', len(entries))
for w in ('clime', 'eftsoons', 'sooth', 'ween', 'rigour', 'wont', 'bower', 'lattice', 'surcease'):
    print(w, '->', entries.get(w, [{}])[0])

# ---------------------------------------------------------------- how the words are said
# Webster prints a respelling under each headword, and it carries the two things a scansion needs:
# where the syllables divide, and which one takes the beat.
#
#     Beau"te*ous     BEAU-te-ous, three syllables, the first stressed
#     A*non"          a-NON, two syllables, the second stressed
#     Where"fore      WHERE-fore
#
# A `*` divides two syllables; a `"` divides them AND marks the one before it as stressed. This matters
# because the pronouncing dictionary the pipeline otherwise runs on is a dictionary of contemporary
# American speech, built for speech recognition, and it simply has not got the literary vocabulary:
# no 'beheld', no 'quoth', no 'anon', no 'wherefore', no 'methinks'. Across this library that leaves
# 375,863 words of two syllables or more with no stress at all for the metre to read.
#
# Checked against the pronouncing dictionary on the 18,739 words both of them hold, this respelling
# agrees on the syllable count 92.1% of the time and, where it agrees on that, on which syllable takes
# the stress 96.5% of the time. The disagreements are mostly real: 'abstract' and 'accent' and 'access'
# are noun one way and verb the other, and the two dictionaries chose different defaults.
RESP = re.compile(r'\n([A-Z][A-Z\'\- ;]{1,40})\n([A-Z][A-Za-z\'\"\*\-]{0,40})', re.M)

def respelling(r):
    """(number of syllables, index of the stressed one) or (n, None) if none is marked."""
    parts, cur, stress = [], '', None
    for ch in r:
        if ch == '*':
            parts.append(cur); cur = ''
        elif ch == '"':
            # the mark is set after the syllable it belongs to, and the first one is the primary
            if stress is None: stress = len([p for p in parts if p])
            parts.append(cur); cur = ''
        elif ch == "'":
            parts.append(cur); cur = ''      # secondary stress; it still ends a syllable
        else:
            cur += ch
    if cur: parts.append(cur)
    return len([p for p in parts if p]), stress

said = {}
for m in RESP.finditer(raw):
    head = re.sub(r"[^a-z']", '', m.group(1).strip().lower())
    r = m.group(2)
    if '*' not in r and '"' not in r: continue
    if not head or head in said: continue
    n, st = respelling(r)
    if n: said[head] = [n, st]
json.dump(said, open(os.path.join(CACHE, 'webster-stress.json'), 'w'), separators=(',', ':'))
print('respellings:', len(said))
for w in ('anon', 'beauteous', 'wherefore', 'methinks', 'thither', 'haply'):
    print('   %-12s %s' % (w, said.get(w)))
