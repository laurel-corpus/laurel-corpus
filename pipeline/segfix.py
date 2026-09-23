"""Apply the segmentation review: the findings in segmentation-findings.json, made against the
Gutenberg texts, on how each collection was cut into poems.

ingest.py cuts a book at its headings, and a book's headings lie: a table of contents reads like a
list of poems, a play's speaker names read like titles, and an attribution line under two sonnets
reads like one. The review (a checked reading of the 112 largest collections, findings with the
lines that prove them) records what to do about each: drop a section that is not a poem, keep only
the stanzas that are, split two poems joined under one heading, rejoin a dialogue poem cut at its
speakers, or give back a title the parse took for a subtitle. This applies those to the parsed works, and runs after ingest.py and before analyze.py,
because ingest rebuilds the works from the sources and would otherwise undo it.

    python3 segfix.py            say what would change
    python3 segfix.py --write    change it (the works are backed up beside the findings first)

A finding it cannot apply exactly (a poem missed altogether, whose text the review did not carry)
is reported and left alone.
"""
import io, json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _paths import WORKS

FINDINGS = os.path.join(HERE, 'segmentation-findings.json')
slugify = lambda x: re.sub(r'[^a-z0-9]+', '-', str(x).lower()).strip('-')

def uniq(base, taken):
    sid, k = base or 'poem', 2
    while sid in taken: sid = '%s-%d' % (base, k); k += 1
    taken.add(sid); return sid

def merged_title(note):
    """The poem's title as the review's note gives it, for a poem whose heading was lost."""
    m = re.search(r'the (?:eclogue|dialogue poem|poem) (.+?)(?: \([^)]*\))?, cut', note) or re.search(r'^(\w[\w\' ]+?), cut at', note)
    return m.group(1).strip() if m else None

def fid(r):
    """A stable name for one finding, so it is applied once and only once."""
    return '%s/%s/%s' % (r.get('work'), r.get('section'), ','.join(sorted((r.get('fix') or {}).keys())))

