# Rules from the literature, tested

Every rule proposed by the prosodists and the computational scanners is tried here one at a time,
against the rulers in this directory, Haider's development half (`perline.py --train`), and
`precision.py`, and is kept only if it improves the first without harming the last. The held-out
control is scored once, after a rule is kept, never while choosing. What was tried and rejected is
recorded with the same care as what was kept, so nobody tries it twice.

The literature survey behind these is summarised in the pipeline's git history and at
`docs/scansion.md`; the primary sources are Halle & Keyser 1971, Kiparsky 1975 and 1977, Hanson &
Kiparsky 1996, Hayes 1983 and 1989, Hayes, Wilson & Shisko 2012, Attridge 1982, Bridges 1921, Groves
2013, and Tarlinskaja.

## Kept

**The last foot must rise** (`_place()` in scansion.py). An inverted or empty fifth foot costs four
times a substitution elsewhere. Bridges: inversion is "most common in the first foot ... most rare in
fifth." Groves excludes fifth-foot reversals and swaps by rule. Hayes, Wilson and Shisko count a
falling final foot in about half of one per cent of lines and fit it a weight of two. Result: Schipper
52.5% → 52.7% of lines fully right, Saintsbury 37.3% → 37.9%, Leigh 73.7% → 78.9%, Haider development
74.3% → 74.6%; nothing worse; precision unchanged.

**A falling metre takes no initial inversion** (`_place()`). Halle and Keyser: trochaic verse takes an
extra initial syllable but never an initial iamb. The scanner gave an inverted first foot the same
discount in every metre, so a trochaic line could open on an iamb for less than an inversion costs
anywhere else, and a line that opens 01 in a poem of trochees was read as trochaic with a licence
instead of as what it is. Now charged four times a substitution, like the last foot; a spondee or
pyrrhic opening a trochaic line keeps the discount. Result: Brown 61.0% → 62.3% of lines, Guest
stress 80.8% → 81.2%, Haider development 74.6% → 75.0%, sonnets wrongly not iambic 0.5% → 0.2%,
blank verse unchanged; Schipper 54.4% → 54.6%, Saintsbury and Latham within a syllable. Control,
scored once after: stress in the poem's metre 92.8% → 93.1%, lines every mark right 74.5% → 75.0%.

The first run of this rule showed Schipper 52.7% → 51.9% and Saintsbury 37.9% → 37.3%, and the
losses were the ruler's, not the rule's: 16 of Schipper's 19 worse lines and 6 of Saintsbury's 10 were
lines marked `-+...` that `foot_of` filed as falling because a displaced accent lands the remaining
beats on even positions. They are Schipper's shifted-accent specimens ('Surprised with blind flame
and to her mind') and Tennyson's 'Dying Swan', rising poems both, which the pipeline reads in the
rising foot. `foot_of` now files a line that opens slack-then-beat as rising, which is the same
observation from the ruler's side, and the figures above are under that ruler. Schipper's baseline
rose from 52.7% to 54.4% by the fix alone.

**An inversion after a phrase break is as ordinary as one at the head** (`edge_inversions()`).
Kiparsky licenses an inversion after a syntactic break; the scanner charged one after a comma or a
full stop exactly what it charged one in the middle of a phrase. Punctuation stands in for the break,
which is why evidence() now carries it. The relief is the complement of the head discount, so that
'To be, or not to be: THAT is the question' costs what an inverted opening costs; no value was
swept, since Haider's gold has no punctuation to sweep it on. Result: Schipper stress 89.2% → 89.4%,
Saintsbury 78.3% → 78.4%, Brown one syllable down on a word-list caption; Haider development and
precision unchanged. On Schipper ten readings changed, seven for the better, two for the worse. The
control, scored once after, is unchanged at 93.1% and 75.0%, since its gold has no punctuation either.

