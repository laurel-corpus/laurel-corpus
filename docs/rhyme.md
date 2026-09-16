# Rhyme

*Part of the [Laurel corpus](../README.md). The [method index](../METHOD.md) lists the other documents,
and terms are defined in the [glossary](glossary.md).*

## What counts as a rhyme

Two lines rhyme when their last words share a **rhyme key**: the stressed vowel of the final foot and
everything after it, taken from the
[CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict). *Prove* is `UW1 V`, *love*
is `AH1 V`, and the two do not match.

Those codes are the dictionary's own alphabet for the sounds of English, one code to a sound. `UW` is
the vowel in *boot*, `AH` is the vowel in *but*, and `V` is the consonant at the end of both words. The
digit on a vowel is its stress, `1` for the syllable you lean on and `0` for one you do not. So *prove*
and *love* end on the same consonant after different vowels, which is why they look like a rhyme on the
page and are not one in the mouth.

Three rules keep the key from matching things that do not rhyme:

* **A word that is not in the dictionary gets a key by spelling analogy**, from an index of how words
  with the same ending are actually pronounced, and not from the letters alone.
* **A key of one sound is not evidence.** Admitting a bare final vowel made every word ending in an
  unstressed *-y* rhyme with every other, so that *cherries*, *peaches* and *oranges* were lettered as
  rhymes at the opening of *Goblin Market*. Two segments is the minimum.
* **A word with two pronunciations carries both keys.** *Again* is `AH0 G EH1 N` and `AH0 G EY1 N`,
  and taking only the first made *pain* and *grain* rhyme through it.

A line whose ending is not a word (a stage direction, a bare numeral, a brace) has no rhyme and is left
blank rather than lettered.

## Scheme lettering

Stanzas are lettered independently, which is the right choice for every closed form: the sonnet,
ottava rima, rhyme royal, the Spenserian stanza, the ballad quatrain. Byron's stanza is ABABABCC, and
lettering the next one I through P would be perverse.

Interlocking forms call for the opposite, and there the notation is the point. Terza rima is ABA BCB
CDC because the middle line of each tercet seeds the next, and restarting at A would hide the whole
interest of the form. So each poem is asked which kind it is: the scanner counts how many stanza-final
rhymes find their partner in the next stanza, and where that is how the poem works, it letters straight
through. Matching stays strict (the same key, a different word, within six lines), since otherwise a
long poem lettered continuously collects every accidental echo down its length.

## Rhymes that have drifted

A pair that the poet rhymed and a modern dictionary does not is recorded per work: *love* and *prove*,
*gone* and *upon*, Byron's *Juan* and *one*. Thirteen works carry them, 10,700 distinct pairs in all.

Two limits are worth stating. A pair is only tested where the poem has a declared stanza form and the
stanza has the expected number of lines, so the count is a floor rather than a census. And more than
half of these pairs (Petrarch's sonnets, *Orlando Furioso*, *Jerusalem Delivered*) are in
**translations**. Those are the translator's rhymes, in the translator's English, and nothing about them
describes Petrarch, Ariosto or Tasso. The reader is told whose verse it is, and the same rule governs
metre and form throughout this corpus.
