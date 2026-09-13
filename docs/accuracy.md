# How accurate the scansion is

*Part of the [Laurel corpus](../README.md) — see the [method index](../METHOD.md).*

Scored against [For Better For Verse](https://github.com/waynegraham/for_better_for_verse), the
University of Virginia's corpus of poems hand-scanned by a prosodist. It is the only public expert
scansion of English verse that a machine can read. Nothing from it is used in the corpus; it is a ruler,
not a source.

| | |
|---|---|
| agreement with the editor, overall | **88%** (61 of 69 poems) |
| line length correct | **91%** |
| against separately documented metres | 21 of 23 exact, **23 of 23 on the foot** |

**The test is easier than those numbers suggest, in three separate ways.**

*The corpus is 90% iambic.* 62 of the 69 poems are iambic, so a scanner that always guessed "iambic" and
counted feet would score well. Only 7 non-iambic poems exist in it, which means **trochaic and dactylic
detection are essentially untested**. Treat those labels as reasonable guesses, not findings.

*The corpus shaped the scanner.* Rules were changed after reading which poems it failed on — the
one-licence rule came directly from watching Hiawatha fail. That is human overfitting. The ten poems
whose failures were read were quarantined and the confidence floor was chosen on one half of the
remainder and tested on the other, but the corpus as a whole functions as a development set, and 88% is
optimistic.

*Confidence does not separate right from wrong.* Precision sits near 88% at every setting of the floor.
The errors are not the unconfident cases; they are the genuinely contested ones, where a good reader
might also disagree. The floor exists to keep non-lyric material out, not to raise precision.

The second, cleaner check is the 23 works whose metre is documented in published scholarship, recorded
before the scanner existed. Every one of them is now identified by the correct foot; two are named at
the wrong length.

Dactylic hexameter in English (Evangeline, Clough) is declined rather than guessed. English substitutes
spondees too freely for the templates used here.
