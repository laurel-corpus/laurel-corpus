"""The battery a rule has to pass. One command, one table.

A change to the scanner is judged against every ruler at once: the hand-marked verse in marked/,
Haider's development half, and the poems whose metre is not in doubt. The baseline is stored, so
every trial is compared with the same numbers, and the deltas are printed beside each figure.

    python3 rules.py --baseline     score the scanner as it stands and store the result
    python3 rules.py                score it again and print each figure against the baseline
    python3 rules.py --keep         a rule has passed: the current figures become the baseline

The held-out control is not here. It is scored once, by hand, after a rule is kept, and never while
one is being chosen. The small rulers are printed but carry no weight: four lines cannot vote.
"""
import io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, 'marked', 'baseline.json')
PY = sys.executable

def run(args):
    r = subprocess.run([PY, '-u'] + args, cwd=HERE, capture_output=True, text=True)
    return r.stdout + r.stderr

def measure():
    out = {}
    m = run(['marked.py'])
    for block in re.split(r'\n(?=[A-Z][^\n]* \d{4}: )', m):
        head = re.match(r'([^\n]*?) (\d{4}): (\d+) marked lines', block)
        if not head: continue
        name, n = head.group(1), int(head.group(3))
        st = re.search(r'read in the foot the marks imply.*?\n\s*stress\s+([\d.]+)%', block, re.S)
        ln = re.search(r'read in the foot the marks imply.*?lines every mark right\s+([\d.]+)%', block, re.S)
        if st and ln:
            out['ruler:' + name] = {'n': n, 'stress': float(st.group(1)), 'lines': float(ln.group(1))}
    p = run(['perline.py', '--train'])
    g = re.search(r'EVERY MARK RIGHT\s+([\d.]+)%\s+\(\d[\d,]* of (\d[\d,]*)', p)
    if g: out['haider:dev'] = {'n': int(g.group(2).replace(',', '')), 'lines': float(g.group(1))}
    q = run(['precision.py'])
    # the scorers' own output, for reading per-metre figures after a run
    io.open(os.path.join(HERE, 'marked', 'last-run.txt'), 'w', encoding='utf-8').write(m + '\n' + p + '\n' + q)
    a = re.search(r'NOT iambic at all\s+([\d.]+)%', q)
    b = re.search(r'WRONG foot\s+([\d.]+)%', q)
    if a: out['precision:sonnets wrong'] = {'pct': float(a.group(1))}
    if b: out['precision:blank verse wrong'] = {'pct': float(b.group(1))}
    return out

def show(cur, base):
    print('%-32s %7s %7s %7s' % ('', 'base', 'now', 'delta'))
    def row(label, b, c, key, lower_is_better=False):
        if b is None or c is None: print('%-32s %7s %7s' % (label, '-', '%.1f' % c if c is not None else '-')); return
        d = c - b
        mark = ''
        if abs(d) >= 0.05: mark = ('worse' if (d < 0) != lower_is_better else 'better')
        print('%-32s %7.1f %7.1f %+7.1f  %s' % (label, b, c, d, mark))
    for k in sorted(cur):
        if not k.startswith('ruler:'): continue
        name, n = k[6:], cur[k]['n']
        weight = '' if n >= 40 else '   (too small to vote)'
        row('%s (%d) lines' % (name, n), base.get(k, {}).get('lines'), cur[k]['lines'], k)
        row('%s stress' % ('' if False else ' ' * len(name)), base.get(k, {}).get('stress'), cur[k]['stress'], k)
        if weight: print('%s%s' % (' ' * 32, weight.strip()))
    k = 'haider:dev'
    if k in cur: row('Haider development (%d) lines' % cur[k]['n'], base.get(k, {}).get('lines'), cur[k]['lines'], k)
    for k, label in (('precision:sonnets wrong', 'precision: sonnets wrong %'),
                     ('precision:blank verse wrong', 'precision: blank verse wrong %')):
        if k in cur: row(label, base.get(k, {}).get('pct'), cur[k]['pct'], k, lower_is_better=True)

if __name__ == '__main__':
    cur = measure()
    if '--baseline' in sys.argv or '--keep' in sys.argv:
        # read the old figures before they are overwritten, so a keep still shows what it kept
        base = json.load(open(BASE)) if '--keep' in sys.argv and os.path.exists(BASE) else cur
        json.dump(cur, open(BASE, 'w'), indent=1)
        print('baseline stored' if '--baseline' in sys.argv else 'kept: baseline moved to the current figures')
        show(cur, base)
    else:
        base = json.load(open(BASE)) if os.path.exists(BASE) else {}
        show(cur, base)
