"""Annotate every line of every work for the reader, the analysis tool and the games.

Inputs : the works (site/data/works/<slug>.json, or the published TEI via teiread.py);
         optionally pipeline/cache/webster.json, built by webster.py, for glossaries
Outputs: site/data/works/<slug>.lines.json     line-level annotations
         site/data/works/<slug>.glossary.json  Webster 1913 glosses for the work's less common words
         site/data/library.json                index with per-work statistics

Line record (compact arrays to keep files small):
  [section, stanza, line, endWord, rhymeKey, inCmu(0/1), syllables, stressStr, syllablesList, meterFit]
  stressStr: one char per syllable: 'S' stressed (from a polysyllable), 'U' unstressed (polysyllable or function word), 'x' free (other monosyllables, secondary stress)
  readings.py adds a tenth field once the poem's metre is settled: the scanner's reading of the line, '+' a beat, '-' a slack
"""
import json, sys, os, re, collections, itertools, unicodedata
import pyphen
from nltk.corpus import cmudict

HERE = os.path.dirname(os.path.abspath(__file__))
from _paths import WORKS, DATA
CMU = cmudict.dict()
HYPH = pyphen.Pyphen(lang='en_US')
# Webster's 1913 is 16 MB of definitions, used for glossaries and for judging how common a word is.
# It is not part of scansion, so the corpus does not ship it and the pipeline does not insist on it:
# without it every word is equally common and no work gets a glossary, which is exactly what the
# corpus already publishes for works whose editions carried none. webster.py rebuilds it from
# Project Gutenberg eBook 29765 if you want glossaries back.
WEBFILE = os.path.join(HERE, 'cache', 'webster.json')
WEB = json.load(open(WEBFILE, encoding='utf-8')) if os.path.exists(WEBFILE) else {}

# Webster prints a respelling under each headword, and it carries what a scansion needs: where the
# syllables divide, and which one takes the beat. Beau"te*ous is BEAU-te-ous; A*non" is a-NON.
#
# This matters because the pronouncing dictionary the pipeline otherwise runs on is a dictionary of
# contemporary American speech, built for speech recognition, and it has not got the literary
# vocabulary: no beheld, no quoth, no anon, no wherefore, no methinks. Across this library that left
# 375,863 words of two syllables or more with no stress at all for the metre to read against, 4.4% of
# every word in the corpus.
#
# webster.py writes this file; it is 1.3 MB against the dictionary's 16 MB, so it can travel with the
# pipeline. Measured against the pronouncing dictionary on the 18,739 words both of them hold, it
# agrees on the syllable count 92.1% of the time, and on which syllable takes the stress 96.5% of the
# time where they agree on the count.
SAIDFILE = os.path.join(HERE, 'cache', 'webster-stress.json')
SAID = json.load(open(SAIDFILE, encoding='utf-8')) if os.path.exists(SAIDFILE) else {}

# ------------------------------------------------------------ word helpers
def norm(w):
    return w.lower().replace('’', "'").replace('‘', "'")

def variants(w):
    """Spelling variants to try in American dictionaries."""
    out = [w]
    if w.endswith("'d"): out.append(w[:-2] + 'ed')
    if w.endswith("'st"): out.append(w[:-3] + 'est')
    out.append(re.sub(r"[^a-z]", '', w))
    out.append(re.sub(r'our$', 'or', w)); out.append(re.sub(r'our(s|ed|ing)$', r'or\1', w))
    out.append(re.sub(r'ise$', 'ize', w)); out.append(re.sub(r'ised$', 'ized', w))
    out.append(re.sub(r'yse$', 'yze', w))
    # Early Modern spelling doubles a final consonant and adds a silent e: starre, warre, sunne, ledde,
    # bedde. These are tried BEFORE the -re/-er rule below, and that rule is kept off them, because it
    # otherwise reads Lovelace's 'Starre' as 'starer' -- one who stares, a real word, so the dictionary
    # accepts it -- and gives the line the rhyme sound of something the poet never wrote.
    out.append(re.sub(r'([bcdfgklmnprstvz])\1e$', r'\1', w))
    out.append(re.sub(r'([bcdfgklmnprstvz])\1$', r'\1', w))
    if not re.search(r'([bcdfgklmnprstvz])\1e$', w): out.append(re.sub(r're$', 'er', w))
    out.append(re.sub(r"'", '', w))
    seen, res = set(), []
    for v in out:
        if v and v not in seen: seen.add(v); res.append(v)
    return res

def phones(w):
    for v in variants(w):
        if v in CMU: return CMU[v]
    if w.endswith("'d"):
        base = w[:-2] + 'ed'
        if base in CMU:
            ph = list(CMU[base][0])
            # 'd suppresses a syllabic -ed after d/t only; otherwise identical
            if w[-3] in 'dt' and len(ph) >= 2 and ph[-2][-1].isdigit(): ph = ph[:-2] + [ph[-1]]
            return [ph]
    return inflected(w)

# A word the dictionary does not have, whose stem it does. 'Expedients' is absent where 'expedient' is
# present, so the word fell through to the letter-counting heuristic, came out three syllables instead of
# four, and -- worse -- carried no stress at all, which let the metre put the beat on '-dients', as it
# did in a line of Shelley's. Across a sample of three and a half million words this recovers
# about one token in a hundred, which sounds small and is not: they are content words, and a content word
# with no stress is exactly the syllable a template is free to get wrong.
#
# The danger is the reverse error. CMU holds a great deal of debris -- 'mee', 'dre', 'daye' are all in it
# -- so a rule that strips letters until something matches will turn 'meed' into 'mee' and invent a stress
# for a word that had a perfectly good one. Hence the guard: the stem must be a substantial word in its
# own right, not a fragment left over from cutting.
SUFFIX = (("'s", 'Z'), ('es', 'Z'), ('s', 'Z'), ('ed', 'D'), ('est', 'ST'), ('eth', 'TH'), ('ing', 'NG'))
SIBILANT = {'S', 'Z', 'SH', 'ZH', 'CH', 'JH'}

def inflected(w):
    """The phones of an inflected form, built from the stem the dictionary does have.

    The ending is spoken, so it is added rather than ignored, and it earns a syllable of its own only
    where English gives it one: -es after a hiss ('glances'), -ed after d or t ('wanted'), and -est,
    -eth and -ing always. Elsewhere it is a consonant on the end of the stem's last syllable, which
    is why 'griefs' stays one syllable and 'garlands' stays two.
    """
    for suf, tail in SUFFIX:
        if not w.endswith(suf) or len(w) - len(suf) < 4: continue
        stems = [w[:-len(suf)]]
        if suf in ('es', 'ed', 'est', 'eth'): stems.append(w[:-len(suf) + 1])
        if suf == 'es' and w.endswith('ies'): stems.append(w[:-3] + 'y')
        if suf == 'ing': stems.append(w[:-3] + 'e')
        for stem in stems:
            if len(stem) < 4: continue
            ph = None
            for v in variants(stem):
                if v in CMU: ph = list(CMU[v][0]); break
            if not ph: continue
            last = ph[-1]
            if suf in ('est', 'eth', 'ing'): ph = ph + ['IH0'] + list(tail_phones(tail))
            elif suf in ("'s", 'es', 's') and last in SIBILANT: ph = ph + ['IH0', 'Z']
            elif suf == 'ed' and last in ('T', 'D'): ph = ph + ['IH0', 'D']
            else: ph = ph + [tail]
            return [ph]
    return None

