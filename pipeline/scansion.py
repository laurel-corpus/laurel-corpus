"""Name a poem's metre by proposing metres and testing the words against them.

The older detector in generic.py measured the gap between one dictionary-fixed stress and the next.
That works on a book and fails on a poem. Shakespeare's eighteenth sonnet scans

    Shall I compare thee to a summer's day?      xuUSuuuSUx

-- ten syllables carrying two stresses the dictionary will vouch for. A whole Paradise Lost supplies
tens of thousands of such gaps and settles easily; fourteen lines supply twenty-eight and settle into
nothing. That is why 12,621 of 18,108 poems came back unnamed.

A person does not scan that way. A person proposes iambic pentameter, reads the line against it, and
sees whether the words fight. So does this: every candidate metre is built as a template, every
syllable of every line is tested against it, and the metre that argues least with the words wins.
A sonnet then offers 140 syllables of evidence instead of 28.

Scored against For Better For Verse, the University of Virginia's hand-scansion corpus, in which a
prosodist has marked the metre of every line of some ninety poems. Nothing from it is copied into the
site; it is a ruler, not a source.
"""
import collections, json, os, re

# 1 is where the metre wants a stress, 0 where it wants a slack.
FEET = {'iambic': '01', 'trochaic': '10', 'anapaestic': '001', 'dactylic': '100'}
LENGTHS = {1: 'monometer', 2: 'dimeter', 3: 'trimeter', 4: 'tetrameter', 5: 'pentameter',
           6: 'hexameter', 7: 'heptameter', 8: 'octameter'}
RISING = ('iambic', 'anapaestic')

# The dictionary fixes the stress inside a word of two syllables or more -- nobody says a-MA-zing any
# other way -- and says nothing at all about a word of one. That silence is most of English verse:
#
#     That saved a wretch like me      uxuxxu
#
# Six syllables, six words, not one of them fixed. A method that listens only to the dictionary is
# deaf to the ballads, the hymns and most of Dickinson, which is to say to the poems whose metre is
# least in doubt. A reader is not deaf to them, because a reader knows that 'saved', 'wretch' and 'me'
# carry the sense while 'that', 'a' and 'like' only join them up. English gives its beats to the words
# that mean something.
#
# So a monosyllable votes too, quietly. A closed-class word -- article, preposition, conjunction,
# pronoun, auxiliary -- expects a slack; anything else expects a beat. The vote is worth a fraction of
# a dictionary stress because it is a tendency, not a fact: verse inverts it constantly, and the whole
# art of a line like 'Of Man's first disobedience' is the preposition taking the beat.
FUNCTION = set("""
 a an the and or but nor for yet so as if of to in on at by up out off down with from into unto onto
 upon than that this these those there here where when while what which who whom whose why how all
 am are be been is was were will would shall should may might must can could do does did done have
 has had my me mine i we us our ours you your yours ye he him his she her hers it its they them
 their theirs no not now then thus too very such some any each both more most other same o oh ah
 nay ere till nigh though thy thee thou hath doth art wilt shalt didst hast dost let
 through thro since whilst lest whence thence hence midst twixt gainst neath oer ner eer
""".split())
# The second line is the one that was missing. 'Through' is as plain a preposition as 'with', and its
# absence left it with no opinion at all, so a template was free to put the beat on it: Hart Crane's
# 'Through much of what she would not understand' came out with a stressed THROUGH opening the line.
# The rest are the same word class, most of them the contractions this library is full of.

# Swept on the development half once real substitutions existed to charge for. Below 0.08 a bent foot is
# so cheap that every line can be explained and nothing is securely in any metre (87.4%); above 0.35 no
# line may bend at all and the substitutions might as well not be there (91.5%). 0.20 is the top of the
# curve at 92.4%.
SUB_COST = 0.20  # what bending one foot to the other length costs a reading
SOFT = 0.30      # what a monosyllable's part of speech is worth against a stress the dictionary fixes
DEAD = 0.15      # ...and what it is worth for a word the table has watched go both ways (see evidence)