**An inversion straight after a stress, with no break, costs double** (`POST_TONIC` in
`edge_inversions()`). The other half of the same constraint: Hayes, Wilson and Shisko find the
post-tonic inversion the rarest of all and weight it 1.7 to 2.0. Counted where the syllable before an
inverted foot is a stress the words supply, of either kind, and no punctuation stands between. Result:
Haider development 75.0% → 75.4%, Saintsbury stress 78.4% → 78.6%, nothing else moved, precision
unchanged; four ruler readings changed, three for the better. The gain on Haider is the more telling
because its gold has no punctuation, so every inversion after a stress counts as post-tonic there,
including the ones a comma would have licensed. Control, scored once after: lines every mark right
unchanged at 75.0%, stress in the poem's metre 93.1% → 92.9%, seven syllables, on gold with the same
blindness to punctuation.

**A line re-read to the poem's length is weighed as its neighbours are** (`refit()`, `votes()`). When
a long line was asked which word reads shorter, the re-reading gave every monosyllable a flat weight
instead of the learned table's opinion, and a word cut to one syllable kept the fixed stress of the
first syllable it used to have, so 'our' read short arrived as a beat at full weight. Both paths now
share one function, and a word cut to one syllable takes a monosyllable's opinion. Not a rule from
the literature but a fault the harness could not see until it read lines at the asked length. Haider
development 75.1% → 75.6%, Skeat a syllable better, nothing else moved, precision unchanged.
Control, scored once after, read at the asked length: syllable count agrees 95.0% → 98.0%, 451 lines
scored for 436, 338 fully right for 327 (74.9%), stress in the poem's metre 92.9%; end to end, a wrong
count counting as a wrong line, 70.5% → 73.2%.

**A line may swap the length of two feet, not one** (`MAX_SWAP` in `_feet()`). One swap was enough
for a stray anapaest in an iambic line and not for the loose four-beat verse of the ballads and
Christabel: 'Though the breath of these flowers is sweet to me' needs three, was read as six iambs,
and Longfellow's Reaper lost its four-and-three and was named tetrameter. Each swap still costs a
unit, so the plain reading wins wherever it fits; the iambic template count goes from 13,357 to
33,739. Result: Saintsbury 37.9% → 38.5% of lines, Schipper 54.6% → 54.8% and stress 89.4% → 89.5%,
Haider development 75.6% → 75.7%, blank verse wrongly not iambic 0.7% → 0.6%, nothing worse. Two
changes went in beside it that the battery cannot see: `pattern_of` tries the two commonest lengths
in each stanza position, so the Reaper is named common measure; and `readings.py` holds a line's
reading to the length the poem's own pass settled, so a four-beat line is no longer shown with six.

**Withdrawn the same night.** On the corpus rebuild, 290 poems lost their metre: with two swaps the
iambic foot absorbs an anapaestic poem, and the poem-level foot decision, which the rulers never test
(they read each line in a foot already given), fails. Barnes's 'Childhood' is anapaestic trimeter at
84% with one swap and nothing with two. `MAX_SWAP` is back at one; the namer's and the readings'
changes stay. To be tried again once the foot decision charges swaps apart from the line reading, and
once the battery has a poem-level check for anapaestic verse beside its sonnets and blank verse.

## Rejected

**The pyrrhic-and-spondee as one unit.** Groves's "swap": the two feet are one figure, in 7-9% of
Shakespeare's lines, and the scanner charged them as two substitutions, 2.4 units against a scale of
5. Costing the pair as one made things slightly worse almost everywhere: Schipper 52.5% → 51.9%, Latham
71.1% → 68.4%, Haider 74.3% → 73.2%. The reason is that the rule has a condition the change did not
carry: the two syllables must be split by exactly a word break, and the spondee's second syllable must
be a genuine stress. Cheaper everywhere means taken where no prosodist would. To be tried again with
the licence, which needs word boundaries at the template level.

