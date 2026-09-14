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
