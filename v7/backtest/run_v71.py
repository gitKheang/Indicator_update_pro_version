"""Reproduce the V7.1 backtest figures in ../SPLIT_REPLAY_MEMORY.md.

Run from this folder after downloading data (see README.md):
    python3 run_v71.py
"""
import datetime, pickle, os, collections
import data_load, phase5
from engine import Engine, stats
from v71_rules import V71_CONFIG, v71_hooks

UTC = datetime.timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))
SPLIT = int(datetime.datetime(2025, 7, 1, tzinfo=UTC).timestamp() * 1000)


def context():
    fn = os.path.join(HERE, 'data/ctx.pkl')
    if os.path.exists(fn):
        return pickle.load(open(fn, 'rb'))
    ctx = phase5.build_context(data_load.build(), {})
    pickle.dump(ctx, open(fn, 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
    return ctx


def line(label, s):
    if not s['n']:
        return '%-34s n=0' % label
    return '%-34s n=%3d %s WR %5.1f%%  PF %.2f  exp %+.3fR  total %+6.1fR  maxDD %4.1fR' % (
        label, s['n'], ('(%.2f/day)' % s['perday']) if 'perday' in s else '         ', 100 * s['wr'], s['pf'], s['exp'], s['total'], s['maxdd'])


def main():
    ctx = context()
    T = ctx['T']
    days = (T[-1] - T[0]) / 86400000 * 5 / 7
    print('Data: %s .. %s, %d five-minute bars, ~%d trading days' % (
        datetime.datetime.fromtimestamp(T[0] / 1000, UTC).date(), datetime.datetime.fromtimestamp(T[-1] / 1000, UTC).date(), len(T), days))
    old = Engine(ctx, dict(cost=0.3)).run()
    print(line('Original V7', stats(old.trades, dict(cost=0.3), 'partial', days)))
    new = Engine(ctx, V71_CONFIG, hooks=v71_hooks()).run()
    tr = new.trades
    print(line('V7.1', stats(tr, V71_CONFIG, 'partial', days)))
    print(line('  in-sample  2024-01..2025-06', stats([t for t in tr if t['readyTime'] < SPLIT], V71_CONFIG, 'partial')))
    print(line('  out-of-sample 2025-07..', stats([t for t in tr if t['readyTime'] >= SPLIT], V71_CONFIG, 'partial')))
    by = collections.defaultdict(list)
    for t in tr:
        by[datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).year].append(t)
    for y in sorted(by):
        print(line('  %d' % y, stats(by[y], V71_CONFIG, 'partial')))
    print('TP1 trade-off (same signals):')
    for tp1 in (0.5, 0.75, 1.0, 1.5):
        e = Engine(ctx, V71_CONFIG, hooks=v71_hooks(tp1_r=tp1)).run()
        print(line('  TP1 %.2fR' % tp1, stats(e.trades, V71_CONFIG, 'partial', days)))


if __name__ == '__main__':
    main()
