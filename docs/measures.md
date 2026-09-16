# Measures

*Part of the [Laurel corpus](../README.md). The [method index](../METHOD.md) lists the other documents,
and terms are defined in the [glossary](glossary.md).*

Every work carries a set of measurements of its sound, its syntax and its vocabulary. They are in
`data/measures/<work>.json`, one file per work, and a few summary figures also appear under each work's
`stats` in `data/library.json`.

## The rule behind all of them

A number without a baseline says nothing. If you count how often a poem alliterates and report that it
does so in 27% of its lines, you have measured English rather than the poet, because English
alliterates. The question is always whether *this* poem does it more than its own words would by
accident.

Every figure of that kind is therefore reported three times over:

* **observed**, what the poem actually does
* **expected**, what it would do by chance
* **ratio**, the first divided by the second, where 1.0 means that the poem is doing nothing unusual

The baseline is built by taking the poem's own words, shuffling them across its own lines thirty times
over, and measuring again. Shuffling within the poem rather than against some general corpus of English
keeps the poet's vocabulary fixed, so that whatever remains is arrangement. A poet who simply likes
words beginning with *s* does not score as an alliterator; a poet who puts those words next to each
other does.

```json
"alliteration": {"observed": 0.273, "expected": 0.286, "ratio": 0.96, "ci": [0.264, 0.283]}
```

Akenside alliterates in 27% of his lines, would alliterate in 29% by chance, and so is alliterating
very slightly *less* than his own vocabulary would predict.

## Reading the intervals

`ci` is a 95% confidence interval: the range within which the true figure probably falls, worked out by
re-measuring the poem a thousand times over on random re-samples of its own lines.

It exists because a fourteen-line poem and a ten-thousand-line poem should not make equally confident
claims. A sonnet's interval will be wide and a long narrative poem's narrow, and comparing two works
whose intervals overlap is comparing noise.

## What is measured

### Sound

| | |
|---|---|
| **alliteration** | share of lines in which two or more content words begin with the same consonant, against the shuffled baseline |
| **assonance** | the same, for the stressed vowel rather than the first consonant |

### The line

| | |
|---|---|
| **caesura** | the strong pause inside a line. `share` is how many lines have one, `mean_position` is how far along the line it falls as a fraction, and `thirds` splits them into early, middle and late |
| **feminine** | `rate` is the share of lines ending on an unstressed syllable, so an iambic pentameter running to eleven syllables rather than ten |
| **meter_fit** | how closely the poem's lines follow the metre named for it, averaged over the lines |
| **mode_share** | `mode` is the poem's commonest line length in syllables and `rate` is the share of lines at that length. A poem in a strict measure scores near 1.0; a poem in varied measures scores low, which is itself the finding |

### Vocabulary

| | |
|---|---|
| **mtld** | how varied the vocabulary is. The obvious measure, unique words over total words, falls as any text lengthens and so ends up measuring length. MTLD instead reads through the text and records how far it gets before variety drops below a threshold of 0.72, forward and backward, averaged ([McCarthy and Jarvis 2010](https://doi.org/10.3758/BRM.42.2.381)) |
| **ttr_raw** | the plain unique-over-total figure, kept alongside so that the difference is visible |
| **function_share** | share of words that are closed-class: *the*, *of*, *and*, the small fixed set that English does not add to. A high share indicates a plainer, more spoken style |
| **function_profile** | the twenty commonest of those, per 1,000 words |

### Form

| | |
|---|---|
| **scheme_entropy** | one number for how many different stanza forms a book uses, in bits. A book entirely in sonnets scores 0, because knowing that you are in that book tells you the form. A book that changes shape constantly scores high |
| **schemes_distinct** | how many different rhyme schemes appear |

### Housekeeping

| | |
|---|---|
| **coverage** | share of the poem's words that the pronouncing dictionary knows. Everything above rests on this, so it is reported rather than assumed |
| **lines**, **tokens** | how much text the figures were taken over |
| **template** | the metrical shape the measurements were taken against |
| **sections** | the same figures again, poem by poem, for works that hold many |

## What is in library.json instead

`data/library.json` carries a smaller set under each work's `stats`, intended for the catalogue rather
than for analysis:

| | |
|---|---|
| `lines`, `stanzas`, `sections` | sizes |
| `mean_syllables`, `syllable_mode` | line length |
| `distinct_end_words` | how many different words the work ends lines on |
| `hapax_share` | of those, the share used only once. A high figure means that the poet keeps finding new rhymes; a low one means that the same handful come round again |
| `top_schemes`, `top_end_words` | the commonest forms and rhyme words |
| `mean_meter_fit` | average agreement between the lines and the work's metre |
| `glossary_words` | how many words the work has a gloss for |
| `drifted_pairs` | pairs the poet rhymed that a modern dictionary does not, such as *love* and *prove*. These are shifts in pronunciation rather than errors, and counting them is a rough measure of how far the work's sound has moved from ours |
| `suspect_lines` | lines whose syllable count departs far enough from the work's metre to be worth a human look. Some are scanning faults in the source text and some are the poet doing something deliberate, and the count does not distinguish between them |
