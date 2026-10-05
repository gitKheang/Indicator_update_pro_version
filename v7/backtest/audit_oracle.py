"""Illustration only (uses FUTURE data on purpose): how high can the win rate go at
TP1 > 1.5R if the direction were known perfectly? This bounds what any 'better
information' (trend, zones, confirmation) could possibly achieve."""
from simple_engine import run, metrics, fmt, C, N
from v72_final import V73
def oracle(h):
    return lambda i, s: (C[min(N - 1, i + h)] - C[i]) * s > 0
r = run(V73, show=False); print('%-52s %s' % ('V7.3 (real, no future data)', fmt(metrics(r['trades'], r['cfg'], 719))))
for h, lab in ((12, '1 hour'), (48, '4 hours'), (288, '24 hours')):
    r = run(dict(V73, filter=oracle(h)), show=False)
    print('%-52s %s' % ('V7.3 + PERFECT knowledge of the next %s direction' % lab, fmt(metrics(r['trades'], r['cfg'], 719))))
