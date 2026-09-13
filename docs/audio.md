# Audio timings

*Part of the [Laurel corpus](../README.md) — see the [method index](../METHOD.md).*

Where `data/audio/<work>.json` exists, each poem carries the second at which every line is spoken in a
LibriVox recording, along with the reader's name and the project.

Alignment is by transcription: the recording is transcribed, the transcript matched against the known
text, and the matched words carry their timings back to the lines. A reading is kept only when at least
90% of the poem's words are found in it, which rejects bad microphones, bad rooms, heavy stumbling, and
readers working from a different edition. The rate at which readings pass depends on how a book was
recorded: above 90% for the single-reader projects, nearer 65% where LibriVox has only a collaborative
recording, and 78% taken across the library as a whole.

Two offsets travel with each poem. `start` is where the poem's first line begins, after the spoken
LibriVox announcement. `title`, where present, is the span in which the reader names the poem, which may
fall on either side of that announcement. No audio is included here and none is altered; these are
timings into files that remain whole on the Internet Archive.
