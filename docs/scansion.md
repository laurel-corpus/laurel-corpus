# Syllables, stress and metre

*Part of the [Laurel corpus](../README.md) — see the [method index](../METHOD.md). Terms are defined in
the [glossary](glossary.md).*

Syllables are divided on the CMU Pronouncing Dictionary, with the elisions and expansions verse itself
uses: *every* contracting to *ev'ry* where the line runs long, a spelled *-ed* opening into its own
syllable where the line runs short.

The dictionary settles the stress inside a word of two syllables or more and says nothing about a word
of one. Those unsettled syllables appear in the TEI as `x` in `@real`: the words leave them open, and
the metre may take them either way. How they are weighed when a metre is being determined is set out
below.

## How a poem's metre is determined

### Why the obvious method does not work

The first approach measured the gap between one dictionary-fixed stress and the next: two apart is
duple, three is triple. It works on a whole book and fails on a single poem. Shakespeare's eighteenth
sonnet scans

```
Shall I compare thee to a summer's day?      xx-+xxx+-x
```

That second column is the line's `@real`, the stress the words settle on their own: `+` stressed, `-`
unstressed, `x` a syllable left open because the dictionary has no opinion about it. Only two syllables
in the whole line are fixed, the *-pare* of *compare* and the *sum-* of *summer's*, because everything
else is a word of one syllable and English does not fix those.

Ten syllables, then, carrying two stresses the dictionary will vouch for. Paradise Lost supplies tens of
thousands of such gaps and settles easily; fourteen lines supply twenty-eight and settle into nothing.
Scanned that way, **roughly two thirds of this library returns no metre at all** — and not the obscure
poems but the short ones, which is to say the lyric.

### Proposing metres instead of measuring gaps

A reader does not scan by measuring gaps. A reader proposes iambic pentameter, reads the line against
it, and sees whether the words fight. So does this. Every candidate metre is built as a template, every
syllable of every line is tested against it, and the metre that argues least with the words wins. A
sonnet then offers 140 syllables of evidence rather than 28.

### A metre has to fit the shape of the poem, not just its words

Agreement measures how well the words fall into the pattern. It cannot see that the pattern is the wrong
size. A poem of eight-syllable lines can agree handsomely with anapaestic tetrameter, which wants twelve,
because the alternation is right even though the measure is not: William Barnes's Dorset poems were named
anapaestic tetrameter with not one line of forty at that length, at 0.85 agreement.

So a second test, which the agreement cannot make: **more than half a poem's lines must be a length the
named metre can actually make** — the metre's own length, or that less a syllable, or that plus one.
Named stanza patterns are measured against all of their lengths rather than one, so common measure is
tested against eight syllables and six, and the ballads are not condemned for alternating on purpose.

Raising the confidence floor instead was tried and is much worse: the poems this catches score 0.81 at
the median, so a floor high enough to reach them silences four sound poems for every unsound one.

The rule moved 1,388 poems, about one in thirteen, from a named metre to none. It silences none of the
422 sonnets and none of the 23 works whose metre a scholar has written down. Where an authority names a
metre, the authority still stands: the measurement declining to publish a length of its own does not
overrule a person who signed their work.

### What counts as evidence

| what the syllable is | what it wants | weight |
|---|---|---|
| stressed in the pronouncing dictionary | a beat | 1.00 |
| unstressed in the pronouncing dictionary | a slack | 1.00 |
| a one-syllable closed-class word | a slack | 0.30 |
| any other one-syllable word | a beat | 0.30 |
| an unsettled syllable of a longer word | abstains | 0 |

The dictionary fixes the stress inside a word of two syllables or more and says nothing about a word of
one. That silence is most of English verse. A line of six monosyllables carries no dictionary evidence
at all, which made the method deaf to the ballads, the hymns and much of Dickinson — the poems whose
metre is least in doubt. A reader is not deaf to them, because a reader knows which words carry the
sense. So a monosyllable votes too, from a closed-class list of **129 words** (articles, prepositions,
conjunctions, pronouns, auxiliaries), at **0.30** of a dictionary stress. It is worth a fraction because
it is a tendency and not a fact: verse inverts it constantly, and the whole art of an opening like
Milton's "Of Man's first disobedience" is the preposition taking the beat.

A free syllable is never evidence. Scoring it would let any template claim any line.

### Building the templates

Four feet — iambic `01`, trochaic `10`, anapaestic `001`, dactylic `100` — at every length from one
foot to eight, with the licences real verse takes:

* **acephaly**: the line may open without its first slack
* **catalexis**: it may close without its last, never losing a stress
* **a feminine ending**: it may gain one slack past the final stress
* **one foot swapped** for its neighbour of the other length, which is what *loose iambic* means

