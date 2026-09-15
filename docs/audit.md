# The audit

*Part of the [Laurel corpus](../README.md) — see the [method index](../METHOD.md). Terms are defined in
the [glossary](glossary.md).*

`audit.py` is nineteen checks in one run. Each answers a question with a yes or a list, so a report can be
read in a minute and acted on without re-deriving anything. Nothing it does changes a file; it only looks.

It exists because the same class of fault kept turning up by hand: a form asserted where the data does not
carry it, an illustration pointing past the end of its section, an editor's note citing a line that is not
there.

## What it checks

| | |
|---|---|
| Assets | every image the data names is present; and the reverse, images nothing names |
| Structure | sections that are not poems; recorded line counts against actual ones |
| Pointers | illustrations and commentary point inside the text they are attached to |
| Identity | every poem still resolves to its permanent id — see [references](references.md) |
| Glossary | glossed words actually occur in the work |
| Catalogue | every work in the index has its text, lines, metre and measures |
| Attribution | the credit each licence requires is present where it is required |
| Encoding | mojibake and stray control characters |
| Form | the stated form against the measured rhyme scheme |
| Verse | lines out of step with their section; rhyme schemes that would not resolve |
| Site | pages search engines can reach, reconciled against the sitemap; near-duplicate pages |
| Display | figures a page asks for but the data does not carry; text contrast in both themes |
| Sources | `--links`: every external source URL still answers |

## What it found last

592 findings on 2026-09-13, and they are kept rather than silently cleared:

| | |
|---|---|
| 463 | glossary — a glossed word whose spelling in the text differs from the headword matched |
| 61 | commentary — notes keyed to sections this corpus names differently, so they do not appear |
| 23 | orphaned images |
| 15 | lines out of step with their section |
| 12 | page reachability |
| 10 | near-duplicate pages |
| 7 | sections not recognised as poems |
| 1 | a stated form the measured rhyme does not support |

**The commentary findings have not been auto-repaired, deliberately.** A fuzzy matcher run against them
mapped two different *Evangeline* keys onto one section, which would have put 494 notes on the wrong poem.
Notes missing is a smaller fault than notes lying, so they stay missing until each is settled by hand.
