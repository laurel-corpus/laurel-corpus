# Sources and tools

*Part of the [Laurel corpus](../README.md). The [method index](../METHOD.md) lists the other documents,
and terms are defined in the [glossary](glossary.md).*

Everything that this corpus is built from is public, and it is named here so that any claim in the
corpus can be checked against the thing it came from.

## Texts

| | |
|---|---|
| [Project Gutenberg](https://www.gutenberg.org/) | every text in the corpus; each work's TEI names its ebook number |
| [Internet Archive](https://archive.org/) | scanned school editions whose OCR supplies some of the editorial notes |

## Language data

| | |
|---|---|
| [CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict) | syllable division and word stress; distributed with [NLTK](https://www.nltk.org/) |
| [Webster's Revised Unabridged Dictionary, 1913](https://www.gutenberg.org/ebooks/29765) | word definitions and etymologies (PG ebook 29765) |

## Prosody

| | |
|---|---|
| [For Better For Verse](https://github.com/waynegraham/for_better_for_verse) | University of Virginia; poems scanned by hand by a prosodist. Used **only** to score this corpus's scansion, never as a source. Its `+ - x` notation is adopted here so that the two can be compared directly. |

## Audio

| | |
|---|---|
| [LibriVox](https://librivox.org/) | volunteer readings, dedicated by their readers to the public domain |
| [Internet Archive](https://archive.org/) | hosts the recordings; the corpus stores timings only, and streams rather than copies |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | transcription, used to align a recording against the known text |

## Standards

| | |
|---|---|
| [TEI P5](https://tei-c.org/guidelines/p5/) | the encoding of every work in `tei/` |
| [CTS / the CITE Architecture](https://cite-architecture.github.io/) ([URN spec](https://cite-architecture.github.io/ctsurn_spec/)) | the model for canonical references: author, work, **edition**, passage |
| [CFF](https://citation-file-format.github.io/) | `CITATION.cff`, so that this corpus can be cited as a dataset |
| [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | the license on the apparatus; the texts themselves are public domain |

## Illustrations

The portraits and work illustrations shown on [laurelpoetry.com](https://laurelpoetry.com) come from
[Wikimedia Commons](https://commons.wikimedia.org/). They are accepted only where the file's license is
public domain or CC0 and rejected otherwise, and the file and its Commons page are recorded for each. No
images are included in this repository.
