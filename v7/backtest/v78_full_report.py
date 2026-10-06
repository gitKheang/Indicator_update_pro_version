"""V7.8 full backtest report at the Strategy Tester defaults: 0.01 lot (1 oz, $1 move = $1),
50% closed at TP1, runner to TP2 with the original stop, $0.30 per oz round-trip costs,
one trade at a time. Repaired data, 2024-01-02 .. 2026-10-04."""
import datetime, collections, statistics
from v76_lab import setups, T, N, I0, NYD
from v77_lab import simulate_be, sequential
UTC = datetime.timezone.utc
CFG = dict(chop_max=0, pb_max=0, pe_after_pivot=True)
t24 = int(datetime.datetime(2024, 1, 2, tzinfo=UTC).timestamp() * 1000)
i24 = next(i for i in range(N) if T[i] >= t24)
rows = sequential([simulate_be(r, 'none', 0) for r in setups(CFG, i0=i24, i1=N - 1)[0]])
for r in rows: r['usd'] = r['R'] * r['risk']
D = lambda i: datetime.datetime.fromtimestamp(T[min(i, N - 1)] / 1000, UTC)


def block(rs, title):
    n = len(rs); W = [r for r in rs if r['win']]; Lo = [r for r in rs if not r['win']]
    pos = [r['usd'] for r in rs if r['usd'] > 0]; neg = [r['usd'] for r in rs if r['usd'] < 0]
    eq = pk = dd = 0.0; dd_from = dd_to = peak_i = None; peak_t = rs[0]['i']; uw_max = 0; uw_start = None
    cw = cl = mcw = mcl = 0
    for r in rs:
        eq += r['usd']
        if eq >= pk:
            if uw_start is not None: uw_max = max(uw_max, (T[r['exit'] if r['exit'] < N else N - 1] - T[uw_start]) / 86400000)
            pk = eq; peak_i = r['i']; uw_start = None
        else:
            if uw_start is None: uw_start = peak_i
            if pk - eq > dd: dd = pk - eq; dd_from = peak_i; dd_to = r['i']
        if r['win']: cw += 1; cl = 0
        else: cl += 1; cw = 0
        mcw = max(mcw, cw); mcl = max(mcl, cl)
    hold = [(min(r['exit'], N - 1) - r['i']) * 5 / 60 for r in rs]
    out = collections.Counter(r['res'] for r in rs)
    print('=== %s' % title)
    print('  trades %d (longs %d, shorts %d) | wins %d / losses %d | win rate %.1f%%' % (n, sum(r['s'] == 1 for r in rs), sum(r['s'] == -1 for r in rs), len(W), len(Lo), 100 * len(W) / n))
    print('  outcomes: TP2 %d | TP1 then stop %d | SL %d' % (out['TP2'], out['TP1_STOP'], out['LOSS']))
    print('  net $%.2f | gross profit $%.2f | gross loss $%.2f | PF %.2f | net %.1fR' % (sum(r['usd'] for r in rs), sum(pos), -sum(neg), sum(pos) / -sum(neg), sum(r['R'] for r in rs)))
    print('  avg trade $%.2f | avg win $%.2f | avg loss $%.2f | payoff %.2f | largest win $%.2f | largest loss $%.2f' % (
        sum(r['usd'] for r in rs) / n, statistics.mean(pos), -statistics.mean(neg), statistics.mean(pos) / -statistics.mean(neg), max(pos), -min(neg)))
    print('  max drawdown $%.2f (%s -> %s) | longest time below a previous high %.0f days | max wins in a row %d | max losses in a row %d' % (
        dd, D(dd_from).date() if dd_from else '-', D(dd_to).date() if dd_to else '-', uw_max, mcw, mcl))
    print('  stop size $: median %.2f, max %.2f | hold time h: median %.1f, max %.1f | costs $%.2f' % (
        statistics.median(r['risk'] for r in rs), max(r['risk'] for r in rs), statistics.median(hold), max(hold), 0.3 * n))
    for s, nm in ((1, 'longs'), (-1, 'shorts')):
        x = [r for r in rs if r['s'] == s]
        if x: print('  %-6s %3d trades, win rate %.1f%%, net $%.2f' % (nm, len(x), 100 * sum(r['win'] for r in x) / len(x), sum(r['usd'] for r in x)))


days = len({NYD[i] for i in range(i24, N)})
print('Period %s .. %s, %d trading days, %.2f trades/day' % (D(i24).date(), D(N - 1).date(), days, len(rows) / days))
block(rows, 'FULL 2.75 YEARS')
block([r for r in rows if r['i'] >= I0], 'LATEST 6 MONTHS (2026-04-05 .. 2026-10-04)')
print('=== BY YEAR')
for y in (2024, 2025, 2026):
    x = [r for r in rows if D(r['i']).year == y]
    eq = pk = dd = 0.0
    for r in x: eq += r['usd']; pk = max(pk, eq); dd = max(dd, pk - eq)
    print('  %d: %3d trades, win %.1f%%, net $%8.2f, PF %.2f, max DD $%.2f' % (y, len(x), 100 * sum(r['win'] for r in x) / len(x), eq,
          sum(r['usd'] for r in x if r['usd'] > 0) / -sum(r['usd'] for r in x if r['usd'] < 0), dd))
print('=== BY MONTH')
m = collections.OrderedDict()
for r in rows: m.setdefault(D(r['i']).strftime('%Y-%m'), []).append(r)
cum = 0.0
for k, v in m.items():
    net = sum(r['usd'] for r in v); cum += net
    print('  %s %2d trades %2d W %2d L  net $%+7.2f  running $%8.2f' % (k, len(v), sum(r['win'] for r in v), sum(not r['win'] for r in v), net, cum))
