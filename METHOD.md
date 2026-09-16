# Method

This document sets out how a poem gets from a plain text file to an annotated line, in the order in
which it happens. Each step has a document of its own, listed below. I have tried to write each of them
so that its claims can be checked rather than taken on trust, and where a figure looks better than it
should because the test behind it was an easy one, the document says so.

## How a poem is processed

**1. The text.** A work is taken from Project Gutenberg. The Gutenberg header, footer and license are
removed, and nothing else is altered. The file is then split into poems, and the front matter (title
pages, dedications, tables of contents) is separated from the verse.

**2. Syllables.** Every line is broken into syllables. Words are looked up in a pronouncing dictionary.
A word that the dictionary does not have is tried as an inflection of a word that it does have
(*expedients* as *expedient*), and only when that fails is it counted by letter rules.

**3. What the words insist on.** Each syllable is given one of three verdicts: stressed, unstressed, or
undetermined. A word of two or more syllables takes the stress the dictionary gives it. A word of one
syllable is judged by what it does elsewhere in the corpus and by its part of speech, which is weaker
evidence and is weighted accordingly. Nothing is guessed. A syllable with no evidence behind it is
recorded as undetermined, and the meter is then free to take it either way. This is the `@real`
attribute.

**4. The meter.** Candidate meters are built as templates rather than looked up in a list. The four
feet are taken at every length from one foot to eight, together with the licenses that real verse takes
(a line may open without its first slack, close without its last, or add one slack past the final
stress) and the substitutions that English verse actually makes, such as the inverted first foot. Every
line of the poem is tested against every template, and each reading pays a cost for whatever it bends,
so that the plainest account of the poem wins. If no meter fits well enough, the poem is left without
one rather than given a guess.

**5. Reading the line against its meter.** Once the poem's meter is settled, each line is read again in
that meter. This is the `@met` attribute, which records not what the line is but what the measure asks
of it. Comparing the two attributes is how one finds the places where a poet departs from the measure.

**6. Rhyme.** End words are reduced to a rhyme key from their pronunciation rather than their spelling,
so that *love* and *prove* are recorded as the near rhyme they have since become. Each stanza is then
lettered.

**7. Identity.** Every poem is given a canonical reference that names the edition it came from, and a
permanent identifier that survives retitling and re-parsing, so that a citation made today still
resolves after the text has been corrected.

**8. Checking.** The whole library is audited on every build: broken references, retired addresses,
glossary entries for words that do not occur, images that nothing points at, and a precision test that
asks whether the scanner still believes a sonnet to be in iambic pentameter.

## The documents

| | |
|---|---|
| [Glossary](docs/glossary.md) | every term used anywhere in this repository, with an example: foot, catalexis, caesura, hapax, z-score. Start here if any of the other documents assumes something you have not been told |
| [Texts](docs/texts.md) | which editions the poems come from, how they were cleaned, and why the choice of edition is the weakest point of this corpus |
| [Syllables, stress and meter](docs/scansion.md) | steps 2 to 5 above in full: how syllables are counted, what counts as evidence for a stress, how the templates are built, and how a meter is finally settled |
| [Accuracy](docs/accuracy.md) | how well the scansion agrees with prosodists who did the work by hand, on data held back from the design, and three ways in which that score flatters itself |
| [Rhyme](docs/rhyme.md) | how end words are reduced to a rhyme key, how stanzas are lettered, and what happens to rhymes that have drifted apart since they were written |
| [Measures](docs/measures.md) | the per-work figures in `data/measures/`: alliteration, assonance, caesura, feminine endings, vocabulary range, each given against a baseline so that the number means something |
| [Definitions](docs/definitions.md) | where the glossaries come from, and the poets for whom a dictionary of 1913 is the wrong one |
| [Commentary](docs/commentary.md) | the editors' notes carried over from the source editions, and how they are attached to lines |
| [Original-language texts](docs/languages.md) | the Latin and Greek beside their translations: how quantity is scanned, and how a translation is lined up with its original |
| [Audio timings](docs/audio.md) | how a public domain recording is aligned to the lines of the poem it reads |
| [References](docs/references.md) | the citation scheme, what a URN means, and how an address that moves is retired rather than broken |
| [The audit](docs/audit.md) | the checks run over the whole library on every build, and what the last run found |
| [Sources and tools](docs/sources.md) | every text, dataset, dictionary and standard this work rests on, with links |

## Known limits

I would rather state these here than leave them to be discovered.

* Editions were chosen for being in the public domain, not for being the best witnesses to their texts.
* Trochaic and dactylic meters went untested until a second gold corpus was brought in. They are now
  measured, and they are the weaker ones: iambic 84.4%, trochaic 82.3%, dactylic 84.5%. Some 8% of
  lines cannot be compared at all. This syllabifier and the annotators disagree about how many
  syllables those lines have.
* **Free verse is given a meter it does not have.** All twelve works that these editions call free
  verse come out with a confident meter, and *Leaves of Grass* reads as iambic pentameter. The signal
  that would catch this is present (free verse matches its own settled line length about half the
  time, against 93% for sonnets), but a threshold strict enough to catch Whitman also strips a third of
  the ballads, which alternate four feet with three for a perfectly good reason. This remains
  unsolved, and I would rather say so than hide it.
* **Some pages that are not verse are scanned as verse.** Seven books open with a title or copyright
  page that was ingested as a poem; Milton's cast list for *Comus* is labeled iambic pentameter; and
  the marginal performance directions in Lindsay's *The Congo* are counted as 79 lines of it.
* The accuracy figures come from a corpus that shaped the scanner's design.
* Glossaries are drawn from Webster's 1913, which is the right century for most of this library and
  the wrong one for some of it.
* A small number of editorial notes in the source editions are keyed to sections that this corpus
  names differently, and so do not appear.
* Greek hexameters are solved less often than Latin ones, and the lyric meters are not attempted.
* Between two anchors, a translation is lined up with its original by even spacing rather than by
  evidence.
