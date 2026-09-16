# Definitions

*Part of the [Laurel corpus](../README.md). The [method index](../METHOD.md) lists the other documents,
and terms are defined in the [glossary](glossary.md).*

## Webster's 1913

Word definitions come from *Webster's Revised Unabridged Dictionary* of 1913,
[Project Gutenberg ebook 29765](https://www.gutenberg.org/ebooks/29765), which is in the public domain
and is of roughly the right century for most of this library. It has **96,527 headwords** and runs to
16 MB.

Shipping all of it would be absurd, and shipping only the rare words that the pipeline had flagged
turned out to be worse, since it left a reader who met *wont*, *ere* or *still* in its old sense with
nothing at all. The site therefore keeps the headwords that the library actually contains, split into
small files by their first letters, so that looking up a word fetches a few dozen kilobytes rather than
sixteen megabytes.

**Those files are not in this repository.** They are a public domain dictionary re-cut rather than a
part of the corpus, and they would roughly double its size. `pipeline/webster.py` builds them from the
Gutenberg ebook in one pass, and `pipeline/analyze.py` cuts the per-work glossaries from the result.
What this repository ships is the method, not the dictionary.

## What each work carries

Every work has its own glossary of the words in it that a reader is likely to want. Each entry holds
the part of speech, the definition, the etymology where Webster gives one, and how often the word
occurs in that work. `library.json` records how many words each work has glossed, under
`stats.glossary_words`.

## Where Webster is the wrong dictionary

Webster's is a dictionary of standard English. It has almost nothing for Burns's Scots, next to nothing
for the ballads, and nothing at all for Chatterton's invented fifteenth century, Barnes's Dorset,
Lowell's Yankee, Longfellow's Ojibwe or the Sanskrit in Dutt's Mahabharata.

For those works the glossary that the edition's own editor printed is used instead, shipped with the
work it was written for. A word may carry both. *Gate* is a way or a road in Scots, and Webster's sense
of it is no help at all in Burns.

## Stress and syllables

Pronunciation and word stress come from the
[CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict), with the elisions that verse
itself uses. See [scansion](scansion.md).