# How often each one-syllable word actually takes the beat, learned by monostress.py from the training
# half of the hand-annotated corpora. A word of two syllables or more has its stress in the dictionary
# and is almost never wrong; a word of one has none, and deciding it was 95% of everything the scanner
# got wrong. The single constant above stood in for a range that runs from 3% ('the') to 96% ('life').
#
# The weight matters as much as the guess. A word near even odds is not weak evidence to be nudged with;
# it is a word the METRE should settle, and asserting it at any weight argues with the poem. So the
# weight falls to nothing as the rate approaches a half, and rises towards certainty at either end.
# Two tables, and the order between them matters. mono-corpus.json is learned from this library itself,
# which is a great deal of evidence of a slightly circular kind; mono-stress.json is learned from words a
# person marked by hand. So the corpus fills in the words the hand-annotated set never saw, and where
# both have an opinion the hand-annotated one is taken.
_MONO = {}
_HERE = os.path.dirname(os.path.abspath(__file__))
for _f in ('mono-corpus.json', 'mono-stress.json'):
    try:
        _t = json.load(open(os.path.join(_HERE, _f), encoding='utf-8'))
        _MONO.update(_t.get('rate') or {})
    except Exception:
        pass
# A one-syllable word's habit is evidence, not a fact: 47% of the remaining errors were words the table
# was confident about -- of, and, it, my, not -- in lines where the metre legitimately promotes them.
# At 0.85 the habit was nearly as loud as the dictionary and the metre could not overrule it.
MONO_MAX = 0.70      # the most a one-syllable word may ever assert, against 1.0 for the dictionary
MONO_DEAD = 0.10     # rates within this of even say nothing at all

def mono_opinion(core):
    """(wants, weight) for a one-syllable word, or None if the table has never seen it."""
    r = _MONO.get(core)
    if r is None: return None
    off = abs(r - 0.5)
    if off < MONO_DEAD: return (None, 0.0)          # let the metre decide
    w = MONO_MAX * min(1.0, (off - MONO_DEAD) / (0.5 - MONO_DEAD))
    return ('1' if r > 0.5 else '0', round(w, 3))

def evidence(text):
    """One (wants, weight) per syllable of a line: what the words themselves insist on.

    `wants` is '1' for a stress, '0' for a slack, None where the words have no opinion and the metre
    may do as it likes.
    """
    from analyze import TOKEN, norm, word_syls
    out = []
    for tok in TOKEN.findall(text):
        for part in tok.split('-'):
            core = re.sub(r"^[^a-z']+|[^a-z']+$", '', norm(part))
            sy = word_syls(part)
            if not sy: continue
            mono = len(sy) == 1
            for _, c in sy:
                if c == 'S': out.append(('1', 1.0))
                elif c == 'U': out.append(('0', 1.0))
                elif mono:
                    # Where the learned table has no useful opinion -- either it has never seen the word,
                    # or it has seen it go both ways about equally -- fall back to what part of speech the
                    # word is. Those two cases used to be treated differently: an unseen word got the
                    # part-of-speech prior and a word measured at 50/50 got nothing at all, which is how
                    # 'through' ended up with no opinion. It is a preposition whether or not the training
                    # lines happened to stress it half the time, and a syllable with no opinion is one the
                    # template may do anything with -- which is how a line came to open on a stressed
                    # THROUGH. A dead-zone reading means the table adds nothing, not that nothing is known.
                    op = mono_opinion(core)
                    if op and op[1]: out.append(op)
                    else:
                        w = SOFT if op is None else DEAD
                        out.append(('0' if core in FUNCTION else '1', w))
                else: out.append((None, 0.0))
    return out

# A foot may swap for its neighbour of the other length, and English verse does this constantly. Blake:
#
#     Speak, father, speak to your little boy,     four beats, nine syllables
#     Or else I shall be lost.                     three beats, six syllables
#
# The second line is plain iambic trimeter. The first is an iambic four-beat line with one anapaest in
# it -- what editors call loose iambic -- and refusing the substitution forced it to be read as five
# feet instead of four, which turned a ballad stanza into 'iambic tetrameter' and lost the four-and-
# three that makes it a ballad. Anapaestic verse takes iambs just as freely.
SWAP = {'01': '001', '10': '100', '001': '01', '100': '10'}

