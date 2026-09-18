# Laurel

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22738547.svg)](https://doi.org/10.5281/zenodo.22738547)

Laurel is a corpus of public domain English poetry, encoded in TEI P5, in which every line has been
scanned and most poems have been given a meter. I built it as the material underneath
[laurelpoetry.com](https://laurelpoetry.com), a free reading room for poetry that I maintain, and I
have published it separately so that the work behind the site can be examined, corrected, and put to
other uses. The poems themselves are in the public domain. The encoding and the annotation are released
under CC BY-SA 4.0.

The corpus grows, and the figures for any given release (the number of works, poems, and lines) are
printed by `./assemble.sh`, the script that also builds this repository. I have deliberately not repeated
them here. A number written in two places tends to be wrong in one of them.

## What is in a line

Readers who already know what iambic pentameter is may wish to skip ahead to the example. For everyone
else, a brief explanation is in order.

Every English word of more than one syllable has a syllable that is stressed: *GAR-den*, *a-BOVE*. A
meter is a pattern of stressed and unstressed syllables that a poem keeps to more or less consistently.
Iambic pentameter, by far the most common meter in English, is a line of ten syllables that alternate
unstressed and stressed, beginning with the unstressed: *da-DUM da-DUM da-DUM da-DUM da-DUM*. The
practice of marking which syllables carry the stress is called scansion, and it is what this corpus
records for every line of every poem.

What makes scansion interesting, and what makes it worth storing, is that poets do not follow their
meter exactly. The places where a line departs from its pattern are seldom errors. More often than not,
the departure is where the poet is doing something deliberate. For this reason every line in the corpus
is recorded twice, once as the meter asks for it and once as the words themselves require.

```xml
<l n="7" real="+-x+-x-+-x" met="-+-+-+-+-+">Making a famine where abundance lies,</l>
```

The `met` attribute records what the meter asks for. Sonnet 1 is in iambic pentameter, so the pattern
alternates without exception. The `real` attribute records what the words settle on their own, based on
a pronouncing dictionary and the poem's own syllable counts. The marks are read as follows: a plus sign
is a stressed syllable, a minus sign is an unstressed one, and an `x` is a syllable that the dictionary
does not settle, which the meter is free to take either way.

Lined up against one another, the two rows look like this:

```
     Mak- ing  a   fam- ine where  a-  bun- dance lies
met   -    +    -    +    -    +    -    +    -    +
real  +    -    x    +    -    x    -    +    -    x
      ^    ^
```

The meter wants the line to open softly and place the stress on the second syllable. The word will not
allow it. *Making* is pronounced **MAK**-ing, and no reader would say *ma-KING*. The first two syllables
are therefore reversed, and everything after them falls back into step. This is known as a trochaic
inversion, a reversed foot at the head of the line, and it is the most common liberty that a poet takes
with an iambic line. Shakespeare uses it here to put the weight on *Making*.

It should be noted that most of the line is marked `x`, and that this is not a gap in the dictionary.
Whether a word such as *where* or *lies* carries a stress is decided by the line it sits in rather than by
the word itself. Those syllables are left for the meter to take as it likes, and they are marked as open
rather than guessed at.

Keeping both rows is, in my view, what makes the corpus useful. A corpus that stores only the meter
cannot show where a poem departs from it, and a corpus that stores only the words cannot show that a
departure is in fact a departure. The third example under **Getting started** below runs this comparison
across an entire work.

Every term used in this repository is defined, with an example, in
[docs/glossary.md](docs/glossary.md): foot, catalexis, caesura, hapax, z-score, and the rest. Nothing
elsewhere assumes that the glossary has been read.

The notation is declared in the `<metDecl>` element of each file and follows
[For Better For Verse](https://github.com/waynegraham/for_better_for_verse), the University of Virginia's
hand-scansion corpus, so that the two can be compared directly.

Stanzas carry a rhyme scheme, lettered from rhyme keys rather than from spelling:

```xml
<lg type="stanza" n="1" rhyme="ababcdcdefefgg">
```

## Getting started

Everything in the repository is plain XML and JSON. There is no database, no API key, and no build step.

To print every line of a poem with both scansions:

```python
import xml.etree.ElementTree as ET
TEI = "{http://www.tei-c.org/ns/1.0}"

tree = ET.parse("tei/shakespeare-sonnets.xml")
for line in list(tree.iter(TEI + "l"))[:4]:
    print(line.get("met"), line.get("real"), line.text)
```

To count which poems are in which meter:

```python
import json, collections
metres = json.load(open("data/metres.json"))
count = collections.Counter(
    entry[0]
    for work in metres.values()
    for entry in (work.get("sections") or {}).values()
)
for name, n in count.most_common(10):
    print(f"{n:6,}  {name}")
```

Each entry has the form `[metre, confidence, source, foot, feet]`. The `source` field says how the meter
was settled. A value of `measured` means that the scanner read the poem; anything else is a citation to
the scholarship that settled it.

To find where a poem departs from its meter, which is the question the corpus was built to answer:

```python
import xml.etree.ElementTree as ET
TEI = "{http://www.tei-c.org/ns/1.0}"
tree = ET.parse("tei/shakespeare-sonnets.xml")

for line in tree.iter(TEI + "l"):
    met, real = line.get("met"), line.get("real")
    if not met or not real or len(met) != len(real):
        continue
    clash = [i for i, (m, r) in enumerate(zip(met, real)) if r != "x" and m != r]
    if clash:
        print(f"{line.text}\n  metre wants {met}, the words give {real} at {clash}")
```

## What is in the repository

| path | what it holds |
|---|---|
| `tei/<work>.xml` | TEI P5: the text, stanzas, rhyme scheme, per-line scansion, and the work's URN |
| `data/metres.json` | the meter of each poem, with the confidence it was settled at |
| `data/cite.json` | the canonical reference for every poem |
| `data/stable.json` | permanent identifiers, and retired addresses that still resolve |
| `data/library.json` | the catalog: authors, dates, sources, editions, per-work measures |
| `data/audio/` | line-level timings against public domain recordings |
| `assemble.sh` | rebuilds this repository from the working corpus and prints the figures to check |

## Citing a poem, not just the corpus

A reference to a poem is only reproducible if it names the text that is meant. "The Iliad, line 1" is
not a citation. Translations differ and so do editions. Laurel follows CTS, the scheme that
settled this question for classical literature, and one that will be familiar to anyone who has used the
Perseus Digital Library:

```
urn:laurel:eng:shakespeare.shakespeare-sonnets.pg1041:18.1-18.4
               author      work                edition passage
```

These references resolve at `https://laurelpoetry.com/cite.html?urn=...`, and with `&format=json` or
`&format=text` they return the passage itself. Each poem also has a permanent identifier that survives
being retitled or re-parsed, so that a reference made today will still resolve after the text has been
corrected. The details are in [docs/references.md](docs/references.md).

## How the texts were chosen

Everything here is in the public domain in the United States, which is to say that it was published
before 1931. The texts come from Project Gutenberg, and each work's TEI file names the ebook it was
taken from and links to it. The Gutenberg header, footer, and license text have been removed, and
nothing else has been altered.

I should be honest about what the selection is and is not. It is not a sample in the statistical sense.
It is a reading library, assembled to cover the English tradition from the classical translations through
to the 1920s, which means that it favors poets who are read over poets who are representative. Editions,
moreover, were chosen for being in the public domain rather than for being the best witnesses to their
texts. This is the plainest weakness of the corpus, and it is stated wherever the figures appear.

## Method, and where it is weak

[METHOD.md](METHOD.md) is the index to the method: thirteen short documents, one for each thing the
corpus claims to know. They cover how a meter is determined and what counts as evidence, how accurate
the scansion has been measured to be, how rhyme is keyed, where the definitions come from, how a
recording is aligned to its lines, and what the most recent audit of the whole library found. I have
tried to write them so that each claim can be checked rather than taken on trust. Where a number
flatters the method, the document says so, and the known limits are collected at the end of METHOD.md.

The largest of those limits has recently been narrowed. A meter used to be named whenever the words fell
into a pattern well enough, and a poem can do that while being the wrong shape entirely. William
Barnes's Dorset poems, for example, were called anapaestic tetrameter although not one line in forty was
of that length. A meter is now named only where more than half of a poem's lines are of a length that the
meter can actually produce. This is a test that the confidence score alone could not make. The
poems it catches were scoring well. Well over a thousand poems, roughly one in thirteen, moved from a
wrong answer to no answer as a result. What remains is that a poem with no meter is still not
distinguished from a poem whose meter could not be settled, and a small number of pages that are not
verse at all are still scanned as though they were.

A second limit arrived with this release, and it is in the structure rather than the scansion. Five
verse dramas were added at v1.03, and two of them are divided wrongly. Longfellow's *Christus* carries
the whole of *John Endicott* in a single 2,111-line section headed with that play's cast list, and its
*Giles Corey* has an act heading fused to the first line of dialogue. *Michael Angelo* reads several
speech lines as section headings, so that sections appear under titles such as "To marry him?". The
lines themselves are correct and scanned as usual; it is the division into sections, and therefore the
canonical references that depend on it, that is wrong for those two works. Poe's *Politian*, Lazarus's
*The Spagnoletto* and Longfellow's *Judas Maccabaeus* came out correctly. The parser is being fixed and
the next release will re-divide them.

## License

Two different things are released under two different terms. The poems are in the public domain, and
nothing in this repository makes any claim over them. The apparatus, by which I mean the scansion, the
rhyme lettering, the meter determinations, the canonical references, the identifiers, and the audio
timings, is released under CC BY-SA 4.0. You are welcome to use it, provided that you credit Laurel and
keep any derivative work equally open. See `LICENCE` for the full terms.

## Citing this corpus

    Dome, Garrett. Laurel: a scanned corpus of English verse, with per-line
    stress, identified metre, rhyme, and canonical references.
    https://doi.org/10.5281/zenodo.22738547

That DOI stands for the corpus as a whole and always resolves to the newest version. Where a result
depends on exactly these texts (a count, a scansion, a line reference), please cite the version instead.
The DOI for v1.01 is **https://doi.org/10.5281/zenodo.22738548**. `CITATION.cff` carries both, so
GitHub's "Cite this repository" button and any reference manager will pick them up.
