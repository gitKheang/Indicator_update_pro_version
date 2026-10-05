import datetime, collections
from simple_engine import run, metrics, fmt
UTC = datetime.timezone.utc
Z = ('SUPPLY', 'BEAR_OB', 'PIVOT_RESISTANCE', 'DEMAND', 'BULL_OB', 'PIVOT_SUPPORT')
B2 = dict(tp_mode='hybrid', fixed_tp1=1.51, fixed_tp2=2.5, tp2_fallback=True, clean_room=Z, tp2_cap=0, tp2_before_zone=True, tp_front=0.1)
def yearly(res):
    g = collections.defaultdict(list)
    for t in res['trades']: g[datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).year].append(t)
    return ' | '.join('%d PF %.2f WR %.0f%%' % (y, m['pf'], 100 * m['wr']) for y in sorted(g) for m in [metrics(g[y], res['cfg'])])
r = run(B2, 'B2 final candidate'); print('    ', yearly(r))
wins = [1 if t['tp1Hit'] else 0 for t in r['trades']]
roll = [sum(wins[k:k + 100]) for k in range(0, len(wins) - 99)]
print('     rolling 100-trade win rate: min %d%%  median %d%%  max %d%%' % (min(roll), sorted(roll)[len(roll) // 2], max(roll)))
for lab, kw in (('buf 0.2', dict(buf=0.2)), ('buf 0.5', dict(buf=0.5)), ('TP2 2.0', dict(fixed_tp2=2.0)), ('TP2 3.0', dict(fixed_tp2=3.0)),
                ('front 0', dict(tp_front=0.0)), ('front 0.25', dict(tp_front=0.25)), ('TP1 1.6', dict(fixed_tp1=1.6)), ('TP1 1.75', dict(fixed_tp1=1.75))):
    rr = run(dict(B2, **kw), '  ' + lab, show=False)
    print('  %-10s %s' % (lab, fmt(metrics(rr['trades'], rr['cfg'], 719))), '\n            ', yearly(rr))