# A foot may also be replaced by another of the SAME length, which is what a metrist means by
# substitution. Until now the scanner could only say 'iambic pentameter' or not; it had no way to say
# 'iambic pentameter with the third foot inverted', so a line carrying one was matched to whichever
# whole-line pattern came nearest and the difference was scored as error. Measured on the control, 10%
# of lines had no exact template available within their own foot, and that was the largest single thing
# left between the scanner and a scholar's standard.
#
# Only the substitutions editors actually name. An inversion -- a trochee for an iamb -- is the
# commonest event in English verse; a spondee levels two stresses; a pyrrhic drops both.
SUBSTITUTES = {
    '01': (('10', 1.0), ('11', 1.2), ('00', 1.2)),      # iamb: inverted, spondee, pyrrhic
    '10': (('01', 1.0), ('11', 1.2), ('00', 1.2)),      # trochee, the same in reverse
    '001': (('100', 1.0), ('010', 1.3)),                # anapaest: inverted, or amphibrach
    '100': (('001', 1.0), ('010', 1.3)),
}
MAX_SUB = 2        # a line needing three is not that metre with substitutions, it is another metre
HEAD_DISCOUNT = 0.45   # an inverted FIRST foot is so ordinary it should barely count against a reading

def _feet(foot, n, most=1):
    """Every way to walk n feet: up to `most` of them swapping length, and up to MAX_SUB replaced by a
    foot of the same length. Values are what the reading costs, so the plainest account of a line wins a
    tie and a line bent in three places loses to one that simply is in another metre."""
    alt = SWAP[foot]
    out = {}
    subs = SUBSTITUTES.get(foot, ())
    for mask in range(1 << n):
        k = bin(mask).count('1')
        if k > most: continue
        feet = [alt if (mask >> i) & 1 else foot for i in range(n)]
        base = ''.join(feet)
        if out.get(base, 99) > k: out[base] = k
        if not subs: continue
        # one substitution
        for i in range(n):
            if feet[i] != foot: continue          # a foot already swapped for length is not swapped again
            for rep, c in subs:
                one = feet[:]; one[i] = rep
                cost = k + c * (HEAD_DISCOUNT if i == 0 else 1.0)
                t = ''.join(one)
                if out.get(t, 99) > cost: out[t] = cost
                if MAX_SUB < 2: continue
                # two, which is as far as this goes
                for j in range(i + 1, n):
                    if feet[j] != foot: continue
                    for rep2, c2 in subs:
                        two = one[:]; two[j] = rep2
                        cost2 = cost + c2
                        t2 = ''.join(two)
                        if out.get(t2, 99) > cost2: out[t2] = cost2
    return out

def variants(foot, n):
    """Every shape a line of n feet may legitimately take, and what each one costs.

    Verse lines are not required to fill the last foot or open the first. A trochaic tetrameter
    routinely drops its final slack -- 'Tyger! tyger! burning bright' is seven syllables, not eight --
    and an iambic line as routinely adds one, which is how 'that is the question' ends a pentameter.
    Refusing these would throw away most of English poetry as unscannable.
    """
    out = {}
    def keep(t, cost):
        if t and out.get(t, 99) > cost: out[t] = cost
    k = len(foot) - 1                        # a foot may lose its slacks, never its stress
    for base, subs in _feet(foot, n).items():
        for head in range(k + 1):
            if '1' in base[:head]: break     # never trim into the first stress
            for tail in range(k + 1):
                if tail and '1' in base[len(base) - tail:]: continue
                # One licence to a line, at the head or at the foot, never both. The rule below already
                # says this about a feminine ending; it has to be said about a missing final slack too,
                # and for the same reason. Six trochees that lose their first syllable and their last
                # are ten syllables reading -+-+-+-+-+, which is not merely LIKE iambic pentameter, it
                # is iambic pentameter, letter for letter: 26 of the templates at that length were being
                # offered by both feet. A sonnet then scores the same in either, the tie falls to
                # whichever way the line-openings lean, and Shakespeare -- who begins a great many lines
                # on a stress -- came out trochaic. A reading that has to bend both ends of the line to
                # reach another metre's plainest shape has not found a second reading of the poem.
                if head and tail: continue
                body = base[head:len(base) - tail] if tail else base[head:]
                keep(body, subs)
                # A feminine ending -- one slack past the last stress -- but only on a line that has
                # not already been licensed at the head. Allowing both at once lets an iambic
                # tetrameter drop its first syllable and grow one at the end, which produces the
                # trochaic template exactly; Hiawatha then reads as iambic, and no line is ever
                # securely trochaic again. One licence to a line: a line that wants two is simply in
                # the other foot.
                if not head: keep(body + '0', subs)
    return out

