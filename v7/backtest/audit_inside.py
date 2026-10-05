"""Audit: does V7.3/V7.4 enter while price is already INSIDE an opposing 15m
Pivot S/R zone? The clean-room check only looks at a zone's near edge, which is
behind the entry in that case, so such a zone never counts as an obstacle."""
import collections
from simple_engine import run, metrics, fmt, C, _pool_eng
from r2_common import SPLIT
from v72_final import V73
import famous
ST = famous.supertrend(10, 3.0)
PK = _pool_eng.x['pk']
def inside_opposing(i, s, entry):
    fam = 'pRes' if s == 1 else 'pSup'
    for z in PK[i][fam]:
        if z is not None and z[1] <= entry <= z[0]:
            return True
    return False
def inside_same(i, s, entry):
    fam = 'pSup' if s == 1 else 'pRes'
    for z in PK[i][fam]:
        if z is not None and z[1] <= entry <= z[0]:
            return True
    return False
idx = {t: i for i, t in enumerate(_pool_eng.x['T'])}
V74 = dict(V73, filter=lambda i, s: ST[i] == s)
for lab, cfg in (('V7.3', V73), ('V7.4 (ST)', V74)):
    r = run(cfg, show=False); c = r['cfg']
    g = collections.defaultdict(list)
    for t in r['trades']:
        i = idx[t['readyTime']]
        g['inside opposing' if inside_opposing(i, t['side'], t['entry']) else 'inside same-side' if inside_same(i, t['side'], t['entry']) else 'outside zones'].append(t)
    print('==', lab, fmt(metrics(r['trades'], c, 719)))
    for k, v in g.items():
        print('   %-18s' % k, fmt(metrics(v, c)))
def no_inside(base):
    f0 = base.get('filter')
    return lambda i, s: (f0 is None or f0(i, s)) and not inside_opposing(i, s, C[i])
for lab, cfg in (('V7.3 + not inside opposing', dict(V73, filter=no_inside(V73))), ('V7.4 + not inside opposing', dict(V74, filter=no_inside(V74)))):
    run(cfg, lab)
