# Method, and how far to trust it

Everything below is measured rather than asserted. Where a number is flattering because the test was
easy, that is said.

## Where the texts come from

Project Gutenberg, chosen by ebook number, all published before 1931 and therefore public domain in the
United States. The Gutenberg header, footer and licence were removed; nothing else was altered. Each
work's TEI names its ebook and links to it.

These are editions chosen for being free, not for being authoritative. That is the honest weakness of
this corpus against one built on named scholarly editions with an apparatus criticus. Where a text is
known to be a poor witness it should be treated as such.

## Syllables and stress

Word stress comes from the CMU Pronouncing Dictionary. It settles the stress inside a word of two or
more syllables and says nothing about a word of one, which is most of English verse:

```
That saved a wretch like me      uxuxxu
```

Six syllables, six words, not one of them fixed. A method that listens only to the dictionary is deaf
to the ballads, the hymns and most of Dickinson. So a monosyllable votes too, quietly: a closed-class
word (article, preposition, conjunction, pronoun, auxiliary) expects a slack, anything else expects a
beat. That vote is worth 0.30 of a dictionary stress, because it is a tendency and not a fact.

In the TEI these appear as `x` in `@real`: the words leave them open and the metre may take them either
way.

## How a poem's metre is determined

By proposing each metre and testing the words against it, rather than by measuring the gaps between
stresses. Gap-measuring works on a whole book and fails on a single poem: Sonnet 18 offers only two
dictionary-fixed stresses in ten syllables.

Four feet are tried (iambic, trochaic, anapaestic, dactylic) at every length, with the licences real
verse takes: a line may drop a slack at either end, gain one at the close, and swap one foot for its
neighbour of the other length, which is what "loose iambic" means. Only one licence to a line: a line
that wants two is simply in another foot.

A metre is published only above a confidence of 0.70. **16,396 of 18,107 poems** get one; the rest are
left without, which is the correct answer when the verse will not settle.

Where the shape of the stanza earns a name, that name is given instead: common measure, short measure,
fourteeners, poulter's measure, alexandrines. Long measure is deliberately absent, because nothing in
the lines distinguishes it from any other quatrain of iambic tetrameter.

## How accurate the scansion is

Scored against [For Better For Verse](https://github.com/waynegraham/for_better_for_verse), the
University of Virginia's corpus of poems hand-scanned by a prosodist. It is the only public expert
scansion of English verse that a machine can read.

| | |
|---|---|
| agreement with the editor, overall | **88%** (61 of 69 poems) |
| line length correct | **91%** |
| against separately documented metres | 21 of 23 exact, **23 of 23 on the foot** |

**The test is easier than those numbers suggest.** 62 of the 69 poems are iambic, so a scanner that
always guessed "iambic" and counted feet would score well. Only 7 non-iambic poems exist in the corpus,
which means **trochaic and dactylic detection are essentially untested**. Treat a trochaic or dactylic
label as a reasonable guess rather than a finding.

Two further caveats. The design of the scanner was shaped by looking at which poems it failed on, so
the corpus functions as a development set and 88% is optimistic. And confidence does not separate right
from wrong: precision sits near 88% at every setting of the floor, because the errors are not
unconfident ones but the genuinely contested cases, where a good reader might also disagree.

Dactylic hexameter in English (Evangeline, Clough) is declined rather than guessed. English substitutes
spondees too freely for the templates used here.

## Audio timings

Where `data/audio/<work>.json` exists, each poem carries the second at which every line is spoken in a
LibriVox recording, along with the reader's name and the project.

Alignment is by transcription: the recording is transcribed, the transcript matched against the known
text, and the matched words carry their timings back to the lines. A reading is kept only when at least
90% of the poem's words are found in it, which rejects bad microphones, bad rooms, heavy stumbling, and
readers working from a different edition. Around 78% of attempts pass.

Two offsets travel with each poem. `start` is where the poem's first line begins, after the spoken
LibriVox announcement. `title`, where present, is the span in which the reader names the poem, which may
fall on either side of that announcement. No audio is included here and none is altered; these are
timings into files that remain whole on the Internet Archive.

## Known limits

* Editions are chosen for being public domain, not for being the best witness.
* Trochaic and dactylic metres are under-tested.
* Accuracy figures come from a corpus that shaped the scanner's design.
* Glossaries are drawn from Webster's 1913, which is of the right century for most of this library and
  the wrong one for some of it.
* A small number of editorial notes in the source editions are keyed to sections this corpus names
  differently, and do not appear.
