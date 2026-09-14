# The pipeline

These are the scripts that made the corpus in the folder above. They travel with it so that the
method can be read, checked and re-run, rather than described in a document and taken on trust.

Everything here is plain Python with two dependencies. There is no build step and no framework.

```
python3 -m pip install pyphen nltk
python3 -m nltk.downloader cmudict
```

Built and tested on Python 3.9.6, with nltk 3.9.2 and pyphen 0.17.2. The CMU Pronouncing Dictionary
comes from nltk; it is 123,455 words, and it is what the scansion knows about English stress before it
reads a single line of verse.

## Scanning a poem

The one thing most people want is to point the scanner at a poem and be told what metre it is in. Put
the poem in a file, blank lines between stanzas, and run:

```
$ python3 scansion.py poem.txt
trochaic octameter -- 4 lines agree 89%
```

The percentage is how much the words agree with the metre named. It is not a probability; it is the
share of the evidence in the lines that the winning template accounts for. Poems mostly land between
80 and 95, and anything under 70 is reported as unsettled rather than guessed at.

Add `-l` and every line is printed against the pattern its metre asks for, with the syllables where
the words fight the metre marked underneath:

```
$ python3 scansion.py -l poem.txt
trochaic octameter -- 4 lines agree 89%

  +-+-+-+-+-+-+-+-  Once upon a midnight dreary, while I pondered, weak and weary,
  xxxx+x+-xx+-xx+-

  +-+-+-+-+-+-+-+--  Over many a quaint and curious volume of forgotten lore,
  xx+-xxx+--+-x-+-x
         ^^          the words fight the metre here
```

The top row is the metre, the row under it is what the words themselves settle: `+` a stressed
syllable, `-` an unstressed one, `x` a syllable the dictionary leaves open, which the metre is free to
take either way. Most English monosyllables are `x`, and that is not a failure of the dictionary but a
fact about the language: whether *where* carries a beat is decided by the line it is in.

A metre is a property of a poem and not of a line, so the scanner wants at least four lines and is much
surer given twenty.

## Reading the corpus from Python

`teiread.py` opens the published TEI and hands back the poems in the shape the rest of these scripts
expect, so nothing else has to know that this repository ships TEI rather than JSON.

```python
import teiread

print(len(teiread.slugs()))                    # 416

sonnets = teiread.load_work('shakespeare-sonnets')
print(len(sonnets['sections']))                # 154
print(sonnets['sections'][0]['stanzas'][0][0]) # From fairest creatures we desire increase,
```

The TEI itself carries more than the text: each `<l>` has `@real` for what the words stress, `@met` for
what the metre asks, and an `@n` holding the canonical reference. The README in the folder above shows
how to read those.

## Checking the figures

Three scripts measure the scanner, and all three run against this repository with nothing else
installed.

`bench.py` scores against Thomas Haider's *Metrical Tagging in the Wild*, which gathers three English
gold corpora into one format. The data is fetched from its own repository the first time you run it and
cached under `cache/`; it is never copied into this corpus, because it carries no licence. Haider ships
a train/test division and these scripts keep to it: `bench.py --train` scores the half the scanner was
developed against, and plain `bench.py` scores the held-out control, which is the number worth quoting.

```
$ python3 bench.py
TEST: 563 lines

  syllable count agrees       92.7%   (522 of 563 lines)
  the foot the line reads in  71.2%   (427 lines)

  stress, words only          85.0%   (4,160 syllables)
  stress, free choice         88.0%
  stress, in the poem's metre  92.3%   <- what the reader shows
```

`precision.py` asks a different question, and the more important one. A gold corpus is balanced on
purpose: Haider's is 44% non-iambic, because a test of whether a scanner can tell a trochee from an
iamb would be useless if it were all iambs. Real verse is not balanced, and a scanner tuned until it
finds every trochee will start finding trochees everywhere, which a balanced benchmark cannot see. So
`precision.py` takes the poems whose metre nobody needs to measure, the sonnets and the books whose own
title pages say blank verse or heroic couplets, and counts how often the scanner says something else.

```
$ python3 precision.py --sample 120
120 sonnets read (fourteen lines each)
  iambic pentameter       97.5%   (117)
  some other iambic        1.7%
  NOT iambic at all        0.8%   <- every one of these is wrong
```

It exits non-zero when that last figure goes above its ceiling, so it can sit in a build and stop one.

`goldsplit.py` prints the development and control halves side by side, which is the quickest way to see
whether a change is real or was merely tuned in.

## Rebuilding the measurements

`metres.py` re-measures every poem in the corpus and writes `data/metres.json`. Reading 416 works out of
TEI takes a good deal longer than reading them out of the working copy's JSON, so expect it to run for
a while rather than a moment. `authorities.py` prints the poems whose metre a named scholar has written
down, which the corpus prefers to its own measurement wherever one exists.

## What each file is

| | |
|---|---|
| `scansion.py` | The metre engine. Proposes every metre as a template and tests every syllable against it. Also the command line above. |
| `analyze.py` | Syllables, stress, rhyme and glossaries, line by line. The dictionary work the scansion stands on. |
| `teiread.py` | Reads works out of the published TEI. |
| `_paths.py` | Finds the corpus, so the same scripts run here and in the working copy. |
| `metres.py` | The metre of every poem, with the evidence that settled it. |
| `authorities.py` | Metres named by a scholar, with the scholar named. |
| `precision.py` | What the scanner says about poems whose metre is not in doubt. |
| `bench.py`, `goldsplit.py`, `goldscore.py` | Scoring against hand-annotated gold. |
| `tei.py` | Writes the TEI in the folder above. |
| `ingest.py`, `generic.py` | Turn Project Gutenberg texts into parsed works. |
| `catalog.py` | The catalogue: every work, its Gutenberg number, its dates and its note. |
| `webster.py` | Builds the glossary dictionary from Webster's 1913. |
| `corrections.json` | Every emendation made to a source text, with the reason. Twelve of them. |
| `alden-matched.json` | Specimens from Alden's *English Verse* (1903), matched to poems in the library. |
| `mono-corpus.json`, `mono-stress.json` | What the corpus knows about monosyllables the dictionary will not settle. |

## What does not run here, and why

Four of these scripts need inputs this repository does not carry, and they will tell you so rather than
do something odd.

`ingest.py`, `generic.py` and `webster.py` read Project Gutenberg source files. Those are not shipped
because they are someone else's texts, freely available at their own address, and `corrections.json`
plus the texts already published above record everything that was done to them. `webster.py` wants
eBook 29765; the works each name their own source in the TEI header.

`analyze.py` and `tei.py` read the parsed works as JSON, which the working copy keeps and this
repository does not: fifty megabytes of the same poems in a second format, and a corpus carrying two
copies of its texts will eventually carry two different copies. The TEI here is what they wrote.

Glossaries are the one thing that quietly does less without its input. `analyze.py` runs without
Webster's dictionary, and simply produces no glossary when it is absent.