# Every template is the same for every line, so build them once and file them by length. Without this
# the library takes an hour: eighteen thousand poems x four feet x eight lengths x six licences.
_BY_LEN = {}
def by_length(foot):
    if foot not in _BY_LEN:
        d = collections.defaultdict(list)
        for n in range(1, 9):
            for tpl, subs in variants(FEET[foot], n).items():
                # The stressed positions travel with the template. Scoring a line against it is then a
                # sum over those positions instead of a walk down every syllable -- see weigh().
                ones = tuple(i for i, c in enumerate(tpl) if c == '1')
                d[len(tpl)].append((tpl, n, subs, ones))
        _BY_LEN[foot] = d
    return _BY_LEN[foot]

# What a template pays for contradicting a syllable the DICTIONARY settles. Measured on the control, 41%
# of every wrongly marked syllable was a polysyllable whose stress the dictionary already knew and the
# chosen template overruled -- the metre saying the second syllable of 'lovely' takes the beat. The
# dictionary is right about those 99.2% of the time; the metre should bend around them, not through them.
# Swept on the development half: 1.0 -- no penalty at all -- scores best, and the whole grid from 1.0 to
# 4.5 spans half a point. So the diagnosis was right as a description and wrong as a remedy. Making the
# template respect the dictionary forces it to choose a worse template everywhere else, and the two
# cancel. The kept value is 1.0, which is to say this knob does nothing and is left here named, so the
# next person does not spend an evening rediscovering that.
HARD = 1.0

def fit(ev, tpl):
    """(agreement, weight) of a line against a template. Each syllable votes with its own weight, and a
    syllable the dictionary fixed votes several times over when it is contradicted."""
    ok = n = 0.0
    for (want, w), t in zip(ev, tpl):
        if not w: continue
        if want == t:
            n += w; ok += w
        elif w >= 1.0:
            n += w * HARD                 # disagreeing with the dictionary is expensive
        else:
            n += w
    return (ok / n if n else 0.0), n

def weigh(ev):
    """(total weight, the score of a template that stresses nothing, one term per syllable) for a line.

    fit() above is the readable statement of what a line's agreement with a template means, and it is
    what bench.py and the tests measure against. This is the same arithmetic rearranged so that a line
    can be scored against a thousand templates without walking its syllables a thousand times.

    Per-foot substitution took iambic pentameter from about thirty templates to twelve hundred, which is
    the whole gain in accuracy and also a forty-fold slowdown: a full pass over the library went from
    minutes to most of a day. Rearranging costs nothing in fidelity. Because every syllable's weight is
    counted whether the template agrees with it or not, the denominator is the same for every template
    of the same length, so it is computed once here rather than a thousand times below. And the
    numerator splits: start from what a template scores by marking every syllable slack, then each
    stress the template does mark either gains that syllable's weight (the line wanted a stress there)
    or loses it (the line wanted a slack, and the flat start had already credited it).

    Exact only while HARD is 1.0, which it is; best_line falls back to fit() if that ever changes.
    """
    total = flat = 0.0
    s = []
    for want, w in ev:
        if not w:
            s.append(0.0); continue
        total += w
        if want == '1':
            s.append(w)
        else:
            flat += w; s.append(-w)
    return total, flat, s

