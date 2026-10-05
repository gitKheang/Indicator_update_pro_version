"""Reproduce the V7.2 comparison table in ../README.md (Part 1)."""
import datetime, collections
from simple_engine import run, metrics, fmt, T
from r2_common import structural_hook, body_confirm, BASE, ctx, SPLIT, TWO_Y, DAYS_ALL, DAYS_2Y
from engine import Engine
from v72_final import V72
UTC = datetime.timezone.utc
def to_simple(e):
    out = []
    for t in e.trades:
        d = dict(t); d['risk'] = abs(t['entry'] - t['stop']); d['tp1Hit'] = t['outcome'] != 'STOP'; out.append(d)
    return out
def show(label, tr, cfg):
    print(label)
    print('   ALL', fmt(metrics(tr, cfg, DAYS_ALL)))
    print('   2Y ', fmt(metrics([t for t in tr if t['readyTime'] >= TWO_Y], cfg, DAYS_2Y)))
c = dict(cost=0.3, part=0.5)
# 1) V7.1 AOI pipeline, rules of this task (structural SL beyond AOI/reaction, <= $15, TP1 first structure > 1.5R)
e = Engine(ctx, BASE, hooks={'package': structural_hook(), 'confirm': body_confirm(0.3)}).run()
show('V7.1 AOI pipeline under the new rules', to_simple(e), c)
r = run(V72, show=False); show('V7.2 (clean room ON, default)', r['trades'], r['cfg'])
g = collections.defaultdict(list)
for t in r['trades']: g[datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).year].append(t)
for y in sorted(g): print('   %d' % y, fmt(metrics(g[y], r['cfg'])))
print('   IS ', fmt(metrics([t for t in r['trades'] if t['readyTime'] < SPLIT], r['cfg'])))
print('   OOS', fmt(metrics([t for t in r['trades'] if t['readyTime'] >= SPLIT], r['cfg'])))
wins = [1 if t['tp1Hit'] else 0 for t in r['trades']]
roll = [sum(wins[k:k + 100]) for k in range(0, len(wins) - 99)]
print('   rolling 100-trade WR min/median/max: %d%% / %d%% / %d%%' % (min(roll), sorted(roll)[len(roll) // 2], max(roll)))
cf = dict(r['cfg']); cf['part'] = 1.0
print('   full exit at TP1 (no runner):', fmt(metrics(r['trades'], cf, DAYS_ALL)))
r2 = run(dict(V72, clean_room=()), show=False); show('V7.2 with clean room OFF (input switch)', r2['trades'], r2['cfg'])
