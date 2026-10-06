"""V7.8 report: V7.6 with the fast-pullback, Ichimoku TK and RSI filters OFF (chosen for
profit, not win rate). Repaired data, costs $0.30/oz, one trade at a time, no break-even."""
import datetime, collections
from v76_lab import setups, T, N, I0, NYD
from v77_lab import simulate_be, sequential, summary, fmt
UTC = datetime.timezone.utc
CFG = dict(chop_max=0, pb_max=0, pe_after_pivot=True)
t24 = int(datetime.datetime(2024, 1, 2, tzinfo=UTC).timestamp() * 1000)
i24 = next(i for i in range(N) if T[i] >= t24)
base, _ = setups(CFG, i0=i24, i1=N - 1)
rows = sequential([simulate_be(r, 'none', 0) for r in base])
def d(i): return datetime.datetime.fromtimestamp(T[i] / 1000, UTC)
print('V7.8 full history %s .. %s' % (d(i24).date(), d(N - 1).date()))
print('  all         ', fmt(summary(rows)))
mcl = cur = 0
for r in rows:
    cur = 0 if r['win'] else cur + 1; mcl = max(mcl, cur)
print('  longest losing streak %d, largest stop $%.2f, median stop $%.2f' % (mcl, max(r['risk'] for r in rows), sorted(r['risk'] for r in rows)[len(rows) // 2]))
outc = collections.Counter(r['res'] for r in rows); print('  outcomes', dict(outc))
for lab, a, b in (('2024', 2024, 2024), ('2025', 2025, 2025), ('2026', 2026, 2026)):
    print('  %-12s' % lab, fmt(summary([r for r in rows if a <= d(r['i']).year <= b])))
print('  older (to 2026-04-02)', fmt(summary([r for r in rows if r['i'] < I0])))
print('  latest 6 months     ', fmt(summary([r for r in rows if r['i'] >= I0])))
tv0 = int(datetime.datetime(2026, 8, 9, tzinfo=UTC).timestamp() * 1000)
tvr = [r for r in rows if T[r['i']] >= tv0]
print('  TradingView window (9 Aug..)', fmt(summary(tvr)))
for r in tvr:
    print('     %s %s entry %.3f SL %.3f -> %s %+.2fR' % (d(r['i']).strftime('%Y-%m-%d %H:%M'), 'L' if r['s'] == 1 else 'S', r['entry'], r['stop'], r['res'], r['R']))
print('  by month (net R):')
m = collections.OrderedDict()
for r in rows: m.setdefault(d(r['i']).strftime('%Y-%m'), []).append(r)
neg = 0
for k, v in m.items():
    net = sum(x['R'] for x in v); neg += net < 0
    print('     %s n=%2d WR %5.1f%% net %+5.1fR' % (k, len(v), 100 * sum(x['win'] for x in v) / len(v), net))
print('  losing months: %d of %d' % (neg, len(m)))