…and, within the foot, **the substitutions English verse actually makes**: a trochee for an iamb
(the inverted first foot, the commonest event in the language), a spondee, a pyrrhic, and for the triple
feet an inversion or an amphibrach. Up to two per line — a line needing three is not that metre with
substitutions, it is another metre. This is what lets the scanner say *iambic pentameter with a trochaic
inversion in foot 3* rather than reaching for whichever whole-line pattern is nearest, and it is where
the falling metres were being lost: before it, trochaic lines were identified 16% of the time and
dactylic 10%; after it, both 60%.

Each reading pays for what it bends, so the plainest account of a line wins a tie. An inverted **first**
foot costs less than half what an inversion elsewhere costs, because "**Bát**tered the hóuse" is
utterly ordinary and an inversion in foot four is not. Iambic pentameter has 1,248 templates once this is
allowed, against about thirty before.

**One licence to a line.** A line may take acephaly *or* catalexis *or* a feminine ending — never two.
This rule matters more than it sounds, and it is the difference between a scanner that works and one
that quietly ruins itself.

A trochaic hexameter that drops its first syllable **and** its last is `-+-+-+-+-+`. That is not merely
*like* iambic pentameter; it **is** iambic pentameter, letter for letter. At ten syllables, 26 templates
were reachable by both feet. A sonnet then scores identically in either, the tie falls to whichever way
the line-openings happen to lean — and Shakespeare, who begins a great many lines on a stress, comes out
trochaic. Forbidding the second licence closed it: 26 shared templates became 0, sonnets misread went
from 14.5% to 0.5%, and no recall was lost anywhere.

Substitution costs **0.20** of a reading's agreement, and the cost is charged **only while deciding which
foot the poem walks in**. A poem of iambs must not pass itself off as one of anapaests by bending a foot
in every line. But once the foot is settled the question is only how many feet a line has, and charging
there made Blake's four-beat nine-syllable lines come out as five feet, which is how a ballad stanza
loses the four-and-three that makes it a ballad.

Twelve hundred templates per line is forty times the arithmetic, and a pass over the library went from
minutes to most of a day. The scoring is rearranged rather than the template set cut: every syllable is
counted whether a template agrees with it or not, so the denominator is the same for every template of a
given length and is computed once; and the numerator starts from what a template scores by marking every
syllable slack, then adds or subtracts each stress it does mark. Sixteen times faster, and checked
against the plain statement of the same arithmetic across 96,792 scorings — zero disagreements.

### Three passes, because they are three different questions

1. **Which foot** is asked of every line at once, since it is a property of the poem.
2. **How long each line is** is asked of each line by itself, because a great many poems alternate
   lengths on purpose and the four-and-three of a ballad is not an average of three and a half.
3. **The doubtful lines are asked again**, with the poem's prevailing length in hand. Nine syllables is
   a headless pentameter or a tetrameter with a feminine ending, and no line settles that alone.

Agreement is rounded before ranking, so readings the words cannot separate count as tied and the poem's
own measure breaks the tie. That is how a reader does it: establish the measure, then read the doubtful
line into it.

### Where the thumb is on the scale, and why

A rising and a falling reading of the same alternating line differ only at the ends, and a duple line
can always be read as a triple one with slacks missing. Those scores come out close and the bare winner
is not yet meaningful. English leans duple and rising, so a falling or triple reading is taken only when
it beats the alternative by **0.05** — a margin, not a preference. This is the same convention the
Virginia corpus records as prosodic consensus for a catalectic alternating line.

Where two line-lengths tie, the longer wins: a measure is named by its full line, and calling 4/3/4/3
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

The shape is read **position by position across the stanzas**, not by requiring stanzas to match. A poet
writing common measure crowds an extra syllable in whenever the sense wants one: Dickinson's "A precious,
mouldering pleasure" runs 5/3/4/2, then 4/4/4/3, then 4/3/5/3 — unmistakably four answered by three,
with not one stanza exact. A shape is accepted when the positional mode describes **60%** of the cells;
where a position ties, the reading that names a real measure wins, because that is how a reader settles
it too.

**Long measure is deliberately absent.** It is a real name, but nothing in the lines distinguishes it
from any other quatrain of iambic tetrameter. It is hymnody that makes it long measure, and the lines do
not say whether a poem is a hymn.

### What gets published

A metre is published only above a confidence of **0.70**. **16,181 of 18,210 poems** get one, of which
**794 carry a named measure** — common measure, short measure, fourteeners — rather than a foot and a
length. The rest are left blank, which is the correct answer when the verse will not settle.

Across the library the feet come out iambic 77%, trochaic 13%, anapaestic 4%, dactylic 2%, with
common measure a further 4%. That shape is worth stating because it is the check on the whole exercise:
English verse is overwhelmingly iambic, and a scanner reporting anything else has gone wrong somewhere
the benchmarks cannot see.
