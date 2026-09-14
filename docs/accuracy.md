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
counted feet would score well. Only 7 non-iambic poems exist in it.

## The metres that corpus could not test

That gap has since been closed against a second body of hand-annotated verse: the three English gold
corpora — For Better For Verse, EPG64 and the prosodic corpus — gathered into one format by
[Metrical Tagging in the Wild](https://github.com/tnhaider/metrical-tagging-in-the-wild) (Haider, EACL
2021). 3,183 lines with a stress marked on every syllable, and **44% of them are not iambic**.

Measured over the syllables where the words themselves settle a stress:

| metre | lines | syllables | agreement |
|---|---|---|---|
| iambic | 1,782 | 12,964 | 79.0% |
| trochaic | 417 | 3,110 | 80.5% |
| anapaestic | 256 | 2,204 | 88.8% |
| amphibrachic | 219 | 1,648 | 87.1% |
| dactylic | 209 | 1,421 | 85.2% |
| hexameter | 128 | 1,736 | 92.1% |
| **all** | **3,183** | **24,357** | **82.3%** |

The metres that could not be tested are not the weak ones: trochaic and dactylic both score above
iambic. Two qualifications belong with the figures. **8% of lines are excluded** because this
syllabifier and the annotators disagree about how many syllables the line has — a real disagreement,
not a rounding error, and the honest place to look for the next improvement. And the gold data is
stored one syllable per row, so its words have to be rebuilt before they can be looked up; 93.8% of the
rebuilt words are in the pronouncing dictionary, and the rest are counted as they fall.

Reproduce it with `python3 goldscore.py` in the pipeline. Nothing from that corpus is copied into this
one; it is a ruler, like For Better For Verse.

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
