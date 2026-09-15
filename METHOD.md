# Method

This is how a poem gets from a plain text file to an annotated line, in the order it happens. Each step
has a document of its own below, and each of those is written so the claim can be checked rather than
taken on trust. Where a number looks good because the test was easy, the document says so.

## How a poem is processed

**1. The text.** A work is taken from Project Gutenberg. The Gutenberg header, footer and licence are
removed and nothing else is altered. The file is split into poems, and the front matter — title pages,
dedications, contents — is separated from the verse.

**2. Syllables.** Every line is broken into syllables. Words are looked up in a pronouncing dictionary;
a word it does not have is tried as an inflection of a word it does have (*expedients* as *expedient*),
and only failing that is counted by letter rules.

**3. What the words insist on.** Each syllable is given one of three verdicts: stressed, unstressed, or
undetermined. A polysyllable takes the dictionary's stress. A one-syllable word is judged by what it
does elsewhere in the corpus and by its part of speech, which is weaker evidence and is weighted as
such. Nothing is guessed: a syllable with no evidence is recorded as undetermined, and the metre is
then free to take it either way. This is the `@real` attribute.

**4. The metre.** Candidate metres are built as templates rather than looked up. The four feet, at every
length from one foot to eight, with the licences real verse takes — a line may open without its first
slack, or close without its last, or add one past the final stress — and the substitutions English verse
actually makes, such as the inverted first foot. Every line of the poem is tested against every
template, each reading paying a cost for what it bends, so the plainest account of the poem wins. If no
metre fits well enough, the poem is left without one rather than given a guess.

**5. Reading the line against its metre.** Once the poem's metre is settled, each line is read again in
it. That is the `@met` attribute — not what the line is, but what the measure asks of it. Comparing the
two is how you find where a poet departs from the measure.

**6. Rhyme.** End words are reduced to a rhyme key from their pronunciation rather than their spelling,
so *love* and *prove* are recorded as the near-rhyme they now are. Each stanza is then lettered.

**7. Identity.** Every poem is given a canonical reference naming the edition it came from, and a
permanent identifier that survives re-titling and re-parsing, so a citation made today still resolves
after the text is corrected.

**8. Checking.** The whole library is audited on every build: broken references, retired addresses,
glossary entries for words that do not occur, images nothing points at, and a precision test that asks
whether the scanner still believes a sonnet is in iambic pentameter.

## The documents

| | |
|---|---|
| [Glossary](docs/glossary.md) | every term used anywhere in this repository, with an example: foot, catalexis, caesura, hapax, z-score. Start here if any of the others assume something you have not been told |
| [Texts](docs/texts.md) | which editions the poems come from, how they were cleaned, and why the choice of edition is this corpus's weakest point |
| [Syllables, stress and metre](docs/scansion.md) | steps 2 to 5 above in full: how syllables are counted, what counts as evidence for a stress, how the templates are built, and how a metre is finally settled |
| [Accuracy](docs/accuracy.md) | how well the scansion agrees with prosodists who did it by hand, on data held back from the design; and three ways that score flatters itself |
| [Rhyme](docs/rhyme.md) | how end words are reduced to a rhyme key, how stanzas are lettered, and what happens to rhymes that have drifted apart since they were written |
| [Measures](docs/measures.md) | the per-work figures in `data/measures/`: alliteration, assonance, caesura, feminine endings, vocabulary range, each given against a baseline so the number means something |
| [Definitions](docs/definitions.md) | where the glossaries come from, and the poets for whom a 1913 dictionary is the wrong one |
| [Commentary](docs/commentary.md) | the editors' notes carried from the source editions, and how they are attached to lines |
| [Original-language texts](docs/languages.md) | the Latin and Greek beside their translations: how quantity is scanned, and how a translation is lined up with its original |
| [Audio timings](docs/audio.md) | how a public domain recording is aligned to the lines of the poem it reads |
| [References](docs/references.md) | the citation scheme, what a URN means, and how an address that moves is retired rather than broken |
| [The audit](docs/audit.md) | the checks run over the whole library on every build, and what the last run found |
| [Sources and tools](docs/sources.md) | every text, dataset, dictionary and standard this work rests on, with links |

## Known limits

* Editions are chosen for being public domain, not for being the best witness.
* Trochaic and dactylic metres were untested until a second gold corpus was brought in. They are now
  measured and they are the weaker ones: iambic 84.4%, trochaic 82.3%, dactylic 84.5%. 8% of lines
  cannot be compared at all, because this syllabifier and the annotators disagree about how many
  syllables they have.
* **Free verse is given a metre it does not have.** All twelve works these editions call free verse
  come out with a confident one — *Leaves of Grass* reads as iambic pentameter. The signal that would
  catch it is there (free verse matches its own settled line length half the time, against 93% for
  sonnets) but a threshold that catches Whitman also strips a third of the ballads, which alternate four
  feet with three for an honest reason. Unsolved, and stated here rather than hidden.
* **Some pages that are not verse are scanned as verse.** Seven books open with a title or copyright
  page that was ingested as a poem; Milton's cast list for *Comus* is labelled iambic pentameter; the
  marginal performance directions in Lindsay's *The Congo* are counted as 79 lines of it.
* Accuracy figures come from a corpus that shaped the scanner's design.
* Glossaries are drawn from Webster's 1913, which is of the right century for most of this library and
  the wrong one for some of it.
* A small number of editorial notes in the source editions are keyed to sections this corpus names
  differently, and do not appear.
* Greek hexameters solve less often than Latin ones, and the lyric metres are not attempted.
* Between two anchors, a translation is lined up with its original by even spacing, not by evidence.
