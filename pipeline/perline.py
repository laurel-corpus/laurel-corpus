"""How often a whole line is marked correctly, rather than how many marks are correct.

bench.py reports stress per syllable, which is the right number for 'how many of the marks are right'
and the wrong one for 'what are the odds this line is right'. A line carries eight or ten marks, so a
7.7% error per syllable does not mean 7.7% of lines are wrong. It also does not mean the 49% that
independent errors would give: they cluster, and the gap between those two figures is worth reporting,
because it says the scanner fails on particular lines rather than sprinkling mistakes over all of them.

    python3 perline.py           the held-out control
    python3 perline.py --train   the development half
    python3 perline.py --show N  also print the N worst lines, with the marks side by side
"""
import collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from goldsplit import load_one
from goldscore import words_of
from bench import best, COARSE
import scansion as S

def run(split, show=0):
    gold = load_one(split)
    n = syl_bad = no_metre = scored = perfect = 0
    errs = collections.Counter()
    by_metre = collections.defaultdict(lambda: [0, 0])
    syl = err = 0
    worst = []
    for line in gold:
        n += 1
        text = ' '.join(words_of(line))
        try:
            ev = S.asked(text, len(line))
        except Exception:
            syl_bad += 1; continue
        if len(ev) != len(line):
            syl_bad += 1; continue
        want = COARSE.get(line[0][6])
        if not want:
            no_metre += 1; continue
        g = ''.join('1' if f[2] == '+' else '0' for f in line)
        b = best(ev, [S.FEET[want]])
        if not b:
            no_metre += 1; continue
        scored += 1
        wrong = sum(1 for x, c in zip(b, g) if x != c)
        errs[wrong] += 1
        syl += len(g); err += wrong
        if not wrong: perfect += 1
        else: worst.append((wrong, text, g, b, want))
        by_metre[want][1] += 1
        by_metre[want][0] += (wrong == 0)

    pc = lambda a, b: 100.0 * a / b if b else 0.0
    print('%s: %s lines\n' % (split.replace('.txt', '').upper(), format(n, ',')))
    print('  syllable count already disagrees   %s  (%.1f%%)' % (format(syl_bad, ','), pc(syl_bad, n)))
    print('  no metre recorded to read against  %s  (%.1f%%)' % (format(no_metre, ','), pc(no_metre, n)))
    print('  lines scored                       %s  (%.1f%%)\n' % (format(scored, ','), pc(scored, n)))
    print('  EVERY MARK RIGHT      %5.1f%%   (%s of %s)' % (pc(perfect, scored), format(perfect, ','), format(scored, ',')))
    print('  one mark or more wrong %5.1f%%\n' % (pc(scored - perfect, scored)))
    for k in sorted(errs):
        if k: print('     %2d wrong  %5s lines  (%4.1f%%)' % (k, format(errs[k], ','), pc(errs[k], scored)))
    p = err / syl if syl else 0
    mean = syl / scored if scored else 0
    print('\n  per syllable %.1f%% wrong over %s syllables, %.1f to a line.' % (100 * p, format(syl, ','), mean))
    print('  Scattered evenly that would spoil %.1f%% of lines; it spoils %.1f%%, so they cluster.'
          % (100 * (1 - (1 - p) ** mean), pc(scored - perfect, scored)))
    print('\n  end to end, a wrong syllable count counting as a wrong line: %.1f%% right'
          % pc(perfect, scored + syl_bad))
    print('\n  by what the metre really is:')
    for m, q in sorted(by_metre.items(), key=lambda kv: -kv[1][1]):
        print('     %-12s every mark right %5.1f%%  of %s' % (m, pc(q[0], q[1]), format(q[1], ',')))
    if show:
        print('\n  the worst of them:')
        for wrong, text, g, b, want in sorted(worst, reverse=True)[:show]:
            print('\n     %s   (%s, %d wrong)' % (text, want, wrong))
            print('     gold     %s' % g.replace('1', '+').replace('0', '-'))
            print('     ours     %s' % b.replace('1', '+').replace('0', '-'))
            print('              %s' % ''.join('^' if x != c else ' ' for x, c in zip(b, g)))

if __name__ == '__main__':
    show = int(sys.argv[sys.argv.index('--show') + 1]) if '--show' in sys.argv else 0
    run('train.txt' if '--train' in sys.argv else 'test.txt', show)
