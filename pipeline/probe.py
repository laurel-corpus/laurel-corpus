"""Which ruler readings a change to the scanner altered, and whether for better or worse.

rules.py says how much a rule moved each figure; this says which lines moved it, so a loss can be
read. Before a rule goes in, copy the scanner aside; after, compare:

    cp scansion.py /tmp/scansion.before; cp bench.py /tmp/bench.before
    python3 probe.py /tmp/scansion.before /tmp/bench.before [--show 6]

The backup is executed as if it were the pipeline's own file, so that its data paths resolve; loaded
from anywhere else it silently runs without its learned tables and measures a different scanner.
"""
import io, os, sys, types
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

def load(name, path):
    """A backup executed as if it were the pipeline's own file, so its data paths still resolve."""
    m = types.ModuleType(name)
    m.__file__ = os.path.join(HERE, name + '.py')
    sys.modules[name] = m
    exec(compile(io.open(path, encoding='utf-8').read(), m.__file__, 'exec'), m.__dict__)
    return m

def readings(scansion_path, bench_path):
    for name in ('scansion', 'bench', 'marked'):
        sys.modules.pop(name, None)
    m = load('scansion', scansion_path)
    b = load('bench', bench_path)
    import marked as M
    out = {}
    for name in ('schipper', 'saintsbury', 'brown', 'latham', 'guest', 'leigh', 'skeat', 'kirkham'):
        for plain, g in M.load(name):
            ev = m.evidence(plain)
            if len(ev) != len(g): continue
            foot = M.foot_of(g)
            if not foot: continue
            out[(name, plain)] = (g, foot, b.best(ev, [m.FEET[foot]]))
    return out

old = readings(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'bench.py'))
new = readings(os.path.join(HERE, 'scansion.py'), os.path.join(HERE, 'bench.py'))
show = int(sys.argv[sys.argv.index('--show') + 1]) if '--show' in sys.argv else 3
for name in ('schipper', 'saintsbury', 'brown', 'latham', 'guest', 'leigh', 'skeat', 'kirkham'):
    changed = better = worse = 0; ex = []
    for k, (g, foot, t0) in old.items():
        if k[0] != name: continue
        t1 = new[k][2]
        if t0 == t1: continue
        changed += 1
        gg = g.replace('+', '1').replace('-', '0')
        wrong = lambda t: sum(1 for a, c in zip(t or '', gg) if c in '01' and a != c)
        e0, e1 = wrong(t0), wrong(t1)
        better += e1 < e0; worse += e1 > e0
        ex.append((e1 - e0, k[1], foot, gg, t0, e0, t1, e1))
    if not changed: continue
    print('%-11s changed %3d   better %3d   worse %3d' % (name, changed, better, worse))
    for d, plain, foot, gg, t0, e0, t1, e1 in sorted(ex, key=lambda x: -abs(x[0]))[:show]:
        print('     %-56s %s\n       gold %s\n       was  %s (%d wrong)\n       now  %s (%d wrong)' % (plain[:56], foot, gg, t0, e0, t1, e1))
