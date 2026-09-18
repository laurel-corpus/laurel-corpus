#!/bin/zsh
# Rebuild this repository from the working corpus.
#
# Everything here is generated: the TEI is written by pipeline/tei.py and the data files are copied from
# the built site. The repository was first assembled by hand, which meant it quietly fell behind the
# corpus -- it was still shipping a Southey whose first section was a modern publisher's cataloguing
# record, corrected in the working tree days earlier. This script is so that never happens again: run it,
# check the figures it prints against README.md, and commit.
#
#   ./assemble.sh                 # source defaults to ../Poetry Analysis
#   ./assemble.sh /path/to/site   # or name the working copy
set -e
SRC="${1:-$(cd "$(dirname "$0")/../Poetry Analysis" && pwd)}"
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -d "$SRC/pipeline" ] || { echo "no pipeline at $SRC"; exit 1 }

echo "== regenerating the TEI"
(cd "$SRC/pipeline" && python3 tei.py >/dev/null)

echo "== copying"
rm -rf "$HERE/tei"; mkdir -p "$HERE/tei"
cp "$SRC/site/tei/"*.xml "$HERE/tei/"
mkdir -p "$HERE/data/audio"
# editions.json is the provenance of every text: which printed edition stands behind the file, who
# transcribed it, and every correction this project made to it. docs/texts.md has pointed at it all
# along while the corpus shipped it nowhere, which left the one question a scholar asks first --
# what edition am I reading? -- documented and unanswerable.
for f in library.json cite.json metres.json stable.json editions.json; do cp "$SRC/site/data/$f" "$HERE/data/$f"; done
cp "$SRC/site/data/audio/"*.json "$HERE/data/audio/"

# The per-work measures: alliteration and assonance against a shuffled baseline, caesura, feminine
# endings, metre fit, lexical diversity. docs/measures.md described these for months while the corpus
# shipped none of them, so a reader following the documentation went looking for figures that were not
# here. They are 5.7 MB against 123 MB of TEI, which is a small price for the documentation being true.
rm -rf "$HERE/data/measures"; mkdir -p "$HERE/data/measures"
for f in "$SRC/site/data/works/"*.measures.json; do
  cp "$f" "$HERE/data/measures/$(basename "$f" .measures.json).json"
done

# The method travels with the corpus it produced, so the scripts are copied too. They are named one by
# one rather than globbed: the working pipeline also holds the deploy scripts, the dev server and a
# config file with a live password, none of which belong in a public repository.
for f in _paths.py teiread.py ingest.py catalog.py corrections.json analyze.py scansion.py tei.py \
         mono-corpus.json mono-stress.json metres.py authorities.py alden-matched.json \
         generic.py webster.py precision.py bench.py perline.py goldscore.py goldsplit.py marked.py \
         markedin.py rules.py probe.py readings.py poemmetres.py poem-metres.json segfix.py segmentation-findings.json; do
  cp "$SRC/pipeline/$f" "$HERE/pipeline/$f"
done
# Verse a prosodist marked by hand, in print, a century ago: the third ruler, and the one that reaches
# the early modern verse the two modern gold corpora barely touch. Small, public domain, and it ships.
# The rulers, the record of every rule tried against them, and the figures the battery compares with.
mkdir -p "$HERE/pipeline/marked"; cp "$SRC/pipeline/marked/"*.tsv "$SRC/pipeline/marked/SOURCES.md" "$SRC/pipeline/marked/RULES.md" "$SRC/pipeline/marked/baseline.json" "$HERE/pipeline/marked/"

# Only the files named above are copied, so nothing else can wander in. This repository used to carry a
# .gitignore listing node_modules and __pycache__, which is boilerplate from a code project and belongs
# nowhere near a corpus; the one thing it really guarded against was a stray Finder file, and sweeping
# them here is both smaller and harder to forget.
find "$HERE/tei" "$HERE/data" -name '.DS_Store' -delete 2>/dev/null || true

echo "== figures (check these against README.md and CITATION.cff)"
python3 - "$SRC" "$HERE" <<'PY'
import json, os, sys, glob
src, here = sys.argv[1], sys.argv[2]
lib = json.load(open(os.path.join(src, 'site/data/library.json'), encoding='utf-8'))
aud = json.load(open(os.path.join(src, 'site/data/audio/index.json'), encoding='utf-8'))
audit = json.load(open(os.path.join(src, 'site/data/audit.json'), encoding='utf-8'))
lines = audit['summary'].get('encoding', '').split()[0]
print('   works      %s' % format(len(lib), ','))
# library.json used to carry a 'sections' list per work; it now carries the count in
# stats.sections, and this line counted the old shape until the release of 18 September.
print('   poems      %s' % format(sum((w.get('stats') or {}).get('sections', 0) for w in lib), ','))
print('   lines      %s' % lines)
print('   recordings %s across %d works' % (format(sum(len(v) for v in aud.values()), ','), len(aud)))
print('   tei files  %d' % len(glob.glob(os.path.join(here, 'tei', '*.xml'))))
print('   measures   %d' % len(glob.glob(os.path.join(here, 'data', 'measures', '*.json'))))
print('   scripts    %d' % len(glob.glob(os.path.join(here, 'pipeline', '*.py'))))
PY