def best_line(ev, foot, lo=1, hi=8, prefer=None, cost=True):
    """(agreement, weight, feet) for the best reading of one line in a given foot.

    Where a length admits two readings -- nine syllables is a headless pentameter or a tetrameter with
    a feminine ending, and no line settles that by itself -- `prefer` lets the poem's prevailing count
    decide, which is how a reader settles it too.
    """
    f = FEET[foot]
    best = None
    total, flat, s = weigh(ev)
    w = total
    get = s.__getitem__
    for tpl, n, subs, ones in by_length(foot).get(len(ev), ()):
        if not lo <= n <= hi: continue
        if HARD == 1.0:
            a = (flat + sum(map(get, ones))) / total if total else 0.0
        else:
            a, w = fit(ev, tpl)
        # A reading that needs no substitution is the plainer account of the line, so it wins a tie.
        # The cost is charged only while deciding WHICH FOOT the poem walks in, so that a poem of
        # iambs cannot pass itself off as one of anapaests by bending a foot in every line. Once the
        # foot is settled the question is only how many of them a line has, and charging for the
        # substitution there made 'Father, father, where are you going?' -- four beats and nine
        # syllables -- come out as five feet, which is how a ballad stanza loses its four-and-three.
        if cost: a -= SUB_COST * subs
        # Agreement is rounded before ranking so that readings the words cannot separate count as
        # tied, and the poem's own prevailing measure breaks the tie. That is how a reader does it:
        # establish the measure, then read the doubtful line in it.
        key = (round(a, 2), -abs(n - prefer) if prefer else 0, w, len(f) * n == len(ev), n)
        if best is None or key > best[0]: best = (key, n, a, w)
    if best is None: return 0.0, 0.0, 0
    return max(0.0, best[2]), best[3], best[1]

def scan(evs):
    """The metre of a set of lines: (foot, feet, confidence, shape), or (None, ...) if it will not settle.

    Three passes, because the questions differ. Which foot the poem walks in is asked of every line at
    once, since it is a property of the poem. How long the line is, is asked of each line by itself --
    a great many poems alternate lengths on purpose, and the four-and-three of a ballad is not an
    average of three and a half. Then the lines that admit two readings are asked again, with the
    poem's prevailing length in hand.
    """
    evs = [e for e in evs if e and len(e) >= 3]
    if len(evs) < 4: return None, None, 0.0, None
    scores = {}
    for foot in FEET:
        num = den = 0.0
        for e in evs:
            a, w, _ = best_line(e, foot)
            num += a * w; den += w
        scores[foot] = num / den if den else 0.0
    foot = max(scores, key=scores.get)
    # A rising and a falling reading of the same alternating line differ only at the ends, and a duple
    # line can always be read as a triple one with two slacks missing, so these scores come out close
    # and the bare winner is not yet meaningful. English leans duple and rising; depart from that only
    # when the words clearly say so.
    #
    # What says so is how the lines BEGIN. A falling metre puts a
    # stress in the first syllable of the line, over and over; a rising one does not. Weighted across a
    # poem the two do not overlap: L'Allegro 48%, Locksley Hall 62%, the Mermaid Tavern 69%, The Raven
    # 62%, To a Skylark 49% -- against Gray's Elegy 10%, the Nightingale 24%, Paradise Lost 27%. Every
    # one of those falling poems comes out iambic without it, because an iambic line that has lost its first
    # slack is letter for letter a catalectic trochaic line, and the tie was broken by a rule that knew
    # only that English prefers iambs.
    up = tot = 0.0
    for e in evs:
        w, wt = e[0]
        if w is None or wt <= 0: continue
        tot += wt; up += wt * (w == '1')
    opens_falling = (up / tot) >= HEAD_FALLING if tot else False
    bias = 0.0 if opens_falling else 0.05
    if foot == 'trochaic' and scores['trochaic'] - scores['iambic'] < bias: foot = 'iambic'
    if foot == 'dactylic' and scores['dactylic'] - scores['anapaestic'] < bias: foot = 'anapaestic'
    # ...and where the poem plainly opens on stresses, a near miss goes the other way instead.
    if opens_falling:
        if foot == 'iambic' and scores['iambic'] - scores['trochaic'] < HEAD_MARGIN: foot = 'trochaic'
        elif foot == 'anapaestic' and scores['anapaestic'] - scores['dactylic'] < HEAD_MARGIN: foot = 'dactylic'
    if foot in ('anapaestic', 'dactylic'):
        duple = 'iambic' if foot == 'anapaestic' else 'trochaic'
        if scores[foot] - scores[duple] < 0.05: foot = duple
    conf = scores[foot]
    first = collections.Counter(best_line(e, foot, cost=False)[2] for e in evs)
    first.pop(0, None)
    if not first: return None, None, 0.0, None
    mode = max(first.items(), key=lambda kv: (kv[1], kv[0]))[0]
    shape = [best_line(e, foot, prefer=mode, cost=False)[2] for e in evs]
    lens = collections.Counter(n for n in shape if n)
    if not lens: return None, None, 0.0, None
    return foot, max(lens.items(), key=lambda kv: (kv[1], kv[0]))[0], round(conf, 3), shape

