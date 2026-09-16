# Syllables, stress and meter

*Part of the [Laurel corpus](../README.md). The [method index](../METHOD.md) lists the other documents,
and terms are defined in the [glossary](glossary.md).*

Syllables come from the CMU Pronouncing Dictionary, with the elisions and expansions that verse itself
uses. Verse contracts and expands words as it needs them, so the dictionary's count is not always the
poem's: *every* becomes *ev'ry* where a line runs long, and a spelled *-ed* opens into a syllable of its
own where a line runs short.

The dictionary fixes the stress inside any word of two syllables or more. It says nothing about words of
one syllable. Those appear in the TEI as `x` in `@real`, meaning that the words have left them open and
the meter may take them either way. How much weight they carry when a meter is being determined is set
out below.

## How a poem's meter is determined

### Why counting the gaps between stresses does not work

The first version of the scanner measured the distance from one dictionary-fixed stress to the next. Two
apart is duple, three apart is triple. That works on a whole book, and it fails on a single poem.
Shakespeare's eighteenth sonnet scans as follows:

```
Shall I compare thee to a summer's day?      xx-+xxx+-x
```

The second column is the line's `@real`, the stress that the words settle on their own: `+` for a
stressed syllable, `-` for an unstressed one, and `x` for a syllable that the dictionary will not settle.
Only two syllables out of ten are fixed, the *-pare* of *compare* and the *sum-* of *summer's*.
Everything else is a word of one syllable and English does not fix those.

*Paradise Lost* supplies tens of thousands of such gaps and settles easily. Fourteen lines supply
twenty-eight, and settle into nothing. Scanned that way, **roughly two thirds of this library came back
with no meter at all**, and the failures were not the obscure poems but the short ones, which is to say
the lyric.

### Proposing meters instead of measuring gaps

A reader does not scan by measuring gaps. A reader proposes iambic pentameter, reads the line against
it, and listens for the places where the words resist. The scanner now does the same. Every candidate
meter is built as a template, every syllable of every line is tested against it, and the meter that
argues least with the words wins. A sonnet then offers 140 syllables of evidence instead of 28.

### Checking the line length as well as the stresses

The agreement score says how well the stresses fall into the pattern. It says nothing about whether the
pattern is the right size.

William Barnes's Dorset poems were coming out as anapaestic tetrameter, which wants twelve syllables to a
line, although not one line in forty was twelve syllables long. The score was 0.85. The
alternation really was anapaestic; only the length was wrong.

There is therefore a second test. More than half of a poem's lines have to be a length that the named
meter can make: the meter's own length, one syllable less, or one syllable more. Stanza patterns are
checked against all of their lengths, so that common measure, which alternates eight syllables with six,
counts at both.

I tried raising the confidence floor first, and it does not work. These poems sit at 0.81, above the
existing floor of 0.70, and a floor high enough to catch them takes out four good poems for every bad
one.

Under the length test, 1,388 poems lost their meter, roughly one in thirteen. No sonnets were among
them, and none of the twenty-three works whose meter comes from a named scholar. Those still take the
scholar's answer even where the measurement declines to give one.

### What counts as evidence

| what the syllable is | what it wants | weight |
|---|---|---|
| stressed in the pronouncing dictionary | a beat | 1.00 |
| unstressed in the pronouncing dictionary | a slack | 1.00 |
| a one-syllable closed-class word | a slack | 0.30 |
| any other one-syllable word | a beat | 0.30 |
| an unsettled syllable of a longer word | abstains | 0 |

The dictionary fixes the stress inside a word of two syllables or more and says nothing about a word of
one, and that silence covers most of English verse. A line of six monosyllables carries no dictionary
evidence at all. This is what made the first method deaf to the ballads, the hymns and much of Dickinson,
which are precisely the poems whose meter is least in doubt.

A reader is not deaf to them. A reader knows which words carry the sense. So a monosyllable
votes as well. There is a closed-class list of **129 words** (articles, prepositions, conjunctions,
pronouns, auxiliaries), and each one votes at **0.30** of a dictionary stress.

The fraction matters. This is a tendency rather than a fact. Verse inverts it constantly, and the whole
art of an opening like Milton's "Of Man's first disobedience" lies in the preposition taking the beat.

A free syllable is never evidence. Scoring it would let any template claim any line.

### Building the templates

The four feet (iambic `01`, trochaic `10`, anapaestic `001`, dactylic `100`) are taken at every length
from one foot to eight, with the licenses that real verse takes:

* **acephaly**: the line may open without its first slack
* **catalexis**: it may close without its last, though never losing a stress
* **a feminine ending**: it may gain one slack past the final stress
* **one foot swapped** for its neighbour of the other length, which is what *loose iambic* means

Within the foot there are also **the substitutions that English verse actually makes**: a trochee for
an iamb, which is the inverted first foot and the commonest event in the language; a spondee; a pyrrhic;
and, for the triple feet, an inversion or an amphibrach.

A line may take up to two of those. A line that needs three is not that meter with substitutions. It is
another meter.

