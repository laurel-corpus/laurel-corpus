# Canonical references and permanent identity

*Part of the [Laurel corpus](../README.md). The [method index](../METHOD.md) lists the other documents,
and terms are defined in the [glossary](glossary.md).*

A citation has to name the edition, not only the work. "The Iliad, line 1" is not a reference, because
texts differ. The scheme used here follows CTS, which settled this question for classical literature,
and it uses the same four parts:

```
urn:laurel:eng:shakespeare.shakespeare-sonnets.pg1041:18.1-18.4
               author      work                edition passage
```

The passage is the reference that a scholar would actually write. Sonnets, cantos and books are cited
by number, and a titled lyric by its own stable name. Ranges are written `18.1-18.4`.

References resolve at `https://laurelpoetry.com/cite.html?urn=...`, and with `&format=json` or
`&format=text` they return the passage itself, so that something other than a browser can follow a
citation.

Each poem also has a permanent identifier (`L00036`), recorded in `data/stable.json` and carried in the
TEI as `@n`. Identifiers are never reused. When a poem's address changes, the old one is retired rather
than dropped, and a reference written against it goes on resolving.
