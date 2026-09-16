# Glossary

*Part of the [Laurel corpus](../README.md). The [method index](../METHOD.md) lists the other documents.*

This is every term that the rest of these documents uses, each with an example. Nothing here assumes
that you have read the other documents, and nothing elsewhere assumes that you have read this one.

## Reading a line

**Syllable.** One beat of the voice. *Poem* has two, *poetry* has three.

**Stress.** The syllable you lean on when you say a word: *POem*, not *poEM*. English fixes the stress
of words of two syllables or more, so a dictionary can tell you where it falls. It does not fix
one-syllable words. Whether *where* is stressed depends on the sentence it is in.

**Scansion.** Marking which syllables in a line carry the beat. It is what this corpus does to every
line, and the marks are written `+` for a stressed syllable and `-` for an unstressed one.

**Foot.** The unit that a metre repeats. English verse uses four:

| foot | pattern | sounds like | example |
|---|---|---|---|
| **iamb** | `-+` | da-DUM | *a-BOVE* |
| **trochee** | `+-` | DUM-da | *GAR-den* |
| **anapaest** | `--+` | da-da-DUM | *in-ter-VENE* |
| **dactyl** | `+--` | DUM-da-da | *MER-ri-ly* |

An iamb and an anapaest are **rising**, because they end on the beat. A trochee and a dactyl are
**falling**, because they begin on it.

**Metre.** The pattern a poem keeps, named by its foot and by how many feet the line has.

| feet in the line | name |
|---|---|
| two | dimeter |
| three | trimeter |
| four | tetrameter |
| five | pentameter |
| six | hexameter |
| seven | heptameter |
| eight | octameter |

So **iambic pentameter** is five iambs, ten syllables, `-+-+-+-+-+`. It is the metre of Shakespeare's
sonnets, of *Paradise Lost*, and of most long poems in English. **Trochaic octameter** is eight trochees,
sixteen syllables, `+-+-+-+-+-+-+-+-`, and is the metre of *The Raven*.

A metre is a property of a poem rather than of a line. One line rarely settles which foot it is in;
twenty lines almost always do.

## Where a poem bends its metre

A poem that never departed from its metre would be unreadable. These are the licensed departures, and
the corpus records where each one falls.

**Substitution.** One foot swapped for a different foot of the same length. By far the commonest is a
**trochaic inversion**, a trochee standing in the first foot of an iambic line, which is how a great
many lines of English verse open.

**Pyrrhic** (`--`) is a foot with no stress in it, and **spondee** (`++`) is a foot with two. They
usually come as a pair, the one lending its beat to the other.

**Catalexis.** Dropping the last syllable of the last foot. A catalectic trochaic octameter is fifteen
syllables rather than sixteen, ending on the beat instead of after it. Poe alternates the two through
*The Raven*.

**Acephalous**, or **headless**. The same thing at the other end: the line is missing its first
unstressed syllable. An acephalous iambic pentameter is nine syllables, `+-+-+-+-+`. Sonnet 18 does
this in its second line, *Thou art more lovely and more temperate*.

Acephaly and catalexis are worth keeping straight, because a headless iambic line and a catalectic
trochaic line are the same string of marks. Only the rest of the poem says which it is.

**Feminine ending.** An unstressed syllable left over at the end of the line, so that an iambic
pentameter runs to eleven syllables: *To be or not to be, that is the question.*

**Elision.** Reading two syllables as one, in the way that *flower* can be said as one beat and *many
a* as two. Poets write to be read this way, and a line that looks a syllable too long often is not.

**Caesura.** The strong pause inside a line, usually where the punctuation is.

## Stanzas and rhyme

**Stanza.** A group of lines set off from the next by a space.

**Rhyme key.** What Laurel compares to decide whether two lines rhyme: the stressed vowel of the last
word and every sound after it, taken from a pronouncing dictionary rather than from the spelling. The
dictionary writes sounds in its own alphabet, one code to a sound, with a digit on each vowel for its
stress. *Prove* is `UW1 V` and *love* is `AH1 V`, the same final consonant after different vowels.

**Rhyme scheme.** Which lines rhyme with which, lettered in order of appearance. `abab` means that the
first and third lines rhyme, and the second and fourth. A Shakespearean sonnet is `ababcdcdefefgg`.

Because the key is built from sound rather than spelling, *though* and *tough* are never lettered as a
rhyme merely for ending in the same four letters. The reverse case is a **drifted rhyme**: a pair that
the poet rhymed and a modern dictionary does not, such as *love* and *prove*, whose vowels have parted
since the poem was written. Those are recorded per work rather than quietly lettered as full rhymes, so
that the corpus neither pretends the rhyme still works nor pretends the poet did not make one.

**Closed forms.** Stanzas with a fixed shape and rhyme, which a poet chooses whole. The **sonnet** is
fourteen lines; **ottava rima** is eight lines rhyming `abababcc`, the stanza of Byron's *Don Juan*;
**rhyme royal** is seven lines rhyming `ababbcc`; the **Spenserian stanza** is nine lines, eight of five
feet and a ninth of six, rhyming `ababbcbcc`; and the **ballad quatrain** is four lines in common
measure.