def tail_phones(t):
    return {'ST': ('S', 'T'), 'TH': ('TH',), 'NG': ('NG',)}.get(t, (t,))

def fold_ir(out):
    """IY before R is the IH of 'near': the dictionary spells one English sound two ways.

    210 words are keyed IH R and 28 IY R, with beer, near, dear, fear and clear on one side and here,
    hear, ear and bier on the other. Nothing in English turns on the difference, and the browser's
    prosody.js has always read them as one. Until this fold the pipeline did not, so Kipling's
    'pint o' beer' / 'no red-coats here' went unlettered, along with 2,450 other line ends."""
    for i, p in enumerate(out):
        if p == 'IY' and i + 1 < len(out) and out[i + 1] in ('R', '*R'): out[i] = 'IH'
    return out

def cmu_key(ph):
    idx = max((i for i, p in enumerate(ph) if p[-1] in '12'), default=None)
    if idx is None: idx = max((i for i, p in enumerate(ph) if p[-1] in '012'), default=0)
    return ' '.join(fold_ir([p.rstrip('012') for p in ph[idx:]]))

def loose_key(ph):
    """Final-syllable key with reduced vowels as wildcards: catches rhymes on an unstressed last syllable
    (dress / wantonness, there / stomacher) that the primary-stress key misses. Documented on methods.html."""
    idx = max((i for i, p in enumerate(ph) if p[-1].isdigit()), default=None)
    if idx is None: return ''
    out = []
    for p in ph[idx:]:
        if p[-1].isdigit(): out.append('*' if p[-1] == '0' else p.rstrip('012'))
        elif p == 'ER': out.append('*R')
        else: out.append(p)
    return ' '.join(fold_ir(out))
def loose_keys_match(a, b):
    if not a or not b: return False
    if a.startswith('SP:') or b.startswith('SP:'):
        # spelling comparison when either word is outside the dictionary: the same consonant tail after the last vowel
        tail = lambda k: re.sub(r'^[aeiouy]+', '', k[3:]) if k.startswith('SP:') else ''.join(p for p in k.split(' ')[1:] if p != '*')
        ta, tb = tail(a), tail(b)
        if a.startswith('SP:') and b.startswith('SP:'): return a[3:] == b[3:] and len(a) > 4
        if not ta or not tb: return False
        LET = {'D': 'd', 'T': 't', 'M': 'm', 'N': 'n', 'S': 's', 'Z': 's', 'K': 'k', 'L': 'l', 'R': 'r', 'V': 'v', 'F': 'f', 'P': 'p', 'B': 'b', 'G': 'g', 'NG': 'ng', 'SH': 'sh', 'CH': 'ch', 'TH': 'th', 'DH': 'th'}
        ph = b if a.startswith('SP:') else a; sp = a if a.startswith('SP:') else b
        lhs = ''.join(LET.get(p, '?') for p in ph.split(' ')[1:] if p != '*')
        rhs = re.sub(r'^[aeiouy]+', '', sp[3:]).replace('ck', 'k')
        # A single consonant after the last vowel is the English plural and past tense ending, which is
        # grammar and not rhyme. On that much alone this branch matched quinces against cherries and
        # peaches against strawberries in the opening of Goblin Market, and lettered ten lines as one
        # rhyme. Two consonants is the least that is evidence of anything. Words that genuinely rhyme on
        # a single consonant still meet through the strict key, as cherries and dewberries do.
        return len(lhs) >= 2 and lhs == rhs
    CONVENTION = {('AH V', 'UW V'), ('AE V', 'EY V'), ('AH M', 'OW M'), ('UH D', 'AH D'), ('AO R', 'UW R'), ('EH R', 'IH R'), ('AY', 'IY')}   # love/move, have/grave, come/home, good/blood, poor/door, there/here, eye/-y
    if (a, b) in CONVENTION or (b, a) in CONVENTION: return True
    A, B = a.split(' '), b.split(' ')
    if len(A) != len(B): return False
    # This tier pairs a stressed ending with an unstressed one (dress / wantonness). It is not for two
    # unstressed endings: everything that survives of those is the consonant after the reduced vowel, so
    # every -es and -ies plural in English reduces to '* Z' and matches every other. That is how the
    # opening of Goblin Market lettered oranges and peaches as rhymes of cherries and strawberries.
    if A[0] == '*' and B[0] == '*': return False
    # A one-token key is a single final sound and so very little evidence. The old -y / eye rhyme of the
    # older poets (civility / tie) is real and stays. The wildcard must not be let into it: '*' stands for
    # ANY unstressed final vowel, so admitting it here made every word ending in one rhyme with every word
    # ending in -y or -eye. That is how the opening of Goblin Market came to letter 'together' and
    # 'weather' as rhymes of 'by', 'fly' and 'buy'.
    if len(A) == 1: return A[0] == B[0] or {A[0], B[0]} == {'IY', 'AY'}
    return all(x == y or x == '*' or y == '*' for x, y in zip(A, B)) and any(x == y and x != '*' for x, y in zip(A, B))
# suffix index for out-of-dictionary rhyme keys
SUF = collections.defaultdict(collections.Counter)
for w, phs in CMU.items():
    if not w.isalpha(): continue
    for L in (3, 4, 5, 6):
        if len(w) > L: SUF[w[-L:]][cmu_key(phs[0])] += 1

OVR_SYL = {'juan': 2, 'haidee': 2, 'dudu': 2, 'adeline': 3, 'lambro': 2, 'gulbeyaz': 3, 'inez': 2, 'jose': 2, 'alfonso': 3, 'julia': 2,
           'antonia': 3, 'baba': 2, 'suwarrow': 3, 'ismail': 2, 'amundeville': 4, 'aurora': 3, 'raby': 2, 'lenore': 2, 'pallas': 2,
           "o'er": 1, "e'er": 1, "ne'er": 1, "e'en": 1, "'tis": 1, "'twas": 1, "'twere": 1, "th'": 0, "'em": 1, "heav'n": 1, "ev'ry": 2,
           "i'll": 1, "i'm": 1, "i've": 1, "i'd": 1, "you'll": 1, "you're": 1, "you've": 1, "we'll": 1, "we're": 1, "they'll": 1, "they're": 1,
           "he'll": 1, "she'll": 1, "it's": 1, "that's": 1, "there's": 1, "what's": 1, "let's": 1, "don't": 1, "can't": 1, "won't": 1, "shan't": 1}
