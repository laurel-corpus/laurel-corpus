# Syllables, stress and metre

*Part of the [Laurel corpus](../README.md) — see the [method index](../METHOD.md).*

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
Shall I compare thee to a summer's day?      xuUSuuuSUx
```

Ten syllables carrying two stresses the dictionary will vouch for. Paradise Lost supplies tens of
thousands of such gaps and settles easily; fourteen lines supply twenty-eight and settle into nothing.
Scanned that way, **roughly two thirds of this library returns no metre at all** — and not the obscure
poems but the short ones, which is to say the lyric.

### Proposing metres instead of measuring gaps

A reader does not scan by measuring gaps. A reader proposes iambic pentameter, reads the line against
it, and sees whether the words fight. So does this. Every candidate metre is built as a template, every
syllable of every line is tested against it, and the metre that argues least with the words wins. A
sonnet then offers 140 syllables of evidence rather than 28.

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
at all, which made the method deaf to the ballads, the hymns and most of Dickinson — the poems whose
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

**One licence to a line.** A line that wants two is simply in another foot. This rule matters more than
it sounds. An iambic tetrameter that drops its first syllable *and* gains one at the end produces the
trochaic template exactly — so without the rule, Hiawatha reads as iambic and no line in English is ever
securely trochaic again.

Substitution is capped at one foot per line and costs **0.12** of a reading's agreement, and the cost is
charged **only while deciding which foot the poem walks in**. A poem of iambs must not pass itself off
as one of anapaests by bending a foot in every line. But once the foot is settled the question is only
how many feet a line has, and charging there made Blake's four-beat nine-syllable lines come out as five
feet, which is how a ballad stanza loses the four-and-three that makes it a ballad.

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

A metre is published only above a confidence of **0.70**. **16,396 of 18,107 poems** get one, of which
**940 carry a named measure** rather than a foot-and-length. The rest are left blank, which is the
correct answer when the verse will not settle.