**Blank verse.** Iambic pentameter that does not rhyme: *Paradise Lost*, and most verse drama.

**Heroic couplet.** Iambic pentameter rhyming in pairs: Pope, Dryden, Chaucer.

**Common measure.** Four iambic feet answered by three, rhyming `abab` or `abcb`. It is the shape of the
ballads and of much of Dickinson, who uses it more than any other measure. It has its own name because
calling it iambic tetrameter throws away the half of the pattern that matters. **Short measure** and
**poulter's measure** are its relatives, and **fourteeners** are seven iambs to a line.

**Quantity.** How long a syllable takes to say, rather than how hard it is hit. Latin and Greek verse is
built on quantity and English verse on stress, and the two are different systems: a Latin line is a
pattern of long and short syllables. Laurel scans the original-language texts by quantity and their
English translations by stress, which is why a translation's metre belongs to the translator and never
to the original poet.

**Lemma.** In an editor's note, the word or phrase from the poem that the note is about, quoted at its
head so that you can tell what is being annotated.

**Apparatus criticus.** The list at the foot of a scholarly edition recording where the surviving copies
of a text disagree and which reading the editor chose. Laurel's texts come from Project Gutenberg and
have none, which is the plainest weakness of this corpus against an edition that does.

## What the corpus writes down

**TEI**, the Text Encoding Initiative, is the standard that scholars use for encoding texts, and TEI P5
is its current version. It is XML with an agreed vocabulary, so a tool that reads one TEI corpus can
read another. Laurel publishes every work as TEI so that what it knows about a line travels with the
line.

**`@met`** on a line is the pattern that the poem's metre asks for. **`@real`** is what the words
themselves settle. The places where the two differ are the places of interest.

* `+` stressed
* `-` unstressed
* `x` a syllable the dictionary does not settle, which the metre may take either way

Most one-syllable words are `x`, and that is a fact about English rather than a gap in the dictionary.

**`@n`** carries the canonical reference, and **`<metDecl>`** in each file declares the notation, which
follows [For Better For Verse](https://github.com/waynegraham/for_better_for_verse), the University of
Virginia's hand-scansion corpus, so that the two can be compared directly.

**URN and CTS.** A URN is a permanent name for a thing rather than an address for it. CTS is the scheme
that settled citation for classical literature, naming author, work, edition and passage in that order.
`urn:laurel:eng:shakespeare.shakespeare-sonnets.pg1041:18.1-18.4` is the first four lines of Sonnet 18
in the Gutenberg edition this corpus used. It says which text it means, which a page number does not.

**Confidence.** The share of the evidence in a poem's lines that the named metre accounts for. It is
not a probability that the answer is right. Poems mostly land between 0.80 and 0.95, and below 0.70 the
corpus names no metre at all. A low figure often means an interesting poem rather than a failed
reading.

## Measurements

These appear in `data/library.json` under each work's `stats`, and [measures.md](measures.md) lists
every one of them.

**Alliteration** is two or more content words in a line starting with the same consonant;
**assonance** is the same for the stressed vowel.

**Against a baseline.** Poems alliterate because English alliterates, so an alliteration count on its
own says nothing. Every such figure is therefore reported twice: as observed, and as it comes out when
the poem's own words are shuffled across its own lines. The second figure is what the poem would do by
accident, and only the gap between the two belongs to the poet.

**Z-score.** How far the observed figure sits from that shuffled baseline, counted in standard
deviations. Zero means that the poem does exactly what chance would. Two or more means that it is doing
something on purpose.

**Bootstrap interval.** A range within which the true figure probably falls, worked out by re-sampling
the poem's own lines a thousand times. It is how a fourteen-line poem and a ten-thousand-line poem are
kept from claiming the same certainty.

**MTLD** measures how varied a poem's vocabulary is. The plain measure, unique words over total words,
falls as any text lengthens, so it ends up measuring length instead of variety. MTLD reads through the
text and counts how far it gets before variety drops below a threshold, which does not depend on how
long the text is ([McCarthy and Jarvis 2010](https://doi.org/10.3758/BRM.42.2.381)).

**Hapax share.** In this corpus the figure counts line endings rather than the whole vocabulary: it is
the share of a work's distinct rhyme words that it uses only once. A high share means that the poet
keeps finding new words to end lines on; a low one means that the same handful of rhymes come round
again.

**Scheme entropy.** One number for how many different stanza forms a book uses. A book entirely in
sonnets scores zero. A book that changes form constantly scores high.

**Closed-class**, or **function words**. The small fixed set that English does not add to: *the*, *of*,
*and*, *but*, *in*. Everything else, the nouns and verbs and adjectives, is **open-class** or **content
words**, and new ones enter the language all the time.
