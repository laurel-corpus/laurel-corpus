# The audit

*Part of the [Laurel corpus](../README.md). The [method index](../METHOD.md) lists the other documents,
and terms are defined in the [glossary](glossary.md).*

`audit.py` runs nineteen checks in one pass. Each answers a question with a yes or with a list, so that
the report can be read in a minute and acted on without re-deriving anything. Nothing it does changes a
file; it only looks.

It exists because the same class of fault kept turning up by hand: a form asserted where the data does
not carry it, an illustration pointing past the end of its section, an editor's note citing a line that
is not there.

## What it checks

| | |
|---|---|
| Assets | every image the data names is present; and the reverse, images that nothing names |
| Structure | sections that are not poems; recorded line counts against actual ones |
| Pointers | illustrations and commentary point inside the text they are attached to |
| Identity | every poem still resolves to its permanent id (see [references](references.md)) |
| Glossary | glossed words actually occur in the work |
| Catalogue | every work in the index has its text, lines, metre and measures |
| Attribution | the credit each licence requires is present where it is required |
| Encoding | mojibake and stray control characters |
| Form | the stated form against the measured rhyme scheme |
| Verse | lines out of step with their section; rhyme schemes that would not resolve |
| Site | pages that search engines can reach, reconciled against the sitemap; near-duplicate pages |
| Display | figures a page asks for but the data does not carry; text contrast in both themes |
| Sources | with `--links`, every external source URL still answers |

## What it found last

There were 592 findings on 13 September 2026, and they are kept on record rather than silently cleared:

| | |
|---|---|
| 463 | glossary: a glossed word whose spelling in the text differs from the headword matched |
| 61 | commentary: notes keyed to sections this corpus names differently, so they do not appear |
| 23 | orphaned images |
| 15 | lines out of step with their section |
| 12 | page reachability |
| 10 | near-duplicate pages |
| 7 | sections not recognised as poems |
| 1 | a stated form the measured rhyme does not support |

**The commentary findings have deliberately not been repaired automatically.** A fuzzy matcher run
against them mapped two different *Evangeline* keys onto one section, which would have put 494 notes on
the wrong poem. Notes that are missing are a smaller fault than notes that are wrong, so they stay
missing until each is settled by hand.
