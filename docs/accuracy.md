# How accurate the scansion is

*Part of the [Laurel corpus](../README.md) — see the [method index](../METHOD.md).*

Scored against [For Better For Verse](https://github.com/waynegraham/for_better_for_verse), the
University of Virginia's corpus of poems hand-scanned by a prosodist. It is the only public expert
scansion of English verse that a machine can read. Nothing from it is used in the corpus; it is a ruler,
not a source.

| | |
|---|---|
| stress over 3,183 hand-annotated lines | **85.6%** |
| stress read against the poem's own metre, held-out half | **92.3%** |
| against separately documented metres | 21 of 23 exact, **23 of 23 on the foot** |
| sonnets called something other than iambic | **0.5%** of 422 |

**The test is easier than those numbers suggest, in three separate ways.**

*The corpus is 90% iambic.* 62 of the 69 poems are iambic, so a scanner that always guessed "iambic" and
counted feet would score well. Only 7 non-iambic poems exist in it.

## The metres that corpus could not test

That gap has since been closed against a second body of hand-annotated verse: the three English gold
corpora — For Better For Verse, EPG64 and the prosodic corpus — gathered into one format by
[Metrical Tagging in the Wild](https://github.com/tnhaider/metrical-tagging-in-the-wild) (Haider, EACL
2021). 3,183 lines with a stress marked on every syllable, and **44% of them are not iambic**.

Measured over the syllables where the words themselves settle a stress:

| metre | lines | syllables | agreement |
|---|---|---|---|
| iambic | 1,782 | 12,455 | 84.4% |
| trochaic | 417 | 2,996 | 82.3% |
| anapaestic | 256 | 2,150 | 89.5% |
| amphibrachic | 219 | 1,552 | 88.1% |
| dactylic | 209 | 1,476 | 84.5% |
| hexameter | 128 | 1,759 | 91.7% |
| **all** | **3,183** | **23,627** | **85.6%** |

Two qualifications belong with the figures. **8% of lines are excluded** because this syllabifier and
the annotators disagree about how many syllables the line has — a real disagreement, not a rounding
error, and the honest place to look for the next improvement. And the gold data is stored one syllable
per row, so its words have to be rebuilt before they can be looked up; 96.7% of the rebuilt words are in
the pronouncing dictionary, and the rest are counted as they fall.

### The split, and what a reader is actually shown

Haider's own division into a development and a control half is kept, and the control half is never used
to choose anything. On it:

| | |
|---|---|
| syllable count agrees with the annotator | 92.7% |
| stress, from the words alone | 85.0% |
| stress, read against the poem's own metre — **what the reader sees** | **92.3%** |
| the foot a line reads in, judged from that line alone | 71.2% |

The last two differ by twenty points for a reason worth stating: a single line of verse often does not
say which foot it is in. Once the poem has settled its metre the line falls into place, which is how a
reader does it too, and why the figure the site shows is the higher one.

Reproduce with `python3 bench.py --control`.

Reproduce it with `python3 goldscore.py` in the pipeline. Nothing from that corpus is copied into this
one; it is a ruler, like For Better For Verse.

## What a balanced corpus cannot tell you

Every figure above is **recall**: given a line whose metre the annotator recorded, how often does the
scanner agree. None of them asks the opposite question — how often is a confident wrong answer offered
to a poem that was never in doubt.

That distinction is not academic. A gold corpus for testing metre detection has to be balanced, and
Haider's is: 44% of its lines are not iambic, deliberately, because a corpus that was all iambs could
not tell a trochee-detector from a coin. Real English verse is not balanced. This library is about
nine-tenths iambic. A scanner tuned until it finds every trochee on the balanced corpus will begin
seeing trochees everywhere on the unbalanced one — and every measure above will go **up** while it
happens, because none of them is looking.

It happened here. A change that lifted trochaic recall from 16% to 60% on the held-out half
simultaneously took Shakespeare's sonnets from 4 wrong to 12, and every sonnet in the library from 2.4%
misread to 14.5%. The benchmark registered an improvement throughout.

So there is a second test, of a kind the gold corpora cannot provide: poems whose metre needs no
annotation because the form already settles it. A sonnet is fourteen lines of iambic pentameter; that is
most of what the word means. Anything else the scanner says about one is a false positive, and counting
them is the precision the benchmarks were missing.

| class | poems | known answer | wrong |
|---|---|---|---|
| sonnets | 422 | iambic | **0.5%** |
| blank verse and heroic couplets | 545 | iambic | **1.5%** |

`pipeline/precision.py` runs it, and the build refuses to finish if either class goes past 5%. It is not
a substitute for scoring against hand-annotation; it catches the failure that scoring against
hand-annotation is structurally unable to see.

## Three ways these numbers flatter themselves

*The corpus shaped the scanner.* Rules were changed after reading which poems it failed on — the
one-licence rule came directly from watching Hiawatha fail. That is human overfitting. The ten poems
whose failures were read were quarantined and the confidence floor was chosen on one half of the
remainder and tested on the other, but the corpus as a whole functions as a development set, and the
figures above are optimistic by an amount nobody can put a number on.

*Confidence does not separate right from wrong.* Agreement barely moves at any setting of the floor.
The errors are not the unconfident cases; they are the genuinely contested ones, where a good reader
might also disagree. The floor exists to keep non-lyric material out, not to raise precision.

The second, cleaner check is the 23 works whose metre is documented in published scholarship, recorded
before the scanner existed. Every one of them is now identified by the correct foot; two are named at
the wrong length.

Dactylic hexameter in English (Evangeline, Clough) is declined rather than guessed. English substitutes
spondees too freely for the templates used here.
