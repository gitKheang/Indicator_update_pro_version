"""V7.8 in dollars at a fixed lot (0.01 lot = 1 oz: a $1 move = $1), costs $0.30 per oz
round trip. Split = 50% at TP1, runner to TP2 (original stop). All-at-TP1 = whole
position closed at TP1 (what a broker allows at 0.01 lot, which cannot be split)."""
import datetime
from v76_lab import setups, T, H, L, N, I0
from v77_lab import simulate_be, sequential
UTC = datetime.timezone.utc
CFG = dict(chop_max=0, pb_max=0, pe_after_pivot=True)
t24 = int(datetime.datetime(2024, 1, 2, tzinfo=UTC).timestamp() * 1000)
i24 = next(i for i in range(N) if T[i] >= t24)
base, _ = setups(CFG, i0=i24, i1=N - 1)


def all_at_tp1(st, cost=0.3):
    i, s, stop, tp1 = st['i'], st['s'], st['stop'], st['tp1']
    j = i + 1; res = None
    while j < N:
        if (L[j] <= stop) if s == 1 else (H[j] >= stop): res = 'LOSS'; break
        if (H[j] >= tp1) if s == 1 else (L[j] <= tp1): res = 'TP1'; break
        j += 1
    out = dict(st); out['exit'] = j; out['res'] = res or 'OPEN'; out['win'] = res == 'TP1'
    out['usd'] = ((tp1 - st['entry']) * s if res == 'TP1' else -st['risk'] if res == 'LOSS' else 0.0) - cost
    return out


split = sequential([simulate_be(r, 'none', 0) for r in base])
for r in split: r['usd'] = r['R'] * r['risk']          # R already includes the $0.30 cost; x risk = $ for 1 oz
whole = sequential([all_at_tp1(r) for r in base])


def rep(rows, oz=1.0):
    if not rows: return 'n=0'
    eq = pk = dd = 0.0; cur = mcl = 0
    for r in rows:
        eq += r['usd'] * oz; pk = max(pk, eq); dd = max(dd, pk - eq)
        cur = 0 if r['win'] else cur + 1; mcl = max(mcl, cur)
    w = sum(r['win'] for r in rows); gp = sum(r['usd'] for r in rows if r['usd'] > 0); gl = -sum(r['usd'] for r in rows if r['usd'] < 0)
    return 'n=%3d WR %5.1f%% net $%+8.2f PF %.2f max DD $%7.2f avg win $%6.2f avg loss $%6.2f losing streak %d' % (
        len(rows), 100 * w / len(rows), eq, gp / gl if gl else 0, dd,
        oz * gp / max(1, sum(1 for r in rows if r['usd'] > 0)), oz * gl / max(1, sum(1 for r in rows if r['usd'] < 0)), mcl)


tv0 = int(datetime.datetime(2026, 8, 9, tzinfo=UTC).timestamp() * 1000)
for name, rows, oz in (('0.01 lot, 50% at TP1 (split 0.005)', split, 1.0), ('0.01 lot, all at TP1', whole, 1.0), ('0.02 lot, 50% at TP1 (0.01 + 0.01)', split, 2.0)):
    print('=====', name)
    for lab, sel in (('full 2024-01..2026-10', rows), ('2024', [r for r in rows if datetime.datetime.fromtimestamp(T[r['i']] / 1000, UTC).year == 2024]),
                     ('2025', [r for r in rows if datetime.datetime.fromtimestamp(T[r['i']] / 1000, UTC).year == 2025]),
                     ('2026', [r for r in rows if datetime.datetime.fromtimestamp(T[r['i']] / 1000, UTC).year == 2026]),
                     ('latest 6 months', [r for r in rows if r['i'] >= I0]), ('TradingView window (9 Aug..)', [r for r in rows if T[r['i']] >= tv0])):
        print('  %-30s %s' % (lab, rep(sel, oz)))