FUNC = set("""a an the and but or nor for so yet of to in on at by with from as if than then when while where that this these those
it its is was were be been am are do did has have had he she they we you i me him her them us my his their our your thy thine thee thou ye
not no nor up out off o oh ah""".split())

def rhyme_key(w):
    ph = phones(w)
    if ph: return cmu_key(ph[0]), 1
    w2 = re.sub(r"[^a-z]", '', w)
    for L in (6, 5, 4, 3):
        if len(w2) >= L and SUF.get(w2[-L:]):
            return SUF[w2[-L:]].most_common(1)[0][0], 0
    return '~' + w2, 0

def all_keys(w):
    ph = phones(w)
    return {cmu_key(p) for p in ph} if ph else None

def vowel_split(word):
    """Split into syllables at vowel groups with a maximal-onset rule."""
    spans = [(m.start(), m.end()) for m in re.finditer(r'[aeiouy]+', word)]
    if len(spans) <= 1: return [word]
    cuts = []
    for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
        cons = word[a1:b0]
        cuts.append(a1 + (1 if len(cons) > 1 else 0) + (1 if len(cons) > 2 and cons[1] in 'lrw' and cons[0] not in 'lrw' else 0))
    out, prev = [], 0
    for c in cuts: out.append(word[prev:c]); prev = c
    out.append(word[prev:])
    return [o for o in out if o]

def syllabify(word, n):
    """Split a word's letters into n chunks, guided by hyphenation, then vowel groups."""
    if n <= 1: return [word]
    parts = [p for p in HYPH.inserted(word).split('-') if p]
    if len(parts) == n: return parts
    parts = vowel_split(word)
    while len(parts) > n:
        # merge a trailing silent-e syllable first, else the shortest neighbour pair
        if re.match(r'^[^aeiouy]*e[sd]?$', parts[-1]) and len(parts) > 1:
            last = parts.pop(); parts[-1] += last; continue
        i = min(range(len(parts) - 1), key=lambda k: len(parts[k]) + len(parts[k+1]))
        parts[i:i+2] = [parts[i] + parts[i+1]]
    while len(parts) < n:
        # split the syllable holding the longest vowel run (e.g. 'ua' in juan, 'ia' in diamond)
        k = max(range(len(parts)), key=lambda i: len(re.findall(r'[aeiouy]', parts[i])))
        m = re.search(r'([aeiouy])([aeiouy])', parts[k])
        if m:
            parts[k:k+1] = [parts[k][:m.start()+1], parts[k][m.start()+1:]]
        else:
            m2 = re.search(r'[aeiouy]([^aeiouy]+)[aeiouy]', parts[k])
            if m2 and len(parts[k]) > 2: parts[k:k+1] = [parts[k][:m2.start(1)], parts[k][m2.start(1):]]
            else: parts.append('')
    return parts

# Syllable counts learned from a poem's own metre, for words the dictionary does not hold. Filled per work
# by learn_syllables() and cleared between works.
LEARNED = {}


def word_syls(tok):
    """Return list of (syllableText, stressChar) for a token."""
    w = norm(tok)
    core = re.sub(r"^[^a-z']+|[^a-z']+$", '', w)
    if not core: return []
    if core in OVR_SYL:
        n = OVR_SYL[core]
        if n == 0: return []
        return [(core, 'u' if core in FUNC else 'x')] if n == 1 else [(s, 'x') for s in syllabify(core, n)]
    ph = phones(core)
    if ph:
        vs = [p[-1] for p in ph[0] if p[-1].isdigit()]
        n = len(vs)
        if n == 1:
            return [(core, 'u' if core in FUNC else 'x')]
        parts = syllabify(core.replace("'", ''), n)
        if core in FUNC2: return [(parts[i] if i < len(parts) else '', 'x') for i in range(n)]
        return [(parts[i] if i < len(parts) else '', 'S' if vs[i] == '1' else 'U' if vs[i] == '0' else 'x') for i in range(n)]
    # Webster knows the words the pronouncing dictionary does not, and knows their stress. Consulted
    # only after the pronouncing dictionary has been asked, so nothing it says can override a modern
    # pronunciation; and only for words of more than one syllable, because a monosyllable is left open
    # for the metre to decide either way and Webster cannot improve on that.
    said = SAID.get(core) or SAID.get(core.replace("'", ''))
    if said:
        n, st = said[0], said[1]
        if n > 1:
            parts = syllabify(core.replace("'", ''), n)
            if core in FUNC2:
                return [(parts[i] if i < len(parts) else '', 'x') for i in range(n)]
            if st is None:
                return [(parts[i] if i < len(parts) else '', 'x') for i in range(n)]
            return [(parts[i] if i < len(parts) else '', 'S' if i == st else 'U') for i in range(n)]

    # heuristic count
    w2 = re.sub(r"[^a-z]", '', deaccent(core))
    v = re.findall(r'[aeiouy]+', w2); n = len(v)
    if w2.endswith('e') and not w2.endswith(('le', 'ee', 'ye', 'oe', 'ie')) and n > 1: n -= 1
    if w2.endswith('ed') and not w2.endswith(('ted', 'ded')) and n > 1: n -= 1
    if w2.endswith('es') and not w2.endswith(('ses', 'ces', 'zes', 'ges', 'xes', 'shes', 'ches')) and n > 1: n -= 1
    # The rules above are English rules and these are words English has no opinion about. Where the poem's
    # own metre has said otherwise -- Atrides is three syllables, whatever the -es rule supposes -- take the
    # poem's word for it.
    n = max(1, n + LEARNED.get(core, 0))
    return [(core, 'u' if core in FUNC else 'x')] if n == 1 else [(s, 'x') for s in syllabify(w2, n)]

# prepositions and conjunctions of two syllables take the beat the line gives them (in-TO or IN-to): all free
FUNC2 = {'into', 'unto', 'upon', 'without', 'within', 'before', 'until', 'against', 'among', 'amongst', 'between', 'beyond', 'about', 'around', 'toward', 'towards', 'above', 'below', 'beneath', 'behind', 'through', 'throughout', 'although', 'because', 'after', 'over', 'under', 'ere', 'whether', 'unless', 'except', 'therefore', 'whereof', 'whereby', 'wherein', 'thereof', 'thereby', 'therein', 'whence', 'hence', 'thence'}
def glides(core):
    """Syllable indices where one unstressed vowel runs into the next, and verse merges them when the line
    runs long: the classical synaeresis and syncope (di-ence, ri-ous, tu-ous, mem-o-ry, wand-er-ing).

    The first vowel used to have to be an i or u sound, which missed the commonest case of all: a word
    ending -ing on an unstressed stem. 'Echoing' is EH1 K OW0 IH0 NG, an OW running into an IH, and no
    merge was offered, so a line of Dutt's Mahabharata came out at sixteen syllables against its
    neighbours' fifteen. The same omission missed wand'ring, murm'ring, suff'ring and gath'ring.
    This only ever fires under metrical pressure, and only ever merges two syllables the poet left
    unstressed, so it cannot make a line say anything it did not already say.
    """
    ph = phones(core)
    if not ph: return []
    vs = [p for p in ph[0] if p[-1].isdigit()]
    return [k for k in range(len(vs) - 1) if vs[k].endswith('0') and vs[k + 1].endswith('0')]