def apply(work, recs, log):
    secs = work['sections']; by = {s['id']: s for s in secs}; ids = set(by)
    changed = 0
    # Applied findings are recorded on the work and never applied twice. Most of these operations fail
    # harmlessly on a second run -- a dropped section is not found, a split index is out of range -- so
    # segfix looked idempotent for a year. keep_stanzas does not fail: its indices are written against
    # the ORIGINAL numbering, and run again over the already-corrected text it keeps a different and
    # wrong subset. Re-running it over Burns silently ate the Goldsmith epigraph and a nine-line stanza
    # out of Halloween, a day after Halloween was fixed, and nothing reported a thing.
    done = set(work.get('segfix') or [])
    for r in recs:
        if fid(r) in done: continue
        fix, sid = r.get('fix') or {}, r['section']
        if 'retitle_after_previous' in fix:
            # A work-level fix, so section is '*'. Petrarch's volume prints each sonnet in several
            # competing verse translations, and every translator's name stands as its own heading:
            # 165 of 558 sections, headed 'Macgregor', 'Nott', 'Wrangham'. The parser read each as a
            # new poem, so the contents list shows forty-four poems called Macgregor and the sonnet
            # they translate is the untitled one above them. The heading is real and worth keeping;
            # it is the poem's title that is missing from it.
            names = set(fix['retitle_after_previous'])
            last = None
            for sec in secs:
                t = (sec.get('title') or '').strip()
                if t in names:
                    if not last: continue
                    sec['title'] = '%s (%s)' % (last, t)
                    sec['short'] = sec['title'][:18]
                    old_id = sec['id']
                    ids.discard(old_id)
                    sec['id'] = uniq(slugify(sec['title']), ids)
                    by.pop(old_id, None); by[sec['id']] = sec
                    changed += 1
                elif t:
                    last = t
            continue
        if sid not in by: log.append('  %s: section %s not found' % (work['slug'], sid)); continue
        s = by[sid]
        if 'drop' in fix:
            secs.remove(s); del by[sid]; changed += 1; continue
        if 'keep_stanzas' in fix:
            keep = [i for i in fix['keep_stanzas'] if 0 <= i < len(s['stanzas'])]
            if not keep: log.append('  %s: %s keep_stanzas out of range' % (work['slug'], sid)); continue
            s['stanzas'] = [s['stanzas'][i] for i in keep]; changed += 1
        if 'split_at_stanza' in fix:
            n = fix['split_at_stanza']
            if not 0 < n < len(s['stanzas']): log.append('  %s: %s split index %d out of range (%d stanzas)' % (work['slug'], sid, n, len(s['stanzas']))); continue
            title = fix.get('second_title') or 'Untitled'
            new = {'id': uniq(slugify(title), ids), 'title': title, 'short': title[:18], 'stanzas': s['stanzas'][n:]}
            s['stanzas'] = s['stanzas'][:n]
            secs.insert(secs.index(s) + 1, new); by[new['id']] = new; changed += 1
        if 'split_many' in fix:
            # One heading over a whole sequence: eighteen Rochester lyrics all headed A SONG., forty-six
            # Seward sonnets under the second one, fifty-one of Drayton's under "Sonnets". split_at_stanza
            # cuts a section in two and these need cutting into twenty, so the pairs are applied from the
            # END, where each cut leaves the earlier indices untouched. Pairs are [stanza index, title].
            bad = [n for n, _ in fix['split_many'] if not 0 < n < len(s['stanzas'])]
            if bad:
                log.append('  %s: %s split_many out of range %s (%d stanzas)' % (work['slug'], sid, bad, len(s['stanzas'])))
            else:
                for n, t in sorted(fix['split_many'], key=lambda x: -x[0]):
                    new_sec = {'id': uniq(slugify(t), ids), 'title': t, 'short': t[:18], 'stanzas': s['stanzas'][n:]}
                    s['stanzas'] = s['stanzas'][:n]
                    secs.insert(secs.index(s) + 1, new_sec); by[new_sec['id']] = new_sec
                changed += 1
        if 'join_stanzas' in fix:
            # A stanza cut in two where a footnote was lifted out of the middle of it. Pairs are given
            # in the numbering that stands AFTER keep_stanzas and BEFORE any split, which is the
            # numbering you read off the text, and are applied from the end so the earlier ones keep
            # their indices. Halloween had three of these and every one of them made a nine-line
            # stanza out of two fragments that were nine lines together.
            bad = [j for j in fix['join_stanzas'] if not (0 <= j[0] < j[1] < len(s['stanzas']))]
            if bad:
                log.append('  %s: %s join_stanzas out of range %s (%d stanzas)' % (work['slug'], sid, bad, len(s['stanzas'])))
            else:
                for a, b in sorted(fix['join_stanzas'], key=lambda j: -j[0]):
                    s['stanzas'][a:b + 1] = [sum(s['stanzas'][a:b + 1], [])]
                changed += 1
        if 'append_from_next' in fix:
            # The review's count is unreliable (it mixes sections with stanzas); the ids it names in
            # its note are exact, so those are what is rejoined, in the order they stand.
            named = re.search(r'headings?: (.+?) (?:are|is) its', r.get('note', ''))
            if r['section'] == 'sir-galahad-a-christmas-mystery':
                # continues in the next section for fourteen stanzas, which then goes on to another poem
                nxt = secs[secs.index(s) + 1]
                s['stanzas'] += nxt['stanzas'][:14]; nxt['stanzas'] = nxt['stanzas'][14:]; changed += 1; continue
            if r['section'] == 'the-prince' and work['slug'] == 'morris-defence-guenevere':
                i = secs.index(s); take = []
                for t in secs[i + 1:]:
                    if t['title'] not in ('The Prince', 'Rapunzel'): break
                    take.append(t)
            elif named:
                want = [x.strip() for x in named.group(1).replace(' ...', ',').split(',') if x.strip()]
                take = [by[x] for x in want[1:] if x in by and x != sid]
            else:
                log.append('  %s: %s no ids named for append_from_next' % (work['slug'], sid)); continue
            for t in take:
                s['stanzas'] += t['stanzas']; secs.remove(t); del by[t['id']]
            title = merged_title(r.get('note', ''))
            if title and 'lost' in r.get('note', ''): s['title'] = title; s['short'] = title[:18]
            changed += 1
        if 'retitle' in fix:
            # A book that prints the poem's title on one line and its genre on the next -- REMEMBER
            # over "Sonnet", FAITHLESS NELLY GRAY over "A Pathetic Ballad", MUTATION over "A Sonnet"
            # -- loses the title and keeps the genre, and the contents then shows eight poems called
            # Sonnet. The title is not missing from the book, only from the parse, so it is given
            # back here. The old address is left to stable.py, which retires it and keeps it
            # resolving. Nothing about the text changes.
            t = fix['retitle']
            s['title'] = t; s['short'] = t[:18]
            old_id = s['id']
            if fix.get('keep_id') is not True:
                ids.discard(old_id); s['id'] = uniq(slugify(t), ids)
                by.pop(old_id, None); by[s['id']] = s
            changed += 1
        if 'missed' in fix:
            log.append('  %s: %s -- a poem missed, "%s", needs its text from the source; left alone' % (work['slug'], sid, fix['missed'].get('title')))
        done.add(fid(r))
    work['segfix'] = sorted(done)
    return changed

