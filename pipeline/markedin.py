"""Turn a prosodist's marked lines into one shape, whatever notation the book used.

Every handbook marked the beat its own way. Schipper and Latham set an acute on the stressed vowel and
leave the rest bare. Saintsbury, Kirkham and Leigh set a macron on the stressed vowel and a breve on
the unstressed, so a bare syllable there means the author did not say. Goold Brown's transcriber had
no accents to hand and wrote = for a macron and ~ for a breve, before the vowel. Hood set a spacing
acute after the vowel.

Whatever the book did, what comes out is one line per verse line, tab-separated:

    Thĕ wīld wĭnds wēep        the wild winds weep        -++x+

with + where the prosodist marked a beat, - where he marked a slack, and x where he marked nothing.
The scorer never sees the notation.

    python3 markedin.py <source> <textfile> [first-line last-line]

The syllables are the pipeline's own, from word_syls, and the mark is given to whichever syllable
holds the vowel it sits on. That keeps the gold on the same divisions as the reading, so every
disagreement is about stress and none is about counting.
"""
import os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyze import TOKEN, norm, word_syls

# How each book marks a beat and a slack. None for a slack means the book only marks beats, so a bare
# syllable is a slack; a real character means a bare syllable is unmarked.
NOTATION = {
    'acute':  {'beat': set('áéíóúýÁÉÍÓÚÝàèìòùỳÀÈÌÒÙỲ'), 'slack': None},
    'macron': {'beat': None, 'slack': None},        # handled by combining marks below
    'ascii':  {'beat': '=', 'slack': '~'},           # the mark precedes the vowel
    'after':  {'beat': '´', 'slack': None},          # the mark follows the vowel
}
MACRON, BREVE = '̄', '̆'
ACUTE_C, GRAVE_C = '́', '̀'

def read_marks(tok, notation):
    """(plain word, [beat positions], [slack positions]) with positions in the plain word."""
    plain, beats, slacks = [], [], []
    if notation == 'ascii':
        i = 0
        for ch in tok:
            if ch == '=': beats.append(len(plain)); continue
            if ch == '~': slacks.append(len(plain)); continue
            plain.append(ch)
        return ''.join(plain), beats, slacks
    if notation == 'after':
        for ch in tok:
            if ch == '´': beats.append(max(0, len(plain) - 1)); continue
            plain.append(ch)
        return ''.join(plain), beats, slacks
    # accents on the vowel, precomposed or combining
    for ch in tok:
        d = unicodedata.normalize('NFD', ch)
        base = ''.join(c for c in d if not unicodedata.combining(c))
        combs = [c for c in d if unicodedata.combining(c)]
        pos = len(plain)
        plain.append(base)
        if notation == 'acute' and (ACUTE_C in combs or GRAVE_C in combs): beats.append(pos)
        if notation == 'macron':
            if MACRON in combs: beats.append(pos)
            if BREVE in combs: slacks.append(pos)
            # Saintsbury stacks both on a syllable he calls doubtful: leave it unmarked
            if MACRON in combs and BREVE in combs: beats.pop(); slacks.pop()
    return ''.join(plain), beats, slacks

def convert(line, notation):
    """(plain line, mark string) or None if the line carries no mark."""
    t = re.sub(r'\s+', ' ', line.replace('|', '').replace('_', ' ')).strip()
    t = t.strip('"“”\'')
    if not t: return None
    words, marks = [], []
    pat = TOKEN if notation not in ('ascii',) else re.compile(r"[=~]*[^\W\d_](?:[^\W\d_]|['’\-=~])*")
    ms = list(pat.finditer(t))
    for m, nxt in zip(ms, ms[1:] + [None]):
        tok = m.group(0)
        plain, beats, slacks = read_marks(tok, notation)
        core = re.sub(r"[^a-z']", '', plain.lower())
        if not core: continue
        # The punctuation after a word travels with it: a rule licensed at a phrase edge needs to know
        # where the prosodist's line pauses, and the scorer reads the plain line, not the book.
        gap = t[m.end():nxt.start() if nxt else len(t)]
        punct = ''.join(ch for ch in gap if ch in ',;:.!?')
        words.append(plain + punct)
        sy = word_syls(norm(plain)) or []
        n = len(sy)
        if n == 0: continue
        if n == 1:
            marks.append('+' if beats else '-' if slacks else ('-' if NOTATION[notation]['slack'] is None else 'x'))
            continue
        parts = [p for p, _ in sy]
        pos, bounds = 0, []
        for p in parts:
            bounds.append((pos, pos + max(1, len(p)))); pos += max(1, len(p))
        scale = len(re.sub(r"[^A-Za-z']", '', plain)) / max(1, pos)
        for a, b in bounds:
            hit = any(a * scale <= i < b * scale for i in beats)
            low = any(a * scale <= i < b * scale for i in slacks)
            if hit: marks.append('+')
            elif low: marks.append('-')
            else: marks.append('-' if NOTATION[notation]['slack'] is None else 'x')
    m = ''.join(marks)
    if '+' not in m or len(m) < 4: return None
    # A prosodist marks a line of verse right through. A paragraph of his prose that happens to hold
    # one marked word is not a line, and neither is a table of words. Where the notation marks slacks
    # as well as beats, most syllables should carry a mark; where it marks beats only, a line needs
    # more than one beat in it.
    if NOTATION[notation]['slack'] is not None or notation == 'macron':
        if m.count('x') > 0.4 * len(m): return None
    if m.count('+') < 2: return None
    low = [re.sub(r"[^a-z']", '', w.lower()) for w in words]   # the filters look at bare words
    if any(w in ('accented', 'unaccented', 'trochee', 'iambus', 'dactyl', 'anapaest', 'spondee') for w in low): return None
    if not any(w in ('the', 'a', 'an', 'of', 'and', 'to', 'in', 'is', 'his', 'her', 'my', 'thy', 'with', 'for', 'that', 'as', 'or', 'but', 'on', 'at') for w in low): return None
    return ' '.join(words), m, ' '.join(re.sub(r"[,;:.!?]", '', w) for w in words)

def is_marked(line, notation):
    if notation == 'ascii': return len(re.findall(r'[=~][aeiouyAEIOUY]', line)) >= 2
    if notation == 'after': return line.count('´') >= 2
    d = unicodedata.normalize('NFD', line)
    if notation == 'macron': return d.count(MACRON) + d.count(BREVE) >= 3
    return d.count(ACUTE_C) + d.count(GRAVE_C) >= 2

if __name__ == '__main__':
    name, path = sys.argv[1], sys.argv[2]
    notation = sys.argv[3] if len(sys.argv) > 3 else 'acute'
    lo = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    hi = int(sys.argv[5]) if len(sys.argv) > 5 else 10**9
    out, seen = [], set()
    for i, raw in enumerate(open(path, encoding='utf-8', errors='replace'), 1):
        if not lo <= i <= hi: continue
        if not is_marked(raw, notation): continue
        if len(raw.split()) > 18: continue            # a marked word in a prose paragraph, not a line
        r = convert(raw, notation)
        if not r or r[2] in seen: continue      # the same line twice, however it was pointed
        seen.add(r[2]); out.append(r[:2])
    os.makedirs(os.path.join(HERE, 'marked'), exist_ok=True)
    dest = os.path.join(HERE, 'marked', name + '.tsv')
    with open(dest, 'w', encoding='utf-8') as f:
        for plain, m in out: f.write('%s\t%s\n' % (plain, m))
    print('%s: %d marked lines -> %s' % (name, len(out), os.path.relpath(dest, HERE)))
    for plain, m in out[:3]: print('   %-52s %s' % (plain[:52], m))
