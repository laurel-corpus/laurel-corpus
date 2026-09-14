# Laurel

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22738547.svg)](https://doi.org/10.5281/zenodo.22738547)

A free reading room for English poetry, at [laurelpoetry.com](https://laurelpoetry.com). Four hundred
books set out the way a good edition sets them: the rhymes lettered, the stresses marked, the hard
words explained. Nothing costs anything and nothing is behind a login.

**This repository is the corpus underneath it** — the texts, and everything Laurel works out about
them, published so the working can be checked and built on.

**416 works · 18,210 poems · 1,201,722 lines**

Every line carries two scansions: what the words themselves settle, and what the poem's metre asks for.
Every poem carries a canonical reference that names its edition, and a permanent identifier that
survives being re-titled or re-parsed. 1,680 poems also carry line-level timings against public
domain recordings, so a reading can be followed word by word.

## What is here

| path | what it holds |
|---|---|
| `tei/<work>.xml` | TEI P5: text, stanzas, rhyme scheme, per-line scansion, URNs |
| `data/cite.json` | the canonical reference for every poem |
| `data/stable.json` | permanent identifiers, and retired addresses that still resolve |
| `data/metres.json` | the metre of each poem, with the confidence it was settled at |
| `data/audio/` | line-level timings against LibriVox recordings |
| `data/library.json` | the catalogue: authors, dates, sources, editions |

## Canonical references

A citation has to name the edition, not only the work. "The Iliad, line 1" is not a reference,
because texts differ. The scheme follows CTS, which settled this for classical literature:

```
urn:laurel:eng:shakespeare.shakespeare-sonnets.pg1041:18.1-18.4
               author      work                edition passage
```

References resolve at `https://laurelpoetry.com/cite.html?urn=...`, and with `&format=json` or
`&format=text` they return the passage itself. Each poem also has a permanent identifier that
survives being re-titled or re-parsed. See **[docs/references.md](docs/references.md)**.

## Scansion in the TEI

Notation follows [For Better For Verse](https://github.com/waynegraham/for_better_for_verse), the
University of Virginia's hand-scansion corpus, so that the two interoperate.

```xml
<l n="1" real="xx-+xxx+-x" met="-+-+-+-+-+">Shall I compare thee to a summer's day?</l>
```

* `+` a stressed syllable
* `-` an unstressed syllable
* `x` a syllable the dictionary does not settle, which the metre may take either way

`@real` is what the words insist on. `@met` is what the poem's metre asks for. Where they differ is
where the interest is, and no other corpus of English verse publishes both.

Read **[docs/scansion.md](docs/scansion.md)** for how the metre is determined and
**[docs/accuracy.md](docs/accuracy.md)** for how accurate it has been measured to be, including where it
has not been tested.

## Texts

Public domain in the United States: everything here was published before 1931. Texts come from Project
Gutenberg; each work's TEI names its ebook and links to the source. The Gutenberg header, footer and
licence text were removed and nothing else was altered.

## Licence

Two different things, under two different terms.

**The poems are in the public domain.** Nothing here creates a claim over them.

**The apparatus is CC BY-SA 4.0**: the scansion, the rhyme lettering, the metre determinations, the
canonical references, the identifiers and the audio timings. Use them, credit Laurel, and keep
derivatives as open. See `LICENCE`.

## Citing this corpus

    Dome, Garrett. Laurel corpus: English verse in TEI, with scansion and
    canonical references. 2026. https://doi.org/10.5281/zenodo.22738547

That DOI stands for the corpus as a whole and resolves to whatever the newest version is. Where a
result depends on exactly these texts -- a count, a scansion, a line reference -- cite the version
instead: **https://doi.org/10.5281/zenodo.22738548** is v1.0.1. `CITATION.cff` carries both, so GitHub's
"Cite this repository" and any reference manager will pick them up.

A single poem is cited by its own canonical reference, which names its edition. See
**[docs/references.md](docs/references.md)**.