def main(write):
    d = json.load(open(FINDINGS, encoding='utf-8'))
    recs = [r for r in d if 'issue' in r]
    by_work = {}
    for r in recs: by_work.setdefault(r['work'], []).append(r)
    log = []; total = 0; before = after = 0
    backup = os.path.join(HERE, 'segmentation-backup')
    if write: os.makedirs(backup, exist_ok=True)
    for slug, rs in sorted(by_work.items()):
        path = os.path.join(WORKS, slug + '.json')
        if not os.path.exists(path): log.append('  %s: no parsed work' % slug); continue
        work = json.load(open(path, encoding='utf-8'))
        n0 = len(work['sections']); l0 = sum(len(st) for s in work['sections'] for st in s['stanzas'])
        # order: drops and keeps first, then splits (which add sections), then rejoins, which name ids
        order = {'drop': 0, 'keep_stanzas': 0, 'split_at_stanza': 1, 'split_many': 1,
             'append_from_next': 2, 'retitle': 3, 'missed': 4}
        rs = sorted(rs, key=lambda r: order.get(next(iter(r['fix'])) if r.get('fix') else 'missed', 9))
        changed = apply(work, rs, log)
        n1 = len(work['sections']); l1 = sum(len(st) for s in work['sections'] for st in s['stanzas'])
        before += n0; after += n1; total += changed
        print('%-28s %3d findings applied %3d   sections %4d -> %4d   lines %6d -> %6d' % (slug, len(rs), changed, n0, n1, l0, l1))
        if write:
            shutil.copy(path, os.path.join(backup, slug + '.json'))
            # The counts are derived, and dropping or splitting a section changes them. Leaving them
            # as the parser wrote them is why 53 works told the library one number of poems and held
            # another; analyze.py updates the statistics it computes and keeps these as it finds them.
            if work.get('stats'):
                work['stats'].update({'sections': n1, 'stanzas': sum(len(x['stanzas']) for x in work['sections']), 'lines': l1})
            json.dump(work, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
    print('\n%d findings applied across %d works; sections %d -> %d%s' % (total, len(by_work), before, after, '' if write else '   (dry run; --write to apply)'))
    if log: print('\nnot applied:'); print('\n'.join(log))

if __name__ == '__main__':
    main('--write' in sys.argv)
