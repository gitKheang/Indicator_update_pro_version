"""Reproduce the V7.4 tables in ../README.md (Part 1)."""
import datetime, collections
from simple_engine import run, metrics, fmt
from r2_common import SPLIT, TWO_Y, DAYS_ALL, DAYS_2Y
from v72_final import V73, v74
UTC = datetime.timezone.utc
def block(label, r):
    tr = r['trades']; c = r['cfg']
    print('==', label)
    print('   ALL', fmt(metrics(tr, c, DAYS_ALL)))
    print('   2Y ', fmt(metrics([t for t in tr if t['readyTime'] >= TWO_Y], c, DAYS_2Y)))
    print('   IS ', fmt(metrics([t for t in tr if t['readyTime'] < SPLIT], c)))
    print('   OOS', fmt(metrics([t for t in tr if t['readyTime'] >= SPLIT], c)))
    g = collections.defaultdict(list)
    for t in tr: g[datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).year].append(t)
    for y in sorted(g): print('   %d' % y, fmt(metrics(g[y], c)))
    w = [1 if t['tp1Hit'] else 0 for t in tr]
    roll = [sum(w[k:k + 100]) for k in range(0, len(w) - 99)]
    print('   rolling-100 WR min/median/max %d%%/%d%%/%d%%, last 100 trades %d%%' % (min(roll), sorted(roll)[len(roll) // 2], max(roll), roll[-1]))
    days = len(set(datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).date() for t in tr))
    print('   trading days with a trade: %d of ~%d' % (days, int(DAYS_ALL)))
    print('   outcomes', dict(collections.Counter(t['outcome'] for t in tr)))
block('V7.3', run(V73, show=False))
block('V7.4 = V7.3 + Supertrend(10,3)', run(v74(), show=False))
print('-- Supertrend setting sensitivity (V7.4 structure)')
for per, m in ((7, 3.0), (10, 2.0), (10, 3.0), (10, 4.0), (14, 3.0), (20, 3.0)):
    r = run(v74(per, m), show=False); tr = r['trades']; c = r['cfg']
    mi = metrics([t for t in tr if t['readyTime'] < SPLIT], c); mo = metrics([t for t in tr if t['readyTime'] >= SPLIT], c)
    print('   ST(%2d,%.0f) %s | IS WR %.1f%% PF %.2f | OOS WR %.1f%% PF %.2f' % (per, m, fmt(metrics(tr, c, DAYS_ALL)), 100 * mi['wr'], mi['pf'], 100 * mo['wr'], mo['pf']))
