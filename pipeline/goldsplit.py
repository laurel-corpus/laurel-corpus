"""Score the scanner separately on a development set and a held-out control.

The point of the split is that a number you tuned against is not evidence. Haider's data already ships
a train/test division; this keeps to it. Everything looked at while changing the scanner comes from
train. test is scored before and after and otherwise not opened.

    python3 goldsplit.py            score both splits
"""
import collections, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from goldscore import fetch, words_of

def load_one(name):
    out, cur = [], []
    for row in io.open(fetch(name), encoding='utf-8'):
        row = row.rstrip('\n')
        if not row.strip():
            if cur: out.append(cur)
            cur = []; continue
        f = row.split('\t')
        if len(f) >= 9: cur.append(f)
    if cur: out.append(cur)
    return out

def score(gold, label):
    from scansion import evidence
    usable = lines = 0
    opin = hit = 0
    sylls_seen = sylls_match = 0
    for line in gold:
        lines += 1
        text = ' '.join(words_of(line))
        try: ev = evidence(text)
        except Exception: continue
        sylls_seen += 1
        if len(ev) != len(line): continue
        sylls_match += 1; usable += 1
        for (wants, _), f in zip(ev, line):
            if wants is None: continue
            opin += 1
            hit += (wants == '1') == (f[2] == '+')
    print('%-10s  lines %5d   syllable count agrees %5.1f%%   stress agrees %5.1f%%'
          % (label, lines, 100.0*sylls_match/max(1, sylls_seen), 100.0*hit/max(1, opin)))
    return {'lines': lines, 'count': 100.0*sylls_match/max(1, sylls_seen), 'stress': 100.0*hit/max(1, opin)}

if __name__ == '__main__':
    tr, te = load_one('train.txt'), load_one('test.txt')
    print('DEVELOPMENT and CONTROL, as Haider split them:')
    a = score(tr, 'train')
    b = score(te, 'CONTROL')