# A metre can have a name of its own when the LINE LENGTHS make a pattern, not just the feet. Four
# feet answered by three is common measure -- the shape of the ballads and of most of Dickinson -- and
# calling it 'iambic tetrameter' throws away the half of the pattern that matters.
#
# Long measure (8.8.8.8) is deliberately absent. It is a real name, but nothing in the lines
# distinguishes it from any other quatrain of iambic tetrameter; it is hymnody that makes it long
# measure, and the lines do not say whether a poem is a hymn.
PATTERNS = {
    ('iambic', (4, 3, 4, 3)): 'common measure',
    ('iambic', (3, 3, 4, 3)): 'short measure',
    ('iambic', (6, 7)): "poulter's measure",
    ('iambic', (7, 7)): 'fourteeners',
    ('iambic', (6, 6)): 'alexandrines',
    ('iambic', (6, 6, 6, 6)): 'alexandrines',
    ('anapaestic', (4, 3, 4, 3)): 'anapaestic common measure',
}

def pattern_of(foot, stanzas):
    """The name a poem's line lengths earn, or None.

    Asked of the stanzas rather than the poem, because the pattern IS the stanza: a ballad is four
    feet answered by three, over and over.

    Read position by position rather than stanza by stanza. Requiring every stanza to be exactly
    4/3/4/3 threw away most of Dickinson, whose 'A precious, mouldering pleasure' runs 5/3/4/2,
    4/4/4/3, 4/3/5/3, 4/3/4/3 -- unmistakably four answered by three, and not one stanza of it exact.
    A poet writing common measure crowds an extra syllable into a line whenever the sense wants one;
    the pattern is what the lines do on the whole, not what every last one of them does.
    """
    stanzas = [s for s in stanzas if s and all(s)]
    if len(stanzas) < 2: return None
    sizes = collections.Counter(len(s) for s in stanzas)
    k, n = sizes.most_common(1)[0]
    if k not in (2, 4) or n / len(stanzas) < 0.5: return None
    rows = [s for s in stanzas if len(s) == k]
    # Where a position's votes are tied, the evidence does not settle that line and the tie is broken
    # by asking which reading names a measure that exists. Blake's 'Father, father, where are you
    # going?' opens on a trochee, so its nine syllables read as easily in five feet as in four, and
    # with two stanzas to go on the vote is 1-1. Four makes it a ballad stanza; five makes it nothing.
    # A reader settles it the same way, by recognising the stanza and reading the line into it.
    import itertools
    cols = []
    for i in range(k):
        col = collections.Counter(r[i] for r in rows)
        top = max(col.values())
        cols.append(sorted((v for v, n in col.items() if n >= top), reverse=True)[:3])
    best = None
    for combo in itertools.product(*cols):
        agree = sum(sum(1 for r in rows if r[i] == combo[i]) for i in range(k))
        if agree / (k * len(rows)) < 0.6: continue      # a shape most of the lines actually keep
        named = PATTERNS.get((foot, combo))
        if named and (best is None or agree > best[0]): best = (agree, named)
    return best[1] if best else None

# Below this the words are fighting the metre too hard for the name to mean anything. Chosen on half
# the For Better For Verse poems and then tested on the other half, which the choice never saw: it
# keeps 19 poems in 20 and is right about 9 times in 10. It is set no lower because the library holds
# a great deal that is not lyric verse -- arguments, dedications, cast lists -- and a floor is the only
# thing standing between those and a confident wrong answer.
HEAD_FALLING = 0.40   # share of line-openings that must be stressed before a falling reading is considered
HEAD_MARGIN = 0.08    # how far behind the rising reading a falling one may be, once the openings agree

