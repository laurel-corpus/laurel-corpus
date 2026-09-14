# Laurel

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22738547.svg)](https://doi.org/10.5281/zenodo.22738547)

This is the Laurel corpus: public domain English poetry encoded in TEI P5, in which every line carries
a scansion and most poems carry an identified metre. The poems are in the public domain; the encoding
and the annotation are CC BY-SA 4.0.

It is the material underneath [laurelpoetry.com](https://laurelpoetry.com), a free reading room for
poetry, published separately so that the working can be checked, corrected, and built on.

The figures for this release are printed by `./assemble.sh`, which is also what builds the repository.
They are not repeated here, because the corpus grows and a number written in two places goes stale in
one of them.

## What is in a line

Every line is encoded twice over.

```xml
<l n="6" real="+-x+-x-+-x" met="-+-+-+-+-+">Making a famine where abundance lies,</l>
```

`@real` is the stress the words themselves settle: taken from a pronouncing dictionary, together with
this poem's own syllabification. `@met` is the stress the poem's metre asks for.

* `+` a stressed syllable
* `-` an unstressed syllable
* `x` a syllable the dictionary does not settle, which the metre may take either way

Keeping both is the point of the corpus, and this line shows why. Sonnet 1 is iambic pentameter, so
`@met` alternates without exception. But the words open `+-`: "MAK-ing", stressed first. That is a
trochee standing in the first foot of an iambic line — the commonest substitution in English verse, and
the reason the line does not sound mechanical. Compare the two attributes and the corpus tells you
exactly where it happens, in every line of every poem. A corpus that stores only the metre, or only the
words, cannot tell you at all.

The third example under *Getting started* below does this comparison across a whole work.

The notation is declared in each file's `<metDecl>`, and follows
[For Better For Verse](https://github.com/waynegraham/for_better_for_verse), the University of
Virginia's hand-scansion corpus, so the two can be compared directly.

Stanzas carry a rhyme scheme, lettered from rhyme keys rather than from spelling:

```xml
<lg type="stanza" n="1" rhyme="ababcdcdefefgg">
```

## Getting started

Everything is plain XML and JSON. No database, no API key, no build step.

**Every line of a poem, with both scansions:**

```python
import xml.etree.ElementTree as ET
TEI = "{http://www.tei-c.org/ns/1.0}"

tree = ET.parse("tei/shakespeare-sonnets.xml")
for line in list(tree.iter(TEI + "l"))[:4]:
    print(line.get("met"), line.get("real"), line.text)
```

**Which poems are in which metre:**

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

Each entry is `[metre, confidence, source, foot, feet]`. `source` says how it was settled: `measured`
means the scanner read the poem, and anything else is a citation to the scholarship that settled it.

**Where a poem departs from its metre**, which is the question the corpus exists to answer:

```python
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
| `data/metres.json` | the metre of each poem, with the confidence it was settled at |
| `data/cite.json` | the canonical reference for every poem |
| `data/stable.json` | permanent identifiers, and retired addresses that still resolve |
| `data/library.json` | the catalogue: authors, dates, sources, editions, per-work measures |
| `data/audio/` | line-level timings against public domain recordings |
| `assemble.sh` | rebuilds this repository from the working corpus and prints the figures to check |

## Citing a poem, not just the corpus

A reference to a poem is not reproducible unless it names the text it means. "The Iliad, line 1" is not
a citation, because translations differ and so do editions. Laurel follows CTS, the scheme that settled
this for classical literature:

```
urn:laurel:eng:shakespeare.shakespeare-sonnets.pg1041:18.1-18.4
               author      work                edition passage
```

These resolve at `https://laurelpoetry.com/cite.html?urn=...`, and with `&format=json` or `&format=text`
they return the passage itself. Each poem also has a permanent identifier that survives being re-titled
or re-parsed, so a reference made today still resolves after the text is corrected.

See **[docs/references.md](docs/references.md)**.

## How the texts were chosen

Public domain in the United States: everything here was published before 1931. Texts come from Project
Gutenberg, and each work's TEI names the ebook it was taken from and links to it. The Gutenberg header,
footer and licence text were removed; nothing else was altered.

The selection is not a sample in the statistical sense. It is a reading library, assembled to cover the
English tradition from the classical translations through to the 1920s, which means it is weighted
towards poets who are read rather than poets who are representative. **Editions are chosen for being
public domain, not for being the best witness to the text.** That is the corpus's plainest weakness and
it is stated wherever the figures are.

## Method, and where it is weak

**[METHOD.md](METHOD.md)** is the index: twelve short documents, one per thing the corpus claims to know
— how a metre is determined and what counts as evidence, how accurate that has been measured to be, how
rhyme is keyed, where the definitions come from, how a recording is aligned to its lines, and what the
audit over the whole library last found.

They are written to be checked rather than believed. Where a number flatters the method, the document
says so. The known limits are collected at the foot of METHOD.md, and they include real ones: free verse
is still given a metre it does not have, and a handful of pages that are not verse are scanned as though
they were.

## Licence

Two different things under two different terms.

**The poems are in the public domain.** Nothing here creates a claim over them.

**The apparatus is CC BY-SA 4.0**: the scansion, the rhyme lettering, the metre determinations, the
canonical references, the identifiers and the audio timings. Use them, credit Laurel, and keep
derivatives as open. See `LICENCE`.

## Citing this corpus

    Dome, Garrett. Laurel: a scanned corpus of English verse, with per-line
    stress, identified metre, rhyme, and canonical references.
    https://doi.org/10.5281/zenodo.22738547

That DOI stands for the corpus as a whole and resolves to the newest version. Where a result depends on
exactly these texts — a count, a scansion, a line reference — cite the version instead:
**https://doi.org/10.5281/zenodo.22738548** is v1.0.1. `CITATION.cff` carries both, so GitHub's "Cite
this repository" and any reference manager will pick them up.
