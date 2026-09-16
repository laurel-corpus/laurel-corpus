# Verse marked by hand, in print

Every file here is a prosodist's own scansion of English verse, printed with the beats marked, from a
book in the public domain. They are rulers: the scanner is measured against them and never learns
from them. `marked.py` scores them; `markedin.py` reads each book's notation and writes the `.tsv`.

Each `.tsv` line is the plain verse line, a tab, and a mark string: `+` where the prosodist marked a
beat, `-` where he marked a slack, `x` where he marked nothing.

## In use

| file | source | Gutenberg | notation | lines | how to re-extract |
|---|---|---|---|---|---|
| `schipper.tsv` | Jakob Schipper, *A History of English Versification* (Oxford 1910), the modern-English specimens | 43352 | acute on the stressed vowel | 493 | `markedin.py schipper cache/schipper-modern.txt acute` |
| `saintsbury.tsv` | George Saintsbury, *Historical Manual of English Prosody* (1910) | 56187 | macron = beat, breve = slack; both stacked = doubtful | 164 | `markedin.py saintsbury 56187.txt macron` |
| `brown.tsv` | Goold Brown, *The Grammar of English Grammars* (1851), Part IV Versification | 11615 | transcriber's `=` (macron) and `~` (breve) before the vowel | 77 | `markedin.py brown 11615.txt ascii 70893 77900` |
| `latham.tsv` | R. G. Latham, *A Handbook of the English Language* (1841), Part VI Prosody | 28436 | acute on the stressed vowel | 40 | `markedin.py latham 28436.txt acute 12135 13100` |
| `leigh.tsv` | Percival Leigh, *The Comic English Grammar* (1840), ch. II | 43397 (not 44802) | macron/breve | 19 | `markedin.py leigh 43397.txt macron 4429 4900` |
| `guest.tsv` | Edwin Guest, *A History of English Rhythms*, ed. Skeat (1882) | archive.org `historyofenglish00guesuoft` | a bar after the accented syllable, OCR'd as `\|`, `j`, `\\` or `[`; words split at syllables | 65 | matched to the library by letters; kept only where Guest's syllable count equals ours; 124 matched lines dropped for disagreeing, mostly Chaucer's final -e |
| `skeat.tsv` | W. W. Skeat, *Chaucer's Works* vol. VI, Introduction §§98–107 (Oxford 1894) | 43097 | acute on the stressed vowel, encoded `['a]`; `[:e]` is a sounded -e | 11 | `markedin.py skeat cache/skeat-lines.txt acute` after converting the brackets |
| `kirkham.tsv` | Samuel Kirkham, *English Grammar in Familiar Lectures* (1829) | 14070 | macron/breve | 4 | `markedin.py kirkham 14070.txt macron 13172 13400` |

The line counts are after filtering: a line is kept only if the prosodist marked most of it, it holds
at least one function word (a table of paired words is not verse), and it is not a caption naming its
own notation. Saintsbury's book carries about 420 marked lines and 164 survive; the rest are foot
bars without stress marks, hexameter experiments, or partly marked.

Where a book marks beats only (acute), a bare syllable is read as a slack. Where it marks both
(macron/breve), a bare syllable is `x` and not scored.

## Marked, but not a scansion

The rule that governs what goes above: a ruler marks the stress of every syllable in a line. Books
that mark something else were tried and set aside.

- **Elizabeth Barrett Browning**, *The Art of Scansion* (1827; Gutenberg 78519): marks quantity, not
  stress. She was arguing with Uvedale Price about long and short syllables and marks *burnt* short.
  Scored 68% and read as a stress ruler she is simply wrong, because she is measuring something else.
- **Goswin König**, *Der Vers in Shaksperes Dramen* (1888): accents only the stresses that differ from
  modern English, *sphére*, *generál*. One accent to a line is not a scansion. Word-level evidence for
  Elizabethan stress, which is a different and possibly useful thing.
- **Robert Bridges**, *Poetical Works* (1912, Gutenberg 37804): macrons mark vowel quantity in his
  classical experiments.
- **Abbott**, *A Shakespearian Grammar* (1870; ~1,200 lines), **Mayor** (~2,000), **Verity**'s Pitt Press
  appendices, **Guest** in most of his book: foot bars, which mark where feet divide and not which
  syllable carries the beat. In a known foot the one implies the other, but that is an inference, not a
  mark.

## Verified, not yet extracted

| source | where | notation | lines | why not yet |
|---|---|---|---|---|
| Harlan Hatcher, *The Versification of Robert Browning* (1928) | archive.org `versificationofr0000harl` | a bar before the stressed syllable; bars split words | 241 | the poems are *Pauline*, *Sordello*, *The Ring and the Book*, none in the library, so no matching by letters; needs a reader that rejoins split words. Public domain in the US only: Hatcher died in 1998 |
| Lounsbury, *Studies in Chaucer* vols 1–2 (1892) | archive.org `studiesinchaucer0001loun_b2u0`, `studiesinchaucer0000thom` | acute = stress, grave = sounded -e, but OCR renders both as é | ~330 | the two marks cannot be told apart in the text |

## In the journals, verified, not yet extracted

A dozen articles, scattered, each with a few dozen marked lines; page images verified for the ones
marked so. Where an article exists as both a `jstor-` item and a `sim_` microfilm issue on archive.org,
the microfilm OCR keeps the accents and the JSTOR one strips them.

| article | where | lines | notation |
|---|---|---|---|
| J. B. Mayor, "Dr. Guest and Dr. Abbott on English Metre", Trans. Philological Soc. 1873-74 | archive.org `transactions-of-the-philological-society`, OCR lines 39305-40230, image-verified | ~100 barred, ~25 accented | acute + bars |
| W. W. Skeat, "On the Scansion of English Poetry", TPS 1895-98 | `transactionsphi05britgoog`, images only (OCR is noise), leaves n535-536 | 20 hexameters fully marked, 16 grouped | acute, grave, dots for feet |
| C. E. Whitmore, "A Proposed Compromise in Metrics", PMLA 41 (1926) | `publicationsofthemodlangasso41`, accents survive OCR | ~40 | acute + bars |
| F. M. Padelford, "The Scansion of Wyatt's Early Sonnets", SP 20 (1923) | `studiesinphilologyjournal20`, OCR 8979-9950, accents survive | ~40 | acute |
| John Erskine, "A Note on Whitman's Prosody", SP 20 (1923) | same item, OCR 20550-21100 | ~25 | acute + slashes |
| E. W. Scripture, "The Choriambus in English Verse", PMLA 43 (1928) | `publicationsofthemodlangasso43` | ~10 | acute |
| Karl Elze, notes on Othello, Richard II, Coriolanus, Antony, in Englische Studien 6-12 (1883-89) | `englischestudien11leipuoft` etc., bars survive, accents garbled | ~50 | bars, some acute |
| Poe, "The Rationale of Verse", Southern Literary Messenger 1848 | `sim_southern-literary-messenger_1848-10_14_10` and `_11` | ~30 | macron/breve + bars, partly kept |
| R. M. Alden, "The Time Element in English Verse", MLN 14 (1899) | `jstor-2917341`, image-verified | ~10 | bars only |

Leads not checked: Mayor's two further TPS papers (1875-79) and Ellis's replies; Walter Thomas,
"Milton's Heroic Line", MLR 2 (1907); Parry on Morris, MLN 44 (1929). The Princeton Prosody Archive
(prosody.princeton.edu) indexes ~600 works per keyword and is the best finding aid, though it has no
API and its page-text links are dead.

## Found on Gutenberg, verified, not yet extracted

| source | Gutenberg | notation | why not yet |
|---|---|---|---|
| Tom Hood, *Practical Guide to English Versification* (1877) | 51873 | spacing acute after the vowel, ~49 lines | the mark is not where the file was reported to have it; needs a look by hand |
| E. B. Browning, *The Art of Scansion* (letters of 1827, pub. 1916) | 78519 | macron/breve, ~24 verse lines, many partial | small; partial marking |
| Brooks and Hubbard, *Composition-Rhetoric* (1905) | 12088 | a row of `U` and `_` above each line, 26 lines | needs a two-row reader |
| W. F. Webster, *English: Composition and Literature* (1900) | 28097 | caret row above the stressed syllable, 25 lines | needs a two-row reader |

## Marks lost in digitisation

Books about prosody whose scansion did not survive into the text. A different edition or scan may hold it.

- Gerard Manley Hopkins, *Poems* (1918, ed. Bridges), Gutenberg 22403: the 1918 printed stress accents are gone; the transcriber's note admits it.
- Paull F. Baum, *The Principles of English Versification* (1922), Gutenberg 21342: the musical-notation scansions are `[Illustration]` placeholders; what remains is abstract schemes, not marks over words.
- Percival Leigh, Gutenberg 44802: the other edition's marks were transcribed inconsistently as circumflex, grave and diaeresis. Use 43397.
- Robert Bridges, *Poetical Works* (1912), Gutenberg 37804: 122 macron lines, but they mark vowel quantity in his classical experiments, not stress.

## Searched for on Gutenberg and not there

So nobody looks twice: Lanier, *Science of English Verse*; Gummere, *Handbook of Poetics*; Guest,
*History of English Rhythms*; Corson, *Primer of English Verse*; Bridges, *Milton's Prosody*; Mayor,
*Chapters on English Metre*; Omond; Kaluza (Dunstan tr.); Bright and Miller; Brewer, *Orthometry*;
Esenwein and Roberts; Carruth; C. E. Andrews; C. F. Johnson; C. M. Lewis; Liddell; Abbott; Lindley
Murray; Quackenbos; Bain; Kellogg; Hart; Brander Matthews; ten Brink; Poe, *Rationale of Verse*.
These may exist on archive.org or HathiTrust.

## Excluded

Alden, *English Verse* (1903), Gutenberg 32262, is not here because it names the metre of whole poems
rather than marking lines; `authorities.py` uses it for that.

## What the rulers say

Scored with `python3 marked.py`, reading each line in the foot the prosodist's own marks imply, which
is what a poem would have told the scanner:

| ruler | lines | stress | lines fully right |
|---|---|---|---|
| Schipper 1910 | 493 | 89.5% | 54.8% |
| Saintsbury 1910 | 164 | 78.6% | 38.5% |
| Brown 1851 | 77 | 89.8% | 62.3% |
| Latham 1841 | 40 | 91.8% | 71.1% |
| Leigh 1840 | 19 | 97.6% | 78.9% |
| Kirkham 1829 | 4 | 100% | 100% |
| Skeat 1894 | 11 | 80.0% | 30.0% |
| Guest 1882 | 65 | 81.2% | 24.6% |

These are the figures `rules.py` keeps as its baseline, with the rules in `RULES.md` that were kept.

A line is read at the length the prosodist's marks give it, as a poem's own measure would give it
in the pipeline: a line that comes out long is asked which word reads shorter (`scansion.asked`).

Saintsbury is the outlier, and the reason is worth knowing: on the syllables the dictionary fixes
outright, he agrees with it only 86.1% of the time, against 93-96% for the others. He marked what he
heard, argued that quantity mattered, and stacked both marks on syllables he called doubtful. His
figure measures his ear as much as the scanner.

Guest is the other soft ruler. His bars come through OCR as four different characters and sometimes
not at all, and his Chaucer is read with Middle English stress that the pipeline's modern
syllabification does not share; the 124 matched lines dropped for a syllable-count mismatch were
mostly that. The 65 that survive are worth having, especially the Milton, and worth weighing lightly.