ELIDE = {'every': 2, 'heaven': 1, 'given': 1, 'even': 1, 'seven': 1, 'eleven': 2, 'driven': 1, 'power': 1, 'flower': 1, 'hour': 1, 'tower': 1, 'bower': 1,
         'shower': 1, 'ever': 1, 'never': 1, 'over': 1, 'being': 1, 'many': 1, 'spirit': 1, 'fire': 1, 'desire': 2, 'higher': 1, 'prayer': 1, 'poem': 1,
         'quiet': 1, 'real': 1, 'idea': 2, 'towards': 1, 'devil': 1, 'evil': 1, 'riot': 1, 'diamond': 2, 'violet': 2, 'glorious': 2, 'various': 2,
         'tedious': 2, 'curious': 2, 'serious': 2, 'radiant': 2, 'genial': 2, 'lion': 1, 'union': 2, 'opinion': 3, 'million': 2, 'familiar': 3,
         'peculiar': 3, 'immediate': 3, 'obedient': 3, 'experience': 3, 'influence': 2, 'violent': 2, 'society': 3, 'variety': 3, 'pious': 1,
         'earlier': 2, 'happier': 2, 'easier': 2, 'heavier': 2, 'lower': 1, 'slower': 1, 'follower': 2, 'jewel': 1, 'cruel': 1, 'fuel': 1, 'duel': 1,
         'ruin': 1, 'our': 1, 'doing': 1, 'going': 1, 'knowing': 1, 'flowing': 1, 'growing': 1, 'seeing': 1, 'ocean': 1, 'th': 0}


def elide_to(core):
    """The fewest syllables a word is sung in, or None if it does not contract.

    ELIDE above holds the words English verse shortens by habit. Beyond that list there is one regular
    class the dictionary spells long and verse has always spelt short: a stressed AY or AW running into a
    final ER, which is the -ire of empire, entire, require and admire and the -our of hour and power. The
    dictionary gives empire three syllables (EH1 M P AY0 ER0), so a pentameter carrying it was counted at
    eleven and its beats came out a syllable adrift of the words.
    """
    if core in ELIDE: return ELIDE[core]
    ph = phones(core)
    if not ph: return None
    vs = [p for p in ph[0] if p[-1].isdigit()]
    if len(vs) >= 2 and vs[-1].startswith('ER') and vs[-2][:2] in ('AY', 'AW'): return len(vs) - 1
    return None

# Accented letters are letters. The old class stopped at the first one, so Chryseis came apart into
# 'chryse' and 's', and Clytaemnestra's into 'clyt' and 'mnestra's' — two tokens where the poet wrote one,
# a syllable lost from the line, and two words in the index that do not exist.
# Any letter, not a hand-listed range: a Latin-1 range still stopped at OE (U+0152), which is outside it,
# so Homer's OEneus came through as the fragment 'neus'.
TOKEN = re.compile(r"[^\W\d_](?:[^\W\d_]|['’\-])*")

def deaccent(w):
    """Latin letters with their marks removed, for the spelling heuristics, which only know a-z."""
    w = w.replace('æ', 'ae').replace('œ', 'oe').replace('ß', 'ss')
    return ''.join(c for c in unicodedata.normalize('NFKD', w) if not unicodedata.combining(c))
def line_syls(text, expect=None, rising=True):
    """Syllables for a line. If the work expects N syllables, apply poetic elisions
    (every -> ev'ry, heaven -> heav'n) when the line runs long, or expand a spelled -ed
    (learned -> learn-ed) when it runs short."""
    words = []
    for tok in TOKEN.findall(text):
        for part in tok.split('-'):
            core = re.sub(r"^[^a-z']+|[^a-z']+$", '', norm(part))
            sy = word_syls(part)
            if sy: words.append([core, sy])
    total = sum(len(w[1]) for w in words)
    if expect:
        # too long: elide
        el = {i: elide_to(w[0]) for i, w in enumerate(words)}
        order = sorted((i for i, w in enumerate(words) if el[i] is not None and el[i] < len(w[1])),
                       key=lambda i: -(len(words[i][1]) - el[i]))
        allow = lambda: expect + (1 if words and words[-1][1] and words[-1][1][-1][1] == 'U' else 0)
        for i in order:
            if total <= allow(): break
            core, sy = words[i]; n = el[i]
            drop = len(sy) - n
            # keep the stressed syllable; merge the following unstressed ones into it
            k = next((j for j, (_, c) in enumerate(sy) if c == 'S'), 0)
            merged = [list(x) for x in sy]
            while drop > 0 and len(merged) > n:
                j = k + 1 if k + 1 < len(merged) else k - 1
                merged[k][0] = merged[k][0] + merged[j][0] if j > k else merged[j][0] + merged[k][0]
                if j < k: k -= 1
                merged.pop(j); drop -= 1
            words[i][1] = [(t, c) for t, c in merged]
            total = sum(len(w[1]) for w in words)
        # still long: synaeresis inside a word (disobedience -> dis-o-be-dyence), the last syllable pair first
        if total > allow():
            for i, (core, sy) in enumerate(words):
                if total <= allow(): break
                if len(sy) < 2: continue
                for k in reversed(glides(core)):
                    if k + 1 < len(sy) and total > allow():
                        merged = [list(x) for x in sy]; merged[k][0] = merged[k][0] + merged[k + 1][0]; merged[k][1] = 'U'; merged.pop(k + 1)
                        words[i][1] = [(t, c) for t, c in merged]; sy = words[i][1]; total -= 1
        # Too short: expand a spelled -ed to a syllable. Only for a line that is nearly its measure already.
        # Where a stanza mixes line lengths -- Burns's Standard Habbie runs 8-8-8-4-8-4 -- the short lines
        # are short because the poet wrote them so, and stretching them to the long measure invents beats.
        if expect - 2 <= total < expect:
            for i, (core, sy) in enumerate(words):
                if core.endswith('ed') and not core.endswith(('eed', 'ied')) and len(core) > 4 and total < expect:
                    last = sy[-1]
                    if len(last[0]) > 2 and not last[0].endswith(('ted', 'ded')):
                        words[i][1] = sy[:-1] + [(last[0][:-2], last[1]), ('ed', 'U')]
                        total += 1
    if expect and len(words) > 1:
        for i, (core, sy) in enumerate(words):
            ph = phones(core)
            if not ph or len(ph) < 2 or len(sy) < 2: continue
            pats = []
            for alt in ph:
                vs = [p[-1] for p in alt if p[-1].isdigit()]
                if len(vs) != len(sy): continue
                pat = ''.join('S' if v == '1' else 'U' if v == '0' else 'x' for v in vs)
                if pat not in pats: pats.append(pat)
            if len(pats) < 2 or core in FUNC2: continue
            cur = ''.join(c for _, c in sy); best = None
            for pat in pats:
                trial = [(t, pat[j]) for j, (t, _) in enumerate(sy)]
                st = ''.join(c for w in words[:i] for _, c in w[1]) + pat + ''.join(c for w in words[i + 1:] for _, c in w[1])
                f, _ = meter_fit(st, rising)
                if best is None or f > best[0]: best = (f, trial)
            if best: words[i][1] = best[1]
    return [x for w in words for x in w[1]]