This is what lets the scanner report *iambic pentameter with a trochaic inversion in foot 3* instead of
reaching for whichever whole-line pattern sits nearest. It is also where the falling meters had been
getting lost. Before this change, trochaic lines were identified 16% of the time and dactylic lines 10%.
After it, both were identified 60% of the time.

Each reading pays for what it bends, so the plainest account of a line wins a tie. An inverted **first**
foot costs less than half as much as an inversion anywhere else. "**Bát**tered the hóuse" is
completely ordinary and an inversion in the fourth foot is not. Iambic pentameter has 1,248 templates
once all of this is allowed. It had about thirty before.

**One license to a line.** A line may take acephaly, or catalexis, or a feminine ending, but never two
of them. The reason is worth spelling out. A trochaic hexameter that drops its first syllable and its
last is `-+-+-+-+-+`. That is not merely like iambic pentameter; it is iambic pentameter, letter for
letter. At ten syllables, twenty-six templates were reachable by both feet. A sonnet then scored
identically either way, and the tie fell to whichever direction the line openings happened to lean.
Shakespeare begins a great many lines on a stress, so Shakespeare came out trochaic. Forbidding the
second license closed the gap: the twenty-six shared templates became none, sonnets read as something
other than iambic fell from 14.5% to 0.5%, and no recall was lost anywhere.

Substitution costs **0.20** of a reading's agreement, and that cost is charged only while the scanner is
deciding which foot the poem walks in. A poem of iambs must not be allowed to pass itself off as one of
anapaests by bending a foot in every line. Once the foot is settled, the only question left is how many
feet a line has, and charging for substitution there did real damage: it made Blake's four-beat,
nine-syllable lines come out as five feet, which is how a ballad stanza loses the four-and-three that
makes it a ballad.

Twelve hundred templates per line is forty times the arithmetic, and a pass over the library went from
minutes to most of a day. Rather than cut the template set, the scoring was rearranged. Every syllable is
counted whether or not a template agrees with it, so the denominator is the same for every template of
a given length and is computed once, and the numerator starts from what a template scores by marking
every syllable slack and then adds or subtracts each stress it does mark. The result is sixteen times
faster, and it was checked against the plain statement of the same arithmetic across 96,792 scorings
with no disagreements.

### Three passes, three different questions

1. **Which foot** is asked of every line at once. It is a property of the poem.
2. **How long each line is** is asked of each line by itself. A great many poems alternate
   lengths on purpose, and the four-and-three of a ballad is not an average of three and a half.
3. **The doubtful lines are asked again**, with the poem's prevailing length in hand. Nine syllables is
   either a headless pentameter or a tetrameter with a feminine ending, and no line settles that alone.

Agreement is rounded before ranking, so readings that the words cannot separate count as tied and the
poem's own measure breaks the tie. That is how a reader does it as well: establish the measure, then
read the doubtful line into it.

### Where the thumb is on the scale, and why

A rising and a falling reading of the same alternating line differ only at the ends, and a duple line can
always be read as a triple one with slacks missing. Those scores come out close, and the bare winner is
not yet meaningful. English leans duple and rising, so a falling or triple reading is taken only when it
beats the alternative by **0.05**. This is a margin rather than a preference, and it is the same
convention that the Virginia corpus records as the prosodic consensus for a catalectic alternating line.

Where two line lengths tie, the longer wins. A measure is named by its full line, and calling 4/3/4/3
"trimeter" names the answer instead of the question.

### Named measures

Where the line lengths make a pattern, the pattern is the name. Four feet answered by three is common
measure, and calling it "iambic tetrameter" throws away the half that matters.

| shape | name |
|---|---|
| iambic 4/3/4/3 | common measure |
| iambic 3/3/4/3 | short measure |
| iambic 7/7 | fourteeners |
| iambic 6/6 | alexandrines |
| anapaestic 4/3/4/3 | anapaestic common measure |

The shape is read **position by position across the stanzas**, not by requiring the stanzas to match. A
poet writing common measure crowds an extra syllable in whenever the sense wants one. Dickinson's "A
precious, mouldering pleasure" runs 5/3/4/2, then 4/4/4/3, then 4/3/5/3, which is unmistakably four
answered by three although not one stanza is exact. A shape is accepted when the positional mode
describes **60%** of the cells; where a position ties, the reading that names a real measure wins,
because that is how a reader settles it too.

**Long measure is deliberately absent.** It is a real name, but nothing in the lines distinguishes it
from any other quatrain of iambic tetrameter. It is hymnody that makes it long measure, and the lines do
not say whether a poem is a hymn.

### What gets published

A meter is published only above a confidence of **0.70**. **16,181 of 18,210 poems** receive one, of
which **794 carry a named measure** (common measure, short measure, fourteeners) rather than a foot and
a length. The rest are left blank, which is the correct answer when the verse will not settle.

Across the library the feet come out iambic 77%, trochaic 13%, anapaestic 4%, dactylic 2%, with common
measure a further 4%. That distribution is worth stating because it is the check on the whole exercise.
English verse is overwhelmingly iambic, and a scanner reporting anything else has gone wrong somewhere
that the benchmarks cannot see.
