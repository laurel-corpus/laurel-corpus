# The texts

*Part of the [Laurel corpus](../README.md). Method notes: [texts](texts.md) · [scansion](scansion.md) · [accuracy](accuracy.md) · [definitions](definitions.md) · [commentary](commentary.md) · [audio](audio.md) · [references](references.md) · [sources](sources.md)*

## Where they come from

[Project Gutenberg](https://www.gutenberg.org/), chosen by ebook number, all published before 1931 and
therefore public domain in the United States. Each work's TEI names its ebook and links to it.

These are editions chosen for being free, not for being authoritative. That is the honest weakness of
this corpus against one built on named scholarly editions with an apparatus criticus. Where a text is
known to be a poor witness it should be treated as such.

## What was removed, and what was not

The Gutenberg header, footer and licence text are removed. The verse is not otherwise altered. Two
kinds of matter that are *not* the poem are also taken out:

**Printed line numbers.** Some editions set a number in the right margin, and Gutenberg preserves the
margin by padding the line with spaces and putting the number at the end. Left in, the reader is shown
a figure the poet did not write, and worse, the parser takes it for the rhyming word — one Wordsworth
line had `--485` lettered as a rhyme. **2,659 lines across 23 works** carried such a number. The test
for removing one is deliberately narrow, because a poem may legitimately end a line on a number.

**Front matter mistaken for verse.** Division titles, epigraphs and mottoes are folded into the poem
they introduce rather than standing as poems of their own. A motto in another alphabet is not a poem in
it: Longfellow heads *Voices of the Night* with six lines of Euripides, and left alone the parser made
them a poem whose entire text was Ancient Greek.

## Corrections

Where the source text is wrong, the change is recorded rather than made silently. Every alteration this
project made to a text is listed in `data/editions.json` under `changes`, and readers can see them on
the site. **10 corrections** are recorded across the library at present.

## What edition a reader is actually reading

A poem is not a fixed object. It is a particular edition, made by a particular editor, from particular
copies. `data/editions.json` records all of it for **417 works**:

| field | what it holds |
|---|---|
| `printed` | the printed edition behind the file where it names one, its transcriber, its release |
| `edition_named` | whether the source file actually names its printed edition, or does not |
| `critical` | named scholarly editions of the same work, as comparison witnesses |
| `changes` | every alteration this project made on the way to the page |
| `rights` | the public domain determination, with its reasons |

`edition_named` is worth attention: it is often **false**, because many Gutenberg files do not say
which printed text they were set from. Where that is so, the corpus says so rather than guessing.

The `critical` field does not mean the corpus uses those editions — it cannot, as they are in
copyright. It names them so that a reader comparing texts knows which authority to compare against.