FLOOR = 0.70

def refit(text, target):
    """Re-read one line on the assumption that the poem's metre is right and the line is not scanning.

    This is how a person scans: you do not decide in advance that 'hour' is one syllable. You read the
    poem, find it is in four-beat lines, reach a line that comes out five, and
    ask which word in it could be read shorter. Measured over the corpus these words go the short way
    about nine times in ten -- but 2,117 lines in settled metres need 'our', 'fire' and 'power' at their
    full length, and a rule that shortened them everywhere would misread every one.

    So nothing is shortened unless the metre asks, and then only as far as it asks: the word that can
    give up the most goes first, and the moment the line comes out right the rest are left alone.
    """
    from analyze import TOKEN, norm, word_syls, elide_to
    parts = []
    for tok in TOKEN.findall(text):
        for part in tok.split('-'):
            core = re.sub(r"^[^a-z']+|[^a-z']+$", '', norm(part))
            sy = word_syls(part)
            if sy: parts.append([part, core, sy])
    n = sum(len(p[2]) for p in parts)
    if n <= target: return None
    # what each word could give up, largest first
    room = []
    for i, (part, core, sy) in enumerate(parts):
        short = elide_to(core)
        if short is not None and 0 < short < len(sy): room.append((len(sy) - short, i, short))
    room.sort(reverse=True)
    cut = {}
    for give, i, short in room:
        if n <= target: break
        take = min(give, n - target)
        cut[i] = len(parts[i][2]) - take
        n -= take
    if n != target or not cut: return None
    out = []
    for i, (part, core, sy) in enumerate(parts):
        if i in cut:
            k = cut[i]
            sy = [(core, sy[0][1])] if k == 1 else sy[:k]
        for _, c in sy:
            if c == 'S': out.append(('1', 1.0))
            elif c == 'U': out.append(('0', 1.0))
            elif len(sy) == 1: out.append(('0' if core in FUNCTION else '1', SOFT))
            else: out.append((None, 0.0))
    return out


def analyse(lines, stanzas=None):
    """(label, confidence, foot, feet) -- everything known about a poem's metre.

    The reader needs more than the name. Marking the stresses in a line means reading that line against
    the metre the poem is in, and to build the template you need the foot and how many of them the line
    walks; 'common measure' does not say. So both travel with the name.
    """
    evs = [evidence(t) for t in lines]
    foot, feet, conf, shape = scan(evs)
    if not foot or conf < FLOOR: return None, conf, None, None
    # The metre is settled. Now go back to the lines that did not come out at its length and ask whether
    # a word in them reads shorter -- and if enough of them do, read the poem again.
    want = len(FEET[foot]) * feet if foot in FEET else None
    if want:
        again = False
        for i, t in enumerate(lines):
            if len(evs[i]) == want: continue
            alt = refit(t, want)
            if alt is not None: evs[i] = alt; again = True
        if again:
            f2, ft2, c2, sh2 = scan(evs)
            if f2 == foot and ft2 == feet and c2 >= conf: conf, shape = c2, sh2
    name = None
    if stanzas and shape:
        out, i = [], 0
        for k in stanzas:
            out.append(shape[i:i + k]); i += k
        name = pattern_of(foot, out)
    if not name:
        L = LENGTHS.get(feet)
        name = '%s %s' % (foot, L) if L else None
    return name, conf, foot, feet

def describe(lines, stanzas=None):
    """(label, confidence) for a poem: its named pattern where it has one, else foot and length.

    `lines` are the texts; `stanzas` the number of lines in each, when the poem's stanzas are known,
    which is what lets a four-and-three quatrain be called common measure.
    """
    evs = [evidence(t) for t in lines]
    foot, feet, conf, shape = scan(evs)
    if not foot or conf < FLOOR: return None, conf
    if stanzas and shape:
        out, i = [], 0
        for k in stanzas:
            out.append(shape[i:i + k]); i += k
        named = pattern_of(foot, out)
        if named: return named, conf
    L = LENGTHS.get(feet)
    return ('%s %s' % (foot, L), conf) if L else (None, conf)

