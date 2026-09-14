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
for f in library.json cite.json metres.json stable.json; do cp "$SRC/site/data/$f" "$HERE/data/$f"; done
cp "$SRC/site/data/audio/"*.json "$HERE/data/audio/"

# The method travels with the corpus it produced, so the scripts are copied too. They are named one by
# one rather than globbed: the working pipeline also holds the deploy scripts, the dev server and a
# config file with a live password, none of which belong in a public repository.
for f in _paths.py teiread.py ingest.py catalog.py corrections.json analyze.py scansion.py tei.py \
         mono-corpus.json mono-stress.json metres.py authorities.py alden-matched.json \
         generic.py webster.py precision.py bench.py goldscore.py goldsplit.py; do
  cp "$SRC/pipeline/$f" "$HERE/pipeline/$f"
done

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
print('   poems      %s' % format(sum(len(w['sections']) for w in lib), ','))
print('   lines      %s' % lines)
print('   recordings %s across %d works' % (format(sum(len(v) for v in aud.values()), ','), len(aud)))
print('   tei files  %d' % len(glob.glob(os.path.join(here, 'tei', '*.xml'))))
print('   scripts    %d' % len(glob.glob(os.path.join(here, 'pipeline', '*.py'))))
PY
