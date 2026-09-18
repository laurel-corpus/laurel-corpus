"""The scanner's own reading of every line, for the page to show.

analyze.py writes each line's syllables and the stress the words fix; metres.py settles each poem's
foot and length. Neither wrote down how the scanner reads the line in that metre, and the reader page
was filling the open syllables in by plain alternation, so that 'the fire indeed from whence they
caused be' came out FROM whence THEY. This asks the scanner and keeps the answer: one more field on
the line record, the template the line is read by, '+' for a beat and '-' for a slack, only where the
poem's metre is settled and the reading matches the syllables analyze.py counted. An eleventh field
holds a second reading where the scanner could not separate two, so the page can show the line reads
two ways instead of choosing for the reader.

Runs after metres.py and before finish.py:

    python3 readings.py            every work
    python3 readings.py slug ...   only these
"""
import io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _paths import WORKS, DATA
import scansion as S
from analyze import TOKEN, norm

READ = 10   # the field's index on the line record; analyze.py's record ends at 9
READ2 = 11  # a second reading the scanner could not separate from the first, where the line has one

def evidence_of(text, syls, codes):
    """The scanner's evidence for a line, on the syllables analyze.py counted rather than its own.

    The two count alike nearly always, but analyze.py sounds an -ed or elides a vowel under the poem's
    pressure and the page shows its syllables, so the reading has to be made on those or the marks
    slide. Each word takes as many of the counted syllables as spell it, and votes as evidence() does.
    """
    letters = lambda s: re.sub(r"[^a-z']", '', s.lower())
    out, starts, breaks, k = S.Evidence(), [], [], 0
    for tok, brk in S.edges(text):
        for part in tok.split('-'):
            core = re.sub(r"^[^a-z']+|[^a-z']+$", '', norm(part))
            want = len(letters(part))
            if not want or k >= len(syls): continue
            j, got = k, 0
            while j < len(syls) and got < want:
                got += max(1, len(letters(syls[j]))); j += 1
            sy = [(syls[i], codes[i]) for i in range(k, j)]
            k = j
            if not sy: continue
            starts.append(len(out))
            out.extend(S.votes(core, sy))
        if brk and out: breaks.append(len(out) - 1)
    if k != len(syls): return None
    out.starts, out.breaks = tuple(starts), tuple(breaks)
    return out

METRES = {}

def read_work(w):
    """One work's readings, for a pool worker: returns (slug, lines read, lines in all) or None."""
    slug = w['slug']
    path = os.path.join(WORKS, slug + '.lines.json')
    if not os.path.exists(path): return None
    ann = json.load(open(path, encoding='utf-8'))
    work = json.load(open(os.path.join(WORKS, slug + '.json'), encoding='utf-8'))
    secs = (METRES.get(slug) or {}).get('sections', {})
    n_read = 0
    for rec in ann['lines']:
        while len(rec) <= READ2: rec.append(None)
        rec[READ] = rec[READ2] = None
        sec = work['sections'][rec[0]]
        m = secs.get(sec['id'])
        if not m or len(m) < 5 or not m[3] or m[3] not in S.FEET: continue
        foot, feet = m[3], m[4]
        text = sec['stanzas'][rec[1]][rec[2]]
        syls, codes = rec[8] or [], rec[7] or ''
        if not syls or len(syls) != len(codes): continue
        ev = evidence_of(text, syls, codes)
        if ev is None or len(ev) != len(syls): continue
        # the length the poem's own pass would give this line, then the best reading of that length
        n = S.best_line(ev, foot, prefer=feet, cost=False)[2]
        tpl = S.reading(ev, foot, prefer=feet, feet=n or None)
        if not tpl or len(tpl) != len(syls): continue
        rec[READ] = tpl.replace('1', '+').replace('0', '-')
        alt = S.second_reading(ev, foot, prefer=feet, feet=n or None)
        if alt: rec[READ2] = alt.replace('1', '+').replace('0', '-')
        n_read += 1
    json.dump(ann, open(path, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
    return slug, n_read, len(ann['lines'])

def main(only):
    global METRES
    METRES = json.load(open(os.path.join(DATA, 'metres.json'), encoding='utf-8'))
    lib = json.load(open(os.path.join(DATA, 'library.json'), encoding='utf-8'))
    works = [w for w in lib if not only or w['slug'] in only]
    total = read = 0
    # the works are independent and each writes its own file, so they go to a pool of workers
    import multiprocessing as mp
    with mp.get_context('fork').Pool(max(1, mp.cpu_count() - 2)) as pool:
        for r in pool.imap_unordered(read_work, works, chunksize=1):
            if not r: continue
            slug, n_read, n = r
            read += n_read; total += n
            print('%-24s %6d of %6d lines read' % (slug, n_read, n), flush=True)
    print('%s of %s lines carry the scanner\'s reading' % (format(read, ','), format(total, ',')))

if __name__ == '__main__':
    main(set(sys.argv[1:]))