# ------------------------------------------------------------ reading a poem from the command line
# The module is the library the rest of the pipeline imports, but it also answers the one question a
# visitor arrives with -- what metre is this? -- and that wants no corpus, no dictionary build and no
# site directory. Paste a poem in and it reads it.
#
# What it prints for each line is the template the poem's metre asks for, with the line's own
# departures from it marked: the reading, not the syllable-by-syllable record of what the words fix,
# which is a different thing and is what @real in the published TEI holds.
def _cli(argv):
    import io, sys
    if '--help' in argv or '-h' in argv:
        print(__doc__.strip().split('\n\n')[0])
        print('\n    python3 scansion.py poem.txt      name the metre of a poem in a file'
              '\n    ... | python3 scansion.py          or read it on standard input'
              '\n    python3 scansion.py -l poem.txt   and mark every line against that metre'
              '\n\nBlank lines separate stanzas, which is what lets a four-and-three quatrain be'
              '\ncalled common measure rather than iambic tetrameter.')
        return 0
    marked = '-l' in argv or '--lines' in argv
    files = [a for a in argv if not a.startswith('-')]
    text = ''.join(io.open(f, encoding='utf-8').read() for f in files) if files else sys.stdin.read()

    stanzas, cur = [], []
    for raw in text.split('\n'):
        if raw.strip(): cur.append(raw.strip())
        elif cur: stanzas.append(cur); cur = []
    if cur: stanzas.append(cur)
    lines = [l for st in stanzas for l in st]
    if len(lines) < 4:
        print('four lines at least: a metre is a property of a poem, not of a line'); return 1

    name, conf, foot, feet = analyse(lines, [len(st) for st in stanzas])
    if not name:
        print('no metre settles these %d lines (best agreement %.0f%%)' % (len(lines), conf * 100)); return 1
    print('%s -- %d lines agree %.0f%%' % (name, len(lines), conf * 100))
    if not marked: return 0

    print()
    full = len(FEET[foot]) * feet if foot in FEET else None
    for l in lines:
        ev = evidence(l)
        # Read the line against the metre before marking it, which is what the poem is for. Counting
        # every syllable the words can carry and stopping there gave 'Over many a quaint and curious
        # volume of forgotten lore' seventeen syllables and an eight-and-a-half-foot template to match,
        # when the line is read 'man-ya' and 'cur-ious' and comes out at fifteen. A poem in a settled
        # metre offers two lengths, its own and that less the final slack, and the line is asked which
        # of them it reads as. Nothing is ever lengthened: a refrain that is genuinely short stays short.
        if full:
            read = (best_line(ev, foot, prefer=feet)[0], ev)
            for target in (full, full - 1):
                if not 2 <= target < len(ev): continue
                alt = refit(l, target)
                if alt is None or len(alt) != target: continue
                fit_a = best_line(alt, foot, prefer=feet)[0]
                if fit_a > read[0]: read = (fit_a, alt)
            ev = read[1]
        _, _, n = best_line(ev, foot, prefer=feet)
        # The plainest template of this length -- the pure foot repeated, cost 0 -- is the metre the
        # line is written in, as against the reading of it. This is the rule tei.py publishes as @met,
        # and using anything else here would print a pattern with a substitution already folded in.
        pool = by_length(foot).get(len(ev), ())
        best = min((t for t in pool if t[1] == n), key=lambda t: (t[2], t[0]), default=None)
        want = best[0].replace('1', '+').replace('0', '-') if best else '?' * len(ev)
        got = ''.join('+' if k == '1' and w >= 1.0 else '-' if k == '0' and w >= 1.0 else 'x' for k, w in ev)
        # A syllable the dictionary leaves open is no departure: the metre is free to take it either
        # way, and most monosyllables are open. Only a syllable the words fix AGAINST the metre is.
        off = ''.join('^' if g in '+-' and g != m else ' ' for g, m in zip(got, want))
        print('  %s  %s' % (want, l))
        print('  %s' % got)
        if '^' in off: print('  %s  the words fight the metre here' % off)
        print()
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(_cli(sys.argv[1:]))