def meter_fit(stress, rising=True):
    """Best match of hard positions to an alternating template; returns (fit 0..1, offset)."""
    hard = [(i, c) for i, c in enumerate(stress) if c in 'SU']
    if not hard: return 1.0, 0
    best = (0, 0)
    for off in (0, 1):
        ok = sum(1 for i, c in hard if (('S' if ((i + off) % 2 == (1 if rising else 0)) else 'U') == c))
        if ok / len(hard) > best[0]: best = (ok / len(hard), off)
    return round(best[0], 2), best[1]

def end_word(line):
    t = norm(line.strip())
    t = re.sub(r"[\s\.,;:!\?\)\(\]\[\"'“”\-—_\*]+$", '', t)
    t = re.sub(r"^.*[\s—\-\(\"]", '', t)
    t = t.strip("\"'().,;:!?[]“”‘’«»")
    # A rhyming word has to be a word. Braces from a printed cast list, printers' et-ceteras, equals signs
    # and bare numbers were all reaching the rhyme detector, and some were lettered as rhymes: a brace was
    # lettered against a name in Shakuntala's dramatis personae and '&c' against itself in Crashaw's
    # responsory. A line whose ending is not a word simply has no rhyme, and is left blank.
    if not t or t in ('&c', '&c.', '&') or not re.search(r'[a-z]', t): return ''
    if not re.search(r'[aeiouy]', t) and len(t) > 1: return ''
    return t

# ------------------------------------------------------------ commonness from Webster definitions
COMMON = collections.Counter()
for h, es in WEB.items():
    for e in es:
        for w in re.findall(r"[a-z']+", e['defn'].lower()): COMMON[w] += 1

def gloss(w):
    for v in variants(w):
        if v in WEB:
            es = WEB[v]
            good = [e for e in es if len(e['defn']) >= 15 and not re.match(r'^(See |of |\(|Same as|A |An |The )?[A-Z][a-z]*\.$', e['defn']) and not e['defn'].startswith(('See ', 'of ', '(', 'Same as', 'Alt. of', 'imp.', 'p. p.'))]
            if not good: return None
            rare_word = COMMON[w] <= 4
            flagged = [e for e in good if any(f.startswith(('Obs', 'Archaic', 'Poet')) for f in e['flags'])]
            if rare_word and flagged: return flagged[0]
            plain = [e for e in good if not any(f.startswith(('Obs', 'Archaic', 'Poet')) for f in e['flags'])]
            return (plain or good)[0]
    return None

THEMES = {
    'love': 'love lover loved loving beloved kiss kisses kissed heart hearts passion desire embrace bosom tender adore darling wed marriage bride',
    'death': 'death dead die died dying grave tomb corpse mortal ghost funeral buried bury shroud slain perish doom',
    'nature': 'tree trees flower flowers leaf leaves wind river stream mountain hill hills meadow forest wood woods grass bird birds spring summer autumn winter dew moon stars sun sky rain snow',
    'the sea': 'sea ocean wave waves ship sail sailor mariner shore tide deep billows harbour bark mast storm foam',
    'art and poetry': 'poet poets poetry verse rhyme song sing muse muses lyre art painter pen book books page laurel bard',
    'time': 'time hour hours year years age ages moment eternal ancient old youth memory forever past future clock',
    'war': 'war battle sword swords blood soldier soldiers cannon siege army fight fought slaughter victory glory foe enemy',
    'faith': 'god heaven angel angels soul prayer pray holy saint church sin devil hell divine paradise faith',
    'beauty': 'beauty beautiful fair lovely grace graceful bright golden sweet gentle eyes cheek lips hair',
    'satire and society': 'lord lady ladies fashion fashionable society polite politics parliament money gold rich poor wit critic press public dinner ball party',
    'melancholy': 'sad sorrow grief tears weep wept mourn melancholy pain woe weary despair lonely alone gloom',
    'night': 'night midnight dark darkness shadow shadows dream dreams sleep silence lamp candle',
}
THEME_SETS = {k: set(v.split()) for k, v in THEMES.items()}
def themes_for(lines):
    cnt = collections.Counter(); total = 0
    for l in lines:
        for tok in TOKEN.findall(l):
            w = re.sub(r"^[^a-z']+|[^a-z']+$", '', norm(tok)); total += 1
            for k, ws in THEME_SETS.items():
                if w in ws: cnt[k] += 1
    if not total: return []
    scored = [(k, c / total) for k, c in cnt.items() if c >= 3]
    scored.sort(key=lambda x: -x[1])
    return [k for k, r in scored[:3] if r >= 0.008]

# ------------------------------------------------------------ per work
def spell_key(w):
    """Last vowel group and what follows, from the spelling, for words the dictionary lacks: wantonness -> ess."""
    w2 = re.sub(r"[^a-z]", '', w.lower())
    if re.search(r'[^aeiouy]e$', w2) and len(w2) > 3: w2 = w2[:-1]   # silent e: come -> com
    m = re.search(r'[aeiouy]+[^aeiouy]*$', w2)
    return 'SP:' + m.group(0) if m else ''
def loose_of(w):
    ph = phones(w) if w else None
    return loose_key(ph[0]) if ph else spell_key(w)
METER_SYL = {'iambic pentameter': 10, 'mostly iambic pentameter': 10, 'blank verse': 10, 'heroic couplets': 10,
             'iambic tetrameter': 8, 'trochaic tetrameter': 8, 'iambic trimeter': 6, 'trochaic octameter': 16}


def syl_core(tok):
    """The key word_syls() counts under, so what is learned here is looked up there."""
    return re.sub(r"^[^a-z']+|[^a-z']+$", '', norm(tok))


