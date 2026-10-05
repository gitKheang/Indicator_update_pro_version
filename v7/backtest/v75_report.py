"""Reproduce the V7.5 tables in ../README.md (Part 1)."""
import datetime, collections
from simple_engine import run, metrics, fmt
from r2_common import SPLIT, TWO_Y, DAYS_ALL, DAYS_2Y
from v72_final import V73, v74, v75
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
    if len(w) >= 100:
        roll = [sum(w[k:k + 100]) for k in range(0, len(w) - 99)]
        print('   rolling-100 WR min/median/max %d%%/%d%%/%d%%, last 100 trades %d%%' % (min(roll), sorted(roll)[len(roll) // 2], max(roll), roll[-1]))
    days = len(set(datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).date() for t in tr))
    print('   trading days with a trade: %d of ~%d' % (days, int(DAYS_ALL)))
    print('   outcomes', dict(collections.Counter(t['outcome'] for t in tr)))
block('V7.4', run(v74(), show=False))
block('V7.5 balanced (fast pullback only)', run(v75(use_chop=False), show=False))
block('V7.5 default (fast pullback + calm 1H)', run(v75(), show=False))
