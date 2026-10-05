import datetime, collections
from simple_engine import run, metrics, fmt, T
from r2_common import SPLIT
from v72_final import V72
from lab import ET_H
from simple_engine import ctx
PIV = ('PIVOT_RESISTANCE', 'PIVOT_SUPPORT'); LIQ = ('EQH', 'EQL', '4H_SWING_HIGH', '4H_SWING_LOW')
r = run(dict(V72, clean_room=PIV + LIQ), show=False)
idx = {t: i for i, t in enumerate(T)}
for part in (0.33, 0.5, 0.67, 1.0):
    c = dict(r['cfg']); c['part'] = part
    print('close %3d%% at TP1:' % (part * 100), fmt(metrics(r['trades'], c, 719)))
g = collections.defaultdict(lambda: [[], []])
for t in r['trades']:
    i = idx[t['readyTime']]; g[ET_H[i] // 3 * 3][0 if t['readyTime'] < SPLIT else 1].append(t)
print('ET hour buckets (IS | OOS):')
for h in sorted(g):
    a, b = g[h]
    ma, mb = metrics(a, r['cfg']), metrics(b, r['cfg'])
    print('  %02d-%02d  IS n=%3d WR %4.1f%% PF %.2f | OOS n=%3d WR %4.1f%% PF %.2f' % (h, h + 2, ma['n'] if ma else 0, 100 * ma['wr'] if ma else 0, ma['pf'] if ma else 0, mb['n'] if mb else 0, 100 * mb['wr'] if mb else 0, mb['pf'] if mb else 0))