def learn_syllables(work, rising):
    """Learn the syllable count of words the dictionary does not hold, from the metre the poem keeps.

    The spelling rules in word_syls() are rules about English, and a Greek name is not English. 'Atrides'
    ends in -es, so the plural rule takes a syllable off it and makes it two; Pope wrote it as three, and
    did so 67 times, every one of them in a line that then came out a syllable short of his pentameter.
    'Pelides', 'Tydides', 'Deiphobus', 'Machaon' and 'Menelaus' go the same way. The dictionary has no
    opinion about any of them, so the poem is the better witness and is asked instead.

    A word is only credited when the evidence is its own. Lines holding more than one unknown word are
    passed over, because there is no telling which of them is short. Every line holding exactly one is
    counted, including the lines that come out the right length -- counting only the short ones would find
    a deficit for any word that ever appeared in a short line. The commonest deficit must be positive, no
    more than three, and hold three lines and sixty per cent of them before it is believed.
    """
    lines = [t for sec in work['sections'] for st in sec['stanzas'] for t in st if t.strip()]
    if len(lines) < 50: return {}
    raw = [len(line_syls(t, None, rising)) for t in lines]
    expect = METER_SYL.get(work.get('meter'))
    if not expect:
        c = collections.Counter(raw); m, k = c.most_common(1)[0]
        if m < 4 or k < len(raw) * 0.55: return {}     # no metre steady enough to argue from
        expect = m
    # Only a poem that keeps one line length can say anything about a word in it. Burns's Standard Habbie
    # runs 8-8-8-4-8-4, and its four-syllable lines are short by design; asked as though every line wanted
    # eight, the count blamed the shortfall on whatever Scots word happened to be there and made one
    # syllable of 'pund' into four, 'maks' and 'thraw' into two.
    near = sum(1 for r in raw if abs(r - expect) <= 1)
    if near < len(raw) * 0.70: return {}
    ev = collections.defaultdict(collections.Counter)
    for text, total in zip(lines, raw):
        # A line far below the measure is a short line, not a miscounted one.
        if not (expect - 3 <= total <= expect + 1): continue
        unknown = [w for w in (syl_core(t) for t in TOKEN.findall(text))
                   if len(w) > 2 and w not in OVR_SYL and not phones(w)]
        if len(unknown) != 1: continue
        ev[unknown[0]][expect - total] += 1
    out = {}
    for w, c in ev.items():
        tot = sum(c.values())
        d, k = c.most_common(1)[0]
        if not (1 <= d <= 2): continue
        # Three lines that all agree, or four of which most do. Two lines out of three is the shape a word
        # gets by turning up twice in a line that was short for some other reason.
        if (tot >= 3 and k == tot) or (tot >= 4 and k >= tot * 0.6): out[w] = d
    return out


def local_expect(lines, rising, floor=8):
    """The syllable count the lines around a line keep, or None if they do not keep one.

    If every line around a line is the same length, the odd one out is worth a second look. Elision can only ever merge syllables that genuinely contract, so aiming a line
    at what its neighbours do cannot invent anything -- it only asks the question. Without this there is
    nothing to ask: Dutt's Mahabharata is catalogued as 'mixed', so no measure was expected of it, no
    elision was tried, and a line reading 'Like two untamed jungle tuskers in the deep and echoing wood!'
    came out at sixteen against its neighbours' fifteen because 'echoing' was counted in full.
    """
    if len(lines) < floor: return None
    raw = [len(line_syls(t, None, rising)) for t in lines if t.strip()]
    if len(raw) < floor: return None
    mode, n = collections.Counter(raw).most_common(1)[0]
    if mode < 4: return None
    near = sum(1 for r in raw if abs(r - mode) <= 1)
    return mode if (n >= len(raw) * 0.40 and near >= len(raw) * 0.60) else None


INTERLOCK_WINDOW = 6      # a rhyme partner this far away or nearer, counted across the stanza break
INTERLOCK_SHARE = 0.40    # this share of a poem's unlettered ends must find their partner next door
ALPHA52 = [chr(ord('A') + k) for k in range(26)] + [chr(ord('a') + k) for k in range(26)]


def relink_interlocking(work, lines_out, schemes):
    """Letter a poem straight through where its rhyme crosses the stanza break.

    Convention divides here, and the poem says which side it is on. A closed stanza -- ottava rima, rhyme
    royal, the Spenserian stanza, the ballad quatrain, the sonnet -- is its own rhyme unit, and its letters
    restart at A; describing Byron's stanza as ABABABCC is right and calling the next stanza's rhymes
    I through P would be perverse. An interlocking form does the opposite. Terza rima is written
    ABA BCB CDC, and that notation is not a convenience: the whole interest of the form is that the middle
    line of each tercet seeds the next, which restarting at A would hide. Yeats does the same thing in
    The Grey Rock, where 'say' ends one stanza and 'day' opens the next.

    So: count how many of a poem's unlettered ends find a rhyme in the stanza beside them. Where that is
    how the poem works, its lines are lettered as one sequence and the letters run on. Where it is not, the
    stanzas keep their own letters and nothing changes. Matching stays strict -- the same rhyme key, a
    different word, and within a few lines -- because a poem lettered continuously would otherwise collect
    every accidental echo along its length.
    """
    by, order = collections.OrderedDict(), []
    for i, r in enumerate(lines_out):
        k = (r[0], r[1])
        if k not in by: by[k] = []; order.append(k)
        by[k].append(r)
    if len(order) != len(schemes): return schemes, 0

    secs = collections.OrderedDict()
    for idx, k in enumerate(order): secs.setdefault(k[0], []).append(idx)

    changed = 0
    for sec, idxs in secs.items():
        if len(idxs) < 3: continue
        rows = [r for i in idxs for r in by[order[i]]]
        # Terza rima runs long by nature -- Shelley's is 537 lines in one section -- and a cap of a few
        # hundred excluded exactly the poems this is for.
        if len(rows) < 9 or len(rows) > 2000: continue
        if any(len(by[order[i]]) > 30 for i in idxs): continue   # verse paragraphs go by another route
        keys = [r[4] for r in rows]; ews = [r[3] for r in rows]
        # where each line sits in the flat sequence, and which stanza it belongs to
        stanza_of, pos = [], 0
        for i in idxs:
            for _ in by[order[i]]: stanza_of.append(i)
        orph = cross = 0
        base = 0
        for i in idxs:
            sch = schemes[i]
            for li, ch in enumerate(sch):
                if ch != '-' or not keys[base + li]: continue
                orph += 1
                here = base + li
                for m in range(max(0, here - INTERLOCK_WINDOW), min(len(rows), here + INTERLOCK_WINDOW + 1)):
                    if stanza_of[m] == i: continue
                    if keys[m] and keys[m] == keys[here] and ews[m] != ews[here]:
                        cross += 1; break
            base += len(sch)
        if orph < 3 or cross < 3 or cross < orph * INTERLOCK_SHARE: continue

        # letter the section as one sequence, joining only near neighbours
        group = [None] * len(rows); ng = 0
        for a in range(len(rows)):
            for b in range(a + 1, min(len(rows), a + INTERLOCK_WINDOW + 1)):
                if not keys[a] or keys[a] != keys[b] or ews[a] == ews[b]: continue
                if group[a] is None and group[b] is None: group[a] = group[b] = ng; ng += 1
                elif group[a] is None: group[a] = group[b]
                elif group[b] is None: group[b] = group[a]
        remap, out = {}, []
        for gv in group:
            if gv is None: out.append('-'); continue
            if gv not in remap: remap[gv] = ALPHA52[len(remap) % 52]
            out.append(remap[gv])
        at = 0
        for i in idxs:
            n = len(by[order[i]])
            new = ''.join(out[at:at + n]); at += n
            if new != schemes[i]: changed += 1
            schemes[i] = new
    return schemes, changed