**A polysyllable's own stress in a weak place after the first foot** (Kiparsky's stress maximum in W;
Hayes, Wilson and Shisko's lexical-stress constraints). An inversion after the first foot was charged
two and a half times the usual when the stress it accommodates is a polysyllable's, with no
phrase-break licence because punctuation does not reach the scanner. Schipper 52.7% → 51.9% of lines,
stress 88.8% → 88.1%; Saintsbury and Guest each down a tenth; blank-verse precision 0.7% → 0.9% wrong;
Haider development 74.6% → 74.8%. On Schipper the rule changed 22 readings, 3 for the better and 18
for the worse, and the examples are of a kind: 'How for his house-keeping and high renowne', where
Schipper marks KEEP in the weak place and the rule pushed the scanner into a headless reading with a
swap to avoid it. A handbook's specimens are chosen to show the irregularities, so a rule that
forbids them is measured on the lines that break it. Rejected. Might be tried again with the
phrase-break licence, once punctuation is kept.

**Foot two is the second-rarest place for an inversion** (Bridges, Groves). An inverted second foot
charged 2.5 against 1.0 for the third and fourth. Schipper 54.6% → 54.0% of lines, stress 89.2% →
88.9%; Saintsbury stress 78.3% → 78.0%; Brown a syllable down; blank verse wrongly not iambic 0.7% →
0.9%; Haider development 75.0% → 75.3%, Guest stress up 0.3. On Schipper the rule changed nine
readings, none for the better: 'The next morrow with Phoebus' lamp the earth' is marked with MORrow
in the second foot and the scanner now reads 'the NEXT morROW'. Rejected: the event is rare in verse
at large, which is where Haider's gain comes from, but every one of Schipper's specimens of it is a
line from a real poem, and the blank verse the rule loses is Milton's.

**No consecutive inversions** (Groves; Hayes, Wilson and Shisko's 1.35 for two stressless strong
positions in a row). Two inversions side by side charged one unit more than two apart. Changed one
reading in the whole battery, Schipper's 'Long continuance and increasing', for the worse; every other
figure identical. The scanner seldom chooses consecutive inversions as it is, since two substitutions
already cost more than most alternatives. Rejected as doing nothing.

**The swap with its licence.** Tried again with Groves's condition in full: a pyrrhic on syllables the
words leave weak, then a spondee, split at a word boundary, the spondee's second syllable a stress the
words supply; the pair relieved of part of its cost. The relief was chosen on Haider's development
half, which has word boundaries and stress though no punctuation, and every value was worse than none:
74.99% of lines at no relief, 74.94% at 0.6, 74.46% at 1.2, 71.33% at 1.8, 63.54% at 2.4. On the rulers
at 1.2, fourteen readings changed, six better and six worse. Rejected. What it showed: Haider's
annotators, like the scanner, put the beat on the promoted function word, and the prosodists are
divided, so part of the 'refused pyrrhic' count is a difference of convention between rulers.

## Already obeyed

**A feminine ending must fall.** Hayes, Wilson and Shisko fit "no extrametrical syllable without a
fall" at a weight of 15, which is to say it does not happen. Charged at five times an ordinary mismatch
the rule changed nothing: every figure identical to the baseline. On 36 ruler lines a template with a
rising extra syllable was on offer, and the scanner chose it on none of them with the rule switched
off, because the mismatch on the final syllable already costs more than the reading it would buy. The
scanner obeys this rule without being told; the code came out again.

## The harness

**Lines are read at the length the metre asks.** The benchmarks scored each line alone, so nothing
ever asked a long line which word reads shorter, and 'our' counted two syllables against every
annotator's one: of 147 development lines with a wrong count, 79 were an elidable word counted long
and 41 of those were 'our'. `scansion.asked()` re-reads a line to the gold's length the way `analyse()`
re-reads it to the poem's, and the harness scores what the reader is shown. Haider's development half
went from 2,079 lines scored to 2,155, and every-mark-right from 75.4% to 75.1%, the admitted lines
being the harder ones. In the corpus, 'our' is needed at two syllables in 6% of the 14,345 settled
iambic lines that can tell and at one in 82%; the pipeline shortens it when the poem asks, so nothing
there changes.

## Not yet tried, in the order the evidence suggests

1. **Drop any stress-maximum rule.** Hayes, Wilson and Shisko tested seventeen versions and none was
   selected. The scanner has none, and should not acquire one.
