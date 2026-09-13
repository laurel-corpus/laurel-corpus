# Rhyme

*Part of the [Laurel corpus](../README.md) — see the [method index](../METHOD.md).*

## What counts as a rhyme

Two lines rhyme when their last words share a **rhyme key**: the stressed vowel of the final foot and
everything after it, taken from the [CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict).
`prove` is `UW1 V`, `love` is `AH1 V`, and they do not match.

Three rules keep the key from matching things that do not rhyme:

* **A word out of the dictionary gets a key by spelling analogy**, from an index of how words with the
  same ending are actually pronounced — not from the letters alone.
* **A key of one sound is not evidence.** Admitting a bare final vowel made every word ending in an
  unstressed `-y` rhyme with every other, so *cherries*, *peaches* and *oranges* were lettered as rhymes
  at the opening of *Goblin Market*. Two segments is the minimum.
* **A word with two pronunciations carries both keys.** *Again* is `AH0 G EH1 N` and `AH0 G EY1 N`;
  taking only the first made *pain* and *grain* rhyme through it.

A line whose ending is not a word — a stage direction, a bare numeral, a brace — has no rhyme and is
left blank rather than lettered.

## Scheme lettering

Stanzas are lettered independently, which is right for every closed form: the sonnet, ottava rima, rhyme
royal, the Spenserian stanza, the ballad quatrain. Byron's stanza is ABABABCC, and lettering the next one
I through P would be perverse.

Interlocking forms do the opposite, and the notation is the point. Terza rima is ABA BCB CDC because the
middle line of each tercet seeds the next; restarting at A hides the whole interest of the form. So each
poem is asked which it is: count how many stanza-final rhymes find their partner in the next stanza, and
where that is how the poem works, letter it straight through. Matching stays strict — same key, different
word, within six lines — or a long poem lettered continuously collects every accidental echo down its
length.

## Rhymes that have drifted

A pair the poet rhymed and a modern dictionary does not is recorded per work: *love* / *prove*,
*gone* / *upon*, Byron's *Juan* / *one*. 13 works carry them, 10,700 distinct pairs in all.

**Two limits worth stating.** A pair is only tested where the poem has a declared stanza form and the
stanza has the expected number of lines, so the count is a floor, not a census. And more than half these
pairs — Petrarch's sonnets, *Orlando Furioso*, *Jerusalem Delivered* — are in **translations**. Those are
the translator's rhymes, in the translator's English, and nothing about them describes Petrarch, Ariosto
or Tasso. The reader is told whose verse it is; the same rule governs metre and form throughout this
corpus.