def analyze(work):
    lines_out, stanza_schemes = [], []
    counts, forms = collections.Counter(), collections.Counter()
    rising = work.get('meter') != 'trochaic octameter'
    expect = METER_SYL.get(work.get('meter'))
    # Ask the poem about its own hard words before counting a single line with them in it.
    LEARNED.clear(); LEARNED.update(learn_syllables(work, rising))
    known = work.get('scheme')
    for si, sec in enumerate(work['sections']):
        # A book holds many poems, so the measure is asked of the poem, not of the book. The catalogue's
        # meter is preferred where it states one; where it does not, the section's own lines are asked.
        sec_expect = expect or local_expect([t for st in sec['stanzas'] for t in st], rising)
        for ti, st in enumerate(sec['stanzas']):
            keys, alls = [], []
            for li, text in enumerate(st):
                ew = end_word(text)
                rk, incmu = rhyme_key(ew) if ew else ('', 0)
                syls = line_syls(text, sec_expect, rising)
                stress = ''.join(c for _, c in syls)
                fit, off = meter_fit(stress, rising)
                lines_out.append([si, ti, li, ew, rk, incmu, len(syls), stress, [s for s, _ in syls], fit])
                keys.append(rk); alls.append(all_keys(ew) if ew else None)
                for tok in TOKEN.findall(text):
                    counts[re.sub(r"^[^a-z']+|[^a-z']+$", '', norm(tok))] += 1
            # rhyme scheme letters by key identity (long verse paragraphs are not treated as rhyme units)
            letters, order = [], {}
            if len(keys) > 30:
                # a long verse paragraph (couplets, blank verse): a line rhymes only with a neighbour within four lines, so that
                # the paragraph's accidental echoes far apart do not count; letters cycle A-Z, a-z, and colours cycle with them
                ews = [end_word(t) for t in st]; lks = [loose_of(e) for e in ews]; sps = [spell_key(e) for e in ews]
                group = [None] * len(keys); ng = 0
                for i in range(len(keys)):
                    for j in range(i + 1, min(len(keys), i + 5)):
                        same = (keys[i] and keys[i] == keys[j] and ews[i] != ews[j]) or (lks[i] and lks[j] and ews[i] != ews[j] and (loose_keys_match(lks[i], lks[j]) or (lks[i].startswith('SP:') or lks[j].startswith('SP:')) and sps[i] == sps[j] and len(sps[i]) >= 6))
                        if not same: continue
                        if group[i] is None and group[j] is None: group[i] = group[j] = ng; ng += 1
                        elif group[i] is None: group[i] = group[j]
                        elif group[j] is None: group[j] = group[i]
                alphabet = [chr(ord('A') + k) for k in range(26)] + [chr(ord('a') + k) for k in range(26)]
                out = ''.join('-' if g is None else alphabet[g % 52] for g in group)
                stanza_schemes.append(out); forms[('couplets' if out.count('-') < len(out) / 4 and all(out[k] == out[k + 1] for k in range(0, len(out) - 1, 2) if out[k] != '-') else 'long paragraph')] += 1; continue
            # Where a word has more than one pronunciation, the stanza settles which one the poet meant.
            # 'Again' is both AH0 G EH1 N and AH0 G EY1 N, and rhyme_key takes only whichever the dictionary
            # happens to list first; beside 'grain' or 'train' the second is plainly the one intended.
            # Each line is resolved against the lines before it, so first appearance still orders the letters.
            # Group the lines by the pronunciations they can share, narrowing each group to what all its
            # members agree on. Narrowing is what keeps this honest: 'again' is both EH N and EY N, so it
            # will join 'men', and it will equally join 'grain' -- but once it has joined 'men' the group
            # is EH N alone, and 'grain' is refused. Widening instead of narrowing would letter 'men' and
            # 'grain' as a rhyme through 'again' standing between them.
            groups = []
            res = []
            for i, k in enumerate(keys):
                ks = set(alls[i]) if alls[i] else ({k} if k else set())
                if not ks: res.append(k); continue
                for grp in groups:
                    inter = grp[0] & ks
                    if inter: grp[0] = inter; res.append(grp[1]); break
                else:
                    groups.append([ks, k]); res.append(k)
            for k in res:
                if k not in order: order[k] = chr(ord('A') + len(order)) if len(order) < 26 else '?'
                letters.append(order[k])
            # second tier: a line left alone by the strict key joins a neighbour whose final syllable matches loosely
            cnt = collections.Counter(letters)
            if any(v == 1 for v in cnt.values()):
                ews = [end_word(t) for t in st]; lks = [loose_of(e) for e in ews]; sps = [spell_key(e) for e in ews]
                for i in range(len(letters)):
                    if cnt[letters[i]] != 1 or not lks[i]: continue
                    for j in range(len(letters)):
                        if i != j and abs(i - j) <= 4 and ews[i] != ews[j] and (loose_keys_match(lks[i], lks[j]) or (lks[i].startswith('SP:') or lks[j].startswith('SP:')) and sps[i] == sps[j] and len(sps[i]) >= 6):
                            letters[i] = letters[j]; break
                cnt = collections.Counter(letters)
            scheme = ''.join(l if cnt[l] > 1 else '-' for l in letters)
            # re-letter so that used letters are consecutive
            remap, out = {}, ''
            for l in scheme:
                if l == '-': out += '-'; continue
                if l not in remap: remap[l] = chr(ord('A') + len(remap))
                out += remap[l]
            if known and len(known) == len(keys): out = known
            stanza_schemes.append(out)
            forms[out] += 1
    # Poems whose rhyme runs across the stanza break are lettered straight through, as terza rima must be.
    before = list(stanza_schemes)
    stanza_schemes, _relinked = relink_interlocking(work, lines_out, stanza_schemes)
    for i, (was, now) in enumerate(zip(before, stanza_schemes)):
        if was != now and forms.get(was): forms[was] -= 1; forms[now] += 1

    # glossary: words in this work that are uncommon or archaic
    gl = {}
    for w, c in counts.items():
        if len(w) < 4 or not w.isalpha(): continue
        if w in FUNC: continue
        g = gloss(w)
        if not g: continue
        rare = COMMON[w] <= 4 or (COMMON[w] <= 40 and any(f.startswith(('Obs', 'Archaic', 'Poet')) for f in g['flags']))
        if rare and len(g['defn']) <= 200:
            gl[w] = {'pos': g['pos'], 'defn': g['defn'], 'flags': g['flags'], 'n': c, 'etym': g.get('etym', '')}
    return lines_out, stanza_schemes, forms, gl

