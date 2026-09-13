# Measures

*Part of the [Laurel corpus](../README.md) — see the [method index](../METHOD.md).*

Every work carries a set of sound, syntax and lexicon measures. The rule throughout: **a number without a
baseline says nothing.** Poems alliterate because English alliterates; the question is whether this poem
does it more than its own words would by chance.

## Against a baseline

**Alliteration** is the share of lines where two or more content words share a first consonant.
**Assonance** is the same for the stressed vowel. Each is reported observed, and again under a null:
the section's own words shuffled across its own lines, 30 times. The ratio and a z-score come with it.
Shuffling within the section — not against some general English corpus — keeps the poet's vocabulary
constant, so what is left is arrangement.

## With an interval

95% bootstrap intervals, 1,000 resamples over lines, on feminine endings, metre fit, alliteration, and the
share of lines at the poem's modal length. A poem of fourteen lines and a poem of ten thousand do not
deserve the same confidence, and the interval is how that shows.

## The rest

| | |
|---|---|
| **Caesura** | position of the first strong internal pause as a share of the line, and whether it falls early, middle or late |
| **MTLD** | lexical diversity, threshold 0.72, forward and backward averaged ([McCarthy and Jarvis 2010](https://doi.org/10.3758/BRM.42.2.381)) — used because plain type-token ratio falls as a text lengthens and so only measures length |
| **Function profile** | share of tokens that are closed-class, plus the 20 commonest per 1,000 tokens |
| **Scheme entropy** | Shannon entropy in bits over a work's stanza rhyme schemes — one number for how various a book's forms are |
| **Coverage** | share of tokens found in the pronouncing dictionary. This is the confidence figure for everything scansion says about the work |

Per-line derivations are kept beside the summary: for each word its phones, syllables, stress, and
**where each came from** — dictionary, dictionary via a spelling variant, spelling analogy, or vowel-group
count. A claim inherits the weakest source under it, and this is how that stays visible.

416 works carry measures. The random seed is fixed, so a rebuild reproduces the same figures.

## Part of speech

All 417 works are tagged with NLTK's averaged perceptron tagger, one character per token, collapsed to
nine classes (noun, verb, adjective, adverb, pronoun, determiner, preposition/conjunction, modal, other).
Tags are used two ways: to weight a monosyllable's stress in [scansion](scansion.md) — a preposition is
likelier to be the unstressed half of a foot than a noun — and to drive the reader's syntax view. The
tagger was trained on modern prose, which is the honest limit: it handles inversion and archaic verb
forms less well than the poetry it is run on.
