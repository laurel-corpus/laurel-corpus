# Laurel corpus

English verse in the public domain, encoded in TEI P5, with the scansion, rhyme and canonical
references that Laurel adds to it.

**416 works · 18,107 poems · 1,201,730 lines**

Every line carries two scansions: what the words themselves settle, and what the poem's metre asks for.
Every poem carries a canonical reference that names its edition, and a permanent identifier that
survives being re-titled or re-parsed. Around 1,700 poems also carry line-level timings against public
domain recordings, so a reading can be followed word by word.

The site that reads this corpus is at [laurelpoetry.com](https://laurelpoetry.com).

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

A citation has to name the edition, not only the work. "The Iliad, line 1" is not a reference, because
texts differ. The scheme follows CTS, which settled this for classical literature, and uses the same
four parts:

```
urn:laurel:eng:shakespeare.shakespeare-sonnets.pg1041:18.1-18.4
               author      work                edition passage
```

The passage is the reference a scholar would actually write. Sonnets, cantos and books are cited by
number; a titled lyric by its own stable name. Ranges are written `18.1-18.4`.

References resolve at `https://laurelpoetry.com/cite.html?urn=...`, and with `&format=json` or
`&format=text` they return the passage itself, so something other than a browser can follow a citation.

Each poem also has a permanent identifier (`L00036`), recorded in `data/stable.json` and carried in the
TEI as `@n`. Identifiers are never reused. When a poem's address changes the old one is retired rather
than dropped, and a reference written against it goes on resolving.

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

Read `METHOD.md` before relying on the scansion. It states how the metre is determined and how
accurate it has been measured to be, including where it has not been tested.

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

See `CITATION.cff`, or cite a single poem by its own canonical reference.
