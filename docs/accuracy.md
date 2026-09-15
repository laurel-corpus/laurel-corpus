# How accurate the scansion is

*Part of the [Laurel corpus](../README.md) — see the [method index](../METHOD.md). Terms are defined in
the [glossary](glossary.md).*

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
| iambic | 1,782 | 13,947 | 83.8% |
| trochaic | 417 | 3,264 | 82.0% |
| anapaestic | 256 | 2,316 | 89.0% |
| amphibrachic | 219 | 1,791 | 86.7% |
| dactylic | 209 | 1,570 | 84.4% |
| hexameter | 128 | 1,894 | 91.3% |
| **all** | **3,183** | **26,103** | **85.1%** |

Two qualifications belong with the figures. **5% of lines are excluded** because this syllabifier and
the annotators disagree about how many syllables the line has — a real disagreement, not a rounding
error, and the honest place to look for the next improvement. And the gold data is stored one syllable
per row, so its words have to be rebuilt before they can be looked up; 97.3% of the rebuilt words are in
the pronouncing dictionary, and the rest are counted as they fall.

That rebuilding used to be worse, and the figures above are lower and more honest than the ones this
document carried before. The gold marks stress a syllable at a time and says only loosely where one
word ends and the next begins, so the words have to be pieced back together. The rule that did it
charged a fixed penalty for a piece the dictionary could not confirm, which made gluing two unknown
syllables cheaper than separating them: `volley'd and thunder'd` arrived as a single word, and so did
`our lady of pain`. 519 such lumps came through the development half. Charging the penalty by the
syllable instead leaves 8, every one of them a real word the dictionary happens to lack. The scanner
was being handed text that was not English and marked down for failing to scan it, so more lines are
now scored and the average over them is a little lower.

### The split, and what a reader is actually shown

Haider's own division into a development and a control half is kept, and the control half is never used
to choose anything. On it:

| | |
|---|---|
| syllable count agrees with the annotator | 95.0% |
| stress, from the words alone | 84.5% |
| stress, read against the poem's own metre — **what the reader sees** | **92.8%** |
| the foot a line reads in, judged from that line alone | 72.0% |

The last two differ by twenty points for a reason worth stating: a single line of verse often does not
say which foot it is in. Once the poem has settled its metre the line falls into place, which is how a
reader does it too, and why the figure the site shows is the higher one.

### A whole line at a time

Every figure above counts marks, not lines, and a reader does not read a mark. A line carries eight or
ten of them, so 92.8% per syllable does not mean 92.8% of lines are right. On the same control half,
counting a line as wrong if a single mark in it is wrong:

| | |
|---|---|
| lines where **every mark** is right | **74.5%** |
| lines with one mark wrong | 6.2% |
| lines with two wrong | 11.5% |
| lines with three or more wrong | 7.8% |
| syllable count disagrees, so the line is not scored at all | 5.0% |

Counting those unscored lines as failures too, 70.0% of lines come out right end to end.

**The mistakes cluster, and that is the useful part.** At 7.2% per syllable over lines averaging 8.4
syllables, mistakes falling independently would spoil 46.5% of lines. They spoil 25.5%. So the scanner
is not sprinkling error evenly over the corpus: most lines come out clean and the failures concentrate
on particular lines, usually where a word was syllabified wrongly or where the stress is genuinely
arguable. When a line is wrong it is more often wrong twice than once.

By metre, the lines that come out perfect:

| | |
|---|---|
| anapaestic | 91.7% |
| dactylic | 73.2% |
| iambic | 73.2% |
| trochaic | 71.9% |

**What limits this number is mostly not the scanner.** Taking every syllable on the development half
where the scanner and the annotator disagree, and asking what the pronouncing dictionary says about
that syllable:

| | |
|---|---|
| the dictionary has no firm opinion, so the annotator's reading is one of several defensible ones | 76.5% |
| the dictionary sides with the scanner | 18.3% |
| the dictionary sides with the annotator, and the scanner is simply wrong | 5.2% |

Three quarters of the disagreement is over monosyllables that English does not fix and the metre is
free to take either way. `And on the pedestal these words appear` is marked in the gold with the first
foot inverted; the scanner reads it as regular iambic pentameter, and both are defensible readings of a
line whose opening is three function words. Only the last row is error in any useful sense, which is
why chasing this figure much further would mean fitting one annotator's ear rather than getting
anything right.

One structural caution. Haider's corpus is a bag of shuffled lines: consecutive lines share a metre only
1.1 times running, so there are no poems in it. Every figure here therefore measures a line read in
isolation, while the site always has the whole poem in hand and settles the metre across it first. That
is a reason to expect the site to do better than these numbers, and a reason none of them can prove it.
`precision.py` exists because of that gap.

Reproduce the per-line figures with `python3 perline.py` in `pipeline/`, or `--train` for the
development half; `--show 10` prints the worst lines with the two readings side by side.

Reproduce it from this repository. In `pipeline/`, `python3 bench.py` scores the control half and
`python3 bench.py --train` the development half; `python3 goldsplit.py` prints the two side by side, and
`python3 goldscore.py` breaks the result down by metre. The gold data is fetched the first time you run
any of them and cached under `pipeline/cache/`. Nothing from it is copied into this corpus; it is a
ruler, like For Better For Verse.

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
