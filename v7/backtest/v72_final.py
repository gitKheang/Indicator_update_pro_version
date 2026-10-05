import datetime, collections
from simple_engine import run, metrics, fmt, T
UTC = datetime.timezone.utc
Z = ('SUPPLY', 'BEAR_OB', 'PIVOT_RESISTANCE', 'DEMAND', 'BULL_OB', 'PIVOT_SUPPORT')
V72 = dict(tp_mode='hybrid', fixed_tp1=1.51, fixed_tp2=2.5, tp2_fallback=True, clean_room=Z, tp2_cap=0,
           tp2_before_zone=True, tp_front=0.1, buf=0.3, max_sl=15.0, min_sl=2.0, max_hold=10 ** 9)
# V7.3 (maintained): clean-room obstacles = 15m Pivot S/R zones + unswept EQH/EQL + 4H swing.
V73 = dict(V72, clean_room=('PIVOT_RESISTANCE', 'PIVOT_SUPPORT', 'EQH', 'EQL', '4H_SWING_HIGH', '4H_SWING_LOW'))
# V7.4 (maintained): V7.3 + the 5m Supertrend (ta.supertrend, ATR 10, factor 3)
# must point the trade's way on the trigger bar.
def v74(period=10, factor=3.0):
    import famous
    st = famous.supertrend(period, factor)
    return dict(V73, filter=lambda i, s: st[i] == s)
# V7.5 (maintained): V7.4 + fast pullback (break at most 11 bars after the broken
# internal pivot) + calm 1H (Choppiness Index(14) of the last completed 1H bar < 50).
def v75(max_pb=11, chop_max=50.0, use_chop=True, use_fast=True):
    import famous
    from simple_engine import PTOP, PBTM
    from v75_lab import CHOP1H_PINE
    st = famous.supertrend(10, 3.0)
    def f(i, s):
        if st[i] != s: return False
        if use_fast:
            pbar = PTOP[i] if s == 1 else PBTM[i]
            if pbar is None or i - pbar > max_pb: return False
        if use_chop and (CHOP1H_PINE[i] is None or CHOP1H_PINE[i] >= chop_max): return False
        return True
    return dict(V73, filter=f)
if __name__ == '__main__':
    r = run(V72, 'V7.2 final (clean room ON)')
    g = collections.defaultdict(list)
    for t in r['trades']: g[datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).year].append(t)
    for y in sorted(g): print('   %d ' % y, fmt(metrics(g[y], r['cfg'])))
    oc = collections.Counter(t['outcome'] for t in r['trades']); print('   outcomes', dict(oc))
    w0 = int(datetime.datetime(2026, 8, 11, tzinfo=UTC).timestamp() * 1000)
    win = [t for t in r['trades'] if t['readyTime'] >= w0]
    print('   TV window 2026-08-11..', fmt(metrics(win, r['cfg'])))
    c0 = dict(r['cfg']); c0['cost'] = 0.0
    print('   TV window, zero cost  ', fmt(metrics(win, c0)))
    for t in win:
        print('     ', datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).strftime('%m-%d %H:%M'), 'L' if t['side'] == 1 else 'S', round(t['entry'], 2), 'SL', round(t['stop'], 2), 'TP1', round(t['tp1'], 2), 'TP2', round(t['tp2'], 2), t['outcome'])
    r2 = run(dict(V72, clean_room=None, tp2_before_zone=False, tp2_fallback=True, tp_mode='hybrid'), 'clean room OFF (TP2 structural/fallback)', show=False)
    r3 = run(dict(V72, clean_room=()), 'clean room OFF, TP2 before zone')