def nonmodern_pairs(work, lines_out, schemes):
    """Pairs the poet rhymes (by detected scheme or known form) that a modern dictionary does not rhyme."""
    known = work.get('scheme')
    by_st = collections.defaultdict(list)
    for r in lines_out: by_st[(r[0], r[1])].append(r)
    out = collections.Counter(); ex = {}
    for (si, ti), rows in by_st.items():
        rows.sort(key=lambda r: r[2])
        if known and len(rows) == len(known):
            groups = collections.defaultdict(list)
            for r, l in zip(rows, known): groups[l].append(r)
        else:
            continue
        for g in groups.values():
            for a, b in itertools.combinations(g, 2):
                if a[3] == b[3] or not a[3] or not b[3]: continue
                ka, kb = all_keys(a[3]), all_keys(b[3])
                if ka and kb and not (ka & kb):
                    k = tuple(sorted((a[3], b[3]))); out[k] += 1
                    # The pair is keyed alphabetically but the two sounds were stored in the order the
                    # lines came in, so whenever those differed the reader was told which sound belonged
                    # to which word the wrong way round: "everywhere ends in IH R and year in EH R", when
                    # it is the other way about.
                    ks = (ka, kb) if a[3] == k[0] else (kb, ka)
                    ex.setdefault(k, [si, ti, sorted(ks[0])[0], sorted(ks[1])[0]])
    return [[a, b, c] + ex[(a, b)] for (a, b), c in out.most_common()]

if __name__ == '__main__':
    # This annotates the parsed works, which the published corpus does not carry: it ships the TEI that
    # was written from these annotations. Say so rather than raise on the missing index.
    _index = os.path.join(WORKS, 'index.json')
    if not os.path.exists(_index):
        sys.exit('no parsed works at %s\n'
                 'The published corpus carries the TEI, which already holds what this writes. To read\n'
                 'poems out of it instead, use teiread.py.' % WORKS)
    index = json.load(open(_index))
    library = []
    # `python3 analyze.py slug ...` recomputes only those works and keeps the rest of library.json as it was
    only = set(sys.argv[1:]); old_lib = {}
    if only and os.path.exists(os.path.join(DATA, 'library.json')): old_lib = {m['slug']: m for m in json.load(open(os.path.join(DATA, 'library.json')))}
    for meta in index:
        if only and meta['slug'] not in only and meta['slug'] in old_lib: library.append(old_lib[meta['slug']]); continue
        work = json.load(open(os.path.join(WORKS, meta['slug'] + '.json')))
        lines_out, schemes, forms, gl = analyze(work)
        nm = nonmodern_pairs(work, lines_out, schemes)
        ew = collections.Counter(r[3] for r in lines_out if r[3])
        syl = collections.Counter(r[6] for r in lines_out)
        fem = sum(1 for r in lines_out if r[7] and r[7][-1] == 'U' and len(r[7]) > 1)
        stats = {
            'lines': len(lines_out), 'stanzas': len(schemes), 'distinct_end_words': len(ew),
            'hapax_share': round(sum(1 for v in ew.values() if v == 1) / max(len(ew), 1), 3),
            'mean_syllables': round(sum(r[6] for r in lines_out) / max(len(lines_out), 1), 2),
            'syllable_mode': syl.most_common(1)[0][0] if syl else 0,
            'top_schemes': forms.most_common(5), 'top_end_words': ew.most_common(8),
            'glossary_words': len(gl), 'drifted_pairs': len(nm),
            'mean_meter_fit': round(sum(r[9] for r in lines_out) / max(len(lines_out), 1), 3),
        }
        json.dump({'slug': work['slug'], 'lines': lines_out, 'schemes': schemes, 'nonmodern': nm, 'stats': stats},
                  open(os.path.join(WORKS, work['slug'] + '.lines.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
        json.dump(gl, open(os.path.join(WORKS, work['slug'] + '.glossary.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
        m = dict(meta); m['stats'].update(stats)
        for k in ('lang', 'original_title', 'composed', 'translator', 'epic'):
            if work.get(k) is not None: m[k] = work[k]
        m['source'] = work.get('source'); m['corrections'] = work.get('corrections', 0)
        m['sections'] = [{'id': s['id'], 'title': s['title'], 'short': s['short'], 'stanzas': len(s['stanzas']), 'themes': themes_for([l for st in s['stanzas'] for l in st])} for s in work['sections']]
        # Quality report: lines far off the length the work keeps, which are worth a human look. Some are
        # scanning faults in the source text and some are the poet doing something on purpose, and this
        # does not pretend to tell them apart.
        #
        # The length comes from the work itself rather than from a table of metres. A table only knew
        # three metres, so every book in any other measure was checked against nothing; and it had to be
        # told by name to forgive The Raven, whose refrain is deliberately short, which is a rule that
        # holds for exactly one poem. A line that repeats at a length the poem uses on purpose is not
        # suspect, so the lengths the work actually keeps are counted first and any of them is allowed.
        syl_all = collections.Counter(r[6] for r in lines_out)
        common = {n for n, c in syl_all.items() if c >= max(3, 0.05 * len(lines_out))}
        qc = []
        if common:
            for r in lines_out:
                if any(abs(r[6] - n) <= 2 for n in common): continue
                qc.append({'sec': r[0], 'stanza': r[1], 'line': r[2],
                           'why': f'{r[6]} syllables, where this work keeps to ' + ', '.join(str(n) for n in sorted(common)),
                           'text': work['sections'][r[0]]['stanzas'][r[1]][r[2]]})
        json.dump(qc, open(os.path.join(WORKS, work['slug'] + '.qc.json'), 'w'), ensure_ascii=False, indent=0)
        m['stats']['suspect_lines'] = len(qc)
        library.append(m)
        print(f"{work['slug']:22s} lines={len(lines_out):6d} schemes={forms.most_common(3)} gloss={len(gl):5d} drifted={len(nm):4d} fit={stats['mean_meter_fit']}")
    json.dump(library, open(os.path.join(DATA, 'library.json'), 'w'), ensure_ascii=False, indent=1)
    import datetime; json.dump({'build': datetime.datetime.utcnow().strftime('%Y%m%d%H%M')}, open(os.path.join(DATA, 'build.json'), 'w'))
    # compact pronouncing dictionary for the browser-side form checker: word -> [stress digits, rhyme key]
    comp = {}
    for w, phs in CMU.items():
        if not w.isalpha() or len(w) > 18: continue
        ph = phs[0]
        comp[w] = [''.join(p[-1] for p in ph if p[-1].isdigit()), cmu_key(ph)]
    json.dump(comp, open(os.path.join(DATA, 'cmu.json'), 'w'), separators=(',', ':'))
    print('cmu compact:', len(comp))
